from alarmageddon.publishing import publisher
import alarmageddon.result as result
from alarmageddon.validations.validation import Validation, Priority
import pytest


@pytest.fixture(params=[
    result.TestResult("name", Validation("low", Priority.LOW)),
    result.TestResult("name", Validation("normal", Priority.NORMAL)),
    result.TestResult("name", Validation("crit", Priority.CRITICAL))])
def result(request):
    return request.param


def test_should_publish_high(result):
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    should = pub._should_publish(result)
    assert should == (result.priority == Priority.CRITICAL)


def test_should_publish_default(result):
    pub = publisher.Publisher(priority_threshold=Priority.NORMAL)
    should = pub._should_publish(result)
    assert should == (result.priority != Priority.LOW)


def test_should_publish_low(result):
    pub = publisher.Publisher(priority_threshold=Priority.LOW)
    should = pub._should_publish(result)
    assert should is True
