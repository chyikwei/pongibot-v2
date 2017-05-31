from __future__ import print_function

import os
import json
import requests

from chalice import Chalice, Response

app = Chalice(app_name='pongibot')

app.debug = True

FB_POST_URL = "https://graph.facebook.com/v2.8/me/messages"


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

    ret = True
    if body['object'] == 'page':
        for entry in body['entry']:
            for msg in entry.get('messaging', []):
                if 'delivery' in msg:
                    continue
                msg_txt = msg['message']['text']
                sender_id = msg['sender']['id']
                res_text = msg_txt
                send_message(sender_id, res_text)
    return {"success": ret}


def send_message(recipient_id, message_text):

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })

    r = requests.post(FB_POST_URL,
                      params=params,
                      headers=headers,
                      data=data)
    
    if r.status_code != 200:
        print('post Failed: {}'.format(r.text))
