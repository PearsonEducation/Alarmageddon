"""Validation for RabbitMQ"""

import time

from alarmageddon.validations.validation import Validation, Priority

from pika import ConnectionParameters
from pika.adapters import BlockingConnection
from pika.credentials import PlainCredentials
from pika.exceptions import AMQPError


class RabbitMqContext(object):
    """information needed to connect and interact with RabbitMQ"""
    def __init__(self, host, port, user_name, password):
        self.host = host
        self.port = port
        self.user_name = user_name
        self.password = password

    def get_credentials(self):
        """get "plain" credentials based on this object's user name and
        password

        """
        return PlainCredentials(self.user_name, self.password)

    def get_connection(self, timeout=None):
        """Connects to RabbitMQ and returns the connection object

        Third Party (pika) Bug: https://github.com/pika/pika/issues/354 - Once
        this bug is fixed we can take out our own retrying logic and use pika's
        retry logic.  In the mean time, connection failure messages will be
        inaccurate; they'll say that only one connection attempt was made.

        """
        return BlockingConnection(
            ConnectionParameters(host=self.host,
                                 credentials=self.get_credentials(),
                                 connection_attempts=1,
                                 retry_delay=0,
                                 socket_timeout=timeout))


class RabbitMqValidation(Validation):
    """A Validation that can be held against a RabbitMQ server"""
    def __init__(self, rabbitmq_context, name, queue_name, max_queue_size,
                 priority=Priority.NORMAL, timeout=None, num_attempts=4,
                 seconds_between_attempts=2, group=None,
                 ignore_connection_failure=False):
        """Creates a RabbitMqValidation object."""
        super(RabbitMqValidation, self).__init__(
            ("queue '{0}' should have less than {1} messages in in " +
            "it on RabbitMQ host: '{2}' ({3})")
            .format(queue_name, max_queue_size, rabbitmq_context.host, name),
            priority=priority, timeout=timeout, group=group)

        self.rabbitmq_context = rabbitmq_context
        self.max_queue_size = max_queue_size
        self.queue_name = queue_name
        self.num_attempts = num_attempts
        self.seconds_between_attempts = seconds_between_attempts
        self.ignore_connection_failure = ignore_connection_failure

    def perform(self, group_failures):
        """Perform the validation.  If the validation fails, call self.fail
        passing it the reason for the failure.

        """
        try:
            (conn, chan) = self._connect()
        except AMQPError, ex:
            #if we're here we're intentionally ignoring the failure
            return

        try:
            queue = chan.queue_declare(self.queue_name, passive=True)
            message_count = queue.method.message_count

            if message_count > self.max_queue_size:
                self.fail("Too many messages in queue ({0} messages)."
                          .format(message_count))

        except AMQPError, ex:
            self.fail("RabbitMQ exception throw from host: {0}.  {1}"
                      .format(self.rabbitmq_context.host, repr(ex)))

        finally:
            if conn:
                conn.close()

    def _connect(self):
        """connect to the RabbitMQ server"""
        for attempt in range(1, self.num_attempts + 1):
            try:
                conn = self.rabbitmq_context.get_connection(self.timeout)
                chan = conn.channel()
                return (conn, chan)
            except AMQPError, ex:
                if attempt >= self.num_attempts:
                    if self.ignore_connection_failure:
                        raise ex
                    else:
                        self.fail(
                            "Could not access RabbitMQ host {0} because {1}"
                            .format(self.rabbitmq_context.host, repr(ex)))
                else:
                    time.sleep(self.seconds_between_attempts)
