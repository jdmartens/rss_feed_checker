import boto3
import feedparser
from datetime import datetime
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
ses = boto3.client('ses')

def lambda_handler(event, context):
    rss_feeds = [
        'https://example.com/feed1.xml',
        'https://example.com/feed2.xml'
    ]
    
    for feed_url in rss_feeds:
        check_feed(feed_url)

def check_feed(feed_url):
    feed = feedparser.parse(feed_url)
    last_entry = get_last_entry(feed_url)
    new_entries = []

    for entry in feed.entries:
        entry_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
        if last_entry is None or entry_date > last_entry['last_check_date']:
            new_entries.append(entry)

    if new_entries:
        send_email_notification(feed_url, new_entries)
        update_last_entry(feed_url, new_entries[0])

def get_last_entry(feed_url):
    response = table.get_item(Key={'feed_url': feed_url})
    return response.get('Item')

def update_last_entry(feed_url, entry):
    table.put_item(Item={
        'feed_url': feed_url,
        'last_check_date': datetime.now().isoformat(),
        'last_entry_id': entry.id,
        'last_entry_title': entry.title
    })

def send_email_notification(feed_url, new_entries):
    subject = f"New RSS entries for {feed_url}"
    body = "New entries:\n\n"
    for entry in new_entries:
        body += f"Title: {entry.title}\nLink: {entry.link}\n\n"

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = os.environ['SENDER_EMAIL']
    message['To'] = os.environ['RECIPIENT_EMAIL']
    message.attach(MIMEText(body, 'plain'))

    ses.send_raw_email(
        Source=message['From'],
        Destinations=[message['To']],
        RawMessage={'Data': message.as_string()}
    )
