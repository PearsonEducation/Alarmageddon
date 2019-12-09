"""Support for publishing to PagerDuty."""

from alarmageddon.publishing.publisher import Publisher
from alarmageddon.publishing.exceptions import PublishFailure

import requests
import json
import time
import hashlib
import warnings

import logging

logger = logging.getLogger(__name__)

MAX_LEN = 1024


class PagerDutyPublisher(Publisher):
    """A publisher that publishes incidents to PagerDuty.

    A unique ID is generated for each failure, built from the failure message.
    This means that repeated failures for the same test will not cause
    multiple pages if the original failure has not yet been resolved.

    :param api_end_point: The PagerDuty API endpoint.
    :param api_token: A PagerDuty API token.
    :param priority_threshold: Will publish validations of this priority or
      higher.
    :param environment: The environment that tests are being run in.
     """

    def __init__(self, api_end_point, api_key, priority_threshold=None,
                 environment=None):
        if not api_end_point:
            raise ValueError("api_end_point parameter is required")
        if not api_key:
            raise ValueError("api_key parameter is required")

        logger.debug("Constructing publisher with endpoint:{}, key:{}, priority_threshold:{}, environment:{}"
                .format(api_end_point, api_key[:5]+'...', priority_threshold, environment))

        Publisher.__init__(self, "PagerDuty",
                           priority_threshold=priority_threshold,
                           environment=environment or 'unknown')

        self._api_key = api_key
        self._api_end_point = api_end_point

    def __str__(self):
        return "Pagerduty: {} ({})".format( self._api_end_point,
                self.priority_threshold)

    def __repr__(self):
        return "Pagerduty: {} ({}) ({})".format( self._api_end_point,
                self._api_key, self.priority_threshold)

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
        hasher.update(message.encode('utf-8'))
        pagerduty_id = hasher.hexdigest()

        logger.debug("Generated id {} for {}".format(pagerduty_id, result))
        return pagerduty_id

    def _construct_message(self, result):
        message = "Failure in {0}: {1} - {2}".format(
            self.environment,
            result.test_name(),
            result.description())
        if len(message) > MAX_LEN:
            warnings.warn("PagerDuty message had length {0}, truncating to {1}".format(len(message),MAX_LEN), RuntimeWarning)
            message = message[:MAX_LEN]
        return message

    def send(self, result):
        """Creates an incident in pager duty.

        Performs exponential backoff and retry in the case of 403 or 5xx
        responses.

        """

        logger.debug("Checking if we should send {}".format(result))
        if result.is_failure() and self.will_publish(result):
            message = self._construct_message(result)
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
            logger.debug("Sending send {}".format(result))
            for i in range(4):
                resp = requests.post(self._api_end_point,
                                     data=data, headers=headers, stream=True)

                logger.debug("Response from PagerDuty: {}".format(resp.status_code))
                if 200 <= resp.status_code < 300:
                    break
                elif resp.status_code == 403 or resp.status_code >= 500:
                    #PagerDuty docs indicate these codes should result
                    #in a wait and then a retry.
                    time.sleep(2**i)
                else:
                    raise PublishFailure(self, "{0} - {1} ({2})".format(result, resp.text, resp.status_code))
            else:
                raise PublishFailure(self, "{0} - {1} ({2})".format(result, resp.text, resp.status_code))
