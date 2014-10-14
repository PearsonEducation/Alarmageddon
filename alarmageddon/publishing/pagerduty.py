"""Support for publishing to PagerDuty."""

from alarmageddon.publishing.publisher import Publisher
from alarmageddon.publishing.exceptions import PublishFailure

import requests
import json
import time
import hashlib


class PagerDutyPublisher(Publisher):
    """A publisher that publishes incidents to PagerDuty.

    A unique ID is generated for each failure, built from the failure message.
    This means that repeated failures for the same test will not cause
    multiple pages if the original failure has not yet been resolved.

    :param api_end_point: The PagerDuty API endpoint.
    :param api_token: A PagerDuty API token.
    :param priority_threshold: Will publish validations of this priority or
      higher.
     """

    def __init__(self, api_end_point, api_key, priority_threshold=None):
        if not api_end_point:
            raise ValueError("api_end_point parameter is required")
        if not api_key:
            raise ValueError("api_key parameter is required")

        super(PagerDutyPublisher, self).__init__(
            "PagerDuty", priority_threshold)

        self._api_key = api_key
        self._api_end_point = api_end_point

    def _generate_id(self, result):
        """Generate a unique ID for a result.

        By assigning a unique ID for a validation, PagerDuty will not page
        for repeated failures if the original has not been resolved.

        The details of a result may vary, but by using the validation itself,
        this id should be the same from run to run.

        :param message: The message to hash into an id.

        """
        validation = result.validation

        #this is still not optimal - validations may mutate between creation
        #and here
        message = str(type(validation)) + str(validation.__dict__)
        hasher = hashlib.md5()
        hasher.update(message)
        pagerduty_id = hasher.hexdigest()
        return pagerduty_id

    def send(self, result):
        """Creates an incident in pager duty.

        Performs exponential backoff and retry in the case of 403 or 5xx
        responses.

        """
        if result.is_failure() and self.will_publish(result):
            message = "Failure: {0} - {1}".format(result.test_name(),
                                                  result.description())

            headers = {
                "Content-Type": "application/json"
            }

            data = json.dumps({
                "service_key": self._api_key,
                "event_type": "trigger",
                "description": message,
                "incident_key": self._generate_id(result)
            })

            #exponential backoff
            for i in xrange(4):
                resp = requests.post(self._api_end_point,
                                     data=data, headers=headers, stream=True)

                if 200 <= resp.status_code < 300:
                    break
                elif resp.status_code == 403 or resp.status_code >= 500:
                    #PagerDuty docs indicate these codes should result
                    #in a wait and then a retry.
                    time.sleep(2**i)
                else:
                    raise PublishFailure(self, result)
            else:
                raise PublishFailure(self, result)
