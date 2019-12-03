"""Support for publishing via e-mail.

Please refer to the **[SPHINX DOCUMENTATION]** for a detailed usage explanation

"""

from alarmageddon.publishing.publisher import Publisher
from jinja2 import Template, Environment, FileSystemLoader, Undefined

import smtplib

#from email.MIMEMultipart import MIMEMultipart
#from email.MIMEText import MIMEText
from six.moves.email_mime_text import MIMEText
from six.moves.email_mime_multipart import MIMEMultipart
from email import utils

import logging

logger = logging.getLogger(__name__)


def enrich(validation, email_settings, runtime_context=None):
    """ Enriches the validation with a custom email message.

    :param validation: The validation object.
    :param email_settings: A dictionary object containing settings for email
      subject, body, sender and recipients. See below for details.
    :param runtime_context: - Additional replacement context settings available
      at runtime. See below for details.

    email_settings should be a dictionary of the form:
        {
         "email_type": "An environment-specific e-mail type as
                        defined in the email publisher config",
         "subject": "The name of the Jinja template for the e-mail subject",

         "body": "The name of the Jinja template for the e-mail body",

         "sender": "A dictionary of the form
                   {"real_name": "Real Name", "address": "email@address.com"}",
         "recipients": "An iterable of dicionaries of the form
                    {"real_name": "Real Name", "address": "email@address.com"}"
        }

    Note that the location of the Jinja templates is defined in the email
    publisher config.

    runtime_context is a dictionary whose values are consumed at runtime inside
    the Jinja templates defined in email_settings.

    """

    logger.debug("Enriching {}".format(validation))

    if not validation:
        raise ValueError("validation is required.")

    if not email_settings:
        raise ValueError("email_settings are required.")
    else:
        if not "email_type" in email_settings:
            raise KeyError("email_settings.email_type is required.")
        if not "subject" in email_settings:
            raise KeyError("email_settings.subject template is required.")
        if not "body" in email_settings:
            raise KeyError("email_settings.body template name is required.")
        if not "sender" in email_settings:
            raise KeyError("email_settings.sender is required.")
        if not "recipients" in email_settings:
            raise KeyError("email_settings.recipients are required.")

    if not runtime_context:
        runtime_context = {}

    enrichment = {'email_settings': email_settings,
                  'runtime_context': runtime_context}

    #hack because we need an instance. there is probably a better way
    temp_pub = EmailPublisher({"fake": "config"})

    validation.enrich(temp_pub, enrichment, force_namespace=True)
    return validation


class SilentUndefined(Undefined):
    """Dont break pageloads because vars arent there!"""
    def _fail_with_undefined_error(self, *args, **kwargs):
        """jinja2 hack to allow silent ignoring of missing values."""
        return None


class SimpleEmailPublisher(Publisher):
    """A publisher that publishes incidents to e-mail.

    :param config: A config object containing email config information. See
      below for a detailed description.
    :param email_notifications_config_key: The config key that contains
      the email configuration.
    :param name: The name of the publisher.
    :param defaults: Default email templating values.
    :param priority_threshold: Will publish validations of this priority or
      higher if they are appropriately enriched.
    :param connect_timeout_seconds: How long to attempt to connect to the SMTP
      server.
    :param environment: The environment that tests are being run in.
    """

    def __init__(self, sender_address, recipient_addresses,
                 host=None, port=None, name='EmailPublisher',
                 priority_threshold=None, connect_timeout_seconds=10,
                 environment=None):

        Publisher.__init__(self, name,
                           priority_threshold=priority_threshold,
                           environment=environment)

        # Set the initial replacement context to the defaults.
        # Overrides will be applied to this dictionary individually.
        self._connect_timeout = connect_timeout_seconds
        self.sender_address = None
        self.recipient_addresses = []
        if sender_address:
            self.sender_address = self.configure_sender(sender_address)
        if recipient_addresses:
            self.recipient_addresses =\
                self.configure_recipients(recipient_addresses)
        self.host = host
        self.port = port

    def __repr__(self):
        return "{}: sender {}, recipient {}, host {}, port {}, timeout {}".format(
                    type(self).__name__, self.sender_address,
                    self.recipient_addresses, self.host, self.port,
                    self._connect_timeout)

    def send(self, result):
        """Constructs a message from a result and send it as an email.

        This will only send if the priority threshold is met **and** the
        original validation was appropriately enriched.

        :param result: The result to publish.

        """

        logger.debug("Checking if we should send {}".format(result))
        if result.is_failure() and self.will_publish(result):

            message_body = result.description()

            message_subject = result.test_name()

            msg = self.configure_message(self.sender_address,
                                         self.recipient_addresses,
                                         message_subject,
                                         message_body)

            logger.debug("Sending {} to {} from server {}:{}".format(result, self.recipient_addresses, self.host, self.port))

            """ A note regarding recipient addresses:

                smtplib.sendmail requires that multiple recipient addresses
                are structured as an array of addresses.

                MIMEMultipart messages require that multiple recipients
                are structured as a comma-separated list.
            """
            smtpObj = self.configure_smtp_object(self.host, self.port)
            smtpObj.sendmail(msg['From'],
                             self.recipient_addresses,
                             msg.as_string())

    def configure_message(self, sender_address, recipient_addresses,
                          subject, body):
        """ Creates a MIMEMultipart message with a plain-text body.

        :param sender_address: The address the message will be sent from.
        :param recipient_addresses: The addresses the message will be sent to.
        :param subject: The subject of the email.
        :param body: The body of the email.

        """
        msg = MIMEMultipart()

        msg['Subject'] = subject
        msg['From'] = sender_address

        # MIMEMultipart requires the 'To' header to be a comma separated list
        msg['To'] = ", ".join(recipient_addresses)
        msg.attach(MIMEText(body, 'plain'))

        return msg

    def configure_sender(self, sender):
        """Properly formats the sender address.

        :param sender: A dictionary containing information about the sender.

        """
        return utils.formataddr((sender['real_name'], sender['address']))

    def configure_recipients(self, recipients):
        """Properly formats the list of recipient addresses.

        :param recipients: A list containing dictionaries of information about
          the recipients.

        """
        # Recipients are expected to be in an
        # array of objects containing {real_name, address}

        addresses = []

        for recipient in recipients:
            addresses.append(utils.formataddr((recipient['real_name'],
                                               recipient['address'])))

        # sendmail requires the recipients to be an array of addresses
        return addresses

    def configure_smtp_object(self, host, port):
        """Helper method to configure the SMTP object."""

        if not(host and port):
            if not(host):
                # If host isn't specified, try localhost
                smtpObj = smtplib.SMTP('localhost',
                                       timeout=self._connect_timeout)
            else:
                # otherwise, use the host with the default port
                smtpObj = smtplib.SMTP(host,
                                       timeout=self._connect_timeout)
        else:
            smtpObj = smtplib.SMTP(host, port, timeout=self._connect_timeout)

        return smtpObj


class EmailPublisher(SimpleEmailPublisher):
    """A publisher that publishes incidents to e-mail.

    For validations to be published by this publisher, they must be enriched
    with additional data. See :py:func:.emailer.enrich

    :param config: A config object containing email config information. See
      below for a detailed description.
    :param email_notifications_config_key: The config key that contains
      the email configuration.
    :param name: The name of the publisher.
    :param defaults: Default email templating values.
    :param priority_threshold: Will publish validations of this priority or
      higher if they are appropriately enriched.
    :param connect_timeout_seconds: How long to attempt to connect to the SMTP
      server.
    :param environment: The environment that tests are being run in.

    config is an Alarmageddon config object that contains at least the
    following:
      {email_template_directory : Directory containing the e-mail templates.
        Can be relative to the location of the alarmageddon script or an
        absolute directory location,
       environment : EMAIL_NOTIFICATIONS

    Where EMAIL_NOTIFICATIONS is a dictionary of the form:
        "email_notifications" : {
                EMAIL_TYPE: {
                   "email_recipients" : [
                       {"real_name" : "Some other recipient",
                        "address" : "email@address.com"},...
                   ],
                   "email_custom_message" : "Custom email message. Can contain
                     Jinja replacement tokens."
                 },...
             }
        }

    and EMAIL_TYPE is a name that will identify which validations should
    use that config.

    """

    EMAIL_NOTIFICATIONS_CONFIG_KEY = 'email_notifications'

    def __init__(self, config, email_notifications_config_key=None,
                 name='EmailPublisher', defaults=None,
                 priority_threshold=None, connect_timeout_seconds=10,
                 environment=None):

        if not config:
            raise ValueError("config parameter is required.")

        if defaults is None:
            defaults = {}

        SimpleEmailPublisher.__init__(self, None, None, name=name,
                                priority_threshold=priority_threshold,
                                environment=environment)

        # Set the initial replacement context to the defaults.
        # Overrides will be applied to this dictionary individually.
        self._replacement_context = defaults
        self._config = config
        self._template_environment = None
        self._connect_timeout = connect_timeout_seconds
        if not email_notifications_config_key:
            self._email_notifications_config_key = \
                self.EMAIL_NOTIFICATIONS_CONFIG_KEY
        else:
            self._email_notifications_config_key = \
                email_notifications_config_key

    def __repr__(self):
        return "{}: replacement {}, config {}, env {}, timeout {}, key {}".format(
                    type(self).__name__, self._replacement_context, self._config,
                    self._template_environment, self._connect_timeout,
                    self._email_notifications_config_key)

    def send(self, result):
        """Constructs a message from a result and send it as an email.

        This will only send if the priority threshold is met **and** the
        original validation was appropriately enriched.

        :param result: The result to publish.

        """

        if result.is_failure() and self.will_publish(result):
            self.configure_replacement_context(result)

            fileSystemLoader =\
                FileSystemLoader(self._config['email_template_directory'])

            self._template_environment = Environment(loader=fileSystemLoader,
                                                     undefined=SilentUndefined)

            email_settings = self.get_email_settings(result)

            recipient_addresses =\
                self.configure_recipients(email_settings['recipients'])

            sender_address = self.configure_sender(email_settings['sender'])

            message_body = self.replace_tokens(email_settings['body'],
                                               self._replacement_context)

            message_subject = self.replace_tokens(email_settings['subject'],
                                                  self._replacement_context)

            msg = self.configure_message(sender_address,
                                         recipient_addresses,
                                         message_subject,
                                         message_body)

            """ A note regarding recipient addresses:

                smtplib.sendmail requires that multiple recipient addresses
                are structured as an array of addresses.

                MIMEMultipart messages require that multiple recipients
                are structured as a comma-separated list.
            """
            if 'email_host' in self._config:
                host = self._config['email_host']
            if 'email_port' in self._config:
                port = self._config['email_port']

            smtpObj = self.configure_smtp_object(host, port)
            smtpObj.sendmail(msg['From'], recipient_addresses, msg.as_string())

    def replace_tokens(self, template, token_dictionary):
        """Replace templated values with their contents.

        Loops multiple times, to handle the case of a template that contains
        templates.

        Templates should be valid Jinja templates:
            http://jinja.pocoo.org/

        :param template: The template string.
        :param token_dictionary: A mapping from template names to values.

        """
        # Loop over the string five times in case
        # tokens have tokens inside them.
        tokenized_template = self._template_environment.get_template(template)
        detokenized_string = tokenized_template.render(token_dictionary)

        if "{{" in detokenized_string:
            for _num in range(1, 4):
                tokenized_template = Template(detokenized_string,
                                              undefined=SilentUndefined)

                detokenized_string = tokenized_template\
                                      .render(token_dictionary)

        return detokenized_string

    """ To implement a custom email publisher, override the methods below """

    def _can_publish(self, result):
        """Determines if the email validation has the required enrichment.

        :param result: The result to be published.

        """
        try:
            email_settings = self.get_email_settings(result)

            email_settings['email_type']
            email_settings['subject']
            email_settings['body']
            email_settings['sender']
            email_settings['recipients']
            return True
        except (AttributeError, KeyError):
            return False

    def configure_replacement_context(self, result):
        """ Configures the replacement context for this email publisher

            Supported template variables:

            {{test_name}}
            The name of the test.

            {{test_description}}
            The description of the failure.

            {{env}}
            The environment name.

            {{email_custom_message}}
            A custom message used in email alerts. This field can be used to
            summarize a particular type of alert or include additional details

            Runtime Context:
            All dictionary items contained in runtime context are available.

            :param result: The test result whose values will populate the
              replacement context.
        """

        # Configure the replacement context
        if result.test_name():
            self._replacement_context['test_name'] = result.test_name()

        if result.description():
            self._replacement_context['test_description'] = \
                result.description()

        if self._config.environment_name():
            self._replacement_context['env'] = self._config.environment_name()

        email_settings = self.get_email_settings(result)
        if 'email_type' in email_settings:
            email_type = email_settings['email_type']
            self._replacement_context['email_type'] = email_type

            email_config_key = self._email_notifications_config_key
            email_config = \
                self._config.environment_config[email_config_key]

            if email_type in email_config:
                email_config_settings = email_config[email_type]

                if 'email_custom_message' in email_config_settings:
                    self._replacement_context['email_custom_message'] = \
                        email_config_settings['email_custom_message']

        runtime_context = self.get_runtime_context(result)
        if runtime_context is not None:
            self._replacement_context.update(self.get_runtime_context(result))

    def get_email_settings(self, result):
        """Returns the email settings of the given result."""
        return result.validation.get_enriched(self, True)['email_settings']

    def get_runtime_context(self, result):
        """Returns the runtime context of the given result."""
        return result.validation.get_enriched(self, True)['runtime_context']
