![Alarmageddon](logo.png)

An automated service monitoring tool that reports failures to:

* HipChat
* PagerDuty
* Graphite
* Email
* XML file

Alarmageddon can monitor services via HTTP and/or SSH.

HTML documentation can be found on [Read the Docs](http://alarmageddon.readthedocs.org/en/latest/example.html).

```python
import alarmageddon
from alarmageddon.validations.validation import Priority
from alarmageddon.validations.http import HttpValidation
from alarmageddon.validations.ssh import SshCommandValidation
from alarmageddon.publishing.hipchat import HipChatPublisher

validations = []
validations.append(HttpValidation.get("http://127.0.0.1").expect_status_codes([200]))
validations.append(SshCommandValidation(ctx,"Cassandra","ps -ef | grep CassandraDaemon | grep -v 'grep'")
           .add_hosts(['127.0.0.1'])
           .expect_output_contains("CassandraDaemon"))

publishers = []
publishers.append(HipChatPublisher("127.0.0.1","token","stable","hipchat_room"))

alarmageddon.run_tests(validations,publishers)
```

Pull requests welcome!

Validations
======

Validations are the tests that Alarmageddon runs against services. You can define any number of features that you expect the response to contain via the Expectation class. 

A Validation has a priority level, one of LOW, NORMAL, or CRITICAL. Using these levels, you can control where failures are reported. By default, Graphite is always reported to, Hipchat is reported to for NORMAL and CRITICAL, and PagerDuty receives only CRITICAL reports.

You can provide a time limit for a Validation. If the test takes longer than this time limit to complete, it will be treated as a test failure.

You can also assign a Validation to a group. Alarmageddon keeps track of the number of failed tests within a group, which can then be tested using GroupValidations as described below.

The following Validations and Expectations are provided by Alarmageddon, along with a Validation and Expectation class for extending into your own classes.

### HttpValidation 
Can check POST, PUT, GET, DELETE, HEAD, and OPTIONS of a route. The following expectations are supported by default:
* Status codes
* Headers
* Response body
* Content type
* JSON properties

### SshValidation
Executes commands on a remote host via ssh. The following expectations are supported by default:
* Exit codes
* Upstart service status
* Average load
* Output of an arbitrary SSH command

### RabbitMqValidation
Checks that the queue size of a RabbitMQ queue is less than a user-specified maximum.

### CassandraValidation
Verifies the state of a Cassandra ring.

### GroupValidation
A special validation that checks the results of a group of tests, rather than an external service. Whether or not a GroupValidation fails and the priority level it has if it fails depends on the number of failures in the group and on user-provided thresholds.


Publishers
======

Publishers receive the results of testing the Validations and publish them to a service. Alarmageddon provides four - HipChatPublisher, PagerDutyPublisher, GraphitePublisher, and SimpleEmailPublisher/EmailPublisher. These are all subclasses of Publisher, which you can extend to support whatever reporting you need. 

A Publisher can be deactivated or activated depending on the environment. As well, a Publisher has a priority threshold that controls the priority level at which it begins reporting.

All Validations are run before any results are published. This allows for batch reporting.

In addition to sending results to publishers, Alarmageddon generates an XUnit XML file is generated containing the test results.

### Graphite
By default, failures and successes are logged as counters in Graphite. As well, the time a validation took to complete is logged if the validation returns a value when `timer_name()` is called on it - by default, this is only returned by HttpValidations.

### HipChat
Sends a summary of all failed tests (that meet the priority threshold) to a specified room.

### PagerDuty
Creates a PagerDuty incident for each failed test.

### Email
Sends emails on test failure. The SimpleEmailPublisher will email the text of the failure, while the EmailPublisher is highly configurable and can provide custom messages for individual validations.


Troubleshooting
===============

### All Operating Systems

#### virtualenv: command not found

Please run the following to install virtualenv:

    sudo pip install virtualenv

### Mac OS 10

#### c/_cffi_backend.c:13:10: fatal error: 'ffi.h' file not found

This may be caused by a missing /usr/include directory.  This may be fixed by running:

    xcode-select --install

### Ubuntu

#### fatal error: Python.h: No such file or directory

Please run the following to install the python development libraries and header files:

    sudo apt-get install python-dev
