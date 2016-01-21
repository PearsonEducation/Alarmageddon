"""Support for publishing to Graphite."""

import statsd

from alarmageddon.publishing.publisher import Publisher

import logging

logger = logging.getLogger(__name__)


class GraphitePublisher(Publisher):
    """A Publisher that sends results to Graphite.

    Logs the number of successes and failures, and potentially logs how long a
    validation takes.

    :param host: The graphite host.
    :param port: The port that graphite is listening on.
    :param failed_tests_counter: Name of the graphite counter for failed tests.
    :param passed_tests_counter: Name of the graphite coutner for successful
      tests.
    :param prefix: Prefix applied to all graphite fields this publisher will
      write to.
    :param priority_threshold: Will publish validations of this priority or
      higher.
    :param environment: The environment that tests are being run in.

    """

    def __init__(self, host, port,
                 failed_tests_counter='failed',
                 passed_tests_counter='passed',
                 prefix='alarmageddon',
                 priority_threshold=None,
                 environment=None):
        if not host:
            raise ValueError("host parameter is required")

        logger.debug("Constructing publisher with host:{}, port:{}, failed counter:{},"
                "passed counter:{}, prefix:{}, priority_threshold:{}, environment:{}"
                .format(host, port, failed_tests_counter, passed_tests_counter,
                    prefix, priority_threshold, environment))

        Publisher.__init__(self, "Graphite",
                           priority_threshold=priority_threshold,
                           environment=environment)

        self._prefix = prefix
        self._host = host
        if port is not None:
            self._port = int(port)
        else:
            self._port = None

        self._failed_tests_counter = failed_tests_counter
        self._passed_tests_counter = passed_tests_counter

        self._graphite = statsd.StatsClient(
            host=self._host, prefix=self._prefix, port=self._port)

    def send(self, result):
        """Sends a result to Graphite.

        Logs the result as either a success or a failure. Additionally,
        logs how long the validation took, if a timer_name field is present on
        the result.

        """

        logger.debug("Checking if we should send {}".format(result))
        if self.will_publish(result):
            if result.is_failure():
                logger.info("Sending {} to {}".format(result,
                    self._failed_tests_counter))
                self._graphite.incr(self._failed_tests_counter)
            else:
                logger.info("Sending {} to {}".format(result,
                    self._passed_tests_counter))
                self._graphite.incr(self._passed_tests_counter)
            if result.timer_name:
                logger.info("Sending {} to {}".format(result,
                    result.timer_name))
                self._graphite.gauge(result.timer_name, result.time)

    def __repr__(self):
        return "Graphite Publisher: {}:{} with prefix {} ({}/{}). {}".format(
                    self._host, self._port, self._prefix,
                    self._failed_tests_counter, self._passed_tests_counter,
                    self._graphite)
