from __future__ import print_function

import os
import json
import requests

class FacebookMsgSender(object):
    """Send Facebook Messeage through its API
    """

    FB_POST_URL = "https://graph.facebook.com/v2.8/me/messages"

    VALID_SENDER_ACTIONS = [
        "mark_seen",
        "typing_on",
        "typing_off"
    ]

    def __init__(self):
        self.token = os.environ["PAGE_ACCESS_TOKEN"]

    def send_text(self, recipient_id, message_text):

        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": message_text
            }
        })
        ret = self._post_requests(data)
        return ret

    def _post_requests(self, data):
        headers = {
            "Content-Type": "application/json"
        }

        params = {
            "access_token": self.token
        }
        r = requests.post(self.FB_POST_URL,
                          params=params,
                          headers=headers,
                          data=data)
        is_success = (r.status_code == 200)
        if not is_success:
            print(r.content)
        return is_success

    def send_action(self, recipient_id, action):
        if action not in self.VALID_SENDER_ACTIONS:
            raise ValueError("Invalid action: ", action)

        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "sender_action": action
        })
        ret = self._post_requests(data)
        return ret
