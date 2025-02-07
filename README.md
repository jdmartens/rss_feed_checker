# RSS Feed Checker Lambda Function

This AWS Lambda function checks RSS feeds for new entries and sends email notifications for any new entries found. The function uses AWS DynamoDB to keep track of the last checked entry for each feed.

## Prerequisites

- AWS account with access to Lambda, DynamoDB, and SES.
- Python 3.13 or later.