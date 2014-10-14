import alarmageddon.validations.ssh as ssh
import alarmageddon.validations.cassandra as cassandra
from alarmageddon.validations.exceptions import ValidationFailure
import pytest
from validation_mocks import get_mock_key_file, get_mock_ssh_text


def test_cassandra_success(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6
              UN 192.168.0.11 20.5
              UN 192.168.0.12 20.4
              UN 192.168.0.13 20.5
              UN 192.168.0.14 20.1"""
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    (cassandra.CassandraStatusValidation(ssh_ctx, hosts=["127.0.0.1"])
     .perform({}))


def test_cassandra_success_with_percent_signs(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6%
              UN 192.168.0.11 20.5%
              UN 192.168.0.12 20.4%
              UN 192.168.0.13 20.5%
              UN 192.168.0.14 20.1%"""
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    (cassandra.CassandraStatusValidation(ssh_ctx, hosts=["127.0.0.1"])
     .perform({}))


def test_cassandra_down(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6
              UN 192.168.0.11 20.5
              UN 192.168.0.12 20.4
              DN 192.168.0.13 20.5
              UN 192.168.0.14 20.1"""

    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, hosts=["127.0.0.1"])
         .perform({}))


def test_cassandra_threshold(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6
              UN 192.168.0.11 20.5
              UN 192.168.0.12 40.4
              UN 192.168.0.13 20.5
              UN 192.168.0.14 20.1"""
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, owns_threshold=40,
                                             hosts=["127.0.0.1"])
         .perform({}))


def test_cassandra_node_count(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6
              UN 192.168.0.11 20.5
              UN 192.168.0.12 20.5
              UN 192.168.0.13 20.1"""
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, number_nodes=5,
                                             hosts=["127.0.0.1"])
         .perform({}))


def test_no_cassandra(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = "Error connecting to remote JMX agent!"
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, number_nodes=5,
                                             hosts=["127.0.0.1"])
         .perform({}))


def test_non_numeric_output(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6
              UN 192.168.0.11 null
              UN 192.168.0.12 20.5
              UN 192.168.0.13 20.1"""
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, number_nodes=4,
                                             hosts=["127.0.0.1"])
         .perform({}))


def test_invalid_trailing_character(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6
              UN 192.168.0.11 12.2&
              UN 192.168.0.12 20.5
              UN 192.168.0.13 20.1"""
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, number_nodes=4,
                                             hosts=["127.0.0.1"])
         .perform({}))


def test_stack_trace(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """[10.198.10.174] out: Exception java.lang.RuntimeException.
    [10.198.10.174] out: 	at org.apache.cassandra.dht.Murmur3Partitioner.describeOwnership(Murmur3Partitioner.java:120)
    [10.198.10.174] out: 	at org.apache.cassandra.service.StorageService.getOwnership(StorageService.java:3512)
    [10.198.10.174] out: 	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    """
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, number_nodes=4,
                                             hosts=["127.0.0.1"])
         .perform({}))


def test_ignore_joining_nodes(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6
              UN 192.168.0.11 20.5
              UJ 192.168.0.12 20.4
              UN 192.168.0.13 20.5
              UN 192.168.0.14 20.1"""
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    (cassandra.CassandraStatusValidation(ssh_ctx, number_nodes=4,
                                         hosts=["127.0.0.1"])
     .perform({}))


def test_extra_nodes(monkeypatch, tmpdir):
    """Don't complain if there are extra nodes; the cluster might be
    scaling up.
    """
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """UN 192.168.0.10 18.6
              UN 192.168.0.11 20.5
              UN 192.168.0.12 20.4
              UN 192.168.0.13 20.5
              UN 192.168.0.14 20.1"""
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    (cassandra.CassandraStatusValidation(ssh_ctx, number_nodes=4,
                                         hosts=["127.0.0.1"])
     .perform({}))
