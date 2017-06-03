from __future__ import print_function

import os
import json

from chalice import Chalice, Response
from chalicelib import FacebookMsgParser, MsgTable, AsyncReplyTrigger


app = Chalice(app_name='pongibot')

app.debug = True


@app.route('/')
def index():
    return {'hello': 'world'}


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    request = app.current_request
    if request.method == 'GET':
        return webhook_get(request)
    elif request.method == 'POST':
        return webhook_post(request)
    else:
        return Response(body="Cannot handle {}".format(request.method),
                        status_code=404,
                        headers={'Content-Type': 'text/plain'})


def webhook_get(request):
    qs = request.query_params or {}
    # parse params
    mode = qs.get('hub.mode', '')
    token = qs.get('hub.verify_token', '')
    chg = qs.get('hub.challenge', '')
    verify_token = os.environ["VERIFY_TOKEN"]

    if mode == 'subscribe' and token == verify_token:
        txt = chg
    else:
        txt = "{}-{}-{}".format(mode, token, chg)

    return Response(body=str(txt),
                    status_code=200,
                    headers={'Content-Type': 'text/plain'})


def webhook_post(request):
    body = request.json_body
    print(body)
    if not body:
        return {"success": False}

    msgt = MsgTable()
    reply_trigger = AsyncReplyTrigger()
    if body['object'] == 'page':
        for entry in body['entry']:
            for msg in entry.get('messaging', []):
                msg_type = FacebookMsgParser.parse_message_type(msg)

                if msg_type in ('message', 'postback'):
                    try:
                        sender_id = msg['sender']['id']
                        msg_data = {
                            'raw': json.dumps(msg)
                        }
                        if 'message' in msg:
                            msg_data['mid'] = msg['message']['mid']
                        msgt.put(sender_id, msg_data)
                        reply_trigger.invoke(msg)
                    except Exception as e:
                        print(e)
                elif msg_type == 'message_deliveries':
                    continue
                else:
                    print("cannot handle webhook: {}".format(msg_type))
    return {"success": True}
