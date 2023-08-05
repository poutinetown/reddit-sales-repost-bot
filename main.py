import os
import datetime as dt
import time
import html

from bs4 import BeautifulSoup
import feedparser
from pythorhead import Lemmy

def get_new_items(subreddit_rss_url, last_entry=None):
    # Parse the RSS feed
    feed = feedparser.parse(subreddit_rss_url)

    new_items = []
    for entry in feed.entries:
        # Check if the current entry is newer than the last one
        if last_entry is None or entry.published_parsed > last_entry.published_parsed:
            new_items.append(entry)

    # Get the latest entry for future comparisons
    latest_entry = feed.entries[0] if len(feed.entries) > 0 else last_entry

    return new_items, latest_entry

def format_and_extract(summary):
    soup = BeautifulSoup(summary, features="html.parser")
    links = soup.find_all('a')

    extracted_url = None
    formatted = ""

    for link in links:
        first_child = next(link.children).strip()
        url = link.get('href')

        if first_child == '[link]':
            extracted_url = url
            text = 'Link Shared on Reddit'
        elif first_child == '[comments]':
            text = 'Original Reddit Comments'
        elif first_child.startswith('/u/'):
            text = f'Author: {first_child}'
        else:
            if first_child.startswith('['):
                first_child = first_child[1:]
            if first_child.endswith(']'):
                first_child = first_child[:-1]
            text = html.unescape(first_child)
        
        formatted += f"- [{text}]({url})\n"
    
    return formatted, extracted_url

def main():
    instance_url = 'https://lemmy.ca'
    community_name = 'bot_testing_ground'
    subreddit_rss_url = "https://www.reddit.com/r/bapcsalescanada/new/.rss"
    sleep_time = 5

    username = os.environ['LEMMY_USERNAME']
    password = os.environ['LEMMY_PASSWORD']

    time_delta_threshold = dt.timedelta(minutes=5, seconds=30)
    dt_now = dt.datetime.now(dt.timezone.utc)


    lemmy = Lemmy(instance_url)
    lemmy.log_in(username, password)

    community_id = lemmy.discover_community(community_name)
    feed = feedparser.parse(subreddit_rss_url)

    for entry in feed.entries:
        dt_published = dt.datetime.fromisoformat(entry.published)
        time_diff = dt_now - dt_published

        if time_diff > time_delta_threshold:
            time_diff_str = str(time_diff - dt.timedelta(microseconds=time_diff.microseconds))
            print(f"Entry '{entry.link}' was published {time_diff_str} ago, which is greater than {time_delta_threshold}")
        else:
            # Publish the summary to lemmy and sleep for a bit
            formatted, extracted_url = format_and_extract(entry.summary)
            lemmy.post.create(
                community_id=community_id,
                name=html.unescape(entry.title),
                url=extracted_url,
                body=formatted,
            )
            print(f'Posted "{entry.link}"')
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()