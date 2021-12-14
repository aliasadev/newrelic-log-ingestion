import urllib.parse
import boto3
import os
import json
import logging
import asyncio
import gzip
from urllib import request
import aiohttp
from smart_open import open
from pympler import asizeof
from dotenv import load_dotenv


logger = logging.getLogger()

# Max file size in bytes (uncompressed)
MAX_FILE_SIZE = 400 * 1000 * 1024
# Max batch size for sending requests (1MB)
MAX_BATCH_SIZE = 1000 * 1024


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


async def _make_request(log_batch, session):
    payload = {
        "common": {
            "attributes": {
                "logtype": os.getenv("LOG_TYPE"),
            },
        },
        "aws": {
            "s3_bucket_name": log_batch["bucket"]
        },
        **log_batch["logs"]
    }

    # print("I would upload to NR: \n {}\n".format(payload))

    compressed_payload = gzip.compress(json.dumps(payload).encode())
    req = request.Request(
        "https://log-api.newrelic.com/log/v1", compressed_payload)
    req.add_header("X-License-Key", os.getenv("LICENSE_KEY", ""))
    req.add_header("X-Event-Source", "logs")
    req.add_header("Content-Encoding", "gzip")

    try:
        resp = await session.post(req.get_full_url(), data=req.data, headers=req.headers)
        resp.raise_for_status()
        return resp.status, resp.url
    except aiohttp.ClientResponseError as e:
        if e.status == 400:
            raise Exception("{}, {}".format(e, "Unexpected payload"))
        elif e.status == 403:
            raise Exception("{}, {}".format(e, "Review your license key"))
        elif e.status == 404:
            raise Exception("{}, {}".format(e, "Review the region endpoint"))
        elif e.status == 429:
            logger.error(f"There was a {e.status} error. Reason: {e.message}")
        elif e.status == 408:
            logger.error(f"There was a {e.status} error. Reason: {e.message}")
        elif 400 <= e.status < 500:
            raise Exception(e)


async def _process_log_file(log_url, bucket):
    log_batch = {
        "bucket": bucket
    }
    request_batch = []
    async with aiohttp.ClientSession() as session:
        with open(log_url, encoding="utf-8") as log_lines:
            for i, line in enumerate(log_lines):
                log_batch["logs"] = json.loads(line)
                request_batch.append(_make_request(log_batch, session))
            print("Sending data to NR logs.....")
            res = await asyncio.gather(*request_batch)


def handler():
    for message in _get_sqs_messages():
        event = json.loads(message.body)
        # get the file from s3 bucket
        if ('Records' not in event):
            continue
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = urllib.parse.unquote_plus(
                record['s3']['object']['key'], encoding='utf-8')
            log_file_url = _get_file_url_from_s3(bucket, key)

            # Read logfile and add the meta data
            asyncio.run(_process_log_file(log_file_url, bucket))

    return {'message': 'Uploaded logs to New Relic'}


if __name__ == "__main__":
    load_dotenv()
    handler()
