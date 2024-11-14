import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import TypedDict

# Load environment variables from .env file
load_dotenv()

class PostImageRequest(TypedDict):
    story: str
    url: str
    scheduled_publish_time: str
    published: bool

class FacebookService:
    def __init__(self):
        self.BASE_URL = 'https://graph.facebook.com/v21.0/me'
        self.FB_TOKEN = os.environ['FB_ACCESS_TOKEN']

    def publish_post(self, request: PostImageRequest):
        url = f"{self.BASE_URL}/photos"
        params = {
            'caption': request['story'],
            'url': request['url'],
            'scheduled_publish_time': request['scheduled_publish_time'],
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

def get_top_reddit_post():
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = 'https://www.reddit.com/r/ProgrammerHumor/hot.json'
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        posts = response.json()['data']['children']
        
        # Find the first image post that meets our criteria
        for post in posts:
            post_data = post['data']
            url = post_data.get('url', '')
            
            if any(url.lower().endswith(ext) for ext in ('.jpg', '.png', '.gif')):
                return {
                    'url': url,
                    'title': post_data['title']
                }
        
        return None
        
    except Exception as e:
        print(f"Error fetching Reddit post: {e}")
        return None

def post_to_facebook(post):
    try:
        fb_service = FacebookService()
        # Calculate scheduled time (6 hours from now)
        scheduled_time = int((datetime.now() + timedelta(hours=6)).timestamp())
        
        request: PostImageRequest = {
            'story': post['title'],
            'url': post['url'],
            #'scheduled_publish_time': str(scheduled_time),
            'published': 'true'
        }
        
        result = fb_service.publish_post(request)
        if result:
            print(f"Successfully scheduled post: {post['title']} for {datetime.fromtimestamp(scheduled_time)}")
        else:
            print("Failed to schedule post")
            
    except Exception as e:
        print(f"Error posting to Facebook: {e}")

def main():
    while True:
        top_post = get_top_reddit_post()
        
        if top_post:
            post_to_facebook(top_post)
        
        time_to_next_post = timedelta(hours=6)
        print(f'Waiting {time_to_next_post} before next post...')
        time.sleep(time_to_next_post.total_seconds())

if __name__ == "__main__":
    main()