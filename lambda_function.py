import os
import logging
import hashlib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from dateutil import parser
from urllib.parse import urlparse

import boto3
from bs4 import BeautifulSoup
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
    print("Lambda function started")    
    for feed_url in settings.feed_list:
        logging.info(f"Checking feed: {feed_url}")
        check_feed(feed_url)
    print("Lambda function finished")

def check_feed(feed_url):
    feed = feedparser.parse(feed_url)
    last_entry = get_last_entry(feed_url)
    new_entries = []

    for entry in feed.entries:
        print("$$$$ entry", entry)
        entry_date = parser.parse(entry.published)
        entry_timestamp = int(entry_date.timestamp())
        if last_entry is None or entry_timestamp > int(datetime.fromisoformat(last_entry['last_check_date']).timestamp()):
            new_entries.append(entry)

    if new_entries:
        print(f"New entries found for feed: {feed_url}")
        send_email_notification(feed_url, new_entries)
        update_last_entry(feed_url, new_entries[0])

def get_last_entry(feed_url):
    response = table.get_item(Key={'feed_url': feed_url})
    last_entry = response.get('Item')
    print(f"Last entry for feed {feed_url}: {last_entry}")
    return last_entry

def update_last_entry(feed_url, entry):
    entry_id = entry.get('id') or generate_id(entry)
    table.put_item(Item={
        'feed_url': feed_url,
        'last_check_date': datetime.now().isoformat(),
        'last_entry_id': entry_id,
        'last_entry_title': entry.title
    })
    print(f"Updated last entry for feed {feed_url} with entry {entry_id}")

def generate_id(entry):
    hash_input = entry.title or entry.link
    return hashlib.md5(hash_input.encode('utf-8')).hexdigest()

def send_email_notification(feed_url, new_entries):
    parsed_url = urlparse(feed_url)
    domain = parsed_url.netloc

    subject = "New RSS entries for {}".format(domain)
    body = '<h1>New entries:</h1><ul style="list-style-type: none;">'
    for entry in new_entries:
        body += "<li>"
        body += f"<h2>{entry.title}</h2>"
        if 'summary' in entry:
            body += f"<p>{entry.summary}</p>"
        author = None
        if 'authors' in entry and entry.authors:
            author = ', '.join([a['name'] for a in entry.authors if 'name' in a])
        elif 'author' in entry:
            author = entry.author
        elif 'creator' in entry:
          print("cr")
          author = entry.creator.strip('<![CDATA[').strip(']]>')
        if author:
            body += f"<p><strong>Author:</strong> {author}</p>"
        image_url = None
        for link in entry.links:
            if link.get('type') and link['type'].startswith('image/'):
                image_url = link['href']
                break
            elif link.get('rel') == 'enclosure' and link['href'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                image_url = link['href']
                break
        if image_url:
            # Style the image to reduce its size in the email
            body += f"<img src='{image_url}' alt='Image' style='max-width: 500px; height: auto;' />"
        # Parse extended description
        extended_description = ""
        if 'content' in entry and entry.content:
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
            soup = BeautifulSoup(content, 'html.parser')
            extended_description = soup.get_text()[:1000] + "..." if len(soup.get_text()) > 1000 else soup.get_text()
        if extended_description:
            body += f"<p>{extended_description}</p>"
        body += f"<p><a href='{entry.link}'>Read more</a></p>"
        body += "</li>"
    body += "</ul>"
    print(f"Sending email notification for feed {feed_url} with {len(new_entries)} new entries")

    message = MIMEMultipart("alternative")
    message['Subject'] = subject
    message['From'] = os.environ['SENDER_EMAIL']
    message['To'] = os.environ['RECIPIENT_EMAIL']
    message.attach(MIMEText(body, 'html'))

    ses.send_raw_email(
        Source=message['From'],
        Destinations=[message['To']],
        RawMessage={'Data': message.as_string()}
    )
