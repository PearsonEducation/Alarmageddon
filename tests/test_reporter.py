from mocks import *
from alarmageddon.result import Success, Failure


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
