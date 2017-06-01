from __future__ import print_function

import os
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

boto3.setup_default_session(region_name='us-east-1')


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


class User(BaseDDBTable):
    """Reply Msg Models

    primary key: user_id
    """
    def __init__(self, user_id):
        super(User, self).__init__()
        self.primary_key = 'user_id'
        self.table_name = os.environ["USER_TABLE"]
        self.table = self.dynamodb.Table(self.table_name)
        self.user_id = user_id
        self.current_data = {}

    def get_data(self, user_id):
        """get ddb data

        return: dict
        """
        return self._get_item(user_id, consistent=True)

    def get_or_create(self):
        """get or create DDB record

        return: self
        """
        ret = self.get_data(self.user_id)
        if not ret:
            item = {
                'user_id': self.user_id,
                'created_on': datetime.now().isoformat()
            }
            self.current_data = item
        else:
            self.current_data = ret
        return self

    def update_attributes(self, attrs):
        """update DDB attributes

        return: boolean (success or not)
        """
        new_attrs = {}
        for k, v in attrs.iteritems():
            new_attrs[k] = {
                'Value': v,
                'Action': 'PUT',
            }
        new_attrs['last_modified'] = {
            'Value': datetime.now().isoformat(),
            'Action': 'PUT'
        }
        resp = self.table.update_item(
            Key={
                self.primary_key: self.user_id
            },
            AttributeUpdates=new_attrs
        )
        return resp['ResponseMetadata']['HTTPStatusCode'] == 200



class MsgTable(TimestampBasedDDBTable):
    """Msg Models

    primary key: user_id
    range key: timestamp
    index: mid-index
    """
    def __init__(self):
        super(MsgTable, self).__init__()
        self.primary_key = 'user_id'
        self.range_key = 'timestamp'
        self.mid_index = 'mid-index'
        self.table_name = os.environ["MSG_TABLE"]
        self.table = self.dynamodb.Table(self.table_name)

    def put(self, user_id, msg):
        return self._put_item_with_timestamp(user_id, msg)


    def get_item(self, mid):
        resp = self.table.query(
            IndexName=self.mid_index,
            Limit=1,
            KeyConditionExpression=Key('mid').eq(mid)
        )
        if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
            return None
        elif 'Items' in resp and len(resp['Items']) > 0:
            return resp['Items'][0]


    def mark_processed(self, mid, saved_attachments=None):
        item = self.get_item(mid)
        if not item:
            print("cannot find mid {}".format(mid))
            return False

        pk = self.primary_key
        rk = self.range_key
        attrs = {
            'processed_timestmap': {
                'Value': datetime.now().isoformat(),
                'Action': 'PUT'
            }
        }

        if saved_attachments:
            attrs['attachments'] = {
                'Value': saved_attachments,
                'Action': 'PUT'
            }

        resp = self.table.update_item(
            Key={
                pk: item[pk],
                rk: item[rk],
            },
            AttributeUpdates=attrs
        )
        return resp['ResponseMetadata']['HTTPStatusCode'] == 200


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