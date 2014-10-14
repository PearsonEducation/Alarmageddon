"""A Publisher that publishes to a web application using HTTP"""

import time
import requests

from alarmageddon.publishing.publisher import Publisher
from alarmageddon.publishing.exceptions import PublishFailure


class HttpPublisher(Publisher):
    """Creates an HTTP Publisher that publishes successes and/or failures
    to either one or two HTTP end points.

    If you want the same URL to be published to whether or not the the
    Validation result being published failed or succeeded, please
    supply only the url parameter and omit the failure_url and
    success_url parameters.

    Conversely, if you want different URLs to be requested based on
    whether or not the Validation result being published succeeded,
    please omit the url parameter and supply the success_url and
    failure_url parameters.  The HttpPublisher will use the same
    method, headers, and authentication parameters when requesting
    both of those URLs.  If that is not acceptable, please override
    the relevent getter methods.

    :param url: The URL that this publisher should publish successful and
      failed Validation results to.
    :param success_url: The URL that this publisher should publish successful
      Validation results to.
    :param failure_url: The URL that this publisher should publish failed
      Validation results to.
    :param method: The HTTP method to use when posting.  POST is the default
      because it is the only HTTP method that allows you to send the results
      of the published Validation.  The GET method is allowed but cannot send
      the details of the Validation result along with the request.
    :param headers: headers to send along with the request
    :param auth: if your URLs require authentication you can supply a value
      like the following: ``auth=('user', 'pass')``
    :param attempts: the number of times to try to publish to your URL(s).
    :param retry_after_seconds: how many seconds to wait after a failed
      attempt.
    :param timeout_seconds: how long a single attempt can take before it is
      considered a failed attempt.
    :param publish_successes: specify True if you want this HTTP Publisher to
      publish successful results too.  If you provide a success_url, then
      this HttpPublisher will assume you want to publish successes.
    :param expected_status_code:  the HTTP status code to expect from your
      HTTP server if the Validation result was successfully published.
    :param name: The name of this publisher.
    :param priority_threshold: Will publish validations of this priority or
      higher.

    """
    def __init__(self, url=None, success_url=None, failure_url=None,
                 method="POST", headers=None, auth=None, attempts=1,
                 retry_after_seconds=2, timeout_seconds=5,
                 publish_successes=False, expected_status_code=200,
                 name=None, priority_threshold=None):
        super(HttpPublisher, self).__init__(
            name or "HttpPublisher",
            priority_threshold)

        self._success_url = success_url or url
        if not self._success_url:
            raise ValueError("either success_url or url parameter is required")

        self._failure_url = failure_url or url
        if not self._failure_url:
            raise ValueError("either failure_url or url parameter is required")

        self._publish_successes = (success_url is not None) or publish_successes

        self._method = method
        if not self._method:
            raise ValueError("method parameter is requried")

        self._headers = headers
        self._auth = auth

        self._attempts = attempts
        if self._attempts <= 0:
            raise ValueError("attempts parameter must be at least one")

        self._retry_after_seconds = retry_after_seconds
        if self._retry_after_seconds < 0:
            raise ValueError("retry_after_seconds parameter must be positive")

        self._timeout_seconds = timeout_seconds
        self._expected_status_code = expected_status_code

    def _get_method(self, result):
        """Returns the HTTP method (e.g. GET, POST, etc.) that the
        HttpPublisher should use when publishing.

        """
        return self._method

    def _get_url(self, result):
        """Returns the URL that the HttpPublisher should publish to."""
        if result.is_failure():
            return self._failure_url
        else:
            return self._success_url

    def _get_headers(self, result):
        """return the headers, as a dict, that this HttpPublisher should
        include when it publishes.

        """
        return self._headers

    def _get_auth(self, result):
        """Returns None or Authentication information (e.g. ``auth=('user',
        'pass')``) that this HttpPublisher should send along with the
        request.

        """
        return self._auth

    def _get_data(self, result):
        """Returns the data that this HttpPublisher should send along with the
        request.

        It is only relevant when the HTTP Method is ``POST``.

        """
        if self._method == "POST":
            return str(result)
        else:
            return None

    def send(self, result):
        """Publish a test result.

        :param result: The :py:class:`~.result.TestResult` of a test.

        """
        if result.is_failure() or self._publish_successes:
            published = False
            for i in xrange(self._attempts):
                try:
                    response = requests.request(self._get_method(result),
                                                self._get_url(result),
                                                data=self._get_data(result),
                                                headers=self._get_headers(result),
                                                auth=self._get_auth(result),
                                                timeout=self._timeout_seconds)

                    if response.status_code == self._expected_status_code:
                        published = True
                        break
                except Exception:
                    time.sleep(self._retry_after_seconds)
            if not published:
                raise PublishFailure(self, result)

    def __str__(self):
        """Returns a string representation of this HttpPublisher"""
        return "HttpPublisher: '{0}', Method: {1}, Success URL: {2}," +\
                "Failure URL: {3}".format(self._name, self._method,
                                          self._success_url, self._failure_url)
