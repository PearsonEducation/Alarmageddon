from alarmageddon.publishing.teams import TeamsPublisher
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
    return TeamsPublisher(
        hook_url="fakeurl",
        environment="UnitTest")


def test_requires_hook_url():
    with pytest.raises(ValueError):
        TeamsPublisher(hook_url="",
                         environment="UnitTest")


def test_requires_environment():
    with pytest.raises(ValueError):
        TeamsPublisher(hook_url="fakeurl",
                         environment="")


def test_repr():
    teams = new_publisher()
    teams.__repr__()

def test_str():
    teams = new_publisher()
    str(teams)


def testSendSuccess(no_post, monkeypatch):
    teams = new_publisher()
    v = Validation("low", priority=Priority.LOW)
    success = Success("bar", v)
    teams.send(success)


def testSendFailure(no_post, monkeypatch):
    teams = new_publisher()
    v = Validation("low", priority=Priority.LOW)
    failure = Failure("foo", v, "unable to frobnicate")
    with pytest.raises(AttributeError):
        teams.send(failure)


def test_publish_failure(httpserver):
    httpserver.serve_content(code=500, headers={"content-type": "text/plain"},
                             content='{"mode":"NORMAL"}')
    pub = TeamsPublisher(httpserver.url, "env")
    v = Validation("low", priority=Priority.CRITICAL)
    failure = Failure("bar", v, "message")
    with pytest.raises(PublishFailure):
        pub.send(failure)
