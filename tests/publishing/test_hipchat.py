from alarmageddon.publishing.hipchat import HipChatPublisher
from alarmageddon.result import Failure
from alarmageddon.result import Success
from alarmageddon.publishing.exceptions import PublishFailure
from alarmageddon.validations.validation import Validation, Priority
import pytest


#Successes aren't sent, so monkeypatch out post and then
#only failures should notice
@pytest.fixture
def no_post(monkeypatch):
    monkeypatch.delattr("requests.post")


def new_publisher():
    return HipChatPublisher(
        api_end_point="fakeurl",
        api_token="faketoken",
        environment="UnitTest",
        room_name="Alarmageddon")


def test_requires_api_end_point():
    with pytest.raises(ValueError):
        HipChatPublisher(api_end_point="",
                         api_token="faketoken",
                         environment="UnitTest",
                         room_name="Alarmageddon")


def test_requires_api_token():
    with pytest.raises(ValueError):
        HipChatPublisher(api_end_point="fakeurl",
                         api_token="",
                         environment="UnitTest",
                         room_name="Alarmageddon")


def test_requires_environment():
    with pytest.raises(ValueError):
        HipChatPublisher(api_end_point="fakeurl",
                         api_token="token",
                         environment="",
                         room_name="Alarmageddon")


def test_requires_room():
    with pytest.raises(ValueError):
        HipChatPublisher(api_end_point="fakeurl",
                         api_token="token",
                         environment="UnitTest",
                         room_name="")


def test_repr():
    hipchat = new_publisher()
    hipchat.__repr__()


def testSendSuccess(no_post, monkeypatch):
    hipchat = new_publisher()
    v = Validation("low", priority=Priority.LOW)
    success = Success("bar", v)
    hipchat.send(success)


def testSendFailure(no_post, monkeypatch):
    hipchat = new_publisher()
    v = Validation("low", priority=Priority.LOW)
    failure = Failure("foo", v, "unable to frobnicate")
    with pytest.raises(AttributeError):
        hipchat.send(failure)


def test_publish_failure(httpserver):
    httpserver.serve_content(code=300, headers={"content-type": "text/plain"},
                             content='{"mode":"NORMAL"}')
    pub = HipChatPublisher(httpserver.url, "token", "env", "room")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "message")
    with pytest.raises(PublishFailure):
        pub.send(failure)
