"""Exceptions related to publishing TestResults"""


class ValidationFailure(Exception):

    def __init__(self, cause):
        self.cause = cause

    def __str__(self):
        return repr(self.cause)


class EnrichmentFailure(Exception):
    """An exception thrown when the enrichment of a validation fails.

    :param publisher: The publisher the validation was enriched for.
    :param validation: The validation that failed to be enriched.
    :param values: The values that the validation was enriched with.

    """

    def __init__(self, publisher, validation, values):
        super(EnrichmentFailure, self).__init__(
            "Exception while enriching a Validation.")

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

    def __str__(self):
        return "Could not enrich {} with {} (for {}). Validation contained" +\
               "these enriched fields at time of failure:" +\
               "{}".format(self._validation,
                           self._values,
                           self._publisher,
                           self._valid_values)
