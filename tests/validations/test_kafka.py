import alarmageddon.validations.ssh as ssh
import alarmageddon.validations.kafka as kafka
from alarmageddon.validations.exceptions import ValidationFailure
import pytest
from validation_mocks import get_mock_key_file, get_mock_ssh_text
from fabric import Connection

_CLUSTER_NAME='widget streams'

def test_kafka_success(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = "topic: topic1\tpartition: 0\tleader: 140\treplicas: 140,187,96,99,132\tisr: 140,187,96,99,132\r\ntopic: topic1\tpartition: 1\tleader: 187\treplicas: 187,96,99,132,140\tisr: 132,96,187,140,99\r\ntopic: topic1\tpartition: 2\tleader: 96\treplicas: 96,99,132,140,187\tisr: 96,99,132,140,187\r\ntopic: topic1\tpartition: 3\tleader: 99\treplicas: 99,132,140,187,96\tisr: 99,132,140,187,96\r\ntopic: topic1\tpartition: 4\tleader: 132\treplicas: 132,140,187,96,99\tisr: 132,140,187,96,99\r\ntopic: topic2\tpartition: 0\tleader: 187\treplicas: 187,96,99,132,140\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 1\tleader: 96\treplicas: 96,99,132,140,187\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 2\tleader: 99\treplicas: 99,132,140,187,96\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 3\tleader: 132\treplicas: 132,140,187,96,99\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 4\tleader: 140\treplicas: 140,187,96,99,132\tisr: 132,96,187,140,99"

    monkeypatch.setattr(Connection, "run",
                        lambda self, x, warn: get_mock_ssh_text(text, 0))

    (kafka.KafkaStatusValidation(ssh_ctx,
                                 zookeeper_nodes="1.2.3.4:2181",
                                 hosts=["127.0.0.1"],
                                 cluster_name=_CLUSTER_NAME)
     .perform({}))


def test_kafka_duplicate_partiton(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = "topic: topic1\tpartition: 0\tleader: 140\treplicas: 140,187,96,99,132\tisr: 140,187,96,99,132\r\ntopic: topic1\tpartition: 1\tleader: 187\treplicas: 187,96,99,132,140\tisr: 132,96,187,140,99\r\ntopic: topic1\tpartition: 2\tleader: 96\treplicas: 96,99,132,140,187\tisr: 96,99,132,140,187\r\ntopic: topic1\tpartition: 3\tleader: 99\treplicas: 99,132,140,187,96\tisr: 99,132,140,187,96\r\ntopic: topic1\tpartition: 4\tleader: 99\treplicas: 132,140,187,96,99\tisr: 132,140,187,96,99\r\ntopic: topic2\tpartition: 0\tleader: 187\treplicas: 187,96,99,132,140\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 1\tleader: 96\treplicas: 96,99,132,140,187\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 2\tleader: 99\treplicas: 99,132,140,187,96\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 3\tleader: 132\treplicas: 132,140,187,96,99\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 4\tleader: 140\treplicas: 140,187,96,99,132\tisr: 132,96,187,140,99"
    monkeypatch.setattr(Connection, "run",
                        lambda self, x, warn: get_mock_ssh_text(text, 0))
    with pytest.raises(ValidationFailure):
        (kafka.KafkaStatusValidation(ssh_ctx,
                                     zookeeper_nodes="1.2.3.4:2181",
                                     hosts=["127.0.0.1"],
                                     cluster_name=_CLUSTER_NAME)
         .perform({}))


def test_kafka_multiple_duplicate_partition(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = "topic: topic1\tpartition: 0\tleader: 140\treplicas: 140,187,96,99,132\tisr: 140,187,96,99,132\r\ntopic: topic1\tpartition: 1\tleader: 187\treplicas: 187,96,99,132,140\tisr: 132,96,187,140,99\r\ntopic: topic1\tpartition: 2\tleader: 96\treplicas: 96,99,132,140,187\tisr: 96,99,132,140,187\r\ntopic: topic1\tpartition: 3\tleader: 99\treplicas: 99,132,140,187,96\tisr: 99,132,140,187,96\r\ntopic: topic1\tpartition: 4\tleader: 99\treplicas: 132,140,187,96,99\tisr: 132,140,187,96,99\r\ntopic: topic2\tpartition: 0\tleader: 187\treplicas: 187,96,99,132,140\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 1\tleader: 96\treplicas: 96,99,132,140,187\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 2\tleader: 99\treplicas: 99,132,140,187,96\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 3\tleader: 132\treplicas: 132,140,187,96,99\tisr: 132,96,187,140,99\r\ntopic: topic2\tpartition: 4\tleader: 132\treplicas: 140,187,96,99,132\tisr: 132,96,187,140,99"
    monkeypatch.setattr(Connection, "run",
                        lambda self, x, warn: get_mock_ssh_text(text, 0))
    with pytest.raises(ValidationFailure):
        (kafka.KafkaStatusValidation(ssh_ctx,
                                     zookeeper_nodes="1.2.3.4:2181",
                                     hosts=["127.0.0.1"],
                                     cluster_name=_CLUSTER_NAME)
         .perform({}))


def test_kafka_command_not_found(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = "-bash: /opt/kafka2/bin/kdkd: No such file or directory"
    monkeypatch.setattr(Connection, "run",
                        lambda self, x, warn: get_mock_ssh_text(text, 0))
    with pytest.raises(ValidationFailure):
        (kafka.KafkaStatusValidation(ssh_ctx,
                                     zookeeper_nodes="1.2.3.4:2181",
                                     hosts=["127.0.0.1"],
                                     cluster_name=_CLUSTER_NAME)
         .perform({}))


def test_kafka_missing_zookeeper(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """
  Exception in thread "main" joptsimple.OptionMissingRequiredArgumentException: Option ['zookeeper'] requires an argument
    at joptsimple.RequiredArgumentOptionSpec.detectOptionArgument(RequiredArgumentOptionSpec.java:49)
    at joptsimple.ArgumentAcceptingOptionSpec.handleOption(ArgumentAcceptingOptionSpec.java:209)
    at joptsimple.OptionParser.handleLongOptionToken(OptionParser.java:405)
    at joptsimple.OptionParserState$2.handleArgument(OptionParserState.java:55)
    at joptsimple.OptionParser.parse(OptionParser.java:392)
    at kafka.admin.ListTopicCommand$.main(ListTopicCommand.scala:43)
    at kafka.admin.ListTopicCommand.main(ListTopicCommand.scala)
    """
    monkeypatch.setattr(Connection, "run",
                        lambda self, x, warn: get_mock_ssh_text(text, 0))
    with pytest.raises(ValidationFailure):
        (kafka.KafkaStatusValidation(ssh_ctx,
                                     zookeeper_nodes="1.2.3.4:2181",
                                     hosts=["127.0.0.1"],
                                     cluster_name=_CLUSTER_NAME)
         .perform({}))


def test_repr(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """
  Exception in thread "main" joptsimple.OptionMissingRequiredArgumentException: Option ['zookeeper'] requires an argument
    at joptsimple.RequiredArgumentOptionSpec.detectOptionArgument(RequiredArgumentOptionSpec.java:49)
    at joptsimple.ArgumentAcceptingOptionSpec.handleOption(ArgumentAcceptingOptionSpec.java:209)
    at joptsimple.OptionParser.handleLongOptionToken(OptionParser.java:405)
    at joptsimple.OptionParserState$2.handleArgument(OptionParserState.java:55)
    at joptsimple.OptionParser.parse(OptionParser.java:392)
    at kafka.admin.ListTopicCommand$.main(ListTopicCommand.scala:43)
    at kafka.admin.ListTopicCommand.main(ListTopicCommand.scala)
    """
    monkeypatch.setattr(Connection, "run",
                        lambda self, x, warn: get_mock_ssh_text(text, 0))
    v = kafka.KafkaStatusValidation(ssh_ctx,
                                    zookeeper_nodes="1.2.3.4:2181",
                                    hosts=["127.0.0.1"],
                                    cluster_name=_CLUSTER_NAME)
    v.__repr__()


def test_str(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = """
  Exception in thread "main" joptsimple.OptionMissingRequiredArgumentException: Option ['zookeeper'] requires an argument
    at joptsimple.RequiredArgumentOptionSpec.detectOptionArgument(RequiredArgumentOptionSpec.java:49)
    at joptsimple.ArgumentAcceptingOptionSpec.handleOption(ArgumentAcceptingOptionSpec.java:209)
    at joptsimple.OptionParser.handleLongOptionToken(OptionParser.java:405)
    at joptsimple.OptionParserState$2.handleArgument(OptionParserState.java:55)
    at joptsimple.OptionParser.parse(OptionParser.java:392)
    at kafka.admin.ListTopicCommand$.main(ListTopicCommand.scala:43)
    at kafka.admin.ListTopicCommand.main(ListTopicCommand.scala)
    """
    monkeypatch.setattr(Connection, "run",
                        lambda self, x, warn: get_mock_ssh_text(text, 0))
    v = kafka.KafkaStatusValidation(ssh_ctx,
                                    zookeeper_nodes="1.2.3.4:2181",
                                    hosts=["127.0.0.1"],
                                    cluster_name=_CLUSTER_NAME)
    str(v)
