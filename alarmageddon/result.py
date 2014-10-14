""" Classes that represent possible results of running a test."""


class TestResult(object):
    """Base class representing the result of performing a validation.

    Contains the outcome information that Alarmageddon will publish.

    :param test_name: Name of the validation this result is associated with.
    :param validation: The :py:class:`~validation.Validation` this result is
      associated with.
    :param description: Default None. A description of the outcome of the
      validation. If the validation failed, this field is expected to not
      be None.
    :param time: Default None. How long the validation took to perform.

    """

    def __init__(self, test_name, validation,
                 description=None, time=None):
        self._test_name = test_name
        self._description = description

        self.time = time

        # if this is set, it will report the time to graphite and this
        # will be the label in graphite
        self.timer_name = validation.timer_name()
        self.priority = validation.priority

        self.validation = validation

    def test_name(self):
        """Returns the name of the test."""
        return self._test_name

    def description(self):
        """Returns additional descriptive text about the test.

        For Failures, description is required.

        """
        return self._description

    def is_failure(self):
        """Returns True if and only if this Result represents a failed test."""
        pass

    def __str__(self):
        return "Result: '%s', Description: '%s', Failure: %s, Priority: %s" % (
            self._test_name, self._description,
            self.is_failure(), self.validation.priority)

    def __repr__(self):
        return self.__str__()


class Failure(TestResult):
    """The result of a failed validation.

    `description` is required.

    """

    def __init__(self, test_name, validation, description, time=None):
        super(Failure, self).__init__(test_name, validation, description, time)

    def is_failure(self):
        """Returns True."""
        return True


class Success(TestResult):
    """The result of a successful validation."""

    def __init__(self, test_name, validation, description=None, time=None):
        super(Success, self).__init__(test_name, validation, description, time)

    def is_failure(self):
        """Returns False."""
        return False
