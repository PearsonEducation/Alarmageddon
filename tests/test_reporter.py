from mocks import *
from alarmageddon.result import Success, Failure
from alarmageddon.reporter import ReportingFailure
from alarmageddon.publishing.exceptions import PublishFailure


class FailingPublisher:
    def send_batch(self, results):
        raise PublishFailure("publisher","NOT_HIDDEN")


def test_repr(env):
    reporter = env["reporter"]
    reporter.__repr__()

def test_reporter_correctly_sends_success(env, valid):
    reporter = env["reporter"]
    publishers = []
    for i in xrange(10):
        publishers.append(MockPublisher())
    reporter.publishers = publishers
    reporter.collect(Success("success", Validation("valid")))
    reporter.report()
    for pub in publishers:
        assert pub.successes == 1
        assert pub.failures == 0


def test_reporter_correctly_sends_failures(env, valid):
    reporter = env["reporter"]
    publishers = []
    for i in xrange(10):
        publishers.append(MockPublisher())
    reporter.publishers = publishers
    reporter.collect(Failure("failed", Validation("valid"), "why it failed"))
    reporter.report()
    for pub in publishers:
        assert pub.failures == 1
        assert pub.successes == 0


def test_reporter_correctly_batches(env):
    reporter = env["reporter"]
    publishers = []
    for i in xrange(10):
        publishers.append(MockPublisher())
    reporter.publishers = publishers
    reporter.collect(Failure("failed", Validation("valid"), "why it failed"))
    reporter.collect(Failure("failed2", Validation("valid"), "why it failed"))
    reporter.collect(Success("success", Validation("valid")))
    reporter.report()
    for pub in publishers:
        assert pub.failures == 2
        assert pub.successes == 1


def test_reporter_runs_all_publishers_before_raising(env, valid):
    reporter = env["reporter"]
    bad_pub = 5
    publishers = []
    for i in xrange(10):
        publishers.append(MockPublisher())
    publishers[bad_pub] = FailingPublisher()
    reporter.publishers = publishers
    reporter.collect(Success("success", Validation("valid")))
    with pytest.raises(ReportingFailure):
        reporter.report()
    for i,pub in enumerate(publishers):
        if i != bad_pub:
            assert pub.successes == 1
            assert pub.failures == 0

def test_reporter_shows_publish_error_info(env):
    reporter = env["reporter"]
    publishers = [FailingPublisher()]
    reporter.publishers = publishers
    reporter.collect(Success("success", Validation("valid")))
    try:
        reporter.report()
    except ReportingFailure,e:
        assert "NOT_HIDDEN" in str(e) 
