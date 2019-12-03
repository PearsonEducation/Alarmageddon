from alarmageddon.publishing.http import HttpPublisher
from alarmageddon.result import Failure
from alarmageddon.result import Success
from alarmageddon.publishing.exceptions import PublishFailure
from alarmageddon.validations.validation import Validation
from alarmageddon.validations.validation import Priority

import time
import pytest

from pytest_localserver.http import WSGIServer

global request_sent
global requested_url

#==============================================================================
# A well-behaved, always succeeding HTTP Server
#==============================================================================


def good_app(environ, start_response):
    global request_sent
    request_sent = True

    global requested_url
    requested_url = environ['PATH_INFO']

    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)

    return ["Success".encode('utf-8')]


@pytest.fixture()
def goodserver(request):
    """Defines the testserver funcarg"""
    global request_sent
    request_sent = False

    global requested_url
    requested_url = None

    server = WSGIServer(application=good_app)
    server.start()
    request.addfinalizer(server.stop)
    return server

#==============================================================================
# A flaky HTTP Server that fails several times before it succeeds
#==============================================================================

global times_to_fail


def failing_app(environ, start_response):
    global times_to_fail
    if times_to_fail <= 0:
        global request_sent
        request_sent = True

        global requested_url
        requested_url = environ['PATH_INFO']

        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return ["Success".encode('utf-8')]
    else:
        times_to_fail = times_to_fail - 1
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return ["Failure".encode('utf-8')]


@pytest.fixture()
def failingserver(request):
    """Defines the testserver funcarg"""
    global request_sent
    request_sent = False

    global requested_url
    requested_url = None

    server = WSGIServer(application=failing_app)
    server.start()
    request.addfinalizer(server.stop)
    return server

#==============================================================================
# A slow HTTP Server that sleeps for a while before succeeding
#==============================================================================

global sleep_time


def slow_app(environ, start_response):
    global request_sent
    request_sent = True

    global requested_url
    requested_url = environ['PATH_INFO']

    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    time.sleep(sleep_time)
    start_response(status, response_headers)
    return ["Success".encode('utf-8')]


@pytest.fixture()
def slowserver(request):
    global request_sent
    request_sent = False

    global requested_url
    requested_url = None

    server = WSGIServer(application=slow_app)
    server.start()
    request.addfinalizer(server.stop)
    return server

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


def test_publishes_success(goodserver):
    publisher = HttpPublisher(name="Test", url=goodserver.url,
                              publish_successes=True)
    publisher.send(Success("success",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))
    assert request_sent


def test_does_not_publish_success(goodserver):
    publisher = HttpPublisher(name="Test", url=goodserver.url,
                              publish_successes=False)
    publisher.send(Success("success",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))
    assert not request_sent


def test_publishes_success_to_correct_url(goodserver):
    publisher = HttpPublisher(name="Test",
                              success_url=goodserver.url + '/success',
                              failure_url=goodserver.url + '/failure',
                              publish_successes=True)
    publisher.send(Success("success",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))
    assert request_sent
    assert requested_url == '/success'


def test_publishes_failure_to_correct_url(goodserver):
    publisher = HttpPublisher(name="Test",
                              success_url=goodserver.url + '/success',
                              failure_url=goodserver.url + '/failure',
                              publish_successes=True)
    publisher.send(Failure("failure",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))
    assert request_sent
    assert requested_url == '/failure'

#------------------------------------------------------------------------------
# Publishing to failing servers
#------------------------------------------------------------------------------


def test_not_enough_attempts(failingserver):
    global times_to_fail
    times_to_fail = 3

    publisher = HttpPublisher(name="Test", url=failingserver.url, attempts=3)

    with pytest.raises(PublishFailure):
        publisher.send(Failure("failure",
                               Validation("validation",
                                          priority=Priority.NORMAL),
                               "description"))


def test_enough_attempts(failingserver):
    global times_to_fail
    times_to_fail = 2

    publisher = HttpPublisher(name="Test",
                              url=failingserver.url + '/failure', attempts=3)

    publisher.send(Failure("failure",
                           Validation("validation", priority=Priority.NORMAL),
                           "description"))

    assert request_sent
    assert requested_url == '/failure'

#------------------------------------------------------------------------------
# Publishing to slow servers
#------------------------------------------------------------------------------


def test_timeout_too_short(slowserver):
    global sleep_time
    sleep_time = 2

    publisher = HttpPublisher(name="Test",
                              url=slowserver.url,
                              timeout_seconds=1)

    with pytest.raises(PublishFailure):
        publisher.send(Failure("failure",
                               Validation("validation",
                                          priority=Priority.NORMAL),
                               "description"))


def test_timeout_too_short(slowserver):
    global sleep_time
    sleep_time = 2

    publisher = HttpPublisher(name="Test",
                              url=slowserver.url + '/failure',
                              timeout_seconds=3)

    publisher.send(Failure("failure",
                           Validation("validation",
                                      priority=Priority.NORMAL),
                           "description"))
    assert request_sent
    assert requested_url == '/failure'
