"""Methods that support running tests"""

import time
import collections
import multiprocessing
import warnings

from alarmageddon.config import Config
from alarmageddon.reporter import Reporter
from alarmageddon.publishing import hipchat, pagerduty, graphite, junit
from alarmageddon.validations.validation import Priority
from alarmageddon.result import Success, Failure

from alarmageddon import banner


def load_config(config_path, environment_name):
    """Helper method for loading a :py:class:`~alarmageddon.config.Config`

    :param config_path: Path to the JSON configuration file.
    :param environment_name: The config environment to run Alarmageddon in.

    """
    return Config.from_file(config_path, environment_name)


def run_tests(validations, publishers=None, config_path=None,
              environment_name=None, config=None, dry_run=False,
              processes=1, print_banner=True):
    """Main entry point into Alarmageddon.

    Run the given validations and report them to given publishers.

    Either both `config_path` and `environment_name` should not be None,
    or `config` should not be None.

    :param validations: List of :py:class:`~.validation.Validation` objects
      that Alarmageddon will perform.
    :param publishers: List of :py:class:`~.publisher.Publisher`
      objects that Alarmageddon will publish validation results to.
    :param dry_run: When True, will prevent Alarmageddon from performing
      validations or publishing results, and instead will print which
      validations will be published by which publishers upon failure.
    :param processes: The number of worker processes to spawn. Does not run
      spawn additional processes if set to 1.
    :param print_banner: When True, print the Alarmageddon banner.

    .. deprecated:: 1.0.0
        These parameters are no longer used: *config_path*,
        *environment_name*, *config*.
        Configuration happens when constructing publishers instead.

    """

    if config is not None:
        warnings.warn("config keyword argument in run_tests is deprecated" + 
                      " and has no effect.", DeprecationWarning)
    if config_path is not None:
        warnings.warn("config_path keyword argument in run_tests is" + 
                      " deprecated and has no effect.", DeprecationWarning)
    if environment_name is not None:
        warnings.warn("environment_name keyword argument in run_tests is " + 
                      "deprecated and has no effect.", DeprecationWarning)

    

    publishers = publishers or []
    publishers.append(junit.JUnitPublisher("results.xml"))

    # We assume that if one is calling run_tests one actually wanted
    # to run some tests, not just fail silently
    if not validations:
        raise ValueError("run_tests expected non-empty list of validations," +
                         "got {} instead".format(validations))

    # Get rid of trailing c for byte-compiled .pyc files
    name = __file__
    if name[-1] == 'c':
        name = name[:-1]

    if print_banner:
        banner.print_banner(True)

    #always dry run. this will catch weird issues with enrichment
    do_dry_run(validations, publishers)

    if not dry_run:
        # run all of the tests
        _run_validations(validations, Reporter(publishers), processes)


def _run_validations(validations, reporter, processes):
    """ Run the given validations and publish the results

    Sort validations by order and then run them. All results are logged
    to the given reporter. Once everything has been run, the reporter
    will publish.

    :param validations: List of :py:class:`~.validation.Validation` objects
      that Alarmageddon will perform.
    :param publishers: :py:class:`~.reporter.Reporter` object that will
      collect validation results and then report those results to its
      publishers.
    :processes: The number of worker processes to spawn. Does not run
      spawn additional processes if set to 1.

    """
    if processes > 1:
        pool = multiprocessing.Pool(processes)
    else:
        pool = None
    order_dict = collections.defaultdict(list)
    for validation in validations:
        order_dict[validation.order].append(validation)

    ordered_validations = [l for _, l in sorted(order_dict.items())]

    group_failures = {}
    for validation in validations:
        if (validation.group is not None and
                validation.group not in group_failures):
            group_failures[validation.group] = []

    for order_set in ordered_validations:
        immutable_group_failures = dict(group_failures)
        wrapped = [(valid, immutable_group_failures) for valid in order_set]
        if pool is None:
            results = map(_parallel_perform, wrapped)
        else:
            #map can't handle unpickleable validations
            #asynch with get is so we can handle ctrl-c
            results = pool.map_async(_parallel_perform, wrapped).get(999999)
        for result in results:
            if result.is_failure() and result.validation.group is not None:
                group_failures[result.validation.group].append(result.description())
            reporter.collect(result)

    reporter.report()


def _parallel_perform(wrapped_info):
    return _perform(*wrapped_info)


def _perform(validation, immutable_group_failures):
    start = time.time()
    try:
        validation.perform(immutable_group_failures)
        result = Success(validation.name, validation,
                         time=time.time() - start)
    except Exception, e:
        result = Failure(validation.name, validation, str(e),
                         time=time.time() - start)
    try:
        result.time = validation.get_elapsed_time()
    except NotImplementedError:
        pass

    return result


def do_dry_run(validations, publishers):
    """Print which validations will be published by which publishers.

    Assume all validations fail and list the messages that would have
    been published.

    :param validations: List of :py:class:`~.validation.Validation` objects
      that Alarmageddon would perform.
    :param publishers: List of :py:class:`~.publisher.Publisher`
      objects that Alarmageddon would publish validation results to.

    """
    dry_run = _compute_dry_run(validations, publishers)
    publishers = dry_run.keys()
    for publisher in sorted(
            publishers, reverse=True,
            key=lambda x: x.priority_threshold):
        print("Publisher: %s (threshold: %s)" % (
            publisher.name(), Priority.string(publisher.priority_threshold)))
        for validation in dry_run[publisher]:
            print("   %s (priority: %s)" % (
                validation.name, Priority.string(validation.priority)))


def _compute_dry_run(validations, publishers):
    """Helper method for computing which validations are published where.

    Provides programmatic access to the association between publishers
    and validations. Return is of the form {publisher:[validation,...],...}.

    """
    associations = {}
    for publisher in publishers:
        associations[publisher] = []

        for validation in sorted(
                validations, reverse=True,
                key=lambda x: x.priority):
            test_result = Failure(validation.name, validation, "failure")
            if publisher.will_publish(test_result):
                associations[publisher].append(validation)
    return associations


def construct_publishers(config):
    """Construct the built-in publishers.

    :param config: Config object to construct the publishers from.

    """
    publishers = []
    try:
        publishers.append(hipchat.HipChatPublisher(
            config["hipchat_host"],
            config["hipchat_token"],
            config.environment_name(),
            config["hipchat_room"],
            Priority.NORMAL))
    except KeyError:
        pass
    try:
        publishers.append(pagerduty.PagerDutyPublisher(
            config["pagerduty_host"],
            config["pagerduty_token"],
            Priority.CRITICAL))
    except KeyError:
        pass
    try:
        publishers.append(graphite.GraphitePublisher(
            config["graphite_host"],
            config.get("graphite_port"),
            Priority.LOW))
    except KeyError:
        pass
    return publishers
