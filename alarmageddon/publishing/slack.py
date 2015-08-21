"""Support for publishing to Slack"""

import os
import requests
import json
import collections

from alarmageddon.publishing.publisher import Publisher
from alarmageddon.publishing.exceptions import PublishFailure

fallback_text = "There were Alarmageddon failures"


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


class SlackPublisher(Publisher):
    """A Publisher that sends results to Slack.

    Publishes all failures to the provided Slack room.

    :param hook_url: The Slack Hook URL
    :param priority_threshold: Will publish validations of this priority or
      higher.

    """

    def __init__(self, hook_url, environment, priority_threshold=None):
        if not hook_url:
            raise ValueError("hook_url parameter is required")
        if not environment:
            raise ValueError("environment parameter is required")

        super(SlackPublisher, self).__init__("Slack", priority_threshold)

        self._hook_url = hook_url
        self._environment = environment

    def __str__(self):
        return "Slack: {}".format(self.hook_url)

    def send(self, result):
        """sends a result to Slack if the result is a faliure."""
        if result.is_failure() and self.will_publish(result):

            message = "(failed) Failure in {0}\nTest:{1}\nFailed because: {2}".format(
                self._environment,
                result.test_name(),
                result.description())

            message_text = self._build_message(
                fallback_text,
                self._get_jenkins_job_url(),
                message)

            self._send_to_slack(message_text)

    def send_batch(self, results):
        """Send a batch of results to Slack.

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
        message = "{0} failure(s) in {1}:\n".format(errors, self._environment)
        message += "\n".join(_get_collapsed_message(collapsed_result)
                             for collapsed_result in collapsed.itervalues())

        message_text = self._build_message(
            fallback_text,
            self._get_jenkins_job_url(),
            message)

        self._send_to_slack(message_text)

    def _build_message(self, fallback_text, run_link, text):
        pretext = "Alarmageddon run completed."
        if run_link is not None:
            pretext = "{} <{}|View Result>".format(pretext, run_link)

        payload = {
            "attachments": [
                {
                    "fallback": fallback_text,
                    "author_name": "Alarmageddon",
                    "color": "danger",
                    "pretext": pretext,
                    "text": text,
                    "mrkdwn": True
                }
            ]
        }

        return payload

    def _send_to_slack(self, message):
        """Send a message to Slack.

        :param message: The message to be published.

        """
        headers = {
            "Context-Type": "application/json"
        }

        data = json.dumps(message)
        print "Posting to slack {}".format(data)
        resp = requests.post(self._hook_url, data=data, headers=headers)

        if resp.status_code < 200 or resp.status_code >= 300:
            raise PublishFailure(self, "{0} - {1}".format(message, resp.text))

    def _get_jenkins_job_url(self):
        """If we're running in jenkins use enviroment vars to
        construct a job url. If we are not in running in jenkins
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
