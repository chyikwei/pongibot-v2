from __future__ import print_function


class QuickReplyGenerator(object):
    """Quick Reply Generator"""
    TAG_PREFIX = "QR_TAG__"
    TARGET_PREFIX = "QR_TARGET__"
    CANCEL_PAYLOAD = "QR_CANCEL"
    SKIP_PAYLOAD = "QR_SKIP"

    def __init__(self, preference):
        self.preference = preference

    def generate_quick_reply_tags(self, excludes=None, size=3, with_skip=False):
        if excludes:
            excludes = [e.lower() for e in excludes]
        else:
            excludes = []

        quick_replies = []
        user_tags = self.preference.get('tags', [])
        for tag in user_tags:
            if tag.lower() in excludes:
                continue
            quick_replies.append({
                "content_type":"text",
                "title": tag,
                "payload": self.TAG_PREFIX + tag
            })
            if len(quick_replies) >= size:
                break

        if with_skip:
            quick_replies.append(self.generate_skip_reply())

        return quick_replies

    def generate_quick_reply_targets(self, excludes=None, size=3, with_skip=False):
        if excludes:
            excludes = [e.lower() for e in excludes]
        else:
            excludes = []

        quick_replies = []
        target_tags = self.preference.get('targets', [])
        for tag in target_tags:
            if tag.lower() in excludes:
                continue
            quick_replies.append({
                "content_type":"text",
                "title": tag,
                "payload": self.TARGET_PREFIX + tag
            })
            if len(quick_replies) >= size:
                break

        if with_skip:
            quick_replies.append(self.generate_skip_reply())

        return quick_replies

    def generate_cancel_reply(self):
        ret = {
            "content_type":"text",
            "title": "cancel",
            "payload": self.CANCEL_PAYLOAD
        }
        return ret

    def generate_skip_reply(self):
        ret = {
            "content_type":"text",
            "title": "skip",
            "payload": self.SKIP_PAYLOAD
        }
        return ret


class QuickReplyParser(object):

    TAG_PREFIX = "QR_TAG__"
    TARGET_PREFIX = "QR_TARGET__"
    CANCEL_PAYLOAD = "QR_CANCEL"
    SKIP_PAYLOAD = "QR_SKIP"

    @classmethod
    def parse_quick_reply_payload(cls, payload):
        parsed = {}
        if payload == cls.CANCEL_PAYLOAD:
            parsed['signal'] = "CANCEL"
        elif payload == cls.SKIP_PAYLOAD:
            parsed['signal'] = "SKIP"
        elif payload.startswith(cls.TAG_PREFIX):
            parsed['text'] = payload.lstrip(cls.TAG_PREFIX)
        elif payload.startswith(cls.USER_PREFIX):
            parsed['text'] = payload.lstrip(cls.USER_PREFIX)
        return parsed
