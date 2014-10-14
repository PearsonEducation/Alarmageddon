"""The common interface and tools for all Publishers"""


class Publisher(object):
    """Base class for all test result publishers.

    Publishers take test results and publish them to another service.

    :param name: The name of this publisher.
    :param priority_threshold: Will publish validations of this priority or
      higher.

    """

    def __init__(self, name=None, priority_threshold=None):
        self._name = name
        self.priority_threshold = priority_threshold

    def name(self):
        """Return the name of the publisher."""
        return self._name

    def send(self, result):
        """Publish a test result.

        :param result: The :py:class:`~.result.TestResult` of a test.

        """
        pass

    def send_batch(self, results):
        """Publish a collection of test results.

        Directly called by the :py:class:`~.reporter.Reporter` .

        :param result: An iterable of :py:class:`~.result.TestResult` objects.

        """
        for result in results:
            self.send(result)

    def __str__(self):
        return "Publisher: '{}'".format(self._name)

    def will_publish(self, result):
        """Determine if the publisher will publish the result

        To publish a result, the publisher must both be able to publish
        (_can_publish) and have its priority threshold met (_should_publish).

        :param result: The :py:class:`~.result.TestResult` of a test.


        """
        return self._should_publish(result) and self._can_publish(result)

    def _should_publish(self, result):
        """Determine if the publisher should publish the given result.

        Whether or not a result should be published depends on its priority.

        :param result: The :py:class:`~.result.TestResult` of a test.

        """
        priority = result.priority
        return self.priority_threshold <= priority

    def _can_publish(self, result):
        """Determine if the publisher can publish the given result.

        Whether or not a result can be published depends on if the publisher
        requires extra information from the validation belonging to the result,
        and whether or not that validation contains the needed information.

        :param result: The :py:class:`~.result.TestResult` of a test.

        """
        return True
