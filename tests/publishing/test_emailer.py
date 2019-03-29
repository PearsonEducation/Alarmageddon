import alarmageddon.publishing.emailer as emailer
from alarmageddon.publishing.emailer import EmailPublisher, SimpleEmailPublisher
from alarmageddon.publishing.emailer import SilentUndefined
from alarmageddon.validations.validation import Priority
from alarmageddon.validations.http import HttpValidation
from alarmageddon.config import Config
from alarmageddon.result import Failure
from alarmageddon.result import Success
from jinja2 import Environment, FileSystemLoader
import json
import pytest
import socket
import smtplib

def test_simple_email_repr(smtpserver):
    email_pub = SimpleEmailPublisher({"real_name": "test", "address": "test@test.com"},
                                     [{"real_name": "test", "address": "test@test.com"}],
                                     host=smtpserver.addr[0], port=smtpserver.addr[1])
    email_pub.__repr__()


def test_simple_email_str(smtpserver):
    email_pub = SimpleEmailPublisher({"real_name": "test", "address": "test@test.com"},
                                     [{"real_name": "test", "address": "test@test.com"}],
                                     host=smtpserver.addr[0], port=smtpserver.addr[1])
    str(email_pub)


def test_simple_email(httpserver, smtpserver):
    email_pub = SimpleEmailPublisher({"real_name": "test", "address": "test@test.com"},
                                     [{"real_name": "test", "address": "test@test.com"}],
                                     host=smtpserver.addr[0], port=smtpserver.addr[1])
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    result = Failure("Check Status Route", http_validator,
                     description="Validation failure message")
    email_pub.send(result)
    assert len(smtpserver.outbox) == 1
    payload = str(smtpserver.outbox[0].get_payload()[0])
    assert payload.split("\n")[-1] == "Validation failure message"


def test_requires_config():
    with pytest.raises(ValueError):
        EmailPublisher(config=None)


def test_email_publisher_repr(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    email_pub = EmailPublisher(config)
    email_pub.__repr__()


def test_email_publisher_str(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    email_pub = EmailPublisher(config)
    str(email_pub)


def test_email_publisher_with_defaults(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    email_pub = EmailPublisher(config)
    assert email_pub._replacement_context == {}
    assert email_pub._config['email_host'] == smtpserver.addr[0]
    assert email_pub._config['email_port'] == smtpserver.addr[1]
    assert email_pub._email_notifications_config_key == \
        EmailPublisher.EMAIL_NOTIFICATIONS_CONFIG_KEY
    assert email_pub.name() == "EmailPublisher"
    assert email_pub.priority_threshold is None
    assert email_pub._connect_timeout == 10


def test_email_publisher_with_replacement_context_defaults(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    general_defaults = config['email_defaults']['general']
    email_pub = EmailPublisher(config, defaults=general_defaults)
    sender = email_pub._replacement_context['email_sender']['real_name']
    recipient = \
        email_pub._replacement_context['email_recipients'][0]['real_name']
    assert sender == "Alarmageddon Monitor"
    assert recipient == "Test Recipient"


def test_email_publisher_with_custom_config_key(tmpdir, smtpserver):
    config = create_configuration(tmpdir, config_key="email_settings",
                                  smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    email_pub = EmailPublisher(config,
                               email_notifications_config_key="email_settings")
    assert email_pub._email_notifications_config_key == "email_settings"


def test_email_publisher_with_custom_name(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    email_pub = EmailPublisher(config, name="Custom Name")
    assert email_pub.name() == "Custom Name"


def test_email_publisher_with_custom_defaults(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    default_replacement_context = {"custom_replacement": "hello world"}
    email_pub = EmailPublisher(config, defaults=default_replacement_context)
    assert email_pub._replacement_context['custom_replacement'] == \
        "hello world"


def test_email_publisher_with_custom_priority(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    email_pub = EmailPublisher(config, priority_threshold=Priority.CRITICAL)
    assert email_pub.priority_threshold == Priority.CRITICAL


def test_email_publisher_with_custom_timeout_seconds(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    timeout_seconds = 15
    email_pub = EmailPublisher(config, connect_timeout_seconds=timeout_seconds)
    assert email_pub._connect_timeout == timeout_seconds


def test_configure_sender(tmpdir, smtpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    sender = email_pub._config['email_defaults']['general']['email_sender']
    configured_sender = email_pub.configure_sender(sender)
    assert configured_sender == \
        "Alarmageddon Monitor <noreply@alarmageddon.com>"


def test_configure_single_recipient(tmpdir, smtpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    recipients = \
        email_pub._config['email_defaults']['general']['email_recipients']
    configured_recipient = email_pub.configure_recipients(recipients)
    assert configured_recipient[0] == \
        "Test Recipient <testrecipient@alarmageddon.com>"


def test_configure_multiple_recipients(tmpdir, smtpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    email_config = \
        email_pub._config['environment']['test']['email_notifications']
    recipients = email_config['test_alert']['email_recipients']
    configured_recipients = email_pub.configure_recipients(recipients)
    assert configured_recipients[0] == \
        "Test Recipient Override 1 <testrecipientoverride1@alarmageddon.com>"
    assert configured_recipients[1] == \
        "Test Recipient Override 2 <testrecipientoverride2@alarmageddon.com>"


def test_configure_message_single_recipient(tmpdir, smtpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    email_sender = \
        email_pub._config['email_defaults']['general']['email_sender']
    configured_sender = email_pub.configure_sender(email_sender)
    email_recipients = \
        email_pub._config['email_defaults']['general']['email_recipients']
    configured_recipient = email_pub.configure_recipients(email_recipients)
    msg = email_pub.configure_message(configured_sender,
                                      configured_recipient,
                                      "Test Subject",
                                      "Test Body")
    assert msg['Subject'] == "Test Subject"
    assert msg['From'] == "Alarmageddon Monitor <noreply@alarmageddon.com>"
    assert msg['To'] == "Test Recipient <testrecipient@alarmageddon.com>"
    assert str(msg.get_payload()[0]).split('\n')[5] == "Test Body"


def test_configure_message_multiple_recipients(tmpdir, smtpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    email_sender = \
        email_pub._config['email_defaults']['general']['email_sender']
    configured_sender = email_pub.configure_sender(email_sender)
    email_config = \
        email_pub._config['environment']['test']['email_notifications']
    email_recipients = email_config['test_alert']['email_recipients']
    configured_recipients = email_pub.configure_recipients(email_recipients)
    msg = email_pub.configure_message(configured_sender, configured_recipients,
                                      "Test Subject", "Test Body")
    assert msg['Subject'] == "Test Subject"
    assert msg['From'] == "Alarmageddon Monitor <noreply@alarmageddon.com>"
    assert msg['To'] == \
        "Test Recipient Override 1 <testrecipientoverride1@alarmageddon.com>,"\
        " Test Recipient Override 2 <testrecipientoverride2@alarmageddon.com>"
    assert str(msg.get_payload()[0]).split('\n')[5] == "Test Body"


def test_configure_smtp_object(tmpdir, smtpserver, monkeypatch):
    monkeypatch.setattr(smtplib.SMTP, "__init__", mock_smtp_init)
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    email_pub = EmailPublisher(config)
    smtp_obj = email_pub.configure_smtp_object(smtpserver.addr[0],
                                               smtpserver.addr[1])
    assert smtp_obj._host == smtpserver.addr[0]
    assert smtp_obj._port == smtpserver.addr[1]


def test_configure_smtp_object_no_port(tmpdir, smtpserver, monkeypatch):
    monkeypatch.setattr(smtplib.SMTP, "__init__", mock_smtp_init)
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0])
    email_pub = EmailPublisher(config)
    smtp_obj = email_pub.configure_smtp_object(smtpserver.addr[0], None)
    assert smtp_obj._host == smtpserver.addr[0]
    assert smtp_obj._port == 0


def test_configure_smtp_object_no_host(tmpdir, smtpserver, monkeypatch):
    monkeypatch.setattr(smtplib.SMTP, "__init__", mock_smtp_init)
    config = create_configuration(tmpdir, smtp_port=str(smtpserver.addr[1]))
    email_pub = EmailPublisher(config)
    smtp_obj = email_pub.configure_smtp_object(None, smtpserver.addr[1])
    assert smtp_obj._host == "localhost"


def test_configure_smtp_object_custom_timeout(tmpdir, smtpserver, monkeypatch):
    monkeypatch.setattr(smtplib.SMTP, "__init__", mock_smtp_init)
    config = create_configuration(tmpdir, smtp_port=str(smtpserver.addr[1]))
    timeout_seconds = 15
    email_pub = EmailPublisher(config, connect_timeout_seconds=timeout_seconds)
    smtp_obj = email_pub.configure_smtp_object(smtpserver.addr[0],
                                               smtpserver.addr[1])
    assert smtp_obj._timeout == timeout_seconds


def test_replace_tokens(tmpdir, smtpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    template_loader = \
        FileSystemLoader(email_pub._config['email_template_directory'])
    email_pub._template_environment = Environment(loader=template_loader,
                                                  undefined=SilentUndefined)
    create_subject_template(tmpdir)
    replacement_context = {"env": "test", "test_name": "test name"}
    detokenized_template = email_pub.replace_tokens("default_subject.template",
                                                    replacement_context)
    assert detokenized_template == "Validation Failure in test: test name"


def test_replace_nested_tokens(tmpdir, smtpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    template_loader = \
        FileSystemLoader(email_pub._config['email_template_directory'])
    email_pub._template_environment = Environment(loader=template_loader,
                                                  undefined=SilentUndefined)
    create_subject_template(tmpdir)
    replacement_context = {"env": "{{nested_token}}",
                           "test_name": "test name",
                           "nested_token": "test"}
    detokenized_template = email_pub.replace_tokens("default_subject.template",
                                                    replacement_context)
    assert detokenized_template == "Validation Failure in test: test name"


def test_enrich(httpserver):
    httpserver.serve_content("Not Found", 404)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }

    runtime_context = {"custom_override": "hello world"}
    emailer.enrich(http_validator, email_settings, runtime_context)
    temp_pub = EmailPublisher({"fake": "config"})
    data = http_validator.get_enriched(temp_pub)
    assert data["email_settings"] == email_settings
    assert data["runtime_context"] == runtime_context


def test_enrich_no_runtime_context(httpserver):
    httpserver.serve_content("Not Found", 404)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }

    emailer.enrich(http_validator, email_settings)
    temp_pub = EmailPublisher({"fake": "config"})
    data = http_validator.get_enriched(temp_pub)
    assert data["email_settings"] == email_settings
    assert data["runtime_context"] == {}


def test_enrich_requires_validator():
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    with pytest.raises(ValueError):
        emailer.enrich(None, email_settings)


def test_enrich_requires_email_type(httpserver):
    httpserver.serve_content("Not Found", 404)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    with pytest.raises(KeyError):
        emailer.enrich(http_validator, email_settings)


def test_enrich_requires_subject(httpserver):
    httpserver.serve_content("Not Found", 404)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    with pytest.raises(KeyError):
        emailer.enrich(http_validator, email_settings)


def test_enrich_requires_body(httpserver):
    httpserver.serve_content("Not Found", 404)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    with pytest.raises(KeyError):
        emailer.enrich(http_validator, email_settings)


def test_enrich_requires_sender(httpserver):
    httpserver.serve_content("Not Found", 404)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    with pytest.raises(KeyError):
        emailer.enrich(http_validator, email_settings)


def test_enrich_requires_recipients(httpserver):
    httpserver.serve_content("Not Found", 404)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"}
                      }
    with pytest.raises(KeyError):
        emailer.enrich(http_validator, email_settings)


def test_can_publish(tmpdir, smtpserver, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    emailer.enrich(http_validator, email_settings)
    result = Success("validation name", http_validator)
    assert email_pub._can_publish(result) is True


def test_can_publish_requires_enrichment(tmpdir, smtpserver, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    result = Success("validation name", http_validator)
    assert email_pub._can_publish(result) is False


def test_can_publish_requires_email_type(tmpdir, smtpserver,
                                         monkeypatch, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    emailer.enrich(http_validator, email_settings)
    temp_pub = EmailPublisher({"fake": "config"})
    data = http_validator.get_enriched(temp_pub)
    monkeypatch.delitem(data['email_settings'], "email_type")
    result = Success("validation name", http_validator)
    assert email_pub._can_publish(result) is False


def test_can_publish_requires_subject(tmpdir, smtpserver,
                                      monkeypatch, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    emailer.enrich(http_validator, email_settings)
    temp_pub = EmailPublisher({"fake": "config"})
    data = http_validator.get_enriched(temp_pub)
    monkeypatch.delitem(data['email_settings'], "subject")
    result = Success("validation name", http_validator)
    assert email_pub._can_publish(result) is False


def test_can_publish_requires_body(tmpdir, smtpserver,
                                   monkeypatch, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    emailer.enrich(http_validator, email_settings)
    temp_pub = EmailPublisher({"fake": "config"})
    data = http_validator.get_enriched(temp_pub)
    monkeypatch.delitem(data['email_settings'], "body")
    result = Success("validation name", http_validator)
    assert email_pub._can_publish(result) is False


def test_can_publish_requires_sender(tmpdir, smtpserver,
                                     monkeypatch, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    emailer.enrich(http_validator, email_settings)
    temp_pub = EmailPublisher({"fake": "config"})
    data = http_validator.get_enriched(temp_pub)
    monkeypatch.delitem(data['email_settings'], "sender")
    result = Success("validation name", http_validator)
    assert email_pub._can_publish(result) is False


def test_can_publish_requires_recipients(tmpdir, smtpserver,
                                         monkeypatch, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    emailer.enrich(http_validator, email_settings)
    temp_pub = EmailPublisher({"fake": "config"})
    data = http_validator.get_enriched(temp_pub)
    monkeypatch.delitem(data['email_settings'], "recipients")
    result = Success("validation name", http_validator)
    assert email_pub._can_publish(result) is False


def test_get_email_settings(tmpdir, smtpserver, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_type = "test_alert"
    subject = "subject test line"
    body = "body test"
    recipient_array = [{"real_name": "Test Recipient",
                        "address": "testrecipient@alarmageddon.com"}]
    sender = {"real_name": "Alarmageddon Monitor",
              "address": "noreply@alarmageddon.com"}
    email_settings = {"email_type": email_type,
                      "subject": subject,
                      "body": body,
                      "sender": sender,
                      "recipients": recipient_array
                      }
    emailer.enrich(http_validator, email_settings)
    result = Success("validation name", http_validator)
    enriched_email_settings = email_pub.get_email_settings(result)
    assert enriched_email_settings['email_type'] == email_type
    assert enriched_email_settings['subject'] == subject
    assert enriched_email_settings['body'] == body
    assert enriched_email_settings['sender'] == sender
    assert enriched_email_settings['recipients'] == recipient_array


def test_get_runtime_context(tmpdir, smtpserver, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_type = "test_alert"
    subject = "subject test line"
    body = "body test"
    recipient_array = [{"real_name": "Test Recipient",
                        "address": "testrecipient@alarmageddon.com"}]
    sender = {"real_name": "Alarmageddon Monitor",
              "address": "noreply@alarmageddon.com"}
    email_settings = {"email_type": email_type,
                      "subject": subject,
                      "body": body,
                      "sender": sender,
                      "recipients": recipient_array
                      }
    context = {"custom_replacement": "hello world"}
    emailer.enrich(http_validator, email_settings, runtime_context=context)
    result = Success("validation name", http_validator)
    enriched_context = email_pub.get_runtime_context(result)
    assert enriched_context['custom_replacement'] == "hello world"


def test_get_runtime_context_no_context(tmpdir, smtpserver, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_type = "test_alert"
    subject = "subject test line"
    body = "body test"
    recipient_array = [{"real_name": "Test Recipient",
                        "address": "testrecipient@alarmageddon.com"}]
    sender = {"real_name": "Alarmageddon Monitor",
              "address": "noreply@alarmageddon.com"}
    email_settings = {"email_type": email_type,
                      "subject": subject,
                      "body": body,
                      "sender": sender,
                      "recipients": recipient_array
                      }
    emailer.enrich(http_validator, email_settings)
    result = Success("validation name", http_validator)
    enriched_context = email_pub.get_runtime_context(result)
    assert enriched_context == {}


def test_configure_replacement_context_email_type_missing(tmpdir, smtpserver,
                                                          httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "default",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    emailer.enrich(http_validator, email_settings)
    result = Failure("validation name",
                     http_validator,
                     description="A failure occurred.")
    email_pub.configure_replacement_context(result)
    replacement_context = email_pub._replacement_context
    assert replacement_context["test_name"] == "validation name"
    assert replacement_context["test_description"] == "A failure occurred."
    assert replacement_context["env"] == "test"
    assert replacement_context["email_type"] == "default"
    assert replacement_context["email_custom_message"] == ""


def test_configure_replacement_context_email_type_found(tmpdir, smtpserver,
                                                        httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    email_settings = {"email_type": "test_alert",
                      "subject": "subject test line",
                      "body": "body test",
                      "sender": {"real_name": "Alarmageddon Monitor",
                                 "address": "noreply@alarmageddon.com"},
                      "recipients": [{"real_name": "Test Recipient",
                                      "address":
                                      "testrecipient@alarmageddon.com"}]
                      }
    emailer.enrich(http_validator, email_settings)
    result = Failure("validation name", http_validator,
                     description="A failure occurred.")
    email_pub.configure_replacement_context(result)
    replacement_context = email_pub._replacement_context
    assert replacement_context["test_name"] == "validation name"
    assert replacement_context["test_description"] == "A failure occurred."
    assert replacement_context["env"] == "test"
    assert replacement_context["email_type"] == "test_alert"
    assert replacement_context["email_custom_message"] == \
        "Validation failed in environment {{env}}: {{test_name}}."


def test_send(tmpdir, smtpserver, httpserver):
    email_pub = create_default_email_publisher(tmpdir, smtpserver)
    create_subject_template(tmpdir)
    create_body_template(tmpdir)
    http_validator = \
        HttpValidation.get(httpserver.url).expect_status_codes([200])
    general_defaults = email_pub._config["email_defaults"]["general"]
    email_settings = {"email_type": "test_alert",
                      "subject": general_defaults["email_subject_template"],
                      "body": general_defaults["email_template"],
                      "sender": general_defaults["email_sender"],
                      "recipients": general_defaults["email_recipients"]}
    emailer.enrich(http_validator, email_settings)
    failure_message = "Validation failure. Expected 200, received 404."
    result = Failure("Check Status Route", http_validator,
                     description=failure_message)
    email_pub.send(result)
    print(smtpserver.outbox[0])
    assert len(smtpserver.outbox) == 1
    payload = str(smtpserver.outbox[0].get_payload()[0])
    assert payload.split('\n')[5] == "Validation Failure in environment test:"
    assert payload.split('\n')[6] == "Test Name: [Check Status Route]"
    assert payload.split('\n')[7] == \
        "Test Description: [Validation failure. Expected 200, received 404.]"
    custom_message = "Custom Message: [Validation failed in environment " \
                     "test: Check Status Route.]"
    assert payload.split('\n')[8] == custom_message


def mock_smtp_init(self, host='', port=0, local_hostname=None,
                   timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
    self._host = host
    self._port = port
    self._local_hostname = local_hostname
    self._timeout = timeout


def create_default_email_publisher(tmpdir, smtpserver):
    config = create_configuration(tmpdir, smtp_host=smtpserver.addr[0],
                                  smtp_port=str(smtpserver.addr[1]))
    return EmailPublisher(config, defaults=config["email_defaults"]["general"])


def create_configuration(template_directory,
                         environment_name="test",
                         config_key="email_notifications",
                         smtp_host=None,
                         smtp_port=None,
                         subject_template_name=None,
                         subject_template_content=None,
                         body_template_name=None,
                         body_template_content=None):
    """ Create a complete test configuration using the specified parameters
        template_directory - [Required] A directory location for templates.
                                        Must be a py.path.local object.
        environment_name - [Optional] The name of the environment.
                                      Corresponds to environment-specific email
                                      configuration. Defaults to "test".
        config_key - [Optional] The email notification config section key.
                                Defaults to "email_notifications".
        smtp_host - [Optional] SMTP server host name. Must be a string.
                               Defaults to null value.
        smtp_port - [Optional] SMTP server port number. Must be an integer.
                               Defaults to null value.
        subject_template_name - [Optional] The name of the template to create.
                                           Defaults to
                                           "default_subject.template".
        subject_template_content - [Optional] Allows tests to override default
                                              content written to the template.
                                              Must be a valid string. Defaults
                                              to the default.template.
        body_template_name - [Optional] The name of the template to create.
                                        Defaults to "default_subject.template".
        body_template_content - [Optional] Allows tests to override default
                                           content written to the template.
                                           Must be a valid string. Defaults to
                                           the default template.
    """
    email_template_directory = template_directory.mkdir("email_templates")

    body_template = create_body_template(email_template_directory,
                                         body_template_name,
                                         body_template_content)
    subject_template = create_subject_template(email_template_directory,
                                               subject_template_name,
                                               subject_template_content)

    json_config = create_json_config(str(email_template_directory),
                                     environment_name, config_key,
                                     smtp_host, smtp_port,
                                     body_template, subject_template)
    config = Config(json.loads(json_config), environment_name)

    return config


def create_subject_template(template_directory, template_name=None,
                            template_content=None):
    """ Creates a body template for the email.
        template_directory - [Required] A directory location for templates.
                                        Must be a py.path.local object.
        template_name - [Optional] The name of the template to create.
                                   Defaults to "default_subject.template".
        template_content - [Optional] Allows tests to override default content
                                      written to the template. Must be a valid
                                      string. Defaults to the default template.
    """
    if not template_directory:
        raise ValueError("template_directory is required.")
    if not template_name:
        template_name = "default_subject.template"

    subject_template = template_directory.join(template_name)

    if not template_content:
        subject_template.write("Validation Failure in {{env}}: {{test_name}}")
    else:
        subject_template.write(template_content)

    return template_name


def create_body_template(template_directory, template_name=None,
                         template_content=None):
    """ Creates a body template for the email.
        template_directory - [Required] A directory location for templates.
                                        Must be a py.path.local object.
        template_name - [Optional] The name of the template to create.
                                   Defaults to "default.template".
        template_content - [Optional] Allows tests to override default content
                                      written to the template. Must be a valid
                                      string. Defaults to the default template.
    """

    if not template_directory:
        raise ValueError("template_directory is required.")
    if not template_name:
        template_name = "default.template"

    body_template = template_directory.join(template_name)

    if not template_content:
        body_template.write("Validation Failure in environment {{env}}:\n"
                            "Test Name: [{{test_name}}]\n"
                            "Test Description: [{{test_description}}]\n"
                            "Custom Message: [{{email_custom_message}}]")
    else:
        body_template.write(template_content)

    return template_name


def create_json_config(template_directory, environment_name,
                       config_key="email_notifications",
                       smtp_host=None, smtp_port=None,
                       default_template="default.template",
                       default_subject_template="default_subject.template"):
    """ Creates a valid json file for config
        template_directory - [Required] A directory location for templates.
                                        Must be a py.path.local object.
        environment_name - [Required] The name of the environment-specific
                                      config section for use with email configs
        config_key - [Required] The email notifications config section key
        smtp_host - [Optional] SMTP server host name. Must be a string.
                               Defaults to null value.
        smtp_port - [Optional] SMTP server port number. Must be an integer.
                               Defaults to null value.
        default_template - [Optional] The name of the default template.
                                      Defaults to "default.template".
        default_subject_template - [Optional] The name of the default
                                              subject template. Defaults
                                              to "default_subject.template".
    """

    if not template_directory:
        raise ValueError("template_directory is required")
    else:
        template_directory_path = str(template_directory)

    if not environment_name:
        raise ValueError("environment_name is required")

    if not smtp_host:
        smtp_host = "null"
    else:
        smtp_host = '"' + smtp_host + '"'

    if not smtp_port:
        smtp_port = "null"
    else:
        smtp_port = str(smtp_port)

    json_config =\
    '{'\
        '"email_template_directory": "' + template_directory_path + '",'\
        '"email_host": ' + smtp_host + ','\
        '"email_port": ' + smtp_port + ','\
        '"email_defaults": {'\
            '"general": {'\
                '"email_template": "' + default_template + '",'\
                '"email_subject_template": "' + default_subject_template + \
                '",'\
                '"email_sender": {'\
                    '"real_name": "Alarmageddon Monitor",'\
                    '"address": "noreply@alarmageddon.com"'\
                '},'\
                '"email_recipients": ['\
                    '{'\
                        '"real_name": "Test Recipient",'\
                        '"address": "testrecipient@alarmageddon.com"'\
                    '}'\
                '],'\
                '"email_custom_message": ""'\
            '}'\
        '},'\
        '"environment": {'\
            '"' + environment_name + '": {'\
                '"' + config_key + '": {'\
                    '"test_alert": {'\
                        '"email_recipients": ['\
                            '{'\
                                '"real_name": "Test Recipient Override 1",'\
                                '"address": '\
                                '"testrecipientoverride1@alarmageddon.com"'\
                            '},'\
                            '{'\
                                '"real_name": "Test Recipient Override 2",'\
                                '"address": '\
                                '"testrecipientoverride2@alarmageddon.com"'\
                            '}'\
                        '],'\
                        '"email_custom_message": '\
                        '"Validation failed in environment {{env}}: '\
                        '{{test_name}}."'\
                    '}'\
                '}'\
            '}'\
        '}'\
    '}'

    return json_config
