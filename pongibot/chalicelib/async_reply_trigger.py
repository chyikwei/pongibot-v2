from __future__ import print_function

import os
import json
import boto3

boto3.setup_default_session(region_name='us-east-1')


class AsyncReplyTrigger(object):

    def __init__(self):
        self.client = boto3.client('lambda')
        self.function_name = os.environ["REPLY_LAMBDA_NAME"]

    def invoke(self, message):
        resp = self.client.invoke(
            FunctionName=self.function_name,
            InvocationType='Event',
            Payload=json.dumps(message))
        print("triggered lambda with response code: {}".format(resp['StatusCode']))
