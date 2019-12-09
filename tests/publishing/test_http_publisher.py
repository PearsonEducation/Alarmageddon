from alarmageddon.publishing.http import HttpPublisher
from alarmageddon.result import Failure
from alarmageddon.result import Success
from alarmageddon.publishing.exceptions import PublishFailure
from alarmageddon.validations.validation import Validation
from alarmageddon.validations.validation import Priority

from mocks import MockRequestsCall

import requests
import pytest


#==============================================================================
# Unit Tests
#==============================================================================

#------------------------------------------------------------------------------
# Construction Validation Tests
#------------------------------------------------------------------------------


def test_requires_success_url():
    with pytest.raises(ValueError):
        HttpPublisher(failure_url="failure")


def test_requires_failure_url():
    with pytest.raises(ValueError):
        HttpPublisher(success_url="success")


def test_requires_at_least_one_attempt():
    with pytest.raises(ValueError):
        HttpPublisher(url="both",
                      attempts=0)


def test_requires_method():
    with pytest.raises(ValueError):
        HttpPublisher(url="both",
                      attempts=1,
                      method=None)


def test_retry_after_seconds_is_positive():
    with pytest.raises(ValueError):
        HttpPublisher(url="both",
                      attempts=1,
                      retry_after_seconds=-43)


def test_success_and_failure_urls_are_set():
    publisher = HttpPublisher(url="both")

    assert publisher._success_url == "both"
    assert publisher._failure_url == "both"


def test_rep():
    publisher = HttpPublisher(url="both")
    publisher.__repr__()


def test_str():
    publisher = HttpPublisher(url="both")
    str(publisher)


def test_publish_success_if_success_url_is_given():
    publisher = HttpPublisher(success_url="success", failure_url="failure")

    assert publisher._publish_successes

#------------------------------------------------------------------------------
# Publishing to healthy servers
#------------------------------------------------------------------------------


def goodserver_monkeypatch(monkeypatch):
    mock = MockRequestsCall()
    monkeypatch.setattr(requests, "request", mock.request)
    return mock


def test_publishes_success(monkeypatch):
    mock = goodserver_monkeypatch(monkeypatch)
    publisher = HttpPublisher(name="Test", url=mock.host,
                              publish_successes=True)
    publisher.send(Success("success",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))
    assert mock.successes == 1


def test_does_not_publish_success(monkeypatch):
    mock = goodserver_monkeypatch(monkeypatch)
    publisher = HttpPublisher(name="Test", url=mock.host,
                              publish_successes=False)
    publisher.send(Success("success",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))
    assert mock.calls == 0


def test_publishes_success_to_correct_url(monkeypatch):
    mock = goodserver_monkeypatch(monkeypatch)
    publisher = HttpPublisher(name="Test",
                              success_url=mock.host + '/success',
                              failure_url=mock.host + '/failure',
                              publish_successes=True)
    publisher.send(Success("success",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))
    assert mock.successes == 1
    assert mock.last_url == '/success'


def test_publishes_failure_to_correct_url(monkeypatch):
    mock = goodserver_monkeypatch(monkeypatch)
    publisher = HttpPublisher(name="Test",
                              success_url=mock.host + '/success',
                              failure_url=mock.host + '/failure',
                              publish_successes=True)
    publisher.send(Failure("failure",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))
    assert mock.successes == 1
    assert mock.last_url == '/failure'

#------------------------------------------------------------------------------
# Publishing to failing servers
#------------------------------------------------------------------------------


def failserver_monkeypatch(monkeypatch, fail_count):
    mock = MockRequestsCall(fail_first=fail_count)
    monkeypatch.setattr(requests, "request", mock.request)
    return mock


def test_not_enough_attempts(monkeypatch):
    times_to_fail = 3
    mock = failserver_monkeypatch(monkeypatch, times_to_fail)

    publisher = HttpPublisher(name="Test", url=mock.host, attempts=3)

    with pytest.raises(PublishFailure):
        publisher.send(Failure("failure",
                               Validation("validation",
                                          priority=Priority.NORMAL),
                               "description"))
    mock.calls == 3
    mock.successes == 0


def test_enough_attempts(monkeypatch):
    times_to_fail = 2
    mock = failserver_monkeypatch(monkeypatch, times_to_fail)

    publisher = HttpPublisher(name="Test",
                              url=mock.host + '/failure', attempts=3)

    publisher.send(Failure("failure",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))

    assert mock.successes == 1
    assert mock.calls == 3
    assert mock.last_url == '/failure'


#------------------------------------------------------------------------------
# Publishing to slow servers
#------------------------------------------------------------------------------


def slowserver_monkeypatch(monkeypatch, response_time):
    mock = MockRequestsCall(response_time=response_time)
    monkeypatch.setattr(requests, "request", mock.request)
    return mock


def test_timeout_too_short(monkeypatch):
    sleep_time = 2
    mock = slowserver_monkeypatch(monkeypatch, sleep_time)

    publisher = HttpPublisher(name="Test",
                              url=mock.host,
                              timeout_seconds=1)

    with pytest.raises(PublishFailure):
        publisher.send(Failure("failure",
                               Validation("validation",
                                          priority=Priority.NORMAL),
                               "description"))


def test_timeout_too_short(monkeypatch):
    sleep_time = 2
    mock = slowserver_monkeypatch(monkeypatch, sleep_time)

    publisher = HttpPublisher(name="Test",
                              url=mock.host + '/failure',
                              timeout_seconds=3)

    publisher.send(Failure("failure",
                           Validation("validation",
                                      priority=Priority.NORMAL),
                           "description"))
    assert mock.successes == 1
    assert mock.last_url == '/failure'
