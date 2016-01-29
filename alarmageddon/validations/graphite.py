"""Classes that support validation of metrics collected by Graphite"""

import datetime
import requests

from alarmageddon.validations.validation import Validation

from alarmageddon.validations.graphite_expectations import \
    LessThanExpectation, \
    GreaterThanExpectation, \
    AverageLessThanExpectation, \
    AverageGreaterThanExpectation

import logging

logger = logging.getLogger(__name__)


class GraphiteContext(object):
    """Create one of these and then pass it to all of the
    GraphiteValidation objects you create.

    """
    def __init__(self, graphite_host):
        """Creates a GraphiteContext object"""
        self._graphite_host = graphite_host

    def get_graphite_host(self):
        """returns the Graphite host name"""
        return self._graphite_host

    def __repr__(self):
        return "{}: {}".format(type(self).__name__, self._graphite_host)


class GraphiteValidation(Validation):
    """A Validation that queries Graphite for data and then validates any
    defined expecations against that data.

    """
    def __init__(self, context, name, metric_name,
                 time_range=datetime.timedelta(hours=1),
                 **kwargs):
        """Creates a GraphiteValidation object"""
        Validation.__init__(self, name, **kwargs)
        self._context = context
        self.time_range = time_range
        self.metric_name = metric_name
        self._expectations = []

    def perform(self, group_failures):
        """Perform the validation and propagate any failures to reporters"""
        readings = self._get_readings()

        if len(readings) == 0:
            self.fail("No readings for {0} were found"
                      .format(self.metric_name))

        for expectation in self._expectations:
            expectation.validate(readings, self.time_range)

    def fail(self, reason):
        """Causes this GraphiteValidation to fail with the given reason."""
        Validation.fail(self, reason)

    def expect_average_in_range(self, lower_bound, upper_bound):
        """The average reading of the specified time range should fall between
        the upper and lower bound

        """
        self.expect_average_less_than(upper_bound)
        self.expect_average_greater_than(lower_bound)
        return self

    def expect_in_range(self, lower_bound, upper_bound):
        """All readings in the specified time range should fall between the
        upper and lower bound

        """
        self.expect_greater_than(lower_bound)
        self.expect_less_than(upper_bound)
        return self

    def expect_less_than(self, upper_bound):
        """All readings in the specified time range should fall below the
        upper bound

        """
        self._expectations.append(LessThanExpectation(self, upper_bound))
        return self

    def expect_average_less_than(self, upper_bound):
        """The average reading of the specified time range should fall below
        the upper bound

        """
        self._expectations.append(AverageLessThanExpectation(self,
                                                             upper_bound))
        return self

    def expect_greater_than(self, lower_bound):
        """All readings in the specified time range should fall above the
        lower bound

        """
        self._expectations.append(GreaterThanExpectation(self, lower_bound))
        return self

    def expect_average_greater_than(self, lower_bound):
        """The average reading of the specified time range should fall above
        the lower bound

        """
        self._expectations.append(
            AverageGreaterThanExpectation(self, lower_bound))

        return self

    def _build_url(self):
        """Builds the URL for retrieving Graphite data for a metric"""
        return "{0}/render/?target={1}&format=raw&from=-{2}seconds"\
            .format(self._context.get_graphite_host(),
                    self.metric_name,
                    self.time_range.total_seconds())

    def _get_readings(self):
        """Return a list of readings for the metric as a list of floats and/or
        None values.  A None reading means no data was sent to
        Graphite for that time period.

        """
        url = self._build_url()
        logger.debug("Hitting graphite server at {}".format(url))
        resp = requests.get(url)
        logger.debug("Graphite response: {}".format(resp))
        if resp.status_code < 200 or resp.status_code >= 300:
            self.fail(("Could not get data from Graphite.  " +
                       "URL: {0}, Metric: {1}, Status Code: {2}," +
                       "Response: {3}").format(url, self.metric_name,
                                               resp.status_code, resp.text))
        chunks = resp.text.strip().split('|')
        if len(chunks) == 2:
            readings = []
            for tok in chunks[1].split(','):
                if tok == u'None':
                    readings.append(None)
                else:
                    readings.append(float(tok))
            return readings
        else:
            self.fail("Unexpected response from Graphite: {0}"
                      .format(resp.text))
