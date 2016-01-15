from alarmageddon.validations.http import HttpValidation
from alarmageddon.validations.validation import\
    Validation, Priority, GroupValidation
from alarmageddon.publishing.publisher import Publisher
import alarmageddon.run as run
import pytest
import time
from mocks import *


@pytest.fixture(params=[1, 4])
def processes(request):
    return request.param


#We need our mock functions to be pickleable, so define them here
def fail(x):
    raise RuntimeError


def slow_fail(x):
    time.sleep(2)
    raise RuntimeError


def slow_success(x):
    time.sleep(2)


def return_5():
    return 5


def test_run_works_without_config():
    name = "http://127.0.0.1/version"
    validation = HttpValidation.get(name)
    run.run_tests([validation])


def test_run_works_with_config():
    name = "http://127.0.0.1/version"
    validation = HttpValidation.get(name)
    run.run_tests([validation], config="config",
                  config_path="path", environment_name="stg")


def test_run_errors_without_valiations():
    with pytest.raises(ValueError):
        run.run_tests([], config="config")


def test_dry_run():
    validations = [Validation("low", Priority.LOW),
                   Validation("normal", Priority.NORMAL),
                   Validation("critical", Priority.CRITICAL)]

    publishers = [Publisher("low_pub", priority_threshold=Priority.LOW),
                  Publisher("norm_pub", priority_threshold=Priority.NORMAL),
                  Publisher("crit_pub", priority_threshold=Priority.CRITICAL)]

    associations = run._compute_dry_run(validations, publishers)
    lows = associations[publishers[0]]
    norms = associations[publishers[1]]
    crits = associations[publishers[2]]
    assert len(lows) == 3
    assert len(norms) == 2
    assert len(crits) == 1

    assert validations[0] in lows
    assert validations[1] in lows
    assert validations[2] in lows

    assert validations[0] not in norms
    assert validations[1] in norms
    assert validations[2] in norms

    assert validations[0] not in crits
    assert validations[1] not in crits
    assert validations[2] in crits


def test_run_validations_success(env, processes):
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validations = [Validation("success")]
    run._run_validations(validations, reporter, processes)
    assert publishers[0].successes == 1
    assert publishers[0].failures == 0


def construct_failing_validation(name, group=None):
    valid = Validation(name, group=group)
    valid.perform = fail
    return valid


def test_run_validations_failure(env, processes):
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validations = [construct_failing_validation("failed")]
    run._run_validations(validations, reporter, processes)
    assert publishers[0].successes == 0
    assert publishers[0].failures == 1


def test_run_validations_batch(env, processes):
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validations = [Validation("success"),
                   Validation("success"),
                   construct_failing_validation("failed")]
    run._run_validations(validations, reporter, processes)
    assert publishers[0].successes == 2
    assert publishers[0].failures == 1


def test_run_validations_group_failure(env, processes):
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validations = [Validation("success", group="a"),
                   GroupValidation("group a", "a", low_threshold=2),
                   construct_failing_validation("failed", group="a"),
                   construct_failing_validation("failed", group="a")]
    run._run_validations(validations, reporter, processes)
    assert publishers[0].successes == 1
    assert publishers[0].failures == 3


def test_run_validations_group_success(env, processes):
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validations = [Validation("success", group="a"),
                   GroupValidation("group a", "a", low_threshold=2),
                   Validation("success", group="a"),
                   construct_failing_validation("failed", group="a")]
    run._run_validations(validations, reporter, processes)
    assert publishers[0].successes == 3
    assert publishers[0].failures == 1


def test_run_validations_sets_time(env, processes):
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validation = Validation("success")
    validation.perform = slow_success
    run._run_validations([validation], reporter, processes)
    assert abs(reporter._reports[0].time - 2) <= 0.2


def test_run_validations_sets_time_on_failure(env, processes):
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validation = Validation("success")
    validation.perform = slow_fail
    run._run_validations([validation], reporter, processes)
    assert abs(reporter._reports[0].time - 2) <= 0.2


def test_run_validations_sets_time_with_function_if_available(env, processes):
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validation = Validation("success")
    validation.get_elapsed_time = return_5
    run._run_validations([validation], reporter, processes)
    assert reporter._reports[0].time == 5

def test_run_validations_enforces_global_timeout(env, processes):
    timeout = 5
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validation = NeverFinish("never finishes")
    run._run_validations([validation], reporter, processes, timeout)
    assert reporter._reports[0].is_failure()
    assert reporter._reports[0].time == timeout

def test_run_validations_without_timeout_hangs(env, processes):
    #this test just verifies NeverFail behaves as we expect
    timeout = 60
    reporter = env["reporter"]
    publishers = [MockPublisher()]
    reporter.publishers = publishers
    validation = NeverFinish("shouldn't finish but will")
    run._run_validations([validation], reporter, processes, timeout)
    assert not reporter._reports[0].is_failure()
