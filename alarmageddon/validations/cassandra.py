"""Convenience Validations for working with Cassandra"""

from alarmageddon.validations.validation import Priority
from alarmageddon.validations.ssh import SshValidation

from alarmageddon.validations.utilities import format_node, format_cluster

import os
import re

import logging

logger = logging.getLogger(__name__)

# The output for Cassandra's nodetool status command has changed
# between versions.  This new parser is designed to provide a more
# robust way of parsing the output of the nodetool status command.  It
# has to make some assumptions about the output but it tries to make as
# few as possible.
#
# Assumptions:
#   1) There is a header line that lists all of the field names
#   2) The header line begins with a '--  '
#   3) All lines after the header describe nodes
#   4) All lines before the header can be ignored
#   5) Other assumptions I am even aware that I have made
#
# I'd like to illustrate how the output of the nodetool status command
# will be processed.  Here is some example output for Cassandra
# version 2.0.9:
#
#   xss =  -ea -javaagent:/usr/share/cassandra/lib/jamm-0.2.5.jar -XX:+UseThreadPriorities -XX:ThreadPriorityPolicy=42 -Xms10240m -Xmx10240m -Xmn2048m -XX:+HeapDumpOnOutOfMemoryError -Xss256k
#   Note: Ownership information does not include topology; for complete information, specify a keyspace
#   Datacenter: us-east
#   ===================
#   Status=Up/Down
#   |/ State=Normal/Leaving/Joining/Moving
#   --  Address        Load       Tokens  Owns   Host ID                               Rack
#   UN  10.168.7.222   77.82 GB   256     19.9%  27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
#   UN  10.168.14.117  80.9 GB    256     20.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b
#   UN  10.168.4.76    64.07 GB   256     16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
#   UN  10.168.7.208   85.2 GB    256     21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
#   UN  10.168.4.72    83.75 GB   256     21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d
#
# We ignore every line up until the header line (it starts with a '--'
# sequence).  That leaves the following:
#
#   --  Address        Load       Tokens  Owns   Host ID                               Rack
#   UN  10.168.7.222   77.82 GB   256     19.9%  27600dd2-9ebf-4501-820c-37dec6ea2e33  1c
#   UN  10.168.14.117  80.9 GB    256     20.5%  064fd4da-6af8-4647-826c-a68ba038bc8d  1b
#   UN  10.168.4.76    64.07 GB   256     16.4%  a5cc2101-4806-47d6-9228-5a4a45e047fc  1d
#   UN  10.168.7.208   85.2 GB    256     21.9%  c56f5b4a-4863-4a24-a2fd-ee3f82baebf8  1c
#   UN  10.168.4.72    83.75 GB   256     21.2%  dc8cbbdc-d95f-4836-884e-2e12f4adb13a  1d
#
# We now parse the header line to find the boundaries of each node's
# fields.  Here is the header line:
#
#   --  Address        Load       Tokens  Owns   Host ID                               Rack
#
# We assume that all header names are made up of non-space characters
# possibly delimited by single spaces.  That ensures that 'Host ID' is
# treated as a single header name and not two.  Once we have the boundaries:
#
#   |-- |Address      |Load      |Tokens |Owns  |Host ID                              |Rack|
#
# we can use those boundaries to start chopping up the remaining lines
# in the output and creating Nodes from them.
#
#   +---+-------------+----------+-------+------+-------------------------------------+----+
#   |-- |Address      |Load      |Tokens |Owns  |Host ID                              |Rack|
#   +---+-------------+----------+-------+------+-------------------------------------+----+
#   |UN |10.168.7.222 |77.82 GB  |256    |19.9% |27600dd2-9ebf-4501-820c-37dec6ea2e33 |1c  |
#   |UN |10.168.14.117|80.9 GB   |256    |20.5% |064fd4da-6af8-4647-826c-a68ba038bc8d |1b  |
#   |UN |10.168.4.76  |64.07 GB  |256    |16.4% |a5cc2101-4806-47d6-9228-5a4a45e047fc |1d  |
#   |UN |10.168.7.208 |85.2 GB   |256    |21.9% |c56f5b4a-4863-4a24-a2fd-ee3f82baebf8 |1c  |
#   |UN |10.168.4.72  |83.75 GB  |256    |21.2% |dc8cbbdc-d95f-4836-884e-2e12f4adb13a |1d  |
#   +---+-------------+----------+-------+------+-------------------------------------+----+
#


def _is_header_line(line):
    """Determines if line represents the headers for the nodetool status
    output.

    """
    return line.startswith('-- ')

def _is_data_center_line(line):
    """Determines if line introduces nodes from a Datacenter."""
    return line.startswith('Datacenter: ')


def _parse_status(text):
    """receives a Node Status (e.g. 'U' or 'D') and returns the
    corresponding Status code.

    """
    if text:
        return Status.from_text(text[0])
    else:
        return Status.UNKNOWN


def _parse_state(text):
    """receives a Node State (e.g. 'J', 'L', etc.) and returns the
    corresponding State code.

    """
    if text:
        return State.from_text(text[1])
    else:
        return State.UNKNOWN


def _get_percent(text):
    """If text is formatted like '33.2%', remove the percent and convert
    to a float.  Otherwise, just convert to a float.

    """
    if not text:
        return None
    
    if text.endswith('%'):
        text = text[:-1]

    return float(text.strip())


class Status(object):
    """An enum-like object that represents the status of a Cassandra Node

    """
    UNKNOWN, UP, DOWN = list(range(3))

    @staticmethod
    def from_text(text):
        if text == 'U':
            return Status.UP
        elif text == 'D':
            return Status.DOWN
        else:
            return Status.UNKNOWN

    @staticmethod
    def to_text(value):
        """Convert Status to String"""
        if value == Status.UP:
            return 'Up'
        elif value == Status.DOWN:
            return 'Down'
        else:
            return 'Unknown'


class State(object):
    """An enum-like object that represents the state of a Cassandra Node

    """
    UNKNOWN, NORMAL, LEAVING, JOINING, MOVING = list(range(5))

    @staticmethod
    def from_text(text):
        if text == 'N':
            return State.NORMAL
        elif text == 'L':
            return State.LEAVING
        elif text == 'J':
            return State.JOINING
        elif text == 'M':
            return State.MOVING
        else:
            return State.UNKNOWN

    @staticmethod
    def to_text(value):
        """Convert State to String"""
        if value == State.NORMAL:
            return 'Normal'
        elif value == State.LEAVING:
            return 'Leaving'
        elif value == State.JOINING:
            return 'Joining'
        elif value == State.MOVING:
            return 'Moving'
        else:
            return 'Unknown'

class Node(object):
    """Information about a Cassandra node including its load, what percent
    of the ring it owns, its state, etc.

    """
    def __init__(self, ip_address, status=Status.UNKNOWN,
                 state=State.UNKNOWN, load=None, tokens=None,
                 owns=None, host_id=None, rack=None):
        self.ip_address = ip_address
        self.status = status
        self.state = state
        self.load = load
        self.tokens = tokens
        self.owns = owns
        self.host_id = host_id
        self.rack = rack

    def __str__(self):
        return ("Address: %s, Status: %s, State: %s, Load: %s, " +
                "Tokens: %d, Owns: %s, Host ID: %s, Rack: %s") % (
                    self.ip_address, Status.to_text(self.status),
                    State.to_text(self.state), self.load, self.tokens,
                    self.owns, self.host_id, self.rack)


class _Header(object):
    """Information about a field header."""
    def __init__(self, name, start_pos, length, last_header=False):
        self.name = name
        self.start_pos = start_pos
        self.length = length
        self.last_header = last_header

    def __str__(self):
        return "%s (%s,%s)" % (self.name, self.start_pos, self.length)


class NodetoolStatusParser(object):
    """Parses the output of the Cassandra nodetool status command and
    tries to make sense of it despite changes made to the format.
    """
    def __init__(self):
        self.__headers = []

    def parse(self, status_output):
        found_header = False
        nodes = []
        for line in status_output.split(os.linesep):
            if _is_data_center_line(line):
                found_header = False
                self.__headers = None
            elif _is_header_line(line):
                found_header = True
                self.__headers = self.__parse_headers(line)
            elif found_header:
                # If we've already parsed one node and we find a blank line, ignore the rest of the
                # output because it's not information about nodes; it's some other text output that
                # we won't parse at the moment.
                if nodes and not line.strip():
                    break
                nodes.append(self.__parse_node(line))
        logger.info("Found these Cassandra nodes:{}".format(nodes))
        return nodes

    def __parse_headers(self, line):
        headers = []
        # All headers are deliminated by 2 or more spaces.  Note the
        # sentinel added to the end to simplify header processing
        tokens = re.split(r"(\s{2,})", line) + ['']
        name = None
        start_pos = 0
        for token in tokens:
            if len(token) and not re.match(r'\s+', token):
                name = token
            else:
                length = len(name) + len(token)
                headers.append(_Header(name, start_pos, length,
                                       len(token) == 0))
                start_pos = start_pos + length
        return headers

    def __parse_node(self, line):
        """Parses a line and returns a Node object"""
        node = Node(self.__get_ip_address(line),
                    self.__get_status(line),
                    self.__get_state(line),
                    self.__get_load(line),
                    self.__get_tokens(line),
                    self.__get_owns(line),
                    self.__get_host_id(line),
                    self.__get_rack(line))
        return node

    # These methods are broken out because different fields have different
    # types and field names might change in a future release.

    def __get_ip_address(self, line):
        return self.__get_field('address', line)

    def __get_status(self, line):
        return _parse_status(self.__get_field('--', line))

    def __get_state(self, line):
        return _parse_state(self.__get_field('--', line))

    def __get_load(self, line):
        return self.__get_field('load', line)

    def __get_tokens(self, line):
        tokens = self.__get_field('tokens', line)
        if tokens:
            return int(tokens)
        else:
            return None

    def __get_owns(self, line):
        # The following Cassandra issue (https://issues.apache.org/jira/browse/CASSANDRA-10176) causes
        # question mark characters (?) to appear in the 'Owns' column of nodetool status' output.
        owns = self.__get_field('owns', line)
        if owns == '?':
            return None
        else:
            return _get_percent(owns)

    def __get_host_id(self, line):
        return self.__get_field('host id', line)

    def __get_rack(self, line):
        return self.__get_field('rack', line)

    def __get_field(self, field_name, line):
        header = self.__find_header(field_name)
        if header:
            if header.last_header:
                # It's the last header so grab all the rest of the
                # text on the line.
                return line[header.start_pos:].strip()
            else:
                # It's not the last header so just grab as much text
                # as the header length calls for.
                return line[header.start_pos:header.start_pos +
                            header.length].strip()
        else:
            return None

    def __find_header(self, name):
        """find a header by name case-insensitively"""
        for header in self.__headers:
            if header.name.lower() == name.lower():
                return header
        return None


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

    :param cluster_name: the name of the cluster (helps when you're monitoring
                         multiple clusters.  Defaults to 'anonymous'.

    .. note:

        This is not designed for multi region Cassandra clusters.

    """
    def __init__(self, ssh_context, service_state="UN",
                 number_nodes=5, owns_threshold=40,
                 priority=Priority.NORMAL, timeout=None,
                 hosts=None, cluster_name='anonymous'):
        SshValidation.__init__(self, ssh_context,
                               "Cassandra nodetool status",
                               priority=priority,
                               timeout=timeout, hosts=hosts)
        # Service State is different from Service Status but I don't
        # want to break backwards compatibility so we parse the
        # service_state which is really made up of the service state
        # and service status values.
        if service_state and len(service_state) == 2:
            self.service_status = Status.from_text(service_state[0])
            self.service_state = State.from_text(service_state[1])
        else:
            self.service_state = State.UP
            self.service_status = Status.NORMAL
            
        self.number_nodes = number_nodes
        self.owns_threshold = owns_threshold
        self.cluster_name = cluster_name

    def perform_on_host(self, connection):
        """Runs nodetool status and parses the output."""
        output = connection.run('nodetool status', warn=True)
        host = connection.host

        if "Exception" in output:
            self.fail_on_host(host, ("An exception occurred while " +
                                         "checking Cassandra cluster health " +
                                         "on {0} ({1})").format(
                                             format_node(self.cluster_name, host),
                                             output))

        parsed = NodetoolStatusParser().parse(output)
        self.check(host, parsed)

    def check(self, host, nodes):
        """Compares the results of nodetool status to the expected results."""
        #Number of nodes check
        if len(nodes) < self.number_nodes:
            self.fail_on_host(host,
                              ("Cassandra cluster: {0} has {1} nodes but " +
                              "should have {2} nodes.").format(
                                  format_cluster(self.cluster_name),
                                  len(nodes), self.number_nodes))

        # Validate each node's properties in nodetool's nodes
        for node in nodes:
            logger.debug("Checking node: {}".format(node))

            # If a node is joining the cluster, don't check it for errors.
            if node.state == State.JOINING:
                continue

            # check for state
            if node.state != self.service_state:
                self.fail_on_host(host, ("Cassandra node {0} is in " +
                                  "state {1} but the expected state is {2}").format(
                                      format_node(self.cluster_name, node.ip_address),
                                      State.to_text(node.state),
                                      State.to_text(self.service_state)))

            # check for status
            if node.status != self.service_status:
                self.fail_on_host(host, ("Cassandra node {0} has " +
                                  "status {1} but the expected status is {2}").format(
                                      format_node(self.cluster_name, node.ip_address),
                                      Status.from_text(node.status),
                                      Status.from_text(self.service_status)))

            # check for owns threshold
            if node.owns is not None:
                if node.owns > self.owns_threshold:
                    self.fail_on_host(host,
                                      ("Cassandra node {0} owns {1} " +
                                      "percent of the ring which exceeds " +
                                      "threshold of {2}").format(
                                          format_node(self.cluster_name, node.ip_address),
                                          node.owns,
                                          self.owns_threshold))
