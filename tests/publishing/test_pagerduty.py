from alarmageddon.publishing.pagerduty import PagerDutyPublisher
import alarmageddon.publishing.pagerduty as pagerduty
from alarmageddon.result import Failure
from alarmageddon.result import Success
from alarmageddon.publishing.exceptions import PublishFailure
from alarmageddon.validations.validation import Validation, Priority
import alarmageddon.validations.ssh as ssh
import pytest
import requests

from mocks import MockRequestsCall


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


def test_str(no_post):
    pager = new_publisher()
    str(pager)


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


def failserver_monkeypatch(monkeypatch, fail_count):
    mock = MockRequestsCall(fail_first=fail_count)
    monkeypatch.setattr(requests, "post", mock.post_403)
    return mock


def test_publish_retries(monkeypatch):
    times_to_fail = 3
    mock = failserver_monkeypatch(monkeypatch, times_to_fail)
    pub = PagerDutyPublisher(mock.host, "token")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "message")
    pub.send(failure)
    assert mock.successes == 1


def test_publish_stops_retrying(monkeypatch):
    times_to_fail = 4
    mock = failserver_monkeypatch(monkeypatch, times_to_fail)
    pub = PagerDutyPublisher(mock.host, "token")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "message")
    with pytest.raises(PublishFailure):
        pub.send(failure)
    assert mock.successes == 0


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


def test_environment_name_is_present():
    environment = 'xanadu'

    pub = PagerDutyPublisher("url here", "token",
                             environment=environment)

    message = pub._construct_message(
        Failure("ternary computers not supported!",
                Validation("bit frobnication validation",
                           priority=Priority.CRITICAL),
                "unable to frobnicate bits!"))

    assert message.startswith("Failure in %s:" % environment)
