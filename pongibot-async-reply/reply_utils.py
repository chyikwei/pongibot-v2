from __future__ import print_function

import json
import pytz
import dateutil.parser as dp

from datetime import datetime

LOCAL_TIMEZONE = "America/New_York"


class QuickReplyGenerator(object):
    """Quick Reply Generator"""

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
                "payload": json.dumps({"text": tag})
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
                "payload": json.dumps({"text": tag})
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
            "payload": json.dumps({"signal": "CANCEL"})
        }
        return ret

    def generate_skip_reply(self):
        ret = {
            "content_type":"text",
            "title": "skip",
            "payload": json.dumps({"signal": "SKIP"})
        }
        return ret

    def generate_initial_menu(self):
        quick_replies = [
            {
                "content_type":"text",
                "title": "Recent Reports",
                "payload": json.dumps({"signal": "RECENT_REPORT"})
            },
            {
                "content_type":"text",
                "title": "Add report",
                "payload": json.dumps({"signal": "INSERT_NEW"})
            }
        ]
        return quick_replies


class PayloadParser(object):

    @classmethod
    def parse(cls, payload):
        return json.loads(payload)


def convert_to_local_time(iso_time):
    timestamp = dp.parse(iso_time)
    timestamp = timestamp.replace(tzinfo=pytz.UTC)
    local = pytz.timezone(LOCAL_TIMEZONE)
    timestamp = timestamp.astimezone(local)
    return timestamp.strftime('%Y-%m-%d %H:%M')


class TemplateGenerator(object):

    BASE_S3_URL = 'https://s3.amazonaws.com/pongibot/'

    @classmethod
    def convert_report(cls, report):
        ret = {}
        tags= ['#{}'.format(t) for t in report['tags']]
        ret["subtitle"] = " ".join(tags)
        ret['image_url'] = cls.BASE_S3_URL + report['images'][0]
        target = report.get('target')
        local_time = convert_to_local_time(report['timestamp'])
        if target:
            ret['title'] = "{} ({})".format(target, local_time)
        else:
            ret['title'] = local_time
        return ret

    @classmethod
    def generate_list_reports(cls, reports, limit):
        elements = []
        total = len(reports)

        if total <= limit:
            next_timestamp = None
        else:
            next_timestamp = reports[limit]['timestamp']

        for report in reports[:limit]:
            element = cls.convert_report(report)
            elements.append(element)

        if next_timestamp:
            btn_payload = {
                "signal": "RECENT_REPORT",
                "start_timestamp": next_timestamp
            }
            button = {
                "title": "View More",
                "type": "postback",
                "payload": json.dumps(btn_payload)
            }
            elements[-1]["buttons"] = [button]

        payload = {
            "template_type": "generic",
            "image_aspect_ratio": "square",
            "elements": elements
        }

        print(payload)
        return payload

    @classmethod
    def generate_single_report(cls, report):
        element = cls.convert_report(report)        

        payload = {
            "template_type": "generic",
            "image_aspect_ratio": "square",
            "elements": [element]
        }
        return payload

    @classmethod
    def generate_reports(cls, reports, limit):
        if len(reports) < 2:
            return cls.generate_single_report(reports[0])
        else:
            return cls.generate_list_reports(reports, limit)
