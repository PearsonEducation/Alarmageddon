"""Support for publishing to Teams"""

import os
import requests
import json
import collections

from alarmageddon.publishing.publisher import Publisher
from alarmageddon.publishing.exceptions import PublishFailure

import logging

logger = logging.getLogger(__name__)

FALLBACK_TEXT = "There were Alarmageddon failures"


def _get_collapsed_message(results):
    """Helper function to collapse similar failures together.
    If several results have the same reason for failing, combine the
    results to save space and cognitive load on users.
    :param results: List of result objects.
    """
    description = results[0].description()
    names = [result.test_name() for result in results]
    message = ("(failed) {0}\nDescription: {1}").format(", ".join(names),
                                                        description)
    return message


class TeamsPublisher(Publisher):
    """A Publisher that sends results to Teams.
    Publishes all failures to the provided Teams room.
    :param hook_url: The Teams Hook URL
    :param priority_threshold: Will publish validations of this priority or
      higher.
    :param environment: The environment that tests are being run in.
    """

    def __init__(self, hook_url, environment, priority_threshold="Priority.LOW"):
        logger.debug("Constructing publisher with url:{}, priority_threshold:{}, environment:{}"
                .format(hook_url, priority_threshold, environment))

        if not hook_url:
            raise ValueError("hook_url parameter is required")
        if not environment:
            raise ValueError("environment parameter is required")
        Publisher.__init__(self, "Teams")
        self._hook_url = hook_url

    def __str__(self):
        return "Teams: {}".format(self._hook_url)

    def send(self, result):
        """sends a result to Teams if the result is a failure."""
        if result.is_failure() and self.will_publish(result):

            message = "(failed) Failure in {0}\nTest:{1}\nFailed because: {2}".format(
                self.environment,
                result.test_name(),
                result.description())

            message_text = self._build_message(
                FALLBACK_TEXT,
                self._get_jenkins_job_url(),
                message)

            self._send_to_teams(message_text)

    def send_batch(self, results):
        """Send a batch of results to Teams.
        Collapses similar failures together to save space.
        """
        collapsed = collections.defaultdict(list)
        errors = 0
        for result in results:
            if result.is_failure() and self.will_publish(result):
                collapsed[result.description()].append(result)
                errors += 1
        if errors == 0:
            return
        message = "{0} failure(s) :\n".format(errors)
        message += "\n".join(_get_collapsed_message(collapsed_result)
                             for collapsed_result in collapsed.itervalues())

        message_text = self._build_message(
            FALLBACK_TEXT,
            self._get_jenkins_job_url(),
            message)

        self._send_to_teams(message_text)

    def _build_message(self, FALLBACK_TEXT, run_link, text):
        pretext = "Alarmageddon run completed."
        if run_link is not None:
            pretext = "{} <{}|View Result>".format(pretext, run_link)
        jenkins_url = self._get_jenkins_job_url()
        print (jenkins_url)

        payload = {
            "title": os.environ.get('JOB_NAME'),
            "text": text,
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Build",
                    "targets": [{
                                        "os": "default",
                                        "uri": jenkins_url
                        }]
                }
            ]
        }

        return payload

    def _send_to_teams(self, message):
        """Send a message to Teams.
        :param message: The message to be published.
        """
        headers = {
            "Content-Type": "application/json"
        }

        data = json.dumps(message)
        print (data)

        logger.info("Sending {} to {}".format(data, self._hook_url))
        resp = requests.post(self._hook_url, data=data, headers=headers)
        print (resp.text)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise PublishFailure(self, "{0} - {1}".format(message, resp.text))

    def _get_jenkins_job_url(self):
        """If we're running in jenkins use environment vars to
        construct a job URL. If we are not in running in jenkins
        return None
        """

        jenkins_host = os.environ.get('JENKINS_URL')

        if jenkins_host is not None:
            jenkins_job = os.environ.get('JOB_NAME')
            jenkins_build = os.environ.get('BUILD_ID')
            job_url = "{}job/{}/{}/console".format(
                jenkins_host,
                jenkins_job,
                jenkins_build
            )
            return job_url
        else:
            return None
 
