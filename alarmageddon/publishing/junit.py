"""Support for publishing to xml."""
from alarmageddon.publishing.publisher import Publisher

import xml.etree.cElementTree as ET

import logging

logger = logging.getLogger(__name__)

class JUnitPublisher(Publisher):
    """A Publisher that writes results to JUnit formatted XML.

    :param filename: The file to write the XML to.
    :param priority_threshold: Will publish validations of this priority or
      higher.
    :param environment: The environment that tests are being run in.
    """

    def __init__(self, filename, priority_threshold=None,
                 environment=None):
        if not filename:
            raise ValueError("filename parameter is required")

        logger.debug("Constructing publisher with filename:{},"
                "priority_threshold:{}, environment:{}"
                .format(filename, priority_threshold, environment))

        Publisher.__init__(self, "JUnit",
                           priority_threshold=priority_threshold,
                           environment=environment)

        self.filename = filename

    def __repr__(self):
        return "JUnit, publishes to {} (threshold: {})".format(
                self.filename, self.priority_threshold)

    def send_batch(self, results):
        """Write a set of results to an XML file.

        :param results: The validation results to write to file.

        """

        tree = self._construct_tree(results)
        tree.write(self.filename)

    def _construct_tree(self, results):
        failures = 0
        errors = 0
        skips = 0
        tests = len(results)
        time = 0
        for result in results:
            if result.is_failure():
                failures += 1
            time += result.time

        root = ET.Element("testsuite")
        root.set("errors", str(errors))
        root.set("failures", str(failures))
        root.set("name", "alarmageddon")
        root.set("skips", str(skips))
        root.set("tests", str(tests))
        root.set("time", "{:f}".format(time))

        for result in results:
            self._append_result(result, root)

        return ET.ElementTree(root)

    def _append_result(self, result, parent):
        """Add a result as a child of the given parent XML element.

        :param result: The validation result to add.
        :param parent: The parent XML element to add onto.

        """

        case = ET.SubElement(parent, "testcase")

        #remove brackets around type name
        case.set("classname", str(type(result.validation))[8:-2])
        case.set("name", result.test_name())
        case.set("time", "{:f}".format(result.time))

        if result.is_failure():
            failure = ET.SubElement(case, "failure")
            failure.set("message", "test failure")
            failure.text = str(result)

    def send(self, result):
        """This publisher cannot write only a single result"""

        raise NotImplementedError
