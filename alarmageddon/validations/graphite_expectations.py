"""Expectations that can be held against metrics collected in Graphite"""

from abc import abstractmethod

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = SECONDS_PER_MINUTE * 60
SECONDS_PER_DAY = SECONDS_PER_HOUR * 24


def _avg(readings):
    """Python 2.7 does not have an average function"""
    return sum(readings, 0.0) / len(readings)


def _delta_str(delta):
    """Convert a timedelta to a nice string.

    timedelta.__str__ prints out days and times awkwardly.

    """
    days, rem = divmod(delta.total_seconds(), SECONDS_PER_DAY)
    hours, rem = divmod(rem, SECONDS_PER_HOUR)
    minutes, rem = divmod(rem, SECONDS_PER_MINUTE)

    result = []

    if days:
        result.append('{0} day(s)'.format(days))
    if hours:
        result.append('{0} hour(s)'.format(hours))
    if minutes:
        result.append('{0} minute(s)'.format(minutes))
    return ', '.join(result)


class GraphiteExpectation(object):
    """An expectation placed on a list of Graphte readings"""
    def __init__(self, validation, name):
        self._validation = validation
        self._name = name

    @abstractmethod
    def validate(self, readings, time_range):
        """make sure the expectation is met"""
        pass

    def _validate(self, bad_readings, higher_values_are_worse):
        """Derived instances should call this method passing it any readings
        that were outside of specified parameters.

        """
        num_bad_readings = len(bad_readings)
        if num_bad_readings:
            bad_readings = list(set(bad_readings))
            bad_readings.sort(reverse=higher_values_are_worse)
            self._validation.fail(
                "In the last {0} there were {1} readings that " +
                "exceeded allowed parameters.  For example: {2}"
                .format(_delta_str(self._validation.time_range),
                        num_bad_readings,
                        ', '.join([str(x) for x in bad_readings[:20]])))

    def _validate_avg(self, average, is_bad_average):
        """Derived instances should call this method passing the average
        reading and whether or not that average was within specified
        parameters

        """
        if is_bad_average:
            self._validation.fail(
                "In the last {0} the average reading was {1}"
                .format(_delta_str(self._validation.time_range), average))


class GreaterThanExpectation(GraphiteExpectation):
    """Expect that a graphite metric is greater than a specified number"""
    def __init__(self, validation, lower_bound):
        super(GreaterThanExpectation, self).__init__(
              validation,
              "All values must be greater than {0}".format(lower_bound))
        self._lower_bound = lower_bound

    def validate(self, readings, time_range):
        self._validate([x for x in readings if x is not None and
                        x <= self._lower_bound], False)


class LessThanExpectation(GraphiteExpectation):
    """Expect that a graphite metric is less than than a specified number"""
    def __init__(self, validation, upper_bound):
        super(LessThanExpectation, self).__init__(
              validation,
              "All values must be less than {0}".format(upper_bound))
        self._upper_bound = upper_bound

    def validate(self, readings, time_range):
        self._validate([x for x in readings if x is not None and
                        x >= self._upper_bound], True)


class AverageGreaterThanExpectation(GraphiteExpectation):
    """Expect that the average of a graphite metric is greater than a
    specified number

    """
    def __init__(self, validation, lower_bound):
        super(AverageGreaterThanExpectation, self).__init__(
              validation,
              "Average of all values must be greater than {0}"
              .format(lower_bound))
        self._lower_bound = lower_bound

    def validate(self, readings, time_range):
        average = _avg([x for x in readings if x is not None])
        self._validate_avg(average, average <= self._lower_bound)


class AverageLessThanExpectation(GraphiteExpectation):
    """Expect that the average of a graphite metric is less than a
    specified number

    """
    def __init__(self, validation, upper_bound):
        super(AverageLessThanExpectation, self).__init__(
              validation,
              "Average of all values must be less than {0}"
              .format(upper_bound))
        self._upper_bound = upper_bound

    def validate(self, readings, time_range):
        average = _avg([x for x in readings if x is not None])
        self._validate_avg(average, average >= self._upper_bound)
