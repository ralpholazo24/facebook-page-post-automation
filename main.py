import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import TypedDict, Optional, Set
import praw

# Load environment variables from .env file
load_dotenv()

class PostImageRequest(TypedDict):
    story: str
    url: str
    published: bool

class FacebookService:
    def __init__(self):
        self.BASE_URL = 'https://graph.facebook.com/v21.0/me'
        self.FB_TOKEN = os.getenv('FB_ACCESS_TOKEN')
        if not self.FB_TOKEN:
            raise ValueError("FB_ACCESS_TOKEN environment variable is not set")

    def publish_post(self, request: PostImageRequest):
        url = f"{self.BASE_URL}/photos"
        params = {
            'caption': request['story'],
            'url': request['url'],
            'published': str(request['published']).lower(),
            'access_token': self.FB_TOKEN
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error publishing post: {e}")
            return None

def load_posted_urls() -> Set[str]:
    try:
        with open('posted_urls.txt', 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_posted_url(url: str):
    with open('posted_urls.txt', 'a') as f:
        f.write(f"{url}\n")

def get_top_reddit_post() -> Optional[dict]:
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='ProgrammerHumorBot/1.0'
        )
        
        subreddit = reddit.subreddit('ProgrammerHumor')
        posted_urls = load_posted_urls()
        
        # Get hot posts and find the first valid image post that hasn't been posted
        for submission in subreddit.hot(limit=25):
            url = submission.url
            
            if (any(url.lower().endswith(ext) for ext in ('.jpg', '.png')) 
                and url not in posted_urls):
                save_posted_url(url)
                return {
                    'url': url,
                    'title': submission.title
                }
        
        print("No new posts found - all recent posts have already been shared")
        return None
        
    except Exception as e:
        print(f"Error fetching Reddit post: {e}")
        return None

def post_to_facebook(post):
    try:
        fb_service = FacebookService()
        
        request: PostImageRequest = {
            'story': post['title'],
            'url': post['url'],
            'published': True
        }
        
        result = fb_service.publish_post(request)
        if result:
            print(f"Successfully posted: {post['title']}")
        else:
            print("Failed to post")
            
    except Exception as e:
        print(f"Error posting to Facebook: {e}")

def main():
    top_post = get_top_reddit_post()
    if top_post:
        post_to_facebook(top_post)

if __name__ == "__main__":
    main()