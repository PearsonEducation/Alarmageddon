"""Exceptions related to publishing TestResults"""


class PublishFailure(Exception):
    """An exception thrown when sending a test result to a publisher fails.

    :param publisher: The publisher that failed to publish.
    :param result: The result that failed to publish.

    """

    def __init__(self, publisher, result):
        Exception.__init__(self, "Exception while publishing a TestResult.")

        self._publisher = publisher
        self._result = result

    def result(self):
        """Returns the result that could not be published."""
        return self._result

    def publisher(self):
        """Returns the publisher that could not be published to."""
        return self._publisher

    def __repr__(self):
        return "Could not publish {0} to {1}".format(self._result,
                                                     self._publisher)


class EnrichmentFailure(Exception):
    """An exception thrown when the enrichment of a validation fails.

    :param publisher: The publisher the validation was enriched for.
    :param validation: The validation that failed to be enriched.
    :param values: The values that the validation was enriched with.

    """

    def __init__(self, publisher, validation, values):
        Exception.__init__(self, "Exception while enriching a Validation.")

        self._publisher = publisher
        self._validation = validation
        self._values = values

        try:
            self._valid_values = self._values._enriched_data
        except AttributeError:
            self._valid_values = "Missing enriched data field on validation"

    def validation(self):
        """Returns the validation that failed to enrich."""
        return self._validation

    def publisher(self):
        """Returns the publisher that the enrichment was for."""
        return self._publisher

    def values(self):
        """Returns the enrichment values."""
        return self._values

    def __repr__(self):
        return "Could not enrich {} with {} (for {}). Validation contained" +\
               "these enriched fields at time of failure:" +\
               "{}".format(self._validation,
                           self._values,
                           self._publisher,
                           self._valid_values)
