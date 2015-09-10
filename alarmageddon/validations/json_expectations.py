"""Expectations that can be held against some JSON text"""

import re

from alarmageddon.validations.http_expectations import ResponseExpectation


class ExpectedJsonPredicate(ResponseExpectation):
    """An expectation that an HTTP response will be JSON and have a property
    with a specified value.

    """
    def __init__(self, json_property_path, value):
        """Creates an expectation that an HTTP response will have a JSON
        payload with a property equal to the specified value.

        """
        ResponseExpectation.__init__(self)
        self.json_property_path = json_property_path
        self.value = value

    def validate(self, validation, response):
        """Validates that the HTTP response is JSON and that it contains a
        property (found by traversing self.json_property_path) equal to
        self.value

        """
        try:
            json = response.json()
        except ValueError:
            validation.fail(
                "response body was not JSON: {0}, Status Code: {1}"
                .format(response.text, response.status_code))
        actual_value = _JsonQuery.find(json, self.json_property_path)
        self.validate_value(validation, self.value, actual_value)

    def validate_value(self, validation, expected_value, actual_value):
        """validates a JSON value"""
        validation.fail("validate_value must be overriden by derived classes")

    def __repr__(self):
        return "{}: {} should be {}".format(type(self).__name__, self.json_property_path, self.value)


class ExpectedJsonEquality(ExpectedJsonPredicate):
    """expects that a JSON value is equal to a specified value"""
    def __init__(self, json_property_path, value):
        ExpectedJsonPredicate.__init__(self, json_property_path, value)

    def validate_value(self, validation, expected_value, actual_value):
        if not actual_value or actual_value != expected_value:
            validation.fail(
                "expected JSON property {0} to be '{1}', actual value: '{2}'"
                .format(self.json_property_path, expected_value, actual_value))

    def __repr__(self):
        return "{}: {} should be {}".format(type(self).__name__, self.json_property_path, self.value)


class ExpectedJsonValueLessThan(ExpectedJsonPredicate):
    """Expects that a numeric JSON value is less than a specified value"""
    def __init__(self, json_property_path, value):
        ExpectedJsonPredicate.__init__(self, json_property_path, value)

    def validate_value(self, validation, expected_value, actual_value):
        if actual_value is None:
            validation.fail(
                "missing JSON property {0}".format(self.json_property_path))
        elif float(actual_value) >= float(expected_value):
            validation.fail("expected JSON property {0} to be less " +
                            "than {1:.2f} but it was {2:.2f}"
                            .format(self.json_property_path,
                                    float(expected_value),
                                    float(actual_value)))

    def __repr__(self):
        return "{}: {} < {}".format(type(self).__name__, self.json_property_path, self.value)


class ExpectedJsonValueGreaterThan(ExpectedJsonPredicate):
    """Expects that a numeric JSON value is greater than a specified value"""
    def __init__(self, json_property_path, value):
        ExpectedJsonPredicate.__init__(self, json_property_path, value)

    def validate_value(self, validation, expected_value, actual_value):
        if actual_value is None:
            validation.fail(
                "missing JSON property {0}".format(self.json_property_path))
        elif float(actual_value) <= float(expected_value):
            validation.fail("expected JSON property {0} to be less " +
                            "than {1:.2f} but it was {2:.2f}"
                            .format(self.json_property_path,
                                    float(expected_value),
                                    float(actual_value)))

    def __repr__(self):
        return "{}: {} > {}".format(type(self).__name__, self.json_property_path, self.value)


INDEXED_ARRAY = re.compile(r"([^[]+)\[(\d+)\]")


class _JsonQuery(object):
    """Simple JSON query executor"""

    def __init__(self):
        pass

    # If your JSON response contains arrays, you can specify a particular
    # element of that array with the following syntax:
    #
    #   path.to.array[index]
    #
    # Example:
    #
    #   person.address[0]
    #
    # This regular expression helps match property paths using this syntax.

    @staticmethod
    def find(json, property_path):
        """Finds a property by traversing self.json_property_path"""
        root = json
        try:
            for path_elem in property_path.split('.'):
                match = INDEXED_ARRAY.search(path_elem)
                if match:
                    # We have an array property and the caller has specified
                    # which element of the array to validate against
                    name = match.group(1)
                    index = int(match.group(2))
                    root = root[name][index]
                else:
                    root = root[path_elem]
        except Exception:
            return None
        return root
