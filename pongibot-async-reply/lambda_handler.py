from __future__ import print_function

import os

from urlparse import urlparse

from msg_sender import FacebookMsgSender
from file_utils import FileSaver
from ddb_models import User, MsgTable


def get_msg_type(msg):
    if 'quick_reply' in msg:
        return 'quick_reply'
    elif 'text' in msg:
        return 'text'
    elif 'attachments' in msg:
        return 'attachments'


def get_url_file_name(url):
    return urlparse(url).path.split('/')[-1]


def handler(event, context):
    sender_id = event['sender']['id']
    message = event['message']
    mid = message['mid']

    # user records
    user = User(sender_id).get_or_create()

    # msg record
    msg_table = MsgTable()

    # msg sender
    sender = FacebookMsgSender()
    sender.send_action(sender_id, "mark_seen")
    sender.send_action(sender_id, "typing_on")

    # update data
    user_update_data = {'last_mid': mid}
    attachments = []

    msg_type = get_msg_type(message)

    if msg_type == 'quick_reply':
        payload = message['quick_reply']['payload']
        reply_text = "Get payload {}".format(payload)

    elif msg_type == 'text':
        reply_text = message['text']

    elif msg_type == 'attachments':
        fs = FileSaver()
        saved = 0
        for att in message['attachments']:
            if att['type'] in ('image', 'video'):
                url = att['payload']['url']
                file_name = get_url_file_name(att['payload']['url'])
                file_path = os.path.join(sender_id, file_name)
                s3_key = fs.save_s3(url, file_path)
                attachments.append(s3_key)
                saved += 1
        reply_text = "{} file saved.".format(saved)
        if saved != len(message['attachments']):
            reply_text += " (Only support image & video now)"
    else:
        reply_text = "Unknown message type"

    # update user attributes
    user.update_attributes(user_update_data)
    # update msg attributes
    msg_table.mark_processed(mid, saved_attachments=attachments)

    # send reply message
    sender.send_text(sender_id, reply_text)
