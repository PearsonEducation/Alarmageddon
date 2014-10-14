from alarmageddon.result import Failure, Success
from alarmageddon.validations.validation import Validation, Priority

#change the name here so pytest doesn't notice it
from alarmageddon.result import TestResult as ValidResult


def test_failures_are_failures():
    v = Validation("low", priority=Priority.LOW)
    f = Failure("name", v, "desc")
    assert f.is_failure()


def test_successes_are_not_failures():
    v = Validation("low", priority=Priority.LOW)
    s = Success("name", v, "desc")
    assert not s.is_failure()


def test_result_str_works():
    v = Validation("low", priority=Priority.LOW)
    s = ValidResult("name", v, description="desc")
    s.__str__()


def test_result_repr_works():
    v = Validation("low", priority=Priority.LOW)
    s = ValidResult("name", v, description="desc")
    s.__repr__()
