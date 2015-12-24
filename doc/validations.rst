Validations
===========

A validation performs some action and then checks the results of that action against a set of expectations. Alarmageddon comes with validations for checking the results of HTTP calls, checking the output of SSH commands, and checking the length of RabbitMQ queues.

All validations accept a ``priority`` argument. This should be one of ``Priority.LOW``, ``Priority.NORMAL``, or ``Priority.CRITICAL``. This priority level is used to determine whether or not a publisher should publish the results of the validation.


HTTP
--------------

You can create HttpValidations for various HTTP methods::

    HttpValidation.get("http://www.google.com")
    HttpValidation.post("http://www.google.com",data={key:value})
    HttpValidation.put("http://www.google.com"data={key:value})
    HttpValidation.options("http://www.google.com")
    HttpValidation.head("http://www.google.com")

You can change the timeout length::

    HttpValidation.get("http://www.google.com", timeout=10)

Or designate a number of retry attempts::

    HttpValidation.get("http://www.google.com", retries=10)

You can supply custom headers::

    header = {"Authorization":"value"}
    HttpValidation.get("http://www.google.com", headers=header)
    
If you've created a validation that you would like to apply to multiple hosts::
    
    validation = HttpValidation.get("http://www.google.com")
    hosts = ["http://www.bing.com","http://www.yahoo.com"]
    new_validations = validation.duplicate_with_hosts(hosts)

An example of expectations on HttpValidations, where we expect to get either a 200 or 404 status code, and expect the result to contain JSON with the designated value::

    validation = HttpValidation.get("url")
    validation.expect_status_codes([200,404])
    validation.expect_json_property_value("json.path.to.value","expected")

``expect_json_property_value`` accepts query string that allows you to pluck values from json. Consider the following json document

    {"abc": "123", "another": {"nested": "entry"}, "alpha": {"array": [1, 2, 3, 4]}}

``abc`` will reference ``"123"``
``another.nested`` will reference ``"entry"``
``array[4]`` will reference ``4``
``array[*]`` will reference ``[1, 2, 3, 4]`` 

SSH
-------------

To perform validations over SSH, you'll need to supply the appropriate credentials::

    ctx = SshContext("username","keyfile_path")

You can check the average load::

    LoadAverageValidation(ctx).expect_max_1_minute_load(5, hosts=['127.0.0.1'])

You can verify that an upstart service is running::

    UpstartServiceValidation(ctx, "service_name", hosts=['127.0.0.1'])

But ultimately, the above are just convenience classes for common use cases - you can perform arbitrary commands and check the output::

    validation = SshCommandValidation(ctx, "validation name", "ps -ef | grep python", hosts=['127.0.0.1'])
    validation.expect_output_contains("python")

Cassandra
---------

Cassandra validations are a special case of SSH validations::

    CassandraStatusValidation(ssh_ctx, hosts=['127.0.0.1'])

Kafka
-----

Kafka validations will inspect your kafka partitions and leader elections. If a single partition has multiple leaders the validation will fail::

    KafkaStatusValidation(ssh_ctx, zookeeper_nodes='127.0.0.1:2181,127.0.0.2:2181,127.0.0.3:2181',hosts=['127.0.0.1'])

RabbitMQ
--------

As with SSH, you have to supply credentials for RabbitMQ Validations::
    
    ctx = RabbitMqContext("127.0.0.1",80,"username","password")

Once you have the context, you can construct validations that check that the number of messages in a queue is less than some value. For example, the following will fail if the queue "queue_name" has more than 1000 messages in it::

    RabbitMqValidation(ctx, "validation name", "queue_name", 1000)

Graphite
--------

You also need a context for Graphite::

   ctx = GraphiteContext("127.0.0.1") 

Given the context, you can check statistics on various Graphite readings::

    validation = GraphiteValidation(ctx, "validation name", "Errors")
    validation.expect_average_in_range(1,10)

Validation Groups and GroupValidations
--------------------------------------

You may have a set of tests where individual failures are minor but multiple failures indicate a problem (eg, machines behind an HAProxy). Alarmageddon Validations include the notion of a validation group, which indicate that a set of validations belong together::

    validations = []
    validations.append(HttpValidation.get("http://www.google.com",group="a").expect_status_codes([200]))
    validations.append(HttpValidation.get("http://www.yahoo.com",group="a").expect_status_codes([200]))
    validations.append(HttpValidation.get("http://www.bing.com",group="a").expect_status_codes([200]))

In this case, we have three validations that belong to the validation group "a". Now that we have a group, we can create a GroupValidation that contains expectations about the results of other validations::
    
    validations.append(GroupValidation("Group a Validation", "a", normal_threshold=1, critical_threshold=2))

This new validation does not have an explicit priority level. Rather, it defaults to LOW priority. If the number of failures in group "a" reaches the normal_threshold, the validation will be considered a failure and the priority will become NORMAL. If it reaches the critical_threshold, the priority will become CRITICAL (and the validation will still be a failure).

You can create GroupValidations on groups of GroupValidations. The only difference is that an ``order`` parameter must be passed, to ensure that the tests are run in the correct order::

    validations.append(GroupValidation("Group a Validation", "a", normal_threshold=1, critical_threshold=2, group="c"))
    validations.append(GroupValidation("Group b Validation", "b", normal_threshold=1, critical_threshold=2, group="c"))
    validations.append(alarmageddon.validation.GroupValidation("Group c Validation", "c", normal_threshold=2, order=2))
