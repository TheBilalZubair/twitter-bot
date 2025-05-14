import tweepy
import os
import time
from dotenv import load_dotenv
#Similar start to the main file, using variables to mask the true values of the api keys for security

load_dotenv()

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Set up Twitter client
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_SECRET,
    wait_on_rate_limit=False  #Purpose: To handle rate limits myself
)

try:
    # Intentionally post an empty/invalid tweet to safely trigger error and get headers
    print(" Sending test tweet...")
    response = client.create_tweet(text="")  # Empty tweet is invalid

except tweepy.BadRequest as e:
    print(" Expected failure.")
    print("Status Code:", e.response.status_code)

    print("\n Twitter Rate Limit Headers:")
    for key, value in e.response.headers.items():
        if "rate-limit" in key.lower() or "retry-after" in key.lower():
            print(f"{key}: {value}")

    reset_time = e.response.headers.get("x-rate-limit-reset")
    if reset_time:
        reset_time = int(reset_time)
        wait_seconds = max(reset_time - int(time.time()), 0)
        print(f"\n Rate limit window resets in {wait_seconds} seconds.")

except tweepy.TooManyRequests as e:
    print(" Rate Limit Hit (429)")
    print("Headers:")
    for key, value in e.response.headers.items():
        print(f"{key}: {value}")

    reset_time = e.response.headers.get("x-rate-limit-reset")
    if reset_time:
        wait_seconds = max(int(reset_time) - int(time.time()), 0)
        print(f"\n Wait {wait_seconds} seconds before retrying.")

except tweepy.TweepyException as e:
    print(" Tweepy exception:", e)

except Exception as e:
    print(" Unexpected error:", e)

