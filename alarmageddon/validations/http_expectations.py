"""Expectations that can be placed on an HTTP request"""


class ResponseExpectation(object):
    """An expectation placed on an HTTP response."""

    def __init__(self):
        pass

    def validate(self, validation, response):
        """If the expectation is met, do nothing.  If the expectation is
        not met, call validation.fail(...)

        """
        pass


class _ExpectedStatusCodes(ResponseExpectation):
    """An expectation about an HTTP response's status code"""
    def __init__(self, status_codes):
        """Create an ExpectedStatusCodes object that expects the HTTP
        response's status code to be one of the elements in status_codes.

        """
        ResponseExpectation.__init__(self)
        self.status_codes = status_codes

    def validate(self, validation, response):
        """This expectation is met if the HTTP response code is one of the
        elements of self.status_codes

        """
        if response.status_code not in self.status_codes:
            string_code = ' or '.join(str(status)
                                      for status in self.status_codes)
            if len(string_code) > 33:
                string_code = string_code[:34] + "..."
            validation.fail(
                "expected status code: {0}, actual status code: {1} ({2})"
                .format(string_code, response.status_code, response.reason))

    def __repr__(self):
        return "{}: Code {}".format(type(self).__name__, self.status_codes)


class ExpectContainsText(ResponseExpectation):
    """An expectation that an HTTP response will include some text."""
    def __init__(self, text):
        """Creates an ExpectContainsText object that expects the HTTP response
        text to contain the specified text.

        """
        ResponseExpectation.__init__(self)
        self.text = text

    def validate(self, validation, response):
        if not self.text in response.text:
            validation.fail("could not find '{0}' in response body: '{1}'"
                            .format(self.text, response.text))

    def __repr__(self):
        return "{}: expect {}".format(type(self).__name__, self.text)


class ExpectedHeader(ResponseExpectation):
    """An expectation that an HTTP response will include a header with a
    specific name and value.

    """
    def __init__(self, name, value):
        """Creates an ExpectedHeader object."""
        ResponseExpectation.__init__(self)
        self.name = name
        self.value = value

    def validate(self, validation, response):
        if self.name not in response.headers:
            validation.fail("No header named: '{0}'.  Found header names: {1}"
                            .format(self.name,
                                    ', '.join(list(response.headers.keys()))))
        elif self.value != response.headers[self.name]:
            validation.fail(
                "The value of the '{0}' header is '{1}', expected '{2}'"
                .format(self.name, response.headers[self.name], self.value))

    def __repr__(self):
        return "{}: {} should be {}".format(type(self).__name__, self.name, self.value)


class ExpectedContentType(ExpectedHeader):
    """An expectation that an HTTP response will have
    a particular content type

    """
    def __init__(self, content_type):
        ExpectedHeader.__init__(self, "Content-Type", content_type)
