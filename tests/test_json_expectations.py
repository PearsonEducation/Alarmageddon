import pytest
import _pytest
from alarmageddon.validations.exceptions import ValidationFailure
from alarmageddon.validations.json_expectations import ExpectedJsonPredicate,\
    ExpectedJsonEquality, ExpectedJsonValueLessThan,\
    ExpectedJsonValueGreaterThan, _JsonQuery
from alarmageddon.validations.http import HttpValidation


class MockResponse:
    def __init__(self, json):
        self.j = json

    def json(self):
        return self.j


def test_json_equality():
    validation = HttpValidation.get("url")
    exp = ExpectedJsonEquality("path", 5)
    exp.validate_value(validation, 5, 5)


def test_json_wildcard_equality():
    validation = HttpValidation.get("url")
    exp = ExpectedJsonEquality("path[*]", [1, 2, 3])
    exp.validate_value(validation, 2, [1, 2, 3])


def test_json_equality_fails():
    validation = HttpValidation.get("url")
    exp = ExpectedJsonEquality("path", 5)
    with pytest.raises(ValidationFailure):
        exp.validate_value(validation, 5, 6)


def test_json_less_than():
    validation = HttpValidation.get("url")
    exp = ExpectedJsonValueLessThan("path", 5)
    exp.validate_value(validation, 5, 3)


def test_json_less_than_fails():
    validation = HttpValidation.get("url")
    exp = ExpectedJsonValueLessThan("path", 5)
    with pytest.raises(ValidationFailure):
        exp.validate_value(validation, 5, 5)


def test_json_greater_than():
    validation = HttpValidation.get("url")
    exp = ExpectedJsonValueGreaterThan("path", 5)
    exp.validate_value(validation, 5, 7)


def test_json_greater_than_fails():
    validation = HttpValidation.get("url")
    exp = ExpectedJsonValueGreaterThan("path", 5)
    with pytest.raises(ValidationFailure):
        exp.validate_value(validation, 5, 5)


def test_json_query_simple():
    json = {"abc": "123"}
    result = _JsonQuery.find(json, "abc")
    assert result == "123"


def test_json_query_nested():
    json = {"abc": "123", "another": {"nested": "entry"}, "alpha": "beta"}
    result = _JsonQuery.find(json, "another.nested")
    assert result == "entry"


def test_json_query_array():
    json = {"abc": "123", "another": {"nested": "entry"},
            "alpha": {"array": [1, 2, 3, 4]}}
    result = _JsonQuery.find(json, "alpha.array[2]")
    assert result == 3


def test_json_wildcard_query_array():
    json = {"abc": "123", "another": {"nested": "entry"},
            "alpha": {"array": [1, 2, 3, 4]}}
    result = _JsonQuery.find(json, "alpha.array[*]")
    assert result == [1, 2, 3, 4]


def test_validate():
    resp = MockResponse({"path": {"to": {"value": 1}}, "distractor": "value"})
    validation = HttpValidation.get("url")
    exp = ExpectedJsonEquality("path.to.value", 1)
    exp.validate(validation, resp)


def test_validate_fail():
    resp = MockResponse({"path": {"to": {"value": 1}}, "distractor": "value"})
    validation = HttpValidation.get("url")
    exp = ExpectedJsonEquality("path.to.value", 4)
    with pytest.raises(ValidationFailure):
        exp.validate(validation, resp)


def test_validate_bad_json():
    resp = MockResponse({"path": {"no": {"value": 1}}, "distractor": "value"})
    validation = HttpValidation.get("url")
    exp = ExpectedJsonEquality("path.to.value", 4)
    with pytest.raises(ValidationFailure):
        exp.validate(validation, resp)
