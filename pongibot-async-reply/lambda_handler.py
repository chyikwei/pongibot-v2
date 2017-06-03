from __future__ import print_function

import os
import json
from urlparse import urlparse

from msg_sender import FacebookMsgSender
from file_utils import FileSaver
from ddb_models import User, MsgTable, ReportTable
from insert_states import InsertStateContext
from reply_utils import PayloadParser


def get_msg_type(payload):
    if 'postback' in payload:
        return 'postback'

    if 'message' in payload:
        msg = payload['message']
    else:
        return None

    if 'quick_reply' in msg:
        return 'quick_reply'
    elif 'text' in msg:
        return 'text'
    elif 'attachments' in msg:
        return 'attachments'
    else:
        return None


def get_url_file_name(url):
    return urlparse(url).path.split('/')[-1]


def save_attachments(sender_id, message):
    attachments = []
    fs = FileSaver()
    for att in message['attachments']:
        if att['type'] in ('image', 'video'):
            url = att['payload']['url']
            file_name = get_url_file_name(att['payload']['url'])
            file_path = os.path.join(sender_id, file_name)
            s3_key = fs.save_s3(url, file_path)
            attachments.append(s3_key)
    return attachments


def update_user_preference(user_preference, report_data):
    old_tags = user_preference['tags']
    new_tags = report_data['tags']
    for tag in set(old_tags) & set(new_tags):
        user_preference['tags'].remove(tag)
    user_preference['tags'] = new_tags + user_preference['tags']

    target = report_data['target']
    if target in user_preference['targets']:
        user_preference['targets'].remove(target)
    user_preference['targets'].insert(0, target)
    return user_preference


def handler(event, context):
    sender_id = event['sender']['id']

    # user records
    user = User(sender_id).get_or_create()
    context_data = user.get_state_context()
    report_data = user.get_report_data()
    user_preference = user.get_preference()
    state_context = InsertStateContext(
        user, context_data, report_data, user_preference)

    # msg record
    msg_table = MsgTable()

    # msg sender
    sender = FacebookMsgSender()
    sender.send_action(sender_id, "mark_seen")
    sender.send_action(sender_id, "typing_on")

    # update data
    user_update_data = {}
    attachments = []

    # parse action data
    msg_type = get_msg_type(event)
    if msg_type == 'postback':
        payload = event["postback"]["payload"]
        action_data = PayloadParser.parse(payload)

    elif msg_type == 'quick_reply':
        payload = event['message']['quick_reply']['payload']
        action_data = PayloadParser.parse(payload)

    elif msg_type == 'text':
        action_data = {
            'text': event['message']['text']
        }
    elif msg_type == 'attachments':
        message = event['message']
        attachments = save_attachments(sender_id, message)
        saved = len(attachments)
        info_text = "{} file saved.".format(saved)
        if saved != len(message['attachments']):
            info_text += " (Only support image & video now)"
        sender.send_text(sender_id, info_text)
        action_data = {
            'images': attachments
        }
    else:
        action_data = {}

    # update state
    state_context.receive_context(action_data)
    reply_msg = state_context.generate_reply()

    if state_context.is_completed():
        # store
        rpt = ReportTable()
        report_data = state_context.get_report().to_dict()
        rpt.put(sender_id, report_data)
        # update user preference
        new_preference = update_user_preference(user_preference, report_data)
        user.update_preference(new_preference)
        # clean up
        user.remove_attributes(['report', 'context'])
    elif state_context.is_cancelled():
        # clean up
        user.remove_attributes(['report', 'context'])        
    else:
        # store data
        user_update_data['context'] = json.dumps(state_context.get_context())
        user_update_data['report'] = json.dumps(state_context.get_report().to_dict())
        user.update_attributes(user_update_data)

    # update msg attributes
    if 'message' in event:
        mid = event['message']['mid']
        msg_table.mark_processed(mid, saved_attachments=attachments)

    # send reply message
    sender.send_action(sender_id, "typing_off")
    sender.send_reply(sender_id, reply_msg)
