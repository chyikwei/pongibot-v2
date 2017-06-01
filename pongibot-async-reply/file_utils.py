from __future__ import print_function

import os
import boto3
import tempfile
import urllib2

boto3.setup_default_session(region_name="us-east-1")


class FileSaver(object):

    S3_FOLDER = 'saved_attachments'

    def __init__(self):
        self.bucket_name = os.environ["S3_BUCKET"]
        self.bucket = boto3.resource("s3").Bucket(self.bucket_name)

    def save_s3(self, url, file_name):
        s3_key = os.path.join(self.S3_FOLDER, file_name)
        suffix = file_name.split('.')[-1]
        meta = {}
        if suffix in ("jpg", "jpeg"):
            meta["Content-Type"] = "image/jpeg"

        with tempfile.TemporaryFile() as tmp:
            f = urllib2.urlopen(url)
            tmp.write(f.read())
            tmp.seek(0)
            self.bucket.put_object(Key=s3_key, Body=tmp, Metadata=meta)
        return s3_key

    def batch_s3_save(self, urls, file_names):
        ret = []
        for url, file_name in zip(urls, file_names):
            s3_key = self.save_s3(url, file_name)
            ret.append(s3_key)
        return ret
