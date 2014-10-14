"""Classes used by all kinds of Validations."""

from exceptions import EnrichmentFailure, ValidationFailure
GLOBAL_NAMESPACE = "GLOBAL"


class Priority(object):
    """Priority levels that indicate how severe a validation failure is.

    Validations have a priority that publishers use to determine whether
    or not to publish in the case of failure.
    """
    # If a LOW priority Validation fails, the failure be recorded for posterity
    # but not reported to a human (e.g. logged in continuous integration server
    # job history but not reported to IRC/HipChat)
    LOW = 1

    # If a NORMAL priority Validation fails, the failure should be reported to
    # a human but it should not wake up a human (e.g. send a notification to
    # IRC/HipChat, Graphite).  Additionally the failure should be logged for
    # posterity as in the case of LOW priority failures.
    NORMAL = 2

    # If a CRITICAL priority Validation fails, a human should be woken up
    # (e.g. create an incident in PagerDuty).  Additionally the failure should
    # be more politely reported to humans (e.g. via IRC/HipChat, Graphite,
    # etc.) and recorded for posterity as in the case of NORMAL and LOW
    # priority failures.
    CRITICAL = 3

    @staticmethod
    def string(priority):
        """Return the name of the priority (e.g. normal, low, critical)"""
        if priority == Priority.NORMAL:
            return "normal"
        elif priority == Priority.LOW:
            return "low"
        elif priority == Priority.CRITICAL:
            return "critical"
        else:
            return "unknown priority: {0}".format(priority)


class Validation(object):
    """The base class for validations.

    The base class for all classes that represent some form of validation
    (e.g. some expected system property that can be checked and categorized as
    either passing or failing).  Examples of Validations include: an HTTP
    service returning an expected result in a specified amount of time, an
    Upstart process on a Linux server is in the running state, a Message
    Queue's queue length is lower than a maximum value.

    :param name: The name of this validation.
    :param priority: The :py:class:`.Priority` level of this validation.
    :param timeout: How long this validation can take before being considered
      a failure. If None, then the validation will never be considered a
      failure due to timing out.
    :param group: The group this validation belongs to.

    """
    def __init__(self, name, priority=Priority.NORMAL,
                 timeout=None, group=None):
        """Creates a Validation object with the supplied name and priority.

        Arguments:
        name -- The name of this Validation

        Keyword Arguments
        priority -- The priority of this Validation.
        timeout -- If this validation takes longer than this many seconds,
                   it will be considered a failure.
        group -- The group this validation belongs to.

        """
        self.name = name
        self.priority = priority
        self.timeout = timeout

        self.group = group

        #this should never be directly manipulated without very good reason
        #it is used to store extra data for publishers, and the primary
        #method of interaction should be the enric and get_enriched
        #functions in publisher.py
        self._enriched_data = {GLOBAL_NAMESPACE: {}}

        #determines the partial ordering of the validations
        #Alarmageddon guarantees that all Validations with lower order than
        #this Validation's order will run before this Validation runs.
        #most validations have no reason to change this
        self.order = 0

    def perform(self, group_failures):
        """Perform the validation.

        If the validation fails, call self.fail passing it the reason for
        the failure.

        :param kwargs: A dictionary containing information from the whole
          Alarmageddon run.

        """
        pass

    def fail(self, reason):
        """Log the validation as a failure with pytest.

        :param reason: The cause of the failure.
        :param stack_track: Whether or not to include a stack trace in the
          result.

        """
        raise ValidationFailure(reason)

    def get_elapsed_time(self):
        """Return the amount of time this validation took.

        The :py:class:`.reporter.Reporter` will check here before using
        the call time.

        Overwrite this if you need more precise timing than pytest gives -
        eg, if you want to know how long an http request took, as opposed
        to how long that whole test took to execute.

        This function should return a number, not a timedelta.

        """
        raise NotImplementedError

    def __str__(self):
        return "Validation {{ name: '{0}' priority: '{1}' timeout: {2}}}"\
                .format(self.name,
                        Priority.string(self.priority),
                        self.timeout)

    def timer_name(self):
        """Return the name of the timer that corresponds to this validation.

        Used to indicate where a publisher should log the time taken.

        """
        return None

    def enrich(self, publisher, values, force_namespace=False):
        """Adds publisher-specific information to the validation.

        Override at your own peril! Publishers are expected to assume the
        standard behavior from this function.

        :param publisher: The publisher to add enriched data for.
        :param values: The enriched data to add to this validation.
        :param force_namespace: If True, will never add the data to the global
          namespace.

        """

        namespace = str(type(publisher))
        enriched = self._enriched_data
        if namespace in enriched:
            raise EnrichmentFailure(publisher, self, values)
        enriched[namespace] = {}
        for key, value in values.iteritems():
            if force_namespace:
                enriched[namespace][key] = value
            else:
                if key not in enriched[GLOBAL_NAMESPACE]:
                    enriched[GLOBAL_NAMESPACE][key] = value
                else:
                    enriched[namespace][key] = value
        return self

    def get_enriched(self, publisher, force_namespace=False):
        """Retrieve the appropriate publisher-specific data.

        Will retrieve all global enriched data along with any extra
        publisher specific data. This means that if you enrich a
        validation for more than one publisher, this function may
        return a superset of the enriched data for a given publisher.

        Override at your own peril! Publishers are expected to assume the
        standard behavior from this function.

        :param publisher: The publisher to retrieve enriched data for.
        :param force_namespace: If True, will not retrieve global enrichments.

        """

        namespace = str(type(publisher))
        enriched = self._enriched_data

        #copy global
        data = {}
        if not force_namespace:
            data.update(enriched[GLOBAL_NAMESPACE])
        try:
            data.update(enriched[namespace])
        except KeyError:
            pass

        return data


class GroupValidation(Validation):
    """A validation that checks the number of failures in a test group.

    The priority level will be set dynamically based on the number of
    failures and the supplied thresholds.

    :param name: The name of this validation.
    :param checked_group: The name of the group this validation will check.
    :param low_threshold: The number of failures at which this validation
      will itself fail.
    :param normal_threshold: The number of failures at which this validation
      will become NORMAL priority.
    :param critical_threshold: The number of failures at which this validation
      will become CRITICAL priority.
    :param order: This validation will run after all validations of lower
      order have run. Used when order matters - eg, creating a GroupValidation
      for a group of GroupValidations.
    :param group: The group this validation belongs to.

    """

    def __init__(self, name, checked_group, low_threshold=float("inf"),
                 normal_threshold=float("inf"),
                 critical_threshold=float("inf"),
                 order=1, group=None):

        super(GroupValidation, self).__init__(
            name, priority=Priority.LOW, timeout=None, group=group)

        self.low_threshold = low_threshold
        self.normal_threshold = normal_threshold
        self.critical_threshold = critical_threshold
        self._clean_thresholds()
        self.order = order
        self.checked_group = checked_group

    def _clean_thresholds(self):
        """Ensure that the thresholds are consistent.

        `low_threshold` must be less than `normal_threshold` which must be
        less than `critical_threhsold`. If necessary, this function will alter
        the thresholds to ensure this condition is met.

        """
        if self.normal_threshold > self.critical_threshold:
            self.normal_threshold = self.critical_threshold
        if self.low_threshold > self.normal_threshold:
            self.low_threshold = self.normal_threshold

    def perform(self, group_failures):
        """Perform the validation."""
        failures = len(group_failures[self.checked_group])
        messages = group_failures[self.checked_group]
        if failures >= self.low_threshold:
            self._set_priority(failures)
            self.fail("Group {0} had {1} failures! \n{2}".format(
                self.checked_group, failures, messages))

    def _set_priority(self, failures):
        """Set priority of this validation based on the number of failures.

        :param failures: The number of failures in this validation's checked
          group.

        """
        if failures >= self.critical_threshold:
            self.priority = Priority.CRITICAL
        elif failures >= self.normal_threshold:
            self.priority = Priority.NORMAL
        else:
            self.priority = Priority.LOW
