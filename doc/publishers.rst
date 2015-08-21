Publishers
==========

All publishers accept a ``priority_threshold`` argument. This should be one of ``Priority.LOW``, ``Priority.NORMAL``, or ``Priority.CRITICAL``.
A publisher will only publish failing validations if they are at least as critical as the ``priority_threshold``. For example, to report on all failures, you should set your publisher's ``priority_threshold`` to ``Priority.LOW``.

JUnit XML
---------

The JUnit XML publisher will write out all validation results to an XML file. This publisher is automatically created when you run the validations, and will write out to results.xml.

HipChat
-------

The HipChat publisher will report failures to your hipchat room::

    HipChatPublisher("hipchat.route.here","token","stable","hipchat_room")

By default, the HipChat publisher alerts on failures of NORMAL priority or higher.

Slack
-------

The Slack publisher will report failures to your slack channel::

    SlackPublisher("hook.url","stable")

``hook.url`` should be a slack `incoming web hook <https://my.slack.com/services/new/incoming-webhook/>`_ integration
to the channel that should be published to.
By default, the Slack publisher alerts on failures of NORMAL priority or higher.

Http
----

The Http publisher will report failures to an HTTP Server::

    HttpPubliser(success_url="success.url.here", success_url="failure.url.here")

PagerDuty
---------

The PagerDuty publisher will report failures to PagerDuty::

    PagerDutyPublisher("pagerduty.route.here", "pagerduty_key")

By default, the PagerDuty publisher alerts only on CRITICAL failures.

Graphite
--------

The Graphite publisher behaves slightly differently than the other publishers. Instead of only logging failures, it logs both successes and failures, providing you with a way to keep track of how often certain validations are passing or failing::

    GraphitePublisher("127.0.0.1",8080)

The GraphitePublisher will also keep track of how long the validations took, in the case of HttpValidations. By default, GraphitePublisher will publish on all validations.

Email
---------

There are two email publishers. SimpleEmailPublisher provides basic emailing functionality, and will email all test results to the supplied addresses::

    SimpleEmailPublisher({"real_name": "test", "address": "sender@test.com"},
                         [{"real_name": "test", "address": "recipient@test.com"}],
                         host='127.0.0.1', port=1234)

EmailPublisher provides more granular control over the sent messages. For this reason, validations that will be published by the email publisher must be enriched with extra information.

To create an email publisher, you need a config object with the appropriate values in it, and optionally a set of defaults for missing config values::

  email_pub = EmailPublisher(config, defaults=general_defaults)

For enrichment, a convenience method is provided in emailer to ensure that the appropriate value are present::

  emailer.enrich(validation, email_settings, runtime_context)

.. note::
  For the email publisher to publish a failure, the priority threshold must be reached **and** the validation must be enriched.
