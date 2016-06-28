"""Convenience Validations for working with Kafka"""

from fabric.operations import run

from alarmageddon.validations.validation import Priority
from alarmageddon.validations.ssh import SshValidation

import re
from collections import Counter

from alarmageddon.validations.utilities import format_node, format_cluster

import logging

logger = logging.getLogger(__name__)

class KafkaStatusValidation(SshValidation):

    """Validate that the Kafka cluster has all of it's partitions
    distributed across the cluster.

    :param ssh_contex: An SshContext class, for accessing the hosts.

    :param zookeeper_nodes: Kafka zookeeper hosts and ports in CSV.
      e.g. "host1:2181,host2:2181,host3:2181"

    :param kafka_list_topic_command: Kafka command to list topics
      (defaults to "/opt/kafka/bin/kafka-list-topic.sh")

    :param priority: The Priority level of this validation.

    :param timeout: How long to attempt to connect to the host.

    :param hosts: The hosts to connect to.

    :param cluster_name: the name of the cluster (helps when you're monitoring
                         multiple clusters.  Defaults to 'anonymous'.
    """

    def __init__(self, ssh_context,
                 zookeeper_nodes,
                 kafka_list_topic_command="/opt/kafka/bin/kafka-list-topic.sh",
                 priority=Priority.NORMAL, timeout=None,
                 hosts=None, cluster_name='anonymous'):
        SshValidation.__init__(self, ssh_context,
                               "Kafka partition status",
                               priority=priority,
                               timeout=timeout,
                               hosts=hosts)
        self.kafka_list_topic_command = kafka_list_topic_command
        self.zookeeper_nodes = zookeeper_nodes
        self.cluster_name = cluster_name

    def perform_on_host(self, host):
        """Runs kafka list topic command on host"""
        output = run(
            self.kafka_list_topic_command +
            " --zookeeper " +
            self.zookeeper_nodes)

        error_patterns = [
            'No such file', 'Missing required argument', 'Exception']
        if any(x in output for x in error_patterns):
            self.fail_on_host(host, ("An exception occurred while " +
                                         "checking Kafka cluster health " +
                                         "on {0} ({1})").format(
                                             format_node(self.cluster_name,
                                                             host),
                                             output))
        parsed = re.split(r'\t|\n', output)
        topics = [parsed[i] for i in xrange(0, len(parsed), 5)]
        leaders = [parsed[i] for i in xrange(2, len(parsed), 5)]

        tuples = zip(topics, leaders)
        duplicates = [x for x, y in Counter(tuples).items() if y > 1]

        if len(duplicates) != 0:
            duplicates_str =", ".join("%s has %s" %
                                          (dup[0], dup[1]) for dup in duplicates)
            self.fail_on_host(host, ("Kafka partitions are out of sync " +
                                  "on {0}. Multiple leaders for the same " +
                                  "partition for the same replica: {1}").format(
                                      format_cluster(self.cluster_name),
                                      duplicates_str)
)
