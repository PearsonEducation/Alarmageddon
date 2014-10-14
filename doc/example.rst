A Short Example
===============

This will walk you through creating and running a basic suite of Alarmageddon validations.

Alarmageddon has two main components: validations and publishers. Validations are the tests that will be run, and publishers handle passing the results of those validations along to an external system (eg, PagerDuty).

Creating Validations
--------------------

To make sure that the world's search engines are working, let's use HttpValidation::
    
    from alarmageddon.validations.http import HttpValidation

    validations = []
    validations.append(HttpValidation.get("http://www.google.com").expect_status_codes([200]))
    validations.append(HttpValidation.get("http://www.bing.com").expect_status_codes([200]))
    validations.append(HttpValidation.get("http://www.yahoo.com").expect_status_codes([200]))

These validations are constructed to GET the supplied url. We've also set up our expectations about the results of GETting the url - in this case, we expect the status code to be 200. This is the basic structure of Alarmageddon's validations: a validation takes some action and compares the results to the supplied expectations.

Creating Publishers
-------------------

Of course, if no one knows a validation has failed, it isn't particularly useful. To have Alarmageddon report on failures, we must supply it with at least one publisher::

    from alarmageddon.publishers.hipchat import HipChatPublisher    

    publishers = []
    hipchat_endpoint = "127.0.0.1"
    hipchat_token = "token"
    environment = "stable"
    room = "hipchat_room"
    publishers.append(HipChatPublisher(hipchat_endpoint, hipchat_token, environment, room)

This publisher will report failures to hipchat. Note that this example won't work - you'll need to supply a valid endpoint and token!

Running Alarmageddon
--------------------

Given a set of validations and a set of publishers, we can run Alarmageddon::

    import alarmageddon

    alarmageddon.run_tests(validations,publishers)

This will run the validations. If any failures occur, a message will be passed along to the designated HipChat room. In this case, the resulting message might look something like:

    1 failure(s) in stable: (failed) GET http://www.google.com Description: expected status code: 200, actual status code: 504 (Gateway Time-out)

Full Code
---------

Here's the full source of this example::

    import alarmageddon
    from alarmageddon.validations.http import HttpValidation
    from alarmageddon.publishers.hipchat import HipChatPublisher    

    validations = []
    validations.append(HttpValidation.get("http://www.google.com").expect_status_codes([200]))
    validations.append(HttpValidation.get("http://www.bing.com").expect_status_codes([200]))
    validations.append(HttpValidation.get("http://www.yahoo.com").expect_status_codes([200]))

    publishers = []
    hipchat_endpoint = "127.0.0.1"
    hipchat_token = "token"
    environment = "stable"
    room = "hipchat_room"
    publishers.append(HipChatPublisher(hipchat_endpoint, hipchat_token, environment, room)

    alarmageddon.run_tests(validations,publishers)
