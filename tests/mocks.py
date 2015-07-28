import pytest
import alarmageddon.reporter
from alarmageddon.validations.validation import Priority, Validation
import time


class MockPublisher:
    def __init__(self):
        self.failures = 0
        self.successes = 0

    def send_batch(self, results):
        for result in results:
            self.send(result)

    def send(self, result):
        if result.is_failure():
            self.failures += 1
        else:
            self.successes += 1


class MockReporter(alarmageddon.reporter.Reporter):
    def __init__(self):
        super(MockReporter, self).__init__([])
        self.failures = 0
        self.successes = 0

    def collect(self, item, call):
        super(MockReporter, self).collect(item, call)
        if call.excinfo:
            self.failures += 1
        else:
            self.successes += 1


class MockCall:
    def __init__(self, start, stop, error):
        self.start = start
        self.stop = stop
        self.excinfo = None
        self.when = "call"
        if error:
            self.excinfo = type("", (), {})  # empty object
            self.excinfo.value = "error"


class MockItem:
    def __init__(self, name, funcargs):
        self.name = name
        self.funcargs = funcargs

    def __repr__(self):
        return self.name + "," + str(self.funcargs)


class MockConfig:
    def __init__(self, config):
        self.config = config

    def getoption(self, value):
        return self.config.get(value)


class MockRequest():
    def __init__(self, code, json):
        self.status_code = code
        self.payload = json

    def json(self):
        return self.payload


@pytest.fixture
def env():
    env = {}
    env['hipchat'] = MockPublisher()
    env['pager'] = MockPublisher()
    env['graphite'] = MockPublisher()
    env['reporter'] = alarmageddon.reporter.Reporter([env['hipchat'],
                                                      env['pager'],
                                                      env['graphite']])
    env["successful_call"] = MockCall(1, 10, False)
    env["failed_call"] = MockCall(1, 10, True)
    return env


@pytest.fixture(params=[MockCall(1, 10, False), MockCall(1, 10, True)])
def call(request):
    return request.param


@pytest.fixture(params=[Priority.LOW, Priority.NORMAL, Priority.CRITICAL])
def priority(request):
    return request.param

validations = [Validation("low", priority=Priority.LOW),
               Validation("med", priority=Priority.NORMAL),
               Validation("high", priority=Priority.CRITICAL),
               Validation("low", priority=Priority.LOW, timeout=0.1),
               Validation("med", priority=Priority.NORMAL, timeout=0.1),
               Validation("high", priority=Priority.CRITICAL, timeout=0.1),
               Validation("low", priority=Priority.LOW, timeout=10),
               Validation("med", priority=Priority.NORMAL, timeout=10),
               Validation("high", priority=Priority.CRITICAL, timeout=10)]


@pytest.fixture(params=validations)
def valid(request):
    return MockItem(request.param.name, {"test_info": (request.param, {})})

class NeverFinish(Validation):
    #don't actually never finish, that would be bad if we don't handle it well
    def perform(self, group_failures):
        time.sleep(15)
