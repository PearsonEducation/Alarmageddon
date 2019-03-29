from alarmageddon.publishing.graphite import GraphitePublisher
from alarmageddon.result import Failure
from alarmageddon.result import Success
import pytest
from collections import Counter
from alarmageddon.validations.validation import Validation, Priority


@pytest.fixture(autouse=True)
def no_statsd(monkeypatch):
    monkeypatch.setattr("statsd.StatsClient", lambda host, port, prefix: None)


class MockGraphite():
    def __init__(self):
        self.counter = Counter()

    def incr(self, name):
        self.counter[name] += 1


def new_publisher():
    pub = GraphitePublisher(
        host="fakeurl",
        port=8085
    )

    pub._graphite = MockGraphite()

    return pub


def test_requires_host():
    with pytest.raises(ValueError):
        GraphitePublisher(host=None, port=None)

def test_repr():
    graphite = new_publisher()
    graphite.__repr__()

def test_str():
    graphite = new_publisher()
    str(graphite)

def test_send_success():
    graphite = new_publisher()
    v = Validation("low", priority=Priority.LOW)
    success = Success("bar", v)
    graphite.send(success)
    assert graphite._graphite.counter["passed"] == 1
    assert graphite._graphite.counter["failed"] == 0


def testSendFailure():
    graphite = new_publisher()
    v = Validation("low", priority=Priority.LOW)
    failure = Failure("foo", v, "unable to frobnicate")
    graphite.send(failure)
    assert graphite._graphite.counter["passed"] == 0
    assert graphite._graphite.counter["failed"] == 1
