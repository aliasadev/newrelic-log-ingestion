import urllib.parse
import boto3
import os
import json
import logging
from urllib import request


logger = logging.getLogger()

# Max file size in bytes (uncompressed)
MAX_FILE_SIZE = 400 * 1000 * 1024


def _get_sqs_messages():
    """
    Get messages from AWS SQS queue
    """
    sqs = boto3.resource('sqs')
    queue = sqs.Queue(url=os.getenv("QUEUE_URL", ""))
    return queue.receive_messages(MaxNumberOfMessages=10)


def _get_file_url_from_s3(bucket, key):
    """
        Get data from S3 bucket.
    """
    log_file_size = boto3.resource('s3').Bucket(
        bucket).Object(key).content_length
    if log_file_size > MAX_FILE_SIZE:
        logger.error(
            "The log file uploaded to S3 is larger than the supported max size of 400MB")
        return

    log_file_url = "s3://{}/{}".format(bucket, key)
    return log_file_url


def handler():
    for message in _get_sqs_messages():
        event = json.loads(message.body)
        print("event----->", event)
        # get the file from s3 bucket
        if ('Records' not in event):
            continue
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = urllib.parse.unquote_plus(
                record['s3']['object']['key'], encoding='utf-8')
            log_file_url = _get_file_url_from_s3(bucket, key)
            print("I would upload {} to NR".format(log_file_url))

    return {'message': 'Uploaded logs to New Relic'}


if __name__ == "__main__":
    handler()
