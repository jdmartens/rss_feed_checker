import os
import logging
import hashlib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

import boto3
import feedparser
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

class Settings(BaseSettings):
    feed_list: List[str]
    dynamodb_table: str
    sender_email: str
    recipient_email: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
ses = boto3.client('ses')

def lambda_handler(event, context):
    logger.info("Lambda function started")    
    for feed_url in settings.feed_list:
        logging.info(f"Checking feed: {feed_url}")
        check_feed(feed_url)
    logger.info("Lambda function finished")

def check_feed(feed_url):
    feed = feedparser.parse(feed_url)
    last_entry = get_last_entry(feed_url)
    new_entries = []

    for entry in feed.entries:
        entry_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
        if last_entry is None or entry_date > last_entry['last_check_date']:
            new_entries.append(entry)

    if new_entries:
        logger.info(f"New entries found for feed: {feed_url}")
        send_email_notification(feed_url, new_entries)
        update_last_entry(feed_url, new_entries[0])

def get_last_entry(feed_url):
    response = table.get_item(Key={'feed_url': feed_url})
    last_entry = response.get('Item')
    logger.info(f"Last entry for feed {feed_url}: {last_entry}")
    return last_entry

def update_last_entry(feed_url, entry):
    entry_id = entry.get('id') or generate_id(entry)
    table.put_item(Item={
        'feed_url': feed_url,
        'last_check_date': datetime.now().isoformat(),
        'last_entry_id': entry_id,
        'last_entry_title': entry.title
    })
    logger.info(f"Updated last entry for feed {feed_url} with entry {entry_id}")

def generate_id(entry):
    hash_input = entry.title or entry.link
    return hashlib.md5(hash_input.encode('utf-8')).hexdigest()

def send_email_notification(feed_url, new_entries):
    subject = f"New RSS entries for {feed_url}"
    body = "New entries:\n\n"
    for entry in new_entries:
        body += f"Title: {entry.title}\nLink: {entry.link}\n\n"
    logger.info(f"Sending email notification for feed {feed_url} with {len(new_entries)} new entries")

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = os.environ['SENDER_EMAIL']
    message['To'] = os.environ['RECIPIENT_EMAIL']
    message.attach(MIMEText(body, 'plain'))

    # ses.send_raw_email(
    #     Source=message['From'],
    #     Destinations=[message['To']],
    #     RawMessage={'Data': message.as_string()}
    # )
