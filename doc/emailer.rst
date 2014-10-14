Using the Email Publisher
=========================

Due to the extensive flexibility allowed by the email publisher, it involves more configuration than the other publishers. This page is intended to be a guide through that process.

Publisher Configuration
-----------------------

Constructing the Email Publisher is similar to other publishers::

    EmailPublisher(config, priority_threshold=Priority.NORMAL, defaults=general_email_defaults)

``config`` is the usual Alarmageddon config object, but it must contain the following email specific field::

    "email_template_directory" : "path/to/email/templates"

This specifies where the email jinja templates can be found.

There are a few optional fields as well. The full email settings might look like this::

    { 
        "email_host" : null,
        "email_port" : null,
        "email_template_directory" : "email_templates",
        "email_defaults" : {
            "general" : {
                "email_template" : "default.template",
                "email_subject_template" : "default_subject.template",
                "email_sender" : {"real_name" : "Alarmageddon Monitor", "address" : "noreply@host.com"},
                "email_recipients" : [
                    {"real_name" : "Team", "address" : "team@host.com"}
                ],
                "email_custom_message" : ""
            },
        }
    }

``email_host`` and ``email_port`` can be set programatically or included in conf.json. ``email_defaults`` provides default information about what templates to use and extra fields that can be used in the template. You will have to programatically assign email_defaults to the publisher, as shown in the example constructor above.

Validation Enrichment
---------------------

For the email publisher to successfully publish a message, the default information provided to each validation is not enough. To include this extra information, an enrichment function must be called on each validation::

    emailer.enrich(validation,
                   email_settings=validation_settings,
                   runtime_context=email_runtime_context)

``validation_settings`` should be a python dictionary of the form::

    {
        "email_template" : "alert.template",
        "email_subject_template" : "alert_subject.template",
        "email_recipients" : [
            {"real_name" : "Another Team", "address" : "another@host.com"}
        ],
        "email_custom_message" : """The route located at {{test_name}} failed to respond within the alloted time frame.
                                  The node may be offline or missing."""
    }

Note that these fields can also appear in the Email Publisher defaults. If validation-specific fields are present, they will be used instead of the defaults.

``runtime_context`` is a dictionary that can contain arbitrary information to be used by the template.

.. note::
    
    For a validation to be published by the Email Publisher, that validation must both be enriched **and** be of high enough priority.  

    You can use Alarmageddon's dry run feature to verify that the validations that you intended to be published by the email publisher will actually be published by the email publisher.

Email Templates
---------------

The Email Publisher uses jinja2 to create its messages. An example email template is provided below::

    Validation Failure in environment {{env}}:
    {{test_name}} - {{test_description}}

    {{email_custom_message}}

The email templates are files stored in the ``email_template_directory``.
