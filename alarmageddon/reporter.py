"""Reports test results to registered publishers."""

from .publishing.exceptions import PublishFailure
import logging

logger = logging.getLogger(__name__)

class ReportingFailure(Exception):
    """An exception that aggregates multiple PublishFailures.

    :param failures: A list of PublishFailures

    """

    def __init__(self, failures):
        Exception.__init__(self,
                "{} publishing failure(s): ".format(len(failures)) +
                ",".join((str(failure) for failure in failures)))

        self.failures = failures


class Reporter(object):
    """Class for collecting and sending results to publishers.

    :param publishers: List of
        :py:class:`~publisher.Publisher` objects to send results to.

    """

    def __init__(self, publishers):
        self.publishers = publishers
        self._reports = []

    def collect(self, result):
        """Construct a result from item and store for publishing.

        Called by pytest, through the Alarmageddon :py:class:`.plugin`.

        """
        logger.debug("Collecting {}".format(result))
        self._reports.append(result)

    def report(self):
        """Send reports to all publishers"""
        errors = []
        for publisher in self.publishers:
            logger.debug("Reporting to {}".format(publisher))
            try:
                publisher.send_batch(self._reports)
            except PublishFailure as e:
                #we don't want to block other publishers from publishing
                #so just keep going for now
                errors.append(e)

        if errors:
            raise ReportingFailure(errors)

    def __repr__(self):
        return "Reporter: {} {}".format(self.publishers, self._reports)
