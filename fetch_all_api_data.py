"""
Fetch ALL available data from Facebook API and save locally.
Run this to update data, then push to git for Streamlit Cloud.

Strategy:
- Fetch ALL posts from June 2025 to present (for historical trends)
- Fetch reaction breakdown for only recent 30 posts (API limit)
- Fetch all videos with views
"""
import requests
import json
from datetime import datetime
from pathlib import Path

# Import config
try:
    from config import PAGE_ID, PAGE_TOKEN, BASE_URL
except ImportError:
    print("ERROR: config.py not found!")
    exit(1)

api_cache_dir = Path(__file__).parent / 'api_cache'
api_cache_dir.mkdir(exist_ok=True)

# Date filter - fetch from June 1, 2025
START_DATE = "2025-06-01"
START_TIMESTAMP = int(datetime(2025, 6, 1).timestamp())

print("=" * 60)
print("     FETCHING ALL DATA FROM FACEBOOK API")
print(f"     From: {START_DATE} to Present")
print("=" * 60)
print()

all_data = {
    'fetched_at': datetime.now().isoformat(),
    'date_range': {'start': START_DATE, 'end': datetime.now().strftime('%Y-%m-%d')},
    'page_info': {},
    'posts': [],
    'videos': [],
    'reels': [],
    'posts_by_type': {
        'photos': [],
        'videos': [],
        'reels': [],
        'live': [],
        'text': []
    },
    'daily_engagement': {},
    'totals': {}
}

# 1. PAGE INFO
print("1. Fetching Page Info...")
url = f"{BASE_URL}/{PAGE_ID}"
params = {
    'fields': 'name,fan_count,followers_count,talking_about_count,overall_star_rating,rating_count',
    'access_token': PAGE_TOKEN
}
response = requests.get(url, params=params, timeout=30)
data = response.json()
if 'error' not in data:
    all_data['page_info'] = data
    print(f"   Followers: {data.get('fan_count', 0):,}")
    print(f"   Rating: {data.get('overall_star_rating', 0)}/5")
    print(f"   Talking About: {data.get('talking_about_count', 0):,}")
else:
    print(f"   ERROR: {data['error'].get('message', 'Unknown')}")

# 2. POSTS WITH ENGAGEMENT (paginated - get ALL from June 2025)
print()
print("2. Fetching Posts with Engagement (from June 2025)...")
posts = []
url = f"{BASE_URL}/{PAGE_ID}/posts"
params = {
    'fields': 'id,message,created_time,status_type,permalink_url,'
              'reactions.summary(true),comments.summary(true),shares',
    'limit': 25,  # Smaller limit to avoid API data size errors
    'since': START_TIMESTAMP,  # Only posts from June 2025
    'access_token': PAGE_TOKEN
}

page_count = 0
while url and page_count < 50:  # Max 50 pages = ~5000 posts (should cover June-Dec)
    response = requests.get(url, params=params, timeout=60)
    data = response.json()

    if 'error' in data:
        print(f"   ERROR: {data['error'].get('message', 'Unknown')}")
        break

    batch_posts = data.get('data', [])
    if not batch_posts:
        break

    for post in batch_posts:
        processed = {
            'id': post.get('id'),
            'message': post.get('message', '')[:200] if post.get('message') else '',
            'created_time': post.get('created_time'),
            'date': post.get('created_time', '')[:10],
            'status_type': post.get('status_type', 'unknown'),
            'permalink_url': post.get('permalink_url'),
            'reactions': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
            'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0),
            'shares': post.get('shares', {}).get('count', 0) if post.get('shares') else 0,
        }
        processed['engagement'] = processed['reactions'] + processed['comments'] + processed['shares']
        posts.append(processed)

    page_count += 1
    oldest_date = batch_posts[-1].get('created_time', '')[:10] if batch_posts else 'N/A'
    print(f"   Page {page_count}: {len(batch_posts)} posts (total: {len(posts)}, oldest: {oldest_date})")

    # Get next page
    paging = data.get('paging', {})
    url = paging.get('next')
    params = {}  # URL already has params

all_data['posts'] = posts
print(f"   Total posts fetched: {len(posts)}")

# Categorize posts by type
for post in posts:
    status = post.get('status_type', '').lower()
    if 'photo' in status:
        all_data['posts_by_type']['photos'].append(post)
    elif 'video' in status:
        all_data['posts_by_type']['videos'].append(post)
    elif 'mobile_status' in status or status == '':
        all_data['posts_by_type']['text'].append(post)

print(f"   Photos: {len(all_data['posts_by_type']['photos'])}")
print(f"   Videos: {len(all_data['posts_by_type']['videos'])}")
print(f"   Text: {len(all_data['posts_by_type']['text'])}")

# 3. POSTS WITH REACTION BREAKDOWN (limited to 30)
print()
print("3. Fetching Reaction Breakdown (30 posts)...")
url = f"{BASE_URL}/{PAGE_ID}/posts"
params = {
    'fields': 'id,created_time,'
              'reactions.type(LIKE).summary(true).as(like_count),'
              'reactions.type(LOVE).summary(true).as(love_count),'
              'reactions.type(HAHA).summary(true).as(haha_count),'
              'reactions.type(WOW).summary(true).as(wow_count),'
              'reactions.type(SAD).summary(true).as(sad_count),'
              'reactions.type(ANGRY).summary(true).as(angry_count)',
    'limit': 30,
    'access_token': PAGE_TOKEN
}
response = requests.get(url, params=params, timeout=60)
data = response.json()

reaction_breakdown = []
if 'error' not in data:
    for post in data.get('data', []):
        rb = {
            'id': post.get('id'),
            'date': post.get('created_time', '')[:10],
            'like': post.get('like_count', {}).get('summary', {}).get('total_count', 0),
            'love': post.get('love_count', {}).get('summary', {}).get('total_count', 0),
            'haha': post.get('haha_count', {}).get('summary', {}).get('total_count', 0),
            'wow': post.get('wow_count', {}).get('summary', {}).get('total_count', 0),
            'sad': post.get('sad_count', {}).get('summary', {}).get('total_count', 0),
            'angry': post.get('angry_count', {}).get('summary', {}).get('total_count', 0),
        }
        reaction_breakdown.append(rb)

    total_like = sum(r['like'] for r in reaction_breakdown)
    total_love = sum(r['love'] for r in reaction_breakdown)
    print(f"   Like: {total_like:,}, Love: {total_love:,}")
else:
    print(f"   ERROR: {data['error'].get('message', 'Unknown')}")

all_data['reaction_breakdown'] = reaction_breakdown

# 4. VIDEOS WITH VIEWS (from June 2025)
print()
print("4. Fetching Videos with Views (from June 2025)...")
videos = []
url = f"{BASE_URL}/{PAGE_ID}/videos"
params = {
    'fields': 'id,title,description,created_time,length,views,permalink_url',
    'limit': 100,  # Larger limit
    'access_token': PAGE_TOKEN
}

page_count = 0
while url and page_count < 20:  # Max 2000 videos
    response = requests.get(url, params=params, timeout=60)
    data = response.json()

    if 'error' in data:
        print(f"   ERROR: {data['error'].get('message', 'Unknown')}")
        break

    batch_videos = data.get('data', [])
    if not batch_videos:
        break

    for video in batch_videos:
        # Filter by date - only videos from June 2025
        created = video.get('created_time', '')
        if created and created[:10] >= START_DATE:
            processed = {
                'id': video.get('id'),
                'title': video.get('title', ''),
                'description': video.get('description', '')[:100] if video.get('description') else '',
                'created_time': created,
                'date': created[:10],
                'length': video.get('length', 0),
                'views': video.get('views', 0),
                'permalink_url': video.get('permalink_url'),
            }
            videos.append(processed)

    page_count += 1
    oldest_date = batch_videos[-1].get('created_time', '')[:10] if batch_videos else 'N/A'
    print(f"   Page {page_count}: {len(batch_videos)} videos (filtered: {len(videos)}, oldest: {oldest_date})")

    # Stop if we've gone past our date range
    if oldest_date and oldest_date < START_DATE:
        print(f"   Reached videos before {START_DATE}, stopping...")
        break

    paging = data.get('paging', {})
    url = paging.get('next')
    params = {}

all_data['videos'] = videos
total_views = sum(v['views'] for v in videos)
print(f"   Total videos: {len(videos)}, Total views: {total_views:,}")

# 5. REELS
print()
print("5. Fetching Reels...")
reels = []
url = f"{BASE_URL}/{PAGE_ID}/video_reels"
params = {
    'fields': 'id,description,created_time',
    'limit': 50,  # Smaller limit
    'access_token': PAGE_TOKEN
}
response = requests.get(url, params=params, timeout=30)
data = response.json()

if 'error' not in data:
    for reel in data.get('data', []):
        processed = {
            'id': reel.get('id'),
            'description': reel.get('description', '')[:100] if reel.get('description') else '',
            'created_time': reel.get('created_time'),
            'date': reel.get('created_time', '')[:10],
        }
        reels.append(processed)
    print(f"   Total reels: {len(reels)}")
else:
    print(f"   ERROR: {data['error'].get('message', 'Unknown')}")

all_data['reels'] = reels

# 5b. STORIES (NEW!)
print()
print("5b. Fetching Stories...")
stories = []
url = f"{BASE_URL}/{PAGE_ID}/stories"
params = {
    'limit': 100,
    'access_token': PAGE_TOKEN
}

page_count = 0
while url and page_count < 10:  # Max 10 pages
    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    if 'error' in data:
        print(f"   ERROR: {data['error'].get('message', 'Unknown')}")
        break

    batch_stories = data.get('data', [])
    if not batch_stories:
        break

    for story in batch_stories:
        # Convert Unix timestamp to datetime
        creation_time = story.get('creation_time', '')
        if creation_time:
            try:
                dt = datetime.fromtimestamp(int(creation_time))
                created_iso = dt.isoformat()
                date_str = dt.strftime('%Y-%m-%d')
            except:
                created_iso = ''
                date_str = ''
        else:
            created_iso = ''
            date_str = ''

        processed = {
            'post_id': story.get('post_id'),
            'media_id': story.get('media_id'),
            'status': story.get('status'),
            'media_type': story.get('media_type'),
            'url': story.get('url', ''),
            'creation_time': created_iso,
            'date': date_str,
        }
        stories.append(processed)

    page_count += 1
    print(f"   Page {page_count}: {len(batch_stories)} stories (total: {len(stories)})")

    paging = data.get('paging', {})
    url = paging.get('next')
    params = {}

all_data['stories'] = stories
print(f"   Total stories: {len(stories)}")
print(f"   Published: {len([s for s in stories if s['status'] == 'published'])}")
print(f"   Archived: {len([s for s in stories if s['status'] == 'archived'])}")

# 6. CALCULATE DAILY ENGAGEMENT
print()
print("6. Calculating Daily Engagement...")
daily = {}
for post in posts:
    date = post.get('date', '')
    if date:
        if date not in daily:
            daily[date] = {'reactions': 0, 'comments': 0, 'shares': 0, 'posts': 0}
        daily[date]['reactions'] += post.get('reactions', 0)
        daily[date]['comments'] += post.get('comments', 0)
        daily[date]['shares'] += post.get('shares', 0)
        daily[date]['posts'] += 1

all_data['daily_engagement'] = daily
print(f"   Days with data: {len(daily)}")

# 7. CALCULATE TOTALS
print()
print("7. Calculating Totals...")
all_data['totals'] = {
    'total_posts': len(posts),
    'total_videos': len(videos),
    'total_reels': len(reels),
    'total_stories': len(stories),
    'total_reactions': sum(p.get('reactions', 0) for p in posts),
    'total_comments': sum(p.get('comments', 0) for p in posts),
    'total_shares': sum(p.get('shares', 0) for p in posts),
    'total_video_views': sum(v.get('views', 0) for v in videos),
    'followers': all_data['page_info'].get('fan_count', 0),
    'rating': all_data['page_info'].get('overall_star_rating', 0),
}
print(f"   Total Reactions: {all_data['totals']['total_reactions']:,}")
print(f"   Total Comments: {all_data['totals']['total_comments']:,}")
print(f"   Total Shares: {all_data['totals']['total_shares']:,}")
print(f"   Total Video Views: {all_data['totals']['total_video_views']:,}")

# SAVE ALL DATA
print()
print("=" * 60)
print("     SAVING DATA")
print("=" * 60)

# Save complete data
with open(api_cache_dir / 'all_api_data.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)
print(f"Saved: api_cache/all_api_data.json")

# Save individual files for backward compatibility
with open(api_cache_dir / 'page_info.json', 'w', encoding='utf-8') as f:
    json.dump(all_data['page_info'], f, indent=2)
print(f"Saved: api_cache/page_info.json")

posts_data = {
    'fetched_at': all_data['fetched_at'],
    'total_posts': len(all_data['posts']),
    'posts': all_data['posts']
}
with open(api_cache_dir / 'posts.json', 'w', encoding='utf-8') as f:
    json.dump(posts_data, f, indent=2, ensure_ascii=False)
print(f"Saved: api_cache/posts.json")

# Save posts with reactions
posts_with_reactions = []
for post in posts[:30]:
    # Find reaction breakdown for this post
    rb = next((r for r in reaction_breakdown if r['id'] == post['id']), None)
    if rb:
        post_copy = post.copy()
        post_copy.update({
            'like': rb['like'],
            'love': rb['love'],
            'haha': rb['haha'],
            'wow': rb['wow'],
            'sad': rb['sad'],
            'angry': rb['angry'],
        })
        posts_with_reactions.append(post_copy)
    else:
        posts_with_reactions.append(post)

with open(api_cache_dir / 'posts_with_reactions.json', 'w', encoding='utf-8') as f:
    json.dump({
        'fetched_at': all_data['fetched_at'],
        'total_posts': len(posts_with_reactions),
        'posts': posts_with_reactions
    }, f, indent=2, ensure_ascii=False)
print(f"Saved: api_cache/posts_with_reactions.json")

videos_data = {
    'fetched_at': all_data['fetched_at'],
    'total_videos': len(all_data['videos']),
    'total_views': all_data['totals']['total_video_views'],
    'videos': all_data['videos']
}
with open(api_cache_dir / 'videos.json', 'w', encoding='utf-8') as f:
    json.dump(videos_data, f, indent=2, ensure_ascii=False)
print(f"Saved: api_cache/videos.json")

with open(api_cache_dir / 'reels.json', 'w', encoding='utf-8') as f:
    json.dump({
        'fetched_at': all_data['fetched_at'],
        'total_reels': len(all_data['reels']),
        'reels': all_data['reels']
    }, f, indent=2, ensure_ascii=False)
print(f"Saved: api_cache/reels.json")

# Save stories
with open(api_cache_dir / 'stories.json', 'w', encoding='utf-8') as f:
    json.dump({
        'fetched_at': all_data['fetched_at'],
        'total_stories': len(all_data['stories']),
        'published': len([s for s in all_data['stories'] if s['status'] == 'published']),
        'archived': len([s for s in all_data['stories'] if s['status'] == 'archived']),
        'stories': all_data['stories']
    }, f, indent=2, ensure_ascii=False)
print(f"Saved: api_cache/stories.json")

with open(api_cache_dir / 'daily_engagement.json', 'w', encoding='utf-8') as f:
    json.dump({
        'fetched_at': all_data['fetched_at'],
        'daily': all_data['daily_engagement']
    }, f, indent=2)
print(f"Saved: api_cache/daily_engagement.json")

print()
print("=" * 60)
print("     COMPLETE!")
print("=" * 60)
print()
print(f"Data saved to: {api_cache_dir}")
print()
print("To update Streamlit Cloud:")
print("  git add api_cache/")
print("  git commit -m 'Update API data'")
print("  git push")
