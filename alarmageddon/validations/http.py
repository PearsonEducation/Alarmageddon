"""HTTP Validation"""
import time
import os
import requests
import copy
import six.moves.urllib.parse as urlparse

from alarmageddon.validations.validation import Validation, Priority
from alarmageddon.validations.json_expectations import \
    ExpectedJsonValueLessThan, \
    ExpectedJsonValueGreaterThan, \
    ExpectedJsonEquality


from alarmageddon.validations.http_expectations import \
    ExpectedContentType, \
    ResponseExpectation, \
    ExpectedHeader, \
    ExpectContainsText, \
    _ExpectedStatusCodes

import logging

logger = logging.getLogger(__name__)

class HttpValidation(Validation):
    """A Validation that executes an HTTP request and then performs zero or
    more checks on the response.

    """
    def __init__(self, method, url, data=None, headers=None,
                 priority=Priority.NORMAL, timeout=None,
                 group=None, retries=1, ignore_ssl_cert_errors=False,
                 auth=None):
        """Creates an HttpValidation object that will make an HTTP request to
        the provided URL passing the provided headers.

        """
        Validation.__init__(self, "{0} {1}".format(method, url),
                            priority=priority,
                            timeout=timeout,
                            group=group)

        self._url = url
        self._data = data
        self._method = method
        self._headers = copy.copy(headers) or {}
        self._response_code_expectation = _ExpectedStatusCodes(set([200]))
        self._expectations = []
        self._retries = retries
        self._ignore_ssl_cert_errors = ignore_ssl_cert_errors
        self._auth = auth or ()
        self._elapsed_time = -1

    @staticmethod
    def get(url, **kwargs):
        """Create an HttpValidation that will GET to the specified url passing
        specified headers.

        headers - a dictionary where each key is a header name and the
        value that corresponds to the key is the header value.

        priority - the priority of the call; this determines how
        failures are routed.

        timeout - the number of seconds the HTTP request is allowed to take.

        group - the group to include this Validation in

        """
        return HttpValidation("GET", url, **kwargs)

    @staticmethod
    def post(url, **kwargs):
        """Create an HttpValidation that will POST to the specified url passing
        specified headers and payload.

        headers - a dictionary where each key is a header name and the
        value that corresponds to the key is the header value.

        data - data that is sent along with the request

        priority - the priority of the call; this determines how
        failures are routed.

        timeout - the number of seconds the HTTP request is allowed to take.

        group - the group to include this Validation in

        """
        return HttpValidation("POST", url, **kwargs)

    @staticmethod
    def put(url, **kwargs):
        """Create an HttpValidation that will PUT to the specified url passing
        specified headers and payload.

        headers - a dictionary where each key is a header name and the
        value that corresponds to the key is the header value.

        data - data that is sent along with the request

        priority - the priority of the call; this determines how
        failures are routed.

        timeout - the number of seconds the HTTP request is allowed to take.

        group - the group to include this Validation in

        """
        return HttpValidation("PUT", url, **kwargs)

    @staticmethod
    def options(url, **kwargs):
        """Create an HttpValidation that will retrieve OPTIONS for the
        specified url passing specified headers.

        headers - a dictionary where each key is a header name and the
        value that corresponds to the key is the header value.

        priority - the priority of the call; this determines how
        failures are routed.

        timeout - the number of seconds the HTTP request is allowed to take.

        group - the group to include this Validation in

        """
        return HttpValidation("OPTIONS", url, **kwargs)

    @staticmethod
    def head(url, **kwargs):
        """Create an HttpValidation that will retrieve the HEAD of the
        specified url passing specified headers.

        headers - a dictionary where each key is a header name and the
        value that corresponds to the key is the header value.

        priority - the priority of the call; this determines how
        failures are routed.

        timeout - the number of seconds the HTTP request is allowed to take.

        group - the group to include this Validation in

        """
        return HttpValidation("HEAD", url, **kwargs)

    def perform(self, group_failures):
        """Perform the HTTP request and validate the response."""
        for i in range(self._retries):
            logger.debug("Attempt {} for {} {}".format(i, self._method, self._url))
            try:
                resp = requests.request(
                    self._method, self._url, data=self._data,
                    headers=self._headers, verify=self._get_verify(),
                    auth=self._auth, timeout=self.timeout)
                logger.debug("Got response {}".format(resp))
                self._elapsed_time = resp.elapsed.total_seconds()
                self._check_expectations(resp)
                break
            except Exception as ex:
                if type(ex) is requests.exceptions.Timeout:
                    self._elapsed_time = self.timeout
                if i == self._retries - 1:
                    raise ex
                time.sleep(1)

    def get_elapsed_time(self):
        return self._elapsed_time

    def fail(self, reason):
        """Causes this HttpValidation to fail with the given reason."""
        Validation.fail(self, reason)

    def duplicate_with_hosts(self, host_names, port=None):
        """Returns a list of new HttpValidation that are identical to this
        HttpValidation except with the host name replaced by the
        elements of host_names.

        """
        parts = urlparse.urlsplit(self._url)

        # If no port is specified, see if the original URL has a port
        # and use it.
        if not port:
            sub_parts = parts.netloc.split(':')
            if len(sub_parts) == 2:
                port = int(sub_parts[1])

        results = []
        for host_name in host_names:
            if port:
                host_name = "{0}:{1}".format(host_name, port)

            modified_parts = urlparse.SplitResult(
                scheme=parts.scheme,
                netloc=host_name,
                path=parts.path,
                query=parts.query,
                fragment=parts.fragment)
            url = urlparse.urlunsplit(modified_parts)
            result = HttpValidation(
                self._method,
                url,
                data=self._data,
                headers=copy.deepcopy(self._headers),
                priority=self.priority,
                timeout=self.timeout,
                group=self.group,
                retries=self._retries,
                ignore_ssl_cert_errors=self._ignore_ssl_cert_errors)
            for expectation in self._expectations:
                result.add_expectation(expectation)
            results.append(result)
        return results

    def timer_name(self):
        parsed = urlparse.urlparse(self._url)
        tokens = parsed.netloc.split(".")
        tokens = [parsed.scheme] + tokens[::-1]
        #[:1] to skip the first /
        path = parsed.path[1:].split("/")
        tokens.extend(path)
        if parsed.query:
            tokens.append(parsed.query)
        tokens.append(self._method)
        result = ".".join(tokens)
        return result

    def send_header(self, name, value):
        """adds an HTTP header with the specified name and value to the
        request when it's sent

        """
        self._headers[name] = value
        return self

    def add_expectation(self, expectation):
        """Add a custom expecation to the Validation"""
        if isinstance(expectation, ResponseExpectation):
            self._expectations.append(expectation)
            return self
        else:
            raise ValueError("attempt to add expectation that does not" +
                             " derive from ResponseExpectation.")

    def expect_header(self, name, value):
        """Add an expectation that the HTTP response will contain a header
        with the specified name and value.

        """
        self.add_expectation(ExpectedHeader(name, value))
        return self

    def expect_contains_text(self, text):
        """Add an expectation that the HTTP response will contain a particular
        string.

        """
        self.add_expectation(ExpectContainsText(text))
        return self

    def expect_status_codes(self, status_codes):
        """Add an expectation that the HTTP response will have one of the
        specified status_codes.

        """
        self._response_code_expectation = _ExpectedStatusCodes(status_codes)
        return self

    def expect_content_type(self, content_type):
        """Add an expectation that the HTTP response's content type will be
        equal to the specified content_type.

        """
        self.add_expectation(ExpectedContentType(content_type))
        return self

    def expect_json_property_value(self, json_property_path, expected_value):
        """Add an expectation that the HTTP response will be JSON and contain a
        property (found by traversing json_property_path) with the
        specified value.

        """
        self.add_expectation(ExpectedJsonEquality(
            json_property_path, expected_value))
        return self

    def expect_json_property_value_less_than(self, json_property_path,
                                             less_than):
        """Add an expectation that the HTTP response will be JSON and contain
        a numeric property (found by traversing json_property_path) less
        than less_than.

        """
        self.add_expectation(ExpectedJsonValueLessThan(
            json_property_path, less_than))
        return self

    def expect_json_property_value_greater_than(self, json_property_path,
                                                greater_than):
        """Add an expectation that the HTTP response will be JSON and contain
        a numeric property (found by traversing json_property_path) greater
        than greater_than.

        """
        self.add_expectation(ExpectedJsonValueGreaterThan(
            json_property_path, greater_than))
        return self

    def _check_expectations(self, response):
        """An HttpValidation without any expectations always fails"""
        self._expectations.append(self._response_code_expectation)
        if not self._expectations:
            self.fail("no expectations set")
        else:
            for expectation in self._expectations:
                expectation.validate(self, response)

    def _get_verify(self):
        """returns the verify parameter we send to the HTTP requests request
        method.

        """
        if self._ignore_ssl_cert_errors:
            return False

        certificates_file = HttpValidation._get_certificates_file()
        if certificates_file:
            return certificates_file
        else:
            return True

    @staticmethod
    def _get_certificates_file():
        """returns the path to the certificates file (not needed on all
        platforms)

        """
        return os.getenv("CERTS_FILE")

    def __str__(self):
        return "HTTP Validation - method: {0}, url: {1}"\
            .format(self._method, self._url)

    def __repr__(self):
        return "HTTP Validation - method: {0}, url: {1}"\
            .format(self._method, self._url)
