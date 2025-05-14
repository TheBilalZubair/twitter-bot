import tweepy
import requests
import time
import schedule
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

#The api keys are in a hidden .env file which have not been uploaded to github for security reasons
#Which is why you see me use the self named variables as a way to hide them
load_dotenv()


NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
NEWS_PARAMS = {
    "country": "us",
    "apiKey": NEWS_API_KEY,
    "pageSize": 20
}


TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Twitter client
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_SECRET,
    wait_on_rate_limit=False
)

# File to store posted news and tweet logs
POSTED_NEWS_FILE = "posted_news.txt"
TWEET_LOG_FILE = "tweet_log.json"

# Load the posted news
def load_posted_news():
    if os.path.exists(POSTED_NEWS_FILE):
        with open(POSTED_NEWS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

# Save the posted news
def save_posted_news(posted_set):
    with open(POSTED_NEWS_FILE, "w", encoding="utf-8") as f:
        for item in posted_set:
            f.write(item + "\n")

# Load tweet log
def load_tweet_log():
    if os.path.exists(TWEET_LOG_FILE):
        with open(TWEET_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"count": 0, "last_reset": datetime.utcnow().isoformat()}

# Save tweet log
def save_tweet_log(log):
    with open(TWEET_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f)

# Check if daily tweet limit reached
def can_tweet():
    log = load_tweet_log()
    last_reset = datetime.fromisoformat(log["last_reset"])
    now = datetime.utcnow()

    if now - last_reset >= timedelta(days=1):
        log = {"count": 0, "last_reset": now.isoformat()}
        save_tweet_log(log)
        return True

    if log["count"] < 17:
        return True
    else:
        print(f" Daily tweet limit reached: {log['count']} tweets since {log['last_reset']}")
        return False

# Increment the tweet count
def increment_tweet_count():
    log = load_tweet_log()
    log["count"] += 1
    save_tweet_log(log)

# Fetch news articles
def get_news():
    try:
        response = requests.get(NEWS_API_URL, params=NEWS_PARAMS)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", []) if data["status"] == "ok" else []
    except Exception as e:
        print(f" Error fetching news: {e}")
        return []

# Post a news article
def post_news():
    print(f"\n {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking for news to post...")

    if not can_tweet():
        return

    posted_news = load_posted_news()
    articles = get_news()

    for article in articles:
        article_id = f"{article['title']}_{article['url']}"
        if article_id in posted_news:
            continue

        title = article['title']
        url = article['url']
        source = article['source']['name']
        tweet = f"{title}\n\nSource: {source}\n{url}"

        # Trim tweet if needed
        if len(tweet) > 280:
            max_title_length = 280 - len(f"\n\nSource: {source}\n{url}") - 3
            title = title[:max_title_length] + "..."
            tweet = f"{title}\n\nSource: {source}\n{url}"

        try:
            response = client.create_tweet(text=tweet)
            tweet_id = response.data["id"]
            print(f"DONE! Tweet posted: {tweet_id}")
            posted_news.add(article_id)
            save_posted_news(posted_news)
            increment_tweet_count()
            return

        except tweepy.TooManyRequests as e:
            print(" Rate limit hit (429):")
            for key, value in e.response.headers.items():
                if "rate-limit" in key.lower() or "retry-after" in key.lower():
                    print(f"{key}: {value}")
            reset_time = e.response.headers.get("x-rate-limit-reset")
            if reset_time:
                wait_seconds = max(int(reset_time) - int(time.time()), 60)
                print(f" Waiting {wait_seconds} seconds...")
                time.sleep(wait_seconds)
            return

        except Exception as e:
            print(f" Tweet failed: {e}")
            return

    print(" No new articles to post.")

# Main loop
def main():
    print("Beep Boop. Twitter News Bot started.")
    post_news()
    schedule.every(90).minutes.do(post_news)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
