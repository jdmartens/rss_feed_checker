# RSS Feed Monitor Lambda Function

## Overview
This AWS Lambda function monitors RSS feeds, detects new entries, and sends email notifications via Amazon SES. It stores the latest processed entry in DynamoDB to avoid duplicate notifications.

## Features
- Fetches and parses multiple RSS feeds
- Detects new entries based on timestamps
- Sends email notifications via AWS SES
- Stores last processed entry in AWS DynamoDB
- Utilizes AWS Lambda for serverless execution

## Prerequisites
Before deploying the function, ensure you have:
- An AWS account
- An existing DynamoDB table
- An Amazon SES-verified email address
- An `.env` file with required configurations

## Environment Variables
The function relies on the following environment variables:

| Variable        | Description |
|----------------|-------------|
| `FEED_LIST` | Comma-separated list of RSS feed URLs |
| `DYNAMODB_TABLE` | Name of the DynamoDB table |
| `SENDER_EMAIL`  | Verified email address in Amazon SES for sending notifications |
| `RECIPIENT_EMAIL` | Email address to receive notifications |

## Setup

1. Create a DynamoDB table to store the last check information for each feed.
2. Create a Lambda function and copy the code from lamba_function.py.
3. Set up environment variables for the Lambda function.
4. Configure IAM permissions for the Lambda function to access DynamoDB and SES.
5. Set up a CloudWatch Events rule to trigger the Lambda function periodically (e.g., every 4 hours).

### Create DynamoDB Table
Run the following AWS CLI command to create a DynamoDB table for storing the last checked entry for each feed:
```sh
aws dynamodb create-table \
    --table-name rss_feed_checker \
    --attribute-definitions AttributeName=feed_url,AttributeType=S \
    --key-schema AttributeName=feed_url,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

## How It Works
This function operates by continuously monitoring RSS feeds, identifying new entries, and sending notifications when updates occur. Below is a step-by-step breakdown of the process:

1. The function iterates through a list of RSS feeds.
2. It checks for new entries by comparing timestamps with the stored last entry in DynamoDB.
3. If new entries are found, an email notification is sent via SES.
4. The latest entry is updated in DynamoDB for future checks.

## Dependencies
- `boto3` for AWS services (DynamoDB, SES)
- `feedparser` for parsing RSS feeds
- `pydantic` for environment variable validation
- `BeautifulSoup` for processing HTML content
- `dateutil` for handling timestamps

## Error Handling & Logging
- Uses Python's logging module to log events and errors.
- Errors are captured and logged for debugging.

## Future Enhancements
- Add support for additional notification methods like SNS
- Add support for keyword matching where it will send articles that contain s
  specific keywords
- Implement retry logic for failed SES emails

## License
This project is licensed under the MIT License.

