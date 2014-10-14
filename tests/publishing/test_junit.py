from alarmageddon.publishing.junit import JUnitPublisher
from alarmageddon.result import Failure
from alarmageddon.result import Success
from alarmageddon.validations.validation import Validation, Priority
import pytest


def test_requires_filename():
    with pytest.raises(ValueError):
        JUnitPublisher(None)


def test_send_fails():
    pub = JUnitPublisher("should_not_be_created.xml")
    v = Validation("low", priority=Priority.CRITICAL)
    success = Success("bar", v)
    with pytest.raises(NotImplementedError):
        pub.send(success)


def test_construct_tree_failure():
    pub = JUnitPublisher("should_not_be_created.xml")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "unable to transmogrify", time=30)
    tree = pub._construct_tree([failure]).getroot()
    assert tree.get("failures") == str(1)
    assert tree.get("tests") == str(1)
    assert float(tree.get("time")) == 30
    assert len(tree) == 1
    for element in tree:
        assert float(element.get("time")) == 30
        for sub in element:
            assert sub.text


def test_construct_tree_success():
    pub = JUnitPublisher("should_not_be_created.xml")
    v = Validation("low", priority=Priority.CRITICAL)
    success = Success("bar", v, time=30)
    tree = pub._construct_tree([success]).getroot()
    assert tree.get("failures") == str(0)
    assert tree.get("tests") == str(1)
    assert float(tree.get("time")) == 30
    assert len(tree) == 1
    for element in tree:
        assert float(element.get("time")) == 30
        assert len(element) == 0


def test_construct_tree_batch():
    pub = JUnitPublisher("should_not_be_created.xml")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "message", time=30)
    success = Success("foo", v, time=20)
    tree = pub._construct_tree([failure, failure, success]).getroot()
    assert tree.get("failures") == str(2)
    assert tree.get("tests") == str(3)
    assert float(tree.get("time")) == 80
    assert len(tree) == 3
