import alarmageddon.validations.ssh as ssh
import alarmageddon.validations.cassandra as cassandra

from alarmageddon.validations.cassandra import NodetoolStatusParser
from alarmageddon.validations.cassandra import Status
from alarmageddon.validations.cassandra import State

from alarmageddon.validations.exceptions import ValidationFailure
import pytest
from validation_mocks import get_mock_key_file, get_mock_ssh_text


HEALTHY_OUTPUT = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UN  10.168.7.222   77.82 GB   256     19.9%  27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UN  10.168.14.117  80.9 GB    256     20.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UN  10.168.4.76    64.07 GB   256     16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
UN  10.168.4.72    83.75 GB   256     21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_cassandra_success(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = HEALTHY_OUTPUT
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    (cassandra.CassandraStatusValidation(ssh_ctx, hosts=["127.0.0.1"])
     .perform({}))


HEALTHY_OUTPUT_WITHOUT_PERCENT_SIGNS = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UN  10.168.7.222   77.82 GB   256     19.9   27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UN  10.168.14.117  80.9 GB    256     20.5   064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UN  10.168.4.76    64.07 GB   256     16.4   a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     21.9   c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
UN  10.168.4.72    83.75 GB   256     21.2   dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_cassandra_success_without_percent_signs(monkeypatch, tmpdir):
     ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
     text = HEALTHY_OUTPUT_WITHOUT_PERCENT_SIGNS
     monkeypatch.setattr(ssh, "run",
                         lambda x: get_mock_ssh_text(text, 0))
     monkeypatch.setattr(cassandra, "run",
                         lambda x: get_mock_ssh_text(text, 0))

     (cassandra.CassandraStatusValidation(ssh_ctx, hosts=["127.0.0.1"])
      .perform({}))


SERVER_DOWN_OUTPUT = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UJ  10.168.7.222   77.82 GB   256     19.9   27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UL  10.168.14.117  80.9 GB    256     20.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UM  10.168.4.76    64.07 GB   256     16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
DN  10.168.4.72    83.75 GB   256     21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_cassandra_down(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = SERVER_DOWN_OUTPUT
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, hosts=["127.0.0.1"])
         .perform({}))


UNBALANCED_RING_OUTPUT = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UN  10.168.7.222   77.82 GB   256     19.9%  27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UN  10.168.14.117  80.9 GB    256     10.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UN  10.168.4.76    64.07 GB   256      6.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     51.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
UN  10.168.4.72    83.75 GB   256     11.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_cassandra_threshold(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = UNBALANCED_RING_OUTPUT
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, owns_threshold=40,
                                             hosts=["127.0.0.1"])
         .perform({}))


UNHEALTHY_OUTPUT_WITH_PERCENT_SIGNS = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns    Host ID                               Rack
UN  10.168.7.222   77.82 GB   256      9.9%   27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UN  10.168.14.117  80.9 GB    256     40.5%   064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UN  10.168.4.76    64.07 GB   256      6.4%   a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     21.9%   c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
UN  10.168.4.72    83.75 GB   256     21.2%   dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_cassandra_success_with_percent_signs(monkeypatch, tmpdir):
     ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
     text = UNHEALTHY_OUTPUT_WITH_PERCENT_SIGNS
     monkeypatch.setattr(ssh, "run",
                         lambda x: get_mock_ssh_text(text, 0))
     monkeypatch.setattr(cassandra, "run",
                         lambda x: get_mock_ssh_text(text, 0))

     with pytest.raises(ValidationFailure):
        (cassandra.CassandraStatusValidation(ssh_ctx, owns_threshold=40,
                                             hosts=["127.0.0.1"])
         .perform({}))


MISSING_NODE_OUTPUT = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UN  10.168.7.222   77.82 GB   256     19.9%  27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UN  10.168.4.76    64.07 GB   256     16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
UN  10.168.4.72    83.75 GB   256     21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_cassandra_node_count(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = MISSING_NODE_OUTPUT
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


JOINING_NODE_OUTPUT = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UJ  10.168.7.222   77.82 GB   256     19.9%  27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UN  10.168.14.117  80.9 GB    256     20.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UN  10.168.4.76    64.07 GB   256     16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
UN  10.168.4.72    83.75 GB   256     21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_ignore_joining_nodes(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = JOINING_NODE_OUTPUT
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
    text = HEALTHY_OUTPUT
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    (cassandra.CassandraStatusValidation(ssh_ctx, number_nodes=4,
                                         hosts=["127.0.0.1"])
     .perform({}))


VARIED_OUTPUT = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UJ  10.168.7.222   77.82 GB   256     19.9   27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UL  10.168.14.117  80.9 GB    256     20.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UM  10.168.4.76    64.07 GB   256     16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
DN  10.168.4.72    83.75 GB   256     21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_can_parse_normal_nodes():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(VARIED_OUTPUT)
    assert len(nodes) == 5


def test_can_parse_normal_state():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(VARIED_OUTPUT)
    assert nodes[0].state == State.JOINING


def test_can_parse_ownership():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(VARIED_OUTPUT)
    assert nodes[0].owns == 19.9


def test_can_parse_rack():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(VARIED_OUTPUT)
    assert nodes[0].rack == '1c'


def test_can_parse_address():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(VARIED_OUTPUT)
    assert nodes[0].ip_address == '10.168.7.222'


def test_can_parse_status():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(VARIED_OUTPUT)
    assert nodes[0].status == Status.UP


OUTPUT_MISSING_TOKENS = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Owns   Host ID                               Rack
UJ  10.168.7.222   77.82 GB   19.9   27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UL  10.168.14.117  80.9 GB    20.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UM  10.168.4.76    64.07 GB   16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
DN  10.168.4.72    83.75 GB   21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_can_parse_nodes_missing_tokens():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(OUTPUT_MISSING_TOKENS)
    assert len(nodes) == 5


def test_tokens_are_none():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(OUTPUT_MISSING_TOKENS)
    assert nodes[0].tokens == None


OUTPUT_MISSING_OWNERSHIP = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Host ID                               Rack
UJ  10.168.7.222   77.82 GB   256     27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UL  10.168.14.117  80.9 GB    256     064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UM  10.168.4.76    64.07 GB   256     a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
DN  10.168.4.72    83.75 GB   256     dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_can_parse_nodes_missing_ownership():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(OUTPUT_MISSING_OWNERSHIP)
    assert len(nodes) == 5


def test_ownership_is_none():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(OUTPUT_MISSING_OWNERSHIP)
    assert nodes[0].owns == None


MINIMAL_OUTPUT = """--  Address        Load       Tokens  Owns   Host ID                               Rack
UJ  10.168.7.222   77.82 GB   256     19.9   27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UL  10.168.14.117  80.9 GB    256     20.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UM  10.168.4.76    64.07 GB   256     16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
DN  10.168.4.72    83.75 GB   256     21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_can_parse_minimal_output():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(MINIMAL_OUTPUT)
    assert len(nodes) == 5

MULTI_DATACENTER_OUTPUT="""xss =  -ea -javaagent:/usr/share/dse/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms6G -Xmx6G -Xmn2G -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: use1b
=================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UN  10.168.252.216 244.65 MB  256     14.9%  0586776f-b4c2-4edc-8b67-afd02489a308  use1b-r
UN  10.168.252.68  248.72 MB  256     18.8%  234c7abe-26e2-4d85-9e2f-7cf6b8f0bb33  use1b-r
Datacenter: use1c
=================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UN  10.168.253.83  249.26 MB  256     17.7%  570597ff-9ac0-41e5-9ee2-2e1fa27d75e6  use1c-r
UN  10.168.253.50  244.58 MB  256     16.2%  f441bd1a-1227-488c-9e06-7f4ae476787b  use1c-r
Datacenter: use1d
=================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UN  10.168.249.83  247.17 MB  256     15.6%  bfb459e4-9897-47e6-aa17-7c0da370a475  use1d-r
UN  10.168.249.26  247.45 MB  256     16.7%  6281b906-14f9-44f6-ae91-5109f5e5da86  use1d-r"""

def test_can_parse_minimal_output():
    parser = cassandra.NodetoolStatusParser()
    nodes = parser.parse(MULTI_DATACENTER_OUTPUT)
    assert len(nodes) == 6

ZERO_OWNERSHIP_OUTPUT = """xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
Note: Ownership information does not include topology; for complete information, specify a keyspace
Datacenter: us-east
===================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns   Host ID                               Rack
UN  10.168.7.222   77.82 GB   256     0.0%   27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
UN  10.168.14.117  80.9 GB    256     0.0%   064fd4da-6af8-4647-826c-a68ba038bc8d  1b.NORTH
UN  10.168.4.76    64.07 GB   256     0.0%   a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
UN  10.168.7.208   85.2 GB    256     0.0%   c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
UN  10.168.4.72    83.75 GB   256     0.0%   dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d"""


def test_zero_ownership_should_not_fail(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = ZERO_OWNERSHIP_OUTPUT
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    (cassandra.CassandraStatusValidation(ssh_ctx, hosts=["127.0.0.1"])
     .perform({}))


def test_repr(monkeypatch, tmpdir):
    ssh_ctx = ssh.SshContext("ubuntu", get_mock_key_file(tmpdir))
    text = ZERO_OWNERSHIP_OUTPUT
    monkeypatch.setattr(ssh, "run",
                        lambda x: get_mock_ssh_text(text, 0))
    monkeypatch.setattr(cassandra, "run",
                        lambda x: get_mock_ssh_text(text, 0))

    (cassandra.CassandraStatusValidation(ssh_ctx, hosts=["127.0.0.1"])
     .__repr__())
