"""Validations that are performed by executing commands remotely on
other servers using SSH

We're using fabric for easy SSH command execution.

"""

import os
import time
import re
import pytest
import warnings
from fabric.operations import run, sudo
from fabric.exceptions import CommandTimeout
from fabric.context_managers import settings
from fabric.network import disconnect_all
from alarmageddon.validations.validation import Validation, Priority


class SshContext(object):
    """Context that SSH commands execute in: the user and the user's key file.

    Note that the list of hosts is not part of the SshContext because it
    changes at a very high rate compared to the user name and their key file.

    """
    def __init__(self, user, key_file):
        """Creates an SshContext object"""

        if not user:
            raise ValueError("user parameter is required")
        if not key_file:
            raise ValueError("key_file parameter is required")
        if not os.path.exists(os.path.expanduser(key_file)):
            raise ValueError("key_file: {0} does not exist".format(key_file))

        self.user = user
        self.key_file = key_file

    def __str__(self):
        """return a string representation of an SshContext object"""
        return "SSH Context {{ User: {0}, Key File: {1} }}"\
            .format(self.user, self.key_file)


class SshValidation(Validation):
    """A Validation that is performed using SSH (more specifically, fabric)"""

    def __init__(self, ssh_context, name,
                 priority=Priority.NORMAL, timeout=None,
                 group=None, connection_retries=0,
                 hosts=None):
        """Creates an SshValidation object"""
        super(SshValidation, self).__init__(
            name, priority, timeout, group=group)
        self.context = ssh_context
        if hosts is not None:
            self.hosts = hosts
        else:
            self.hosts = []
        self.expectations = []
        self.retries = connection_retries
        self._exit_code_expectation = _ExitCodeEquals(self, 0)

    def add_hosts(self, hosts):
        """Add additional hosts to run validations against"""

        warnings.warn("Add hosts in the constructor rather than through this" +
                      " method", FutureWarning)
        self.hosts.extend(hosts)
        return self

    def perform(self, group_failures):
        """Perform validation against all of this object's hosts"""
        if not self.hosts:
            self.fail("no hosts specified.")

        #now we can add our default expectation
        self.expectations.append(self._exit_code_expectation)

        for host in self.hosts:
            with settings(warn_only=True,
                          host_string=host,
                          user=self.context.user,
                          key_filename=self.context.key_file):
                try:
                    for i in xrange(self.retries + 1):
                        try:
                            self.perform_on_host(host)
                            break
                        except CommandTimeout, ex:
                            #we connected, so don't retry
                            self.fail_on_host(
                                host,
                                "SSH Command timed out: {0}".format(str(ex)))
                        except Exception, ex:
                            if i >= self.retries:
                                self.fail_on_host(
                                    host,
                                    "SSH Command Exception: {0}"
                                    .format(str(ex)))
                                time.sleep(2)
                finally:
                    disconnect_all()

    def fail_on_host(self, host, reason):
        """signal failure the test on a particular host"""
        self.fail("[{0}] {1}".format(host, reason))

    def perform_on_host(self, host):
        """perform a validation against a particular host"""
        self.fail_on_host(
            host, "perform_on_host must be overriden by derived classes")

    def add_expectation(self, expectation):
        """Adds an expectation deriving from SshCommandExpectation to the list
        of expectations to be performed as part of the validation.

        """
        if isinstance(expectation, SshCommandExpectation):
            self.expectations.append(expectation)
            return self
        else:
            raise ValueError("attempt to add expectation that does not" +
                             " derive from SshCommandExpectation.")

    def expect_exit_code(self, exit_code):
        """Add the expectation that the SSH command's exit code is equal
        to exit_code

        """
        self._exit_code_expectation = _ExitCodeEquals(self, exit_code)
        return self

    def expect_output_contains(self, text):
        """Add the expectation that the SSH command's output contains text"""
        self.add_expectation(OutputContains(self, text))
        return self

    def expect_output_does_not_contain(self, text):
        """Add the expectation that the SSH command's output does not
        contain text

        """
        self.add_expectation(OutputDoesNotContain(self, text))
        return self


class SshCommandValidation(SshValidation):
    """A validation that runs a command and checks zero or more expectations
    against its exit code and/or output.

    """
    def __init__(self, ssh_context, name, command, working_directory=None,
                 environment=None, priority=Priority.NORMAL, use_sudo=False,
                 timeout=None, connection_retries=0, group=None, hosts=None):
        super(SshCommandValidation, self).__init__(
            ssh_context,
            name,
            priority=priority,
            timeout=timeout,
            connection_retries=connection_retries,
            group=group,
            hosts=hosts)

        self.command = command
        self.working_directory = working_directory  # Not supported yet
        self.environment = environment or {}        # Not supported yet
        self.use_sudo = use_sudo
        self.expectations = []

    def perform_on_host(self, host):
        """Runs the SSH Command on a host and checks to see if all expectations
        are met.

        """
        if self.use_sudo:
            output = sudo(self.command,
                          combine_stderr=True, timeout=self.timeout)
        else:
            output = run(self.command,
                         combine_stderr=True, timeout=self.timeout)
        exit_code = output.return_code
        for expectation in self.expectations:
            expectation.validate(self, host, output, exit_code)


class UpstartServiceValidation(SshCommandValidation):
    """Validates that the specified upstart process is in the specified state
    (e.g. running)

    """
    def __init__(self, ssh_context, service_name, service_state="running",
                 priority=Priority.NORMAL, timeout=None, group=None,
                 hosts=None):
        SshCommandValidation.__init__(self,
                                      ssh_context,
                                      "{0} service should be {1}"
                                      .format(service_name, service_state),
                                      "status {0}".format(service_name),
                                      use_sudo=True, timeout=None,
                                      group=group,
                                      hosts=hosts)
        self.expect_output_contains(service_state)


class LoadAverageValidation(SshValidation):
    """Validates that a server's load average falls within a set of
    parameters

    """

    def __init__(self, ssh_context, priority=Priority.NORMAL, timeout=None,
                 group=None, hosts=None):
        """Creates an SshLoadAverageValidation object"""
        SshValidation.__init__(self, ssh_context, "load average",
                               priority=priority, timeout=None, group=group,
                               hosts=hosts)
        # If a limit is None, then there is no limit.
        self.limits = {
            1: {'min': None, 'max': None},
            5: {'min': None, 'max': None},
            15: {'min': None, 'max': None}
        }

    def expect_min_1_minute_load(self, min_load):
        """expect a minimum 1 minute load"""
        self.limits[1]['min'] = min_load
        return self

    def expect_min_5_minute_load(self, min_load):
        """expect a minimum 5 minute load"""
        self.limits[5]['min'] = min_load
        return self

    def expect_min_15_minute_load(self, min_load):
        """expect a minimum 15 minute load"""
        self.limits[15]['min'] = min_load
        return self

    def expect_max_1_minute_load(self, max_load):
        """expect a maximum 1 minute load"""
        self.limits[1]['max'] = max_load
        return self

    def expect_max_5_minute_load(self, max_load):
        """expect a maximum 5 minute load"""
        self.limits[5]['max'] = max_load
        return self

    def expect_max_15_minute_load(self, max_load):
        """expect a maximum 15 minute load"""
        self.limits[15]['max'] = max_load
        return self

    def perform_on_host(self, host):
        """Runs the SSH Command on a host and checks to see if all expectations
        are met.

        """
        (load_1, load_5, load_15) = SshCommands.get_uptime()

        self.check(host, 1, load_1)
        self.check(host, 5, load_5)
        self.check(host, 15, load_15)

    def check(self, host, minutes, load):
        """Make sure that the n-minute load average for the given host is
        within the allowed range.

        """
        # Check if the maximum was exceeded (if it was defined)
        if self.limits[minutes]['max'] and load > self.limits[minutes]['max']:
            self.fail_on_host(host,
                              "{0} minute load too high on {1}.  " +
                              "Maximum Load: {2:.2f}, Current Load: {3:.2f}"
                              .format(minutes, host,
                                      self.limits[minutes]['max'],
                                      load))

        # Check if the Minimum was exceeded (if it was defined)
        if self.limits[minutes]['min'] and load < self.limits[minutes]['min']:
            self.fail_on_host(host,
                              "{0} minute load too low on {1}.  " +
                              "Minimum Load: {2:.2f}, Current Load: {3:.2f}"
                              .format(minutes, host,
                                      self.limits[minutes]['min'], load))

    def add_expectation(self, expectation):
        raise NotImplementedError

    def expect_exit_code(self, exit_code):
        raise NotImplementedError


class SshCommandExpectation(object):
    """Base class for expectations that can be placed on an SshValidation"""
    def __init__(self, validation):
        self.validation = validation

    def validate(self, validation, host, command_output, exit_code):
        """Defined by derived classes"""
        pass

    def fail_on_host(self, host, reason):
        """Report a failure and the host the failure occurred on"""
        self.validation.fail_on_host(host, reason)


class _ExitCodeEquals(SshCommandExpectation):
    """Expects that the exit code of an SSH command is equal to a
    specific value

    """
    def __init__(self, validation, exit_code):
        SshCommandExpectation.__init__(self, validation)
        self.exit_code = exit_code

    def validate(self, validation, host, command_output, exit_code):
        if exit_code != self.exit_code:
            self.fail_on_host(host,
                              "Exit Code should have been {0} but was {1}"
                              .format(self.exit_code, exit_code))


class OutputContains(SshCommandExpectation):
    """Expects that the output of an SSH command is contains specified text"""
    def __init__(self, validation, text):
        SshCommandExpectation.__init__(self, validation)
        self.text = text

    def validate(self, validation, host, command_output, exit_code):
        if self.text not in command_output:
            self.fail_on_host(host,
                              "Command output should contain: '{0}'.  " +
                              "Output: '{1}'"
                              .format(self.text, command_output))


class OutputDoesNotContain(SshCommandExpectation):
    """Expects that the output of an SSH command does not contain
    specified text

    """
    def __init__(self, validation, text):
        SshCommandExpectation.__init__(self, validation)
        self.text = text

    def validate(self, validation, host, command_output, exit_code):
        if self.text in command_output:
            self.fail_on_host(host,
                              "Command output should not contain: '{0}'.  " +
                              "Output: '{1}'"
                              .format(self.text, command_output))


class OutputLessThan(SshCommandExpectation):
    """Expects that the output of an SSH command is less than the
    specified value. This method casts the command_output string to a float
    to do the comparison.
    """
    def __init__(self, validation, value):
        SshCommandExpectation.__init__(self, validation)
        self.value = value

    def validate(self, validation, host, command_output, exit_code):
        command_output_as_float = float(command_output)
        if not command_output_as_float < self.value:
            self.fail_on_host(host,
                              "Command output greater than or equal to " +
                              "expected: '{0}'.  Output: '{1}'"
                              .format(self.value, str(command_output)))


class OutputGreaterThan(SshCommandExpectation):
    """Expects that the output of an SSH command is greater than the
    specified value. This method casts the command_output string to a float
    to do the comparison.
    """
    def __init__(self, validation, value):
        SshCommandExpectation.__init__(self, validation)
        self.value = value

    def validate(self, validation, host, command_output, exit_code):
        command_output_as_float = float(command_output)
        if not command_output_as_float > self.value:
            self.fail_on_host(host,
                              "Command output was less than or equal to " +
                              "expected: '{0}'.  Output: '{1}'"
                              .format(self.value, command_output))


UPTIME_REGEX = re.compile(r"load average: (\d+\.\d+), (\d+\.\d+), (\d+\.\d+)")


class SshCommands(object):
    """Some commands that might be helpful"""

    def __init__(self):
        pass

    @staticmethod
    def get_cpu_count():
        """return the number of processors on the server"""
        return int(run("grep processor /proc/cpuinfo | wc -l"))

    @staticmethod
    def get_uptime():
        """return the system uptime"""
        output = run("uptime")
        match = UPTIME_REGEX.search(output)
        if match:
            return (float(match.group(1)),
                    float(match.group(2)),
                    float(match.group(3)))
        else:
            pytest.fail("Could not get uptime.  Command output was: {0}"
                        .format(output))
