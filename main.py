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
        self.BASE_URL = 'https://graph.facebook.com/v21.0'
        self.FB_TOKEN = os.getenv('FB_ACCESS_TOKEN')
        self.PAGE_ID = os.getenv('FB_PAGE_ID')
        self.IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')
        if not self.FB_TOKEN:
            raise ValueError("FB_ACCESS_TOKEN environment variable is not set")
        if not self.PAGE_ID:
            raise ValueError("FB_PAGE_ID environment variable is not set")

    def publish_post(self, request: PostImageRequest):
        """
        Main method to publish a post to Facebook and optionally to Instagram if IG_ACCOUNT_ID is set
        """
        try:
            # Publish to Facebook
            fb_response = self.publish_to_facebook(request)
            if not fb_response:
                print("Failed to publish to Facebook")
                return None
                
            # Only attempt Instagram publishing if IG_ACCOUNT_ID is set
            if self.IG_ACCOUNT_ID:
                ig_response = self.publish_to_instagram(request)
                if not ig_response:
                    print("Failed to publish to Instagram")
                    # Facebook post was successful, but Instagram failed
                    return {'facebook': fb_response, 'instagram': None}
                
                return {
                    'facebook': fb_response,
                    'instagram': ig_response
                }
            
            # If IG_ACCOUNT_ID is not set, only return Facebook response
            return {
                'facebook': fb_response,
                'instagram': None
            }
            
        except Exception as e:
            print(f"Error in publish_post: {e}")
            return None
            
    def publish_to_facebook(self, request: PostImageRequest):
        """Publish a post to Facebook"""
        try:
            # Facebook post - using the correct page ID endpoint
            fb_url = f"{self.BASE_URL}/{self.PAGE_ID}/photos"  # Changed from 'me/photos'
            fb_params = {
                'message': request['story'],  # Changed from 'caption' to 'message'
                'url': request['url'],
                'published': str(request['published']).lower(),
                'access_token': self.FB_TOKEN
            }
            
            fb_response = requests.post(fb_url, params=fb_params)
            fb_response.raise_for_status()
            
            return fb_response.json()
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = f"Facebook API Error: {error_data}"
                except ValueError:
                    pass
            print(f"Error publishing to Facebook: {error_message}")
            return None
            
    def publish_to_instagram(self, request: PostImageRequest):
        """Publish a post to Instagram"""
        try:
            # Instagram post - Step 1: Create container
            ig_container_url = f"{self.BASE_URL}/{self.IG_ACCOUNT_ID}/media"
            ig_container_params = {
                'image_url': request['url'],
                'caption': request['story'],
                'access_token': self.FB_TOKEN
            }
            
            container_response = requests.post(ig_container_url, params=ig_container_params)
            container_response.raise_for_status()
            container_data = container_response.json()
            
            if 'id' not in container_data:
                raise Exception(f"Failed to create Instagram container: {container_data}")

            # Add a small delay to ensure the container is ready
            time.sleep(5)  # Wait 5 seconds

            # Instagram post - Step 2: Publish container
            creation_id = container_data['id']
            ig_publish_url = f"{self.BASE_URL}/{self.IG_ACCOUNT_ID}/media_publish"
            ig_publish_params = {
                'creation_id': creation_id,
                'access_token': self.FB_TOKEN
            }
            
            ig_response = requests.post(ig_publish_url, params=ig_publish_params)
            ig_response.raise_for_status()
            
            return ig_response.json()
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = f"Instagram API Error: {error_data}"
                except ValueError:
                    pass
            print(f"Error publishing to Instagram: {error_message}")
            return None

    def get_recent_posts(self, limit: int = 30) -> Set[str]:
        """Fetch recent post captions to check for duplicates"""
        url = f"{self.BASE_URL}/me/feed"
        params = {
            'fields': 'message',
            'limit': limit,
            'access_token': self.FB_TOKEN
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            posts = response.json().get('data', [])
            return {post.get('message', '') for post in posts}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching recent posts: {e}")
            return set()

def get_top_reddit_post() -> Optional[dict]:
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='ProgrammerHumorBot/1.0'
        )
        
        redditPage = os.getenv('REDDIT_PAGE')
        subreddit = reddit.subreddit(redditPage)
        
        # Get existing post titles from Facebook
        fb_service = FacebookService()
        existing_posts = fb_service.get_recent_posts()
        
        # Get hot posts and find the first valid image post that hasn't been posted
        for submission in subreddit.hot(limit=25):
            url = submission.url.lower()
            
            # Only allow .jpg/.jpeg files for Instagram compatibility
            if (url.endswith('.png') or url.endswith('.jpg') or url.endswith('.jpeg')) and submission.title not in existing_posts:
                return {
                    'url': url,
                    'title': submission.title
                }
        
        print("No new posts found - either all recent posts have been shared or no JPEG images were found")
        return None
        
    except Exception as e:
        print(f"Error fetching Reddit post: {e}")
        return None

def process_post(post):
    try:
        fb_service = FacebookService()
        
        request: PostImageRequest = {
            'story': post['title'],
            'url': post['url'],
            'published': True
        }
        
        result = fb_service.publish_post(request)
        if result:
            print(f"Successfully posted to Facebook and Instagram: {post['title']} {post['url']}")
            print(f"Facebook post ID: {result['facebook'].get('id')}")
            print(f"Instagram post ID: {result['instagram'].get('id')}")
        else:
            print("Failed to post")
            
    except Exception as e:
        print(f"Error posting to social media: {e}")

def main():
    top_post = get_top_reddit_post()
    if top_post:
        process_post(top_post)

if __name__ == "__main__":
    main()