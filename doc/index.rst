.. Alarmageddon documentation master file, created by
   sphinx-quickstart on Fri Apr 18 13:14:01 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: ../logo.*

Alarmageddon is a Python monitoring framework for RESTful services, built on top of Requests and Fabric.

The following example GETs www.google.com, and reports to HipChat if the return code is not 200::

    import alarmageddon
    from alarmageddon.validations.http import HttpValidation
    from alarmageddon.publishers.hipchat import HipChatPublisher

    validations = [HttpValidation.get("http://www.google.com").expect_status_codes([200])]

    publishers = [HipChatPublisher("hipchat.route.here","token","stable","hipchat_room")]

    alarmageddon.run_tests(validations,publishers)

Features
========
* Verify expectations on the following

  * HTTP requests
  * SSH commands
  * RabbitMQ queue lengths
  * Cassandra status
  * Statistics collected in Graphite
  * The behavior of other Alarmageddon tests

* Report failed verifications to

  * HipChat
  * Slack
  * PagerDuty
  * Graphite
  * Email
  * XML file


Getting Started
===============
.. toctree::
   :maxdepth: 2

   example
   validations
   publishers
   emailer

Source
======

.. toctree::
   :maxdepth: 2

   alarmageddon



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
