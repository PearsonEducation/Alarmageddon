import alarmageddon.validations.ssh as ssh
from alarmageddon.validations.exceptions import ValidationFailure
import pytest
import _pytest
import os
from validation_mocks import get_mock_key_file, get_mock_ssh_text

hosts = ["a fake host"]


#note that while we're technically monkey patching ssh, it's actually
#a fabric command that we're overwriting
def test_ssh_works(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    (ssh.SshCommandValidation(ssh_ctx, "name", "cmd", hosts=hosts)
     .perform({}))


def test_ssh_expected_0_by_default(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 1))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(ValidationFailure):
        (ssh.SshCommandValidation(ssh_ctx, "name", "cmd", hosts=hosts)
         .perform({}))


def test_ssh_expected_return_code(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 1))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    (ssh.SshCommandValidation(ssh_ctx, "name", "cmd", hosts=hosts)
     .expect_exit_code(1)
     .perform({}))


def test_ssh_expected_rejects_0_when_changed(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(ValidationFailure):
        (ssh.SshCommandValidation(ssh_ctx, "name", "cmd", hosts=hosts)
         .expect_exit_code(1)
         .perform({}))


def test_load_average_disallows_generic_expections(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(NotImplementedError):
        (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
         .expect_exit_code(1)
         .perform({}))


def test_max_load_average(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run", lambda x: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
     .expect_max_1_minute_load(40)
     .expect_max_5_minute_load(20)
     .expect_max_15_minute_load(10)
     .perform({}))


def test_max_load_correctly_fails_1_minute(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 40.09, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run", lambda x: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    with pytest.raises(ValidationFailure):
        (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
         .expect_max_1_minute_load(40)
         .perform({}))


def test_max_load_correctly_fails_5_minute(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 30.04, 0.05"
    monkeypatch.setattr(ssh, "run", lambda x: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    with pytest.raises(ValidationFailure):
        (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
         .expect_max_5_minute_load(20)
         .perform({}))


def test_max_load_correctly_fails_15_minute(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 12.05"
    monkeypatch.setattr(ssh, "run", lambda x: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    with pytest.raises(ValidationFailure):
        (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
         .expect_max_15_minute_load(10)
         .perform({}))


def test_min_load_average(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 9.09, 2.04, 10.05"
    monkeypatch.setattr(ssh, "run", lambda x: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
     .expect_min_1_minute_load(5)
     .expect_min_5_minute_load(2)
     .expect_min_15_minute_load(10)
     .perform({}))


def test_min_load_correctly_fails_1_minute(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.01, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run", lambda x: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    with pytest.raises(ValidationFailure):
        (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
         .expect_min_1_minute_load(0.02)
         .perform({}))


def test_min_load_correctly_fails_5_minute(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 0.05"
    monkeypatch.setattr(ssh, "run", lambda x: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    with pytest.raises(ValidationFailure):
        (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
         .expect_min_5_minute_load(0.08)
         .perform({}))


def test_min_load_correctly_fails_15_minute(monkeypatch, tmpdir):
    t = "18:01:46 up 62 days, 18:27,  1 user,  load average: 0.09, 0.04, 0.01"
    monkeypatch.setattr(ssh, "run", lambda x: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    with pytest.raises(ValidationFailure):
        (ssh.LoadAverageValidation(ssh_ctx, hosts=hosts)
         .expect_min_15_minute_load(0.02)
         .perform({}))


def test_service_state(monkeypatch, tmpdir):
    t = "running"
    monkeypatch.setattr(ssh, "sudo",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    (ssh.UpstartServiceValidation(ssh_ctx, "citations", hosts=hosts)
     .perform({}))


def test_exit_code_equals(monkeypatch, tmpdir):
    t = "stopped/waiting"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    (ssh.SshCommandValidation(ssh_ctx, "citations", "command", hosts=hosts)
     .expect_exit_code(0)
     .perform({}))


def test_exit_code_not_equals(monkeypatch, tmpdir):
    t = "stopped/waiting"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(ValidationFailure):
        (ssh.SshCommandValidation(ssh_ctx, "citations", "command", hosts=hosts)
         .expect_exit_code(1)
         .perform({}))


def test_output_contains(monkeypatch, tmpdir):
    t = "stopped/waiting"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    (ssh.SshCommandValidation(ssh_ctx, "citations", "command", hosts=hosts)
     .expect_output_contains("stopped")
     .perform({}))


def test_output_contains_correctly_fails(monkeypatch, tmpdir):
    t = "stopped/waiting"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(ValidationFailure):
        (ssh.SshCommandValidation(ssh_ctx, "citations", "command", hosts=hosts)
         .expect_output_contains("what")
         .perform({}))


def test_output_does_not_contain(monkeypatch, tmpdir):
    t = "stopped/waiting"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    (ssh.SshCommandValidation(ssh_ctx, "citations", "command", hosts=hosts)
     .expect_output_does_not_contain("what")
     .perform({}))


def test_output_does_not_contain_correctly_fails(monkeypatch, tmpdir):
    t = "stopped/waiting"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(ValidationFailure):
        (ssh.SshCommandValidation(ssh_ctx, "citations", "command", hosts=hosts)
         .expect_output_does_not_contain("stopped")
         .perform({}))


def test_output_greater_than(monkeypatch, tmpdir):
    t = "100"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    validation = ssh.SshCommandValidation(ssh_ctx,
                                          "citations",
                                          "command",
                                          hosts=hosts)
    validation.add_expectation(ssh.OutputGreaterThan(validation, 90))
    validation.perform({})


def test_output_greater_than_correctly_fails(monkeypatch, tmpdir):
    t = "100"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(ValidationFailure):
        validation = ssh.SshCommandValidation(ssh_ctx,
                                              "citations",
                                              "command",
                                              hosts=hosts)
        validation.add_expectation(ssh.OutputGreaterThan(validation, 110))
        validation.perform({})


def test_output_less_than(monkeypatch, tmpdir):
    t = "100"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    validation = ssh.SshCommandValidation(ssh_ctx,
                                          "citations",
                                          "command",
                                          hosts=hosts)
    validation.add_expectation(ssh.OutputLessThan(validation, 110))
    validation.perform({})


def test_output_less_than_correctly_fails(monkeypatch, tmpdir):
    t = "100"
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: get_mock_ssh_text(t, 0))
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(ValidationFailure):
        validation = ssh.SshCommandValidation(ssh_ctx,
                                              "citations",
                                              "command",
                                              hosts=hosts)
        validation.add_expectation(ssh.OutputLessThan(validation, 90))
        validation.perform({})


def broken_ssh():
    raise Exception


def test_output_correct_on_ssh_failure(monkeypatch, tmpdir):
    monkeypatch.setattr(ssh, "run",
                        lambda x, combine_stderr, timeout: broken_ssh())
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))

    with pytest.raises(ValidationFailure):
        validation = ssh.SshCommandValidation(ssh_ctx,
                                              "citations",
                                              "command",
                                              hosts=hosts)
        validation.add_expectation(ssh.OutputLessThan(validation, 90))
        validation.perform({})
