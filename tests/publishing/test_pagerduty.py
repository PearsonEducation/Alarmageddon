from pytest_localserver.http import WSGIServer
from alarmageddon.publishing.pagerduty import PagerDutyPublisher
import alarmageddon.publishing.pagerduty as pagerduty
from alarmageddon.result import Failure
from alarmageddon.result import Success
from alarmageddon.publishing.exceptions import PublishFailure
from alarmageddon.validations.validation import Validation, Priority
import alarmageddon.validations.ssh as ssh
import pytest


#sorry for the global variables, don't know how to store state in the server
hits = 0
cutoff = 3


def rate_limiting_app(environ, start_response):
    global hits
    global cutoff
    if hits == cutoff:
        status = '200 OK'
        hits = 0
    else:
        status = '403 FORBIDDEN'
        hits += 1
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return ["Slow down?!\n"]


def pytest_funcarg__ratelimited(request):
    """Defines the testserver funcarg"""
    server = WSGIServer(application=rate_limiting_app)
    server.start()
    request.addfinalizer(server.stop)
    return server


#Successes aren't sent, so monkeypatch out post and then
#only failures will notice
@pytest.fixture()
def no_post(monkeypatch):
    monkeypatch.delattr("requests.post")


def new_publisher():
    return PagerDutyPublisher(
        api_end_point="fakeurl",
        api_key="key")


def test_requires_api_end_point():
    with pytest.raises(ValueError):
        return PagerDutyPublisher(
            api_end_point="",
            api_key="key")


def test_requires_api_key():
    with pytest.raises(ValueError):
        return PagerDutyPublisher(
            api_end_point="fakeurl",
            api_key="")


def test_repr(no_post):
    pager = new_publisher()
    pager.__repr__()


def testSendSuccess(no_post):
    pager = new_publisher()
    v = Validation("low", priority=Priority.CRITICAL)
    success = Success("bar", v)
    pager.send(success)


def testSendFailure(no_post):
    pager = new_publisher()
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "unable to transmogrify")
    with pytest.raises(AttributeError):
        pager.send(failure)


def test_publish_failure(httpserver):
    httpserver.serve_content(code=300, headers={"content-type": "text/plain"},
                             content='{"mode":"NORMAL"}')
    pub = PagerDutyPublisher(httpserver.url, "token")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "message")
    with pytest.raises(PublishFailure):
        pub.send(failure)


def test_message_length_capped(httpserver):
    httpserver.serve_content(code=300, headers={"content-type": "text/plain"},
                             content='{"mode":"NORMAL"}')
    pub = PagerDutyPublisher(httpserver.url, "token")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "-"*2000)
    message = pub._construct_message(failure)
    assert len(message) == pagerduty.MAX_LEN


def test_publish_retries(ratelimited):
    global cutoff
    cutoff = 3
    global hits
    hits = 0
    pub = PagerDutyPublisher(ratelimited.url, "token")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "message")
    pub.send(failure)


def test_publish_stops_retrying(ratelimited):
    global cutoff
    cutoff = 4
    global hits
    hits = 0
    pub = PagerDutyPublisher(ratelimited.url, "token")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "message")
    with pytest.raises(PublishFailure):
        pub.send(failure)


def test_generate_id_reflexive():
    pub = PagerDutyPublisher("url", "token")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "unable to transmogrify")
    another = Failure("foo", v, "unable")
    assert pub._generate_id(failure) == pub._generate_id(another)


def test_generate_id_same_content():
    pub = PagerDutyPublisher("url", "token")
    v = Validation("low", priority=Priority.CRITICAL)
    v2 = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "unable to transmogrify")
    another = Failure("foo", v2, "to transmogrify")
    assert pub._generate_id(failure) == pub._generate_id(another)


def test_generate_id_different_result_same_valid():
    pub = PagerDutyPublisher("url", "token")
    v = Validation("low", priority=Priority.CRITICAL)
    v2 = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "unable to transmogrify")
    another = Success("foo", v2, "to transmogrify")
    assert pub._generate_id(failure) == pub._generate_id(another)


def test_generate_id_different_valid_different_id():
    pub = PagerDutyPublisher("url", "token")
    v = Validation("low", priority=Priority.CRITICAL)
    v2 = Validation("what", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "unable to transmogrify")
    another = Failure("foo", v2, "to transmogrify")
    assert pub._generate_id(failure) != pub._generate_id(another)

def ssh_key_file(tmpdir):
    tmp_file = tmpdir.join("secret.pem")
    tmp_file.write('secret')
    return tmp_file.strpath

def test_generate_id_consistency_ssh(tmpdir):

    pub = PagerDutyPublisher("url", "token")
    ssh_ctx = ssh.SshContext("ubuntu", ssh_key_file(tmpdir))
    ssh_ctx2 = ssh.SshContext("ubuntu", ssh_key_file(tmpdir))

    v = ssh.SshCommandValidation(ssh_ctx, "name", "cmd", hosts=["a fake host"])
    v2 = ssh.SshCommandValidation(ssh_ctx2, "name", "cmd", hosts=["a fake host"])

    failure = Failure("bar", v, "unable to transmogrify")
    another = Failure("foo", v2, "to transmogrify")

    assert pub._generate_id(failure) == pub._generate_id(another)

