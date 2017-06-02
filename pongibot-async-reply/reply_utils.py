from __future__ import print_function


class QuickReplyGenerator(object):
    """Quick Reply Generator"""
    TAG_PREFIX = "QR_TAG__"
    TARGET_PREFIX = "QR_TARGET__"
    CANCEL_PAYLOAD = "QR_CANCEL"
    SKIP_PAYLOAD = "QR_SKIP"
    INSERT_NEW_PAYLOAD = "QR_INSERT_NEW"
    RECENT_REPORT_PAYLOAD = "QR_RECENT_REPORT"

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

    def generate_initial_menu(self):
        quick_replies = [
            {
                "content_type":"text",
                "title": "Recent Reports",
                "payload": self.RECENT_REPORT_PAYLOAD,
            },
            {
                "content_type":"text",
                "title": "Add report",
                "payload": self.INSERT_NEW_PAYLOAD,
            }
        ]
        return quick_replies


class QuickReplyParser(object):

    TAG_PREFIX = "QR_TAG__"
    TARGET_PREFIX = "QR_TARGET__"

    PAYLOAD_MAPPING = {
        "QR_CANCEL": "CANCEL",
        "QR_SKIP": "SKIP",
        "QR_INSERT_NEW": "INSERT_NEW",
        "QR_RECENT_REPORT": "RECENT_REPORT",
    }

    @classmethod
    def parse_quick_reply_payload(cls, payload):
        parsed = {}
        if payload in cls.PAYLOAD_MAPPING:
            parsed['signal'] = cls.PAYLOAD_MAPPING[payload]
        elif payload.startswith(cls.TAG_PREFIX):
            parsed['text'] = payload.lstrip(cls.TAG_PREFIX)
        elif payload.startswith(cls.TARGET_PREFIX):
            parsed['text'] = payload.lstrip(cls.TARGET_PREFIX)
        return parsed


class TemplateGenerator(object):

    BASE_S3_URL = 'https://s3.amazonaws.com/pongibot/'

    @classmethod
    def generate_reports(cls, reports):
        elements = []
        for report in reports:
            tags = ['#{}'.format(t) for t in report['tags']]
            img_url = cls.BASE_S3_URL + report['images'][0]
            target = report.get('target')
            if target:
                subtitle = "target: {}, time: {}".format(target, report['timestamp'])
            else:
                subtitle = "time: {}".format(report['timestamp'])

            element = {
                "title": " ".join(tags),
                "image_url": img_url,
                "subtitle": subtitle,
                #"default_action": {
                #    "type": "web_url",
                #    "url": img_url,
                #    "messenger_extensions": True,
                #    "webview_height_ratio": "tall"
                #},
            }
            elements.append(element)
        payload = {
            "template_type": "list",
            "top_element_style": "compact",
            "elements": elements
        }
        return payload
