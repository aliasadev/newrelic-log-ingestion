# Sending Logs to Newrelic with API
When a log file is uploaded to S3 bucket and a SQS event is triggered based on that, then this script will parse the log file and send the logs to Newrelic.

## Required ENV variables
`LICENSE_KEY` - Newrelic's api key

`QUEUE_URL` - The url of the SQS queue

`AWS_PROFILE` - AWS profile for credentials

OR following variables as credentials:

`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`

`LOG_TYPE` - Type of the log (see [newrelic log api](https://docs.newrelic.com/docs/logs/log-api/introduction-log-api/#json-content))
