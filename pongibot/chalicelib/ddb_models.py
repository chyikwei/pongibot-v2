from __future__ import print_function

import os
import boto3
from datetime import datetime


class BaseDDBTable(object):
    """Base DDB table
    """

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')

    def _get_item(self, p_val, consistent=True):
        """Wrapper for get_item function
        """
        resp = self.table.get_item(
            Key={
                self.primary_key: p_val
            },
            ConsistentRead=consistent)
        status = resp['ResponseMetadata']['HTTPStatusCode']
        if status != 200:
            print(resp)
            return None
        else:
            return resp.get('Item', None)

    def _put_item(self, item):
        """Wrapper for put_item function
        """
        resp = self.table.put_item(
            Item=item,
        )
        status = resp['ResponseMetadata']['HTTPStatusCode']
        if status == 200:
            return item
        else:
            print(resp)
            return None


class TimestampBasedDDBTable(BaseDDBTable):

    def _put_item_with_timestamp(self, p_val, data):
        data[self.primary_key] = p_val
        data[self.range_key] = datetime.now().isoformat()
        ret = self._put_item(data)
        return ret != None


class UserTable(BaseDDBTable):
    """Reply Msg Models

    primary key: user_id
    """
    def __init__(self):
        super(UserTable, self).__init__()
        self.primary_key = 'user_id'
        self.table_name = os.environ["USER_TABLE"]
        self.table = self.dynamodb.Table(self.table_name)

    def get(self, user_id):
        return self._get_item(user_id, consistent=True)

    def get_or_create(self, user_id):
        ret = self.get(user_id)      
        if not ret:
            item = {
                'user_id': user_id,
                'created_on': datetime.now().isoformat()
            }
            ret = self._put_item(item)
        return ret


class MsgTable(TimestampBasedDDBTable):
    """Msg Models

    primary key: user_id
    range key: timestamp
    """
    def __init__(self):
        super(MsgTable, self).__init__()
        self.primary_key = 'user_id'
        self.range_key = 'timestamp'
        self.table_name = os.environ["MSG_TABLE"]
        self.table = self.dynamodb.Table(self.table_name)

    def put(self, user_id, msg):
        return self._put_item_with_timestamp(user_id, msg)


class ReplyTable(TimestampBasedDDBTable):
    """Reply Msg Models

    primary key: user_id
    range key: timestamp
    """
    def __init__(self):
        super(ReplyTable, self).__init__()
        self.primary_key = 'user_id'
        self.range_key = 'timestamp'
        self.table_name = os.environ["REPLY_TABLE"]
        self.table = self.dynamodb.Table(self.table_name)

    def put(self, user_id, msg):
        return self._put_item_with_timestamp(user_id, msg)
