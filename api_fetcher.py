"""
Juan365 Facebook API Data Fetcher
Fetches all posts, engagement, video views, and page metrics
"""

import requests
import json
from pathlib import Path
from datetime import datetime

# Try to load config - supports both local config.py and Streamlit secrets
try:
    from config import PAGE_ID, PAGE_TOKEN, BASE_URL
except ImportError:
    # Running on Streamlit Cloud - use secrets
    try:
        import streamlit as st
        PAGE_ID = st.secrets["PAGE_ID"]
        PAGE_TOKEN = st.secrets["PAGE_TOKEN"]
        BASE_URL = st.secrets.get("BASE_URL", "https://graph.facebook.com/v21.0")
    except Exception:
        raise ImportError("No config.py found and Streamlit secrets not available. Please create config.py from config.template.py")

# Data directory
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)


def fetch_page_info():
    """Fetch page-level metrics: followers, rating, etc."""
    print("Fetching page info...")
    url = f"{BASE_URL}/{PAGE_ID}"
    params = {
        'fields': 'name,fan_count,followers_count,talking_about_count,overall_star_rating,rating_count',
        'access_token': PAGE_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()

    if 'error' in data:
        print(f"Error fetching page info: {data['error']['message']}")
        return None

    print(f"  Followers: {data.get('fan_count', 0):,}")
    print(f"  Rating: {data.get('overall_star_rating', 'N/A')}/5 ({data.get('rating_count', 0)} ratings)")
    print(f"  Talking About: {data.get('talking_about_count', 0):,}")

    return data


def fetch_all_posts_with_engagement():
    """Fetch ALL posts with engagement data in smaller batches."""
    print("\nFetching ALL posts with engagement...")

    all_posts = []
    url = f"{BASE_URL}/{PAGE_ID}/posts"
    # Smaller limit and include engagement summary
    params = {
        'fields': 'id,message,created_time,shares,permalink_url,status_type,'
                  'reactions.summary(true),comments.summary(true)',
        'limit': 25,  # Smaller batches to avoid "too much data" error
        'access_token': PAGE_TOKEN
    }

    page_count = 0
    while url:
        response = requests.get(url, params=params if page_count == 0 else None)
        data = response.json()

        if 'error' in data:
            error_msg = data['error'].get('message', 'Unknown error')
            print(f"  Error: {error_msg}")
            # If we hit rate limit or data limit, stop
            if 'reduce the amount' in error_msg.lower() or page_count > 0:
                break
            else:
                print("  Retrying with even smaller batch...")
                params['limit'] = 10
                continue

        posts = data.get('data', [])
        all_posts.extend(posts)
        page_count += 1
        print(f"  Page {page_count}: {len(posts)} posts (total: {len(all_posts)})")

        # Get next page URL
        paging = data.get('paging', {})
        url = paging.get('next')
        params = None  # Next URL already has params

        # Add small delay to avoid rate limiting
        import time
        time.sleep(0.2)

    print(f"  Total posts fetched: {len(all_posts)}")
    return all_posts


def fetch_all_posts():
    """Fetch all posts - basic info first (legacy, use fetch_all_posts_with_engagement instead)."""
    print("\nFetching all posts (basic info)...")

    all_posts = []
    url = f"{BASE_URL}/{PAGE_ID}/posts"
    # Basic fields only - no reactions/comments to avoid data limit
    params = {
        'fields': 'id,message,created_time,shares,permalink_url,status_type',
        'limit': 100,
        'access_token': PAGE_TOKEN
    }

    page_count = 0
    while url:
        response = requests.get(url, params=params if page_count == 0 else None)
        data = response.json()

        if 'error' in data:
            print(f"Error: {data['error']['message']}")
            break

        posts = data.get('data', [])
        all_posts.extend(posts)
        page_count += 1
        print(f"  Page {page_count}: {len(posts)} posts (total: {len(all_posts)})")

        # Get next page URL
        paging = data.get('paging', {})
        url = paging.get('next')
        params = None  # Next URL already has params

    print(f"  Total posts fetched: {len(all_posts)}")
    return all_posts


def fetch_post_engagement(post_ids):
    """Fetch engagement (reactions, comments) for posts in batches."""
    print("\nFetching engagement for posts...")

    engagement_data = {}
    batch_size = 25  # Smaller batches to avoid rate limits

    for i in range(0, len(post_ids), batch_size):
        batch = post_ids[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(post_ids) + batch_size - 1) // batch_size
        print(f"  Batch {batch_num}/{total_batches}: {len(batch)} posts...")

        for post_id in batch:
            url = f"{BASE_URL}/{post_id}"
            params = {
                'fields': 'reactions.summary(true),comments.summary(true)',
                'access_token': PAGE_TOKEN
            }
            try:
                response = requests.get(url, params=params)
                data = response.json()
                if 'error' not in data:
                    engagement_data[post_id] = {
                        'reactions': data.get('reactions', {}).get('summary', {}).get('total_count', 0),
                        'comments': data.get('comments', {}).get('summary', {}).get('total_count', 0)
                    }
            except Exception as e:
                print(f"    Error for {post_id}: {e}")

    print(f"  Got engagement for {len(engagement_data)} posts")
    return engagement_data


def fetch_reaction_breakdown(post_ids):
    """Fetch reaction breakdown for a batch of posts."""
    print("\nFetching reaction breakdown...")

    reactions_data = {}
    batch_size = 50

    for i in range(0, len(post_ids), batch_size):
        batch = post_ids[i:i+batch_size]
        print(f"  Batch {i//batch_size + 1}: {len(batch)} posts...")

        # Use batch API for efficiency
        for post_id in batch:
            url = f"{BASE_URL}/{post_id}"
            params = {
                'fields': 'reactions.type(LIKE).summary(true).as(like),'
                          'reactions.type(LOVE).summary(true).as(love),'
                          'reactions.type(HAHA).summary(true).as(haha),'
                          'reactions.type(WOW).summary(true).as(wow),'
                          'reactions.type(SAD).summary(true).as(sad),'
                          'reactions.type(ANGRY).summary(true).as(angry)',
                'access_token': PAGE_TOKEN
            }
            try:
                response = requests.get(url, params=params)
                data = response.json()
                if 'error' not in data:
                    reactions_data[post_id] = {
                        'like': data.get('like', {}).get('summary', {}).get('total_count', 0),
                        'love': data.get('love', {}).get('summary', {}).get('total_count', 0),
                        'haha': data.get('haha', {}).get('summary', {}).get('total_count', 0),
                        'wow': data.get('wow', {}).get('summary', {}).get('total_count', 0),
                        'sad': data.get('sad', {}).get('summary', {}).get('total_count', 0),
                        'angry': data.get('angry', {}).get('summary', {}).get('total_count', 0)
                    }
            except Exception as e:
                print(f"    Error for {post_id}: {e}")

    print(f"  Got reaction breakdown for {len(reactions_data)} posts")
    return reactions_data


def fetch_all_videos():
    """Fetch all videos with view counts."""
    print("\nFetching video views...")

    all_videos = []
    url = f"{BASE_URL}/{PAGE_ID}/videos"
    params = {
        'fields': 'id,title,description,created_time,length,views,permalink_url',
        'limit': 100,
        'access_token': PAGE_TOKEN
    }

    page_count = 0
    while url:
        response = requests.get(url, params=params if page_count == 0 else None)
        data = response.json()

        if 'error' in data:
            print(f"Error: {data['error']['message']}")
            break

        videos = data.get('data', [])
        all_videos.extend(videos)
        page_count += 1
        print(f"  Page {page_count}: {len(videos)} videos (total: {len(all_videos)})")

        # Get next page URL
        paging = data.get('paging', {})
        url = paging.get('next')
        params = None

    total_views = sum(v.get('views', 0) for v in all_videos)
    print(f"  Total videos: {len(all_videos)}")
    print(f"  Total views: {total_views:,}")

    return all_videos


def process_posts_with_engagement(posts, reactions_data=None):
    """Process posts that already have engagement data included."""
    processed = []
    reactions_data = reactions_data or {}

    for post in posts:
        post_id = post.get('id')

        # Get engagement directly from post (already included in API response)
        reactions_total = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
        comments_total = post.get('comments', {}).get('summary', {}).get('total_count', 0)
        shares_total = post.get('shares', {}).get('count', 0) if post.get('shares') else 0

        # Reaction breakdown from separate fetch (if available)
        post_reactions = reactions_data.get(post_id, {})
        like_count = post_reactions.get('like', 0)
        love_count = post_reactions.get('love', 0)
        haha_count = post_reactions.get('haha', 0)
        wow_count = post_reactions.get('wow', 0)
        sad_count = post_reactions.get('sad', 0)
        angry_count = post_reactions.get('angry', 0)

        # Determine post type from status_type
        status_type = post.get('status_type', 'unknown')
        if status_type == 'added_photos':
            post_type = 'Photo'
        elif status_type == 'added_video':
            post_type = 'Video'
        elif status_type == 'shared_story':
            post_type = 'Shared'
        elif status_type == 'mobile_status_update':
            post_type = 'Text'
        else:
            post_type = status_type.replace('_', ' ').title() if status_type else 'Unknown'

        processed.append({
            'id': post_id,
            'message': post.get('message', '')[:200] if post.get('message') else '',
            'created_time': post.get('created_time'),
            'permalink_url': post.get('permalink_url'),
            'post_type': post_type,
            'reactions': reactions_total,
            'comments': comments_total,
            'shares': shares_total,
            'engagement': reactions_total + comments_total + shares_total,
            'like': like_count,
            'love': love_count,
            'haha': haha_count,
            'wow': wow_count,
            'sad': sad_count,
            'angry': angry_count
        })

    return processed


def process_posts(posts, engagement_data=None, reactions_data=None):
    """Process posts into a clean format for the dashboard (legacy)."""
    processed = []
    engagement_data = engagement_data or {}
    reactions_data = reactions_data or {}

    for post in posts:
        post_id = post.get('id')

        # Get engagement from separate fetch
        post_engagement = engagement_data.get(post_id, {})
        reactions_total = post_engagement.get('reactions', 0)
        comments_total = post_engagement.get('comments', 0)
        shares_total = post.get('shares', {}).get('count', 0) if post.get('shares') else 0

        # Reaction breakdown from separate fetch
        post_reactions = reactions_data.get(post_id, {})
        like_count = post_reactions.get('like', 0)
        love_count = post_reactions.get('love', 0)
        haha_count = post_reactions.get('haha', 0)
        wow_count = post_reactions.get('wow', 0)
        sad_count = post_reactions.get('sad', 0)
        angry_count = post_reactions.get('angry', 0)

        # Determine post type from status_type
        status_type = post.get('status_type', 'unknown')
        if status_type == 'added_photos':
            post_type = 'Photo'
        elif status_type == 'added_video':
            post_type = 'Video'
        elif status_type == 'shared_story':
            post_type = 'Shared'
        elif status_type == 'mobile_status_update':
            post_type = 'Text'
        else:
            post_type = status_type.replace('_', ' ').title() if status_type else 'Unknown'

        processed.append({
            'id': post_id,
            'message': post.get('message', '')[:200] if post.get('message') else '',
            'created_time': post.get('created_time'),
            'permalink_url': post.get('permalink_url'),
            'post_type': post_type,
            'reactions': reactions_total,
            'comments': comments_total,
            'shares': shares_total,
            'engagement': reactions_total + comments_total + shares_total,
            'like': like_count,
            'love': love_count,
            'haha': haha_count,
            'wow': wow_count,
            'sad': sad_count,
            'angry': angry_count
        })

    return processed


def save_data_new(page_info, processed_posts, videos, reactions_data=None):
    """Save all data to JSON files (new version with pre-processed posts)."""
    print("\nSaving data to files...")

    # Save page info
    page_info['fetched_at'] = datetime.now().isoformat()
    with open(DATA_DIR / 'page_info.json', 'w', encoding='utf-8') as f:
        json.dump(page_info, f, indent=2, ensure_ascii=False)
    print(f"  Saved page_info.json")

    # Calculate and add totals
    total_reactions = sum(p.get('reactions', 0) for p in processed_posts)
    total_comments = sum(p.get('comments', 0) for p in processed_posts)
    total_shares = sum(p.get('shares', 0) for p in processed_posts)
    total_engagement = total_reactions + total_comments + total_shares

    # Save posts with totals
    posts_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_posts': len(processed_posts),
        'total_reactions': total_reactions,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'total_engagement': total_engagement,
        'posts': processed_posts
    }
    with open(DATA_DIR / 'posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved posts.json ({len(processed_posts)} posts)")
    print(f"    Total Reactions: {total_reactions:,}")
    print(f"    Total Comments: {total_comments:,}")
    print(f"    Total Shares: {total_shares:,}")
    print(f"    Total Engagement: {total_engagement:,}")

    # Save videos
    videos_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_videos': len(videos),
        'total_views': sum(v.get('views', 0) for v in videos),
        'videos': videos
    }
    with open(DATA_DIR / 'videos.json', 'w', encoding='utf-8') as f:
        json.dump(videos_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved videos.json ({len(videos)} videos)")


def save_data(page_info, posts, videos, engagement_data=None, reactions_data=None):
    """Save all data to JSON files (legacy)."""
    print("\nSaving data to files...")

    # Save page info
    page_info['fetched_at'] = datetime.now().isoformat()
    with open(DATA_DIR / 'page_info.json', 'w', encoding='utf-8') as f:
        json.dump(page_info, f, indent=2, ensure_ascii=False)
    print(f"  Saved page_info.json")

    # Process and save posts
    processed_posts = process_posts(posts, engagement_data, reactions_data)
    posts_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_posts': len(processed_posts),
        'posts': processed_posts
    }
    with open(DATA_DIR / 'posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved posts.json ({len(processed_posts)} posts)")

    # Save videos
    videos_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_videos': len(videos),
        'total_views': sum(v.get('views', 0) for v in videos),
        'videos': videos
    }
    with open(DATA_DIR / 'videos.json', 'w', encoding='utf-8') as f:
        json.dump(videos_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved videos.json ({len(videos)} videos)")


def main():
    print("=" * 60)
    print("JUAN365 FACEBOOK API DATA FETCHER")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Fetch page info
    page_info = fetch_page_info()
    if not page_info:
        print("Failed to fetch page info. Check your token.")
        return

    # Fetch ALL posts with engagement in one go (faster!)
    posts = fetch_all_posts_with_engagement()
    videos = fetch_all_videos()

    # Process posts (engagement already included)
    processed_posts = process_posts_with_engagement(posts)

    # Fetch reaction breakdown for last 100 posts only (optional detail)
    reactions_data = {}
    if posts:
        recent_post_ids = [p['id'] for p in posts[:100]]
        reactions_data = fetch_reaction_breakdown(recent_post_ids)
        # Update processed posts with reaction breakdown
        for p in processed_posts:
            if p['id'] in reactions_data:
                p.update(reactions_data[p['id']])

    # Save to files with totals
    save_data_new(page_info, processed_posts, videos, reactions_data)

    print()
    print("=" * 60)
    print("DATA FETCH COMPLETE!")
    print("=" * 60)
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Files saved to data/ folder:")
    print("  - page_info.json")
    print("  - posts.json (with totals)")
    print("  - videos.json")


if __name__ == '__main__':
    main()
