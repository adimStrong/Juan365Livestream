"""
Refresh API Cache - Fetches data from Facebook API and saves to api_cache/
Run this script locally, then push to git to update Streamlit Cloud.
"""
import requests
import json
from datetime import datetime
from pathlib import Path

# Import config
try:
    from config import PAGE_ID, PAGE_TOKEN, BASE_URL
except ImportError:
    print("ERROR: config.py not found. Please create it with PAGE_ID and PAGE_TOKEN.")
    exit(1)

api_cache_dir = Path(__file__).parent / 'api_cache'
api_cache_dir.mkdir(exist_ok=True)

print("=" * 60)
print("           JUAN365 API CACHE REFRESH")
print("=" * 60)
print()

# 1. Fetch page info
print("Fetching page info...")
url = f"{BASE_URL}/{PAGE_ID}"
params = {
    'fields': 'name,fan_count,followers_count,talking_about_count,overall_star_rating,rating_count',
    'access_token': PAGE_TOKEN
}
response = requests.get(url, params=params, timeout=30)
page_info = response.json()

if 'error' in page_info:
    print(f"  ERROR: {page_info['error'].get('message', 'Unknown error')}")
else:
    page_info['fetched_at'] = datetime.now().isoformat()
    with open(api_cache_dir / 'page_info.json', 'w', encoding='utf-8') as f:
        json.dump(page_info, f, indent=2)
    print(f"  Saved: page_info.json (Followers: {page_info.get('fan_count', 0):,})")

# 2. Fetch posts with reaction breakdown (limit 30)
print("Fetching posts with reactions...")
url = f"{BASE_URL}/{PAGE_ID}/posts"
params = {
    'fields': 'id,message,created_time,shares,permalink_url,status_type,'
              'reactions.summary(true),comments.summary(true),'
              'reactions.type(LIKE).summary(true).as(like_count),'
              'reactions.type(LOVE).summary(true).as(love_count),'
              'reactions.type(HAHA).summary(true).as(haha_count),'
              'reactions.type(WOW).summary(true).as(wow_count),'
              'reactions.type(SAD).summary(true).as(sad_count),'
              'reactions.type(ANGRY).summary(true).as(angry_count)',
    'limit': 30,  # Max for reaction breakdown due to API limits
    'access_token': PAGE_TOKEN
}
response = requests.get(url, params=params, timeout=60)
data = response.json()

if 'error' in data:
    print(f"  ERROR: {data['error'].get('message', 'Unknown error')}")
else:
    posts = []
    for post in data.get('data', []):
        processed = {
            'id': post.get('id'),
            'message': post.get('message', '')[:200] if post.get('message') else '',
            'created_time': post.get('created_time'),
            'permalink_url': post.get('permalink_url'),
            'post_type': post.get('status_type', 'unknown'),
            'reactions': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
            'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0),
            'shares': post.get('shares', {}).get('count', 0) if post.get('shares') else 0,
            'like': post.get('like_count', {}).get('summary', {}).get('total_count', 0),
            'love': post.get('love_count', {}).get('summary', {}).get('total_count', 0),
            'haha': post.get('haha_count', {}).get('summary', {}).get('total_count', 0),
            'wow': post.get('wow_count', {}).get('summary', {}).get('total_count', 0),
            'sad': post.get('sad_count', {}).get('summary', {}).get('total_count', 0),
            'angry': post.get('angry_count', {}).get('summary', {}).get('total_count', 0),
        }
        processed['engagement'] = processed['reactions'] + processed['comments'] + processed['shares']
        posts.append(processed)

    posts_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_posts': len(posts),
        'posts': posts
    }

    with open(api_cache_dir / 'posts_with_reactions.json', 'w', encoding='utf-8') as f:
        json.dump(posts_data, f, indent=2)

    total_like = sum(p['like'] for p in posts)
    total_love = sum(p['love'] for p in posts)
    print(f"  Saved: posts_with_reactions.json ({len(posts)} posts, Like: {total_like:,}, Love: {total_love:,})")

# 3. Fetch videos
print("Fetching videos...")
url = f"{BASE_URL}/{PAGE_ID}/videos"
params = {
    'fields': 'id,title,description,created_time,length,views,permalink_url',
    'limit': 100,
    'access_token': PAGE_TOKEN
}
response = requests.get(url, params=params, timeout=30)
data = response.json()

if 'error' in data:
    print(f"  ERROR: {data['error'].get('message', 'Unknown error')}")
else:
    videos = data.get('data', [])
    total_views = sum(v.get('views', 0) for v in videos)

    videos_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_videos': len(videos),
        'total_views': total_views,
        'videos': videos
    }

    with open(api_cache_dir / 'videos.json', 'w', encoding='utf-8') as f:
        json.dump(videos_data, f, indent=2)
    print(f"  Saved: videos.json ({len(videos)} videos, Total views: {total_views:,})")

print()
print("=" * 60)
print("           REFRESH COMPLETE!")
print("=" * 60)
print()
print("Data saved to api_cache/ folder.")
print()
print("To update Streamlit Cloud:")
print("  1. Run: git add api_cache/")
print("  2. Run: git commit -m \"Update API cache\"")
print("  3. Run: git push")
print()
