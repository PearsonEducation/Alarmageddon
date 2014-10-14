"""Reports test results to registered publishers."""


class Reporter(object):
    """Class for sending constructing and results to publishers.

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
        self._reports.append(result)

    def report(self):
        """Send reports to all publishers"""
        for publisher in self.publishers:
            publisher.send_batch(self._reports)
