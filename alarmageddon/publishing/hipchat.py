"""Suppport for publishing to HipChat"""

import requests
import json
import collections

from alarmageddon.publishing.publisher import Publisher
from alarmageddon.publishing.exceptions import PublishFailure

import logging

logger = logging.getLogger(__name__)


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


class HipChatPublisher(Publisher):
    """A Publisher that sends results to HipChat.

    Publishes all failures to the designated HipChat room. Will publish all
    results in a single message, collapsings similar errors together to
    save space.

    :param api_end_point: The HipChat API endpoint.
    :param api_token: A HipChat API token.
    :param environment: The environment that tests are being run in.
    :param room_name: The HipChat room to publish results to.
    :param priority_threshold: Will publish validations of this priority or
      higher.

    """

    def __init__(self, api_end_point, api_token, environment, room_name,
                 priority_threshold=None):

        logger.debug("Constructing publisher with endpoint:{}, token:{}, room name:{},"
                "priority_threshold:{}, environment:{}"
                .format(api_end_point, api_token, room_name,
                    priority_threshold, environment))

        if not api_end_point:
            raise ValueError("api_end_point parameter is required")
        if not api_token:
            raise ValueError("api_token parameter is required")
        if not environment:
            raise ValueError("environment parameter is required")
        if not room_name:
            raise ValueError("room_name parameter is required")

        Publisher.__init__(self, "HipChat: {0}".format(room_name),
                           priority_threshold=priority_threshold,
                           environment=environment)

        self._api_token = api_token
        self._api_end_point = api_end_point
        self._room_name = room_name

    def __str__(self):
        return "Hipchat: {}, room {}, env {}".format(
                self._api_end_point, self._room_name, self.environment
                )

    def __repr__(self):
        return "Hipchat: {} ({}), room {}, env {}".format(
                self._api_end_point, self._api_token,
                self._room_name, self.environment
                )

    def send_batch(self, results):
        """Send a batch of results to HipChat.

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
        message = "{0} failure(s) in {1}:\n".format(errors, self.environment)
        message += "\n".join(_get_collapsed_message(collapsed_result)
                             for collapsed_result in list(collapsed.values()))
        self._send_to_hipchat(message)

    def _send_to_hipchat(self, message):
        """Send a message to HipChat.

        :param message: The message to be published.

        """
        url = ("{0}/rooms/message?format=json&room_id={1}&auth_token={2}" +
               "&message={3}&from={4}&color=red").format(self._api_end_point,
                                                         self._room_name,
                                                         self._api_token,
                                                         message,
                                                         'Alarmageddon')

        headers = {
            "Content-Type": "application/json"
        }

        data = json.dumps({
            "message": message,
            "message_format": "text",
            "color": "red"
        })

        logger.debug("Sending {} to {}".format(data, url))

        resp = requests.post(url, data=data, headers=headers, stream=True)

        if resp.status_code < 200 or resp.status_code >= 300:
            raise PublishFailure(self, "{0} - {1}".format(message, resp.text))

    def send(self, result):
        """sends a result to HipChat if the result is a Failure."""
        if result.is_failure() and self.will_publish(result):

            message = ("<b>(failed) Failure in {0}</b><br/><b>Test:</b> " +
                       "{1}<br/><b>Failed because:" +
                       "</b> {2}").format(self.environment,
                                          result.test_name(),
                                          result.description())
            self._send_to_hipchat(message)
