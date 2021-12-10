# Sending Logs to Newrelic with API
When a log file is uploaded to S3 bucket and a SQS event is triggered based on that, then this script will parse the log file and send the logs to Newrelic.

## Required ENV variables
`LICENSE_KEY` - Newrelic's api key

`QUEUE_URL` - The url of the SQS queue

`AWS_PROFILE` - AWS credentials

`BRAND` - One of the AMV brands (AT, GP, AW) defaults to AMV
