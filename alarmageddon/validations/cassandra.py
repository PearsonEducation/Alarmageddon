"""Convenience Validations for working with Cassandra"""

from fabric.operations import run

from alarmageddon.validations.validation import Priority
from alarmageddon.validations.ssh import SshValidation


def _get_percentage(text):
    """Converts strings like '12.2' or '32.4%' into floating point numbers."""
    text = text.strip()
    if text.endswith('%'):
        text = text[:-1]
    return float(text)


class CassandraStatusValidation(SshValidation):
    """Validate that the Cassandra ring is within expected parameters.

    Check that the specified Cassandra ring is in the specified
    state and that the ring ownership of the nodes is within a certain
    threshold.

    :param ssh_contex: An SshContext class, for accessing the hosts.

    :param service_state: The expected service state value (defaults to
      "UN").

    :param number_nodes: The expected number of cassandra nodes in the ring.

    :param owns_threshold: The maximum percentage of the ring owned by a node.

    :param priority: The Priority level of this validation.

    :param timeout: How long to attempt to connect to the host.

    :param hosts: The hosts to connect to.

    .. note:

        This is not designed for multi region Cassandra clusters.

    """
    def __init__(self, ssh_context, service_state="UN",
                 number_nodes=5, owns_threshold=40,
                 priority=Priority.NORMAL, timeout=None,
                 hosts=None):
        super(CassandraStatusValidation,self).__init__(ssh_context,
                                           "Cassandra nodetool status",
                                           priority=priority,
                                           timeout=timeout, hosts=hosts)
        self.service_state = service_state
        self.number_nodes = number_nodes
        self.owns_threshold = owns_threshold

    def perform_on_host(self, host):
        """Runs nodetool status and parses the output."""
        output = run(
            "nodetool status | " +
            "egrep '([0-9]{1,3}\\.){3}[0-9]{1,3}' | " +
            "awk 'BEGIN { FS = \" \" }; { print $1,$2,$5 }'")

        if "Exception" in output:
            self.fail_on_host(host, "An exception occurred while " +
                              "checking Cassandra cluster health on {0} ({1})"
                              .format((host, output)))

        parsed = [line.split() for line in output.splitlines() if line.strip()]
        self.check(host, parsed)

    def check(self, host, output):
        """Compares the results of nodetool status to the expected results."""
        #Number of nodes check
        if len(output) < self.number_nodes:
            self.fail_on_host(host,
                              "Cassandra cluster has {0} nodes but" +
                              "should have {1}"
                              .format(len(output), self.number_nodes))

        # Validate each node's properties in nodetool's output
        for fields in output:
            state = fields[0]
            owns = fields[2]
            node = fields[1]

            # While a node is joining the cluster, don't check it for errors.
            if state == 'UJ':
                continue

            #check for status
            if state != self.service_state:
                self.fail_on_host(host,
                                  "Cassandra node {0} is in " +
                                  "state {1} but the expected state is {2}"
                                  .format(node, state, self.service_state))

            #check for owns threshold
            try:
                owns_value = _get_percentage(owns)
                if owns_value > self.owns_threshold:
                    self.fail_on_host(host,
                                      "Cassandra node {0} owns {1} " +
                                      "percent of the ring which exceeds" +
                                      "threashold of {3}"
                                      .format(node, owns_value,
                                              self.owns_threshold))
            except ValueError:
                self.fail_on_host(host,
                                  "Expected nodetool to output an ownership " +
                                  "percentage but got: {0}".format(owns))
