"""
Note: Unfortunately, at the moment, GitHub has no easy way to persist artifacts across
multiple runs, which means this script will try to load a last_date_published.txt file
that will never exist, thus fall back to the default `offset` value. In the future, an
improvement would be to find a way to persist this last_date_published.txt file (or an
environment variable that holds this value), maybe using the github actions workflow or 
some other method.
"""
import os
import datetime as dt
import time
import html

from bs4 import BeautifulSoup
import feedparser
from pythorhead import Lemmy


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


def get_last_published_time(path='last_date_published.txt', offset=dt.timedelta(minutes=10, seconds=45)):
    try:
        with open(path, 'r') as f:
            last_published_str = f.read().strip()
            last_published = dt.datetime.fromisoformat(last_published_str)
    except FileNotFoundError:
        # If last_date_published.txt does not exist, set an initial last_published
        dt_now = dt.datetime.now(dt.timezone.utc)
        last_published = dt_now - offset
    return last_published


def write_last_published_time(dt_now, path='last_date_published.txt'):
    with open(path, 'w') as f:
        f.write(dt_now.isoformat())


def main():
    instance_url = 'https://lemmy.ca'
    community_name = 'bapcsalescanada'
    subreddit_rss_url = "https://www.reddit.com/r/bapcsalescanada/new/.rss"
    sleep_time = 5

    username = os.environ['LEMMY_USERNAME']
    password = os.environ['LEMMY_PASSWORD']

    # Read the last published date from last_date_published.txt

    lemmy = Lemmy(instance_url)
    lemmy.log_in(username, password)

    last_published = get_last_published_time()

    community_id = lemmy.discover_community(community_name)
    feed = feedparser.parse(subreddit_rss_url)
    dt_now = dt.datetime.now(dt.timezone.utc)

    write_last_published_time(dt_now)

    for entry in feed.entries:
        dt_published = dt.datetime.fromisoformat(entry.published)

        if 'General Discussion - Daily Thread' in entry.title:
            print(f'Skipping Reddit Discussion Thread: {entry.title}')
        
        elif dt_published < last_published:
            time_diff = dt_now - dt_published
            time_diff_str = str(
                time_diff - dt.timedelta(microseconds=time_diff.microseconds))
            last_pub_diff = dt_now - last_published
            last_pub_diff_str = str(
                last_pub_diff - dt.timedelta(microseconds=last_pub_diff.microseconds))
            print(
                f"Entry '{entry.link}' was published on reddit {time_diff_str} ago, but the last fetch was {str(last_pub_diff_str)} ago.")
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
