"""
Fetch ALL historical posts from August 2025 to present with full reaction breakdown
(Page was created in August 2025)
"""
import requests
import json
import time
from pathlib import Path
from datetime import datetime

from config import PAGE_ID, PAGE_TOKEN, BASE_URL

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / 'data'
CACHE_DIR = PROJECT_DIR / 'api_cache'

DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)


def fetch_all_posts_since_july():
    """Fetch ALL posts from July 2025 to present"""
    print("=" * 60)
    print("FETCHING ALL POSTS SINCE AUGUST 2025")
    print("=" * 60)

    all_posts = []
    url = f"{BASE_URL}/{PAGE_ID}/posts"

    # Use since parameter to get posts from August 1, 2025
    # Unix timestamp for August 1, 2025 00:00:00 UTC
    # (Page was created in August 2025)
    aug_1_2025 = 1722470400  # August 1, 2025

    params = {
        'fields': 'id,message,created_time,shares,permalink_url,status_type,'
                  'reactions.summary(true),comments.summary(true)',
        'limit': 100,  # Larger batches for historical fetch
        'since': aug_1_2025,
        'access_token': PAGE_TOKEN
    }

    page_count = 0
    while url:
        try:
            response = requests.get(url, params=params if page_count == 0 else None, timeout=60)
            data = response.json()

            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                print(f"  Error: {error_msg}")
                if 'reduce the amount' in error_msg.lower():
                    # Reduce batch size and retry
                    if params and params.get('limit', 100) > 25:
                        params['limit'] = 25
                        print("  Retrying with smaller batch...")
                        continue
                break

            posts = data.get('data', [])
            all_posts.extend(posts)
            page_count += 1

            if posts:
                oldest = posts[-1].get('created_time', '')[:10]
                newest = posts[0].get('created_time', '')[:10]
                print(f"  Page {page_count}: {len(posts)} posts ({newest} to {oldest}) - Total: {len(all_posts)}")
            else:
                print(f"  Page {page_count}: No more posts")

            # Get next page URL
            paging = data.get('paging', {})
            url = paging.get('next')
            params = None  # Next URL already has params

            # Small delay to avoid rate limiting
            time.sleep(0.3)

        except Exception as e:
            print(f"  Exception: {e}")
            break

    print(f"\nTotal posts fetched: {len(all_posts)}")

    # Sort by date
    all_posts.sort(key=lambda x: x.get('created_time', ''), reverse=True)

    return all_posts


def fetch_reaction_breakdown_for_post(post_id):
    """Fetch reaction breakdown for a single post"""
    url = f"{BASE_URL}/{post_id}"
    params = {
        'access_token': PAGE_TOKEN,
        'fields': ','.join([
            'reactions.type(LIKE).summary(true).limit(0).as(like)',
            'reactions.type(LOVE).summary(true).limit(0).as(love)',
            'reactions.type(HAHA).summary(true).limit(0).as(haha)',
            'reactions.type(WOW).summary(true).limit(0).as(wow)',
            'reactions.type(SAD).summary(true).limit(0).as(sad)',
            'reactions.type(ANGRY).summary(true).limit(0).as(angry)'
        ])
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return {
                'like': data.get('like', {}).get('summary', {}).get('total_count', 0),
                'love': data.get('love', {}).get('summary', {}).get('total_count', 0),
                'haha': data.get('haha', {}).get('summary', {}).get('total_count', 0),
                'wow': data.get('wow', {}).get('summary', {}).get('total_count', 0),
                'sad': data.get('sad', {}).get('summary', {}).get('total_count', 0),
                'angry': data.get('angry', {}).get('summary', {}).get('total_count', 0)
            }
    except Exception as e:
        print(f"    Error fetching reactions for {post_id}: {e}")

    return None


def process_post(post, reactions=None):
    """Process a single post into clean format"""
    reactions = reactions or {}

    # Get engagement from API response
    reactions_total = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
    comments_total = post.get('comments', {}).get('summary', {}).get('total_count', 0)
    shares_total = post.get('shares', {}).get('count', 0) if post.get('shares') else 0

    # Determine post type
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

    return {
        'id': post.get('id'),
        'message': post.get('message', '')[:200] if post.get('message') else '',
        'created_time': post.get('created_time'),
        'permalink_url': post.get('permalink_url'),
        'post_type': post_type,
        'reactions': reactions_total,
        'comments': comments_total,
        'shares': shares_total,
        'engagement': reactions_total + comments_total + shares_total,
        'like': reactions.get('like', 0),
        'love': reactions.get('love', 0),
        'haha': reactions.get('haha', 0),
        'wow': reactions.get('wow', 0),
        'sad': reactions.get('sad', 0),
        'angry': reactions.get('angry', 0)
    }


def main():
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Fetch all posts
    raw_posts = fetch_all_posts_since_july()

    if not raw_posts:
        print("No posts fetched!")
        return

    # Check date range
    dates = sorted([p.get('created_time', '')[:10] for p in raw_posts])
    print(f"\nDate range: {dates[0]} to {dates[-1]}")

    # Step 2: Fetch reaction breakdown for ALL posts
    print("\n" + "=" * 60)
    print("FETCHING REACTION BREAKDOWN FOR ALL POSTS")
    print("=" * 60)

    processed_posts = []
    total = len(raw_posts)

    for i, post in enumerate(raw_posts):
        post_id = post.get('id')

        # Progress update every 10 posts
        if (i + 1) % 10 == 0 or i == 0:
            print(f"\rProcessing {i + 1}/{total}...", end='', flush=True)

        # Fetch reaction breakdown
        reactions = fetch_reaction_breakdown_for_post(post_id)

        # Process post
        processed = process_post(post, reactions)
        processed_posts.append(processed)

        # Rate limiting - be conservative
        time.sleep(0.4)

    print(f"\rProcessed {total}/{total} posts")

    # Step 3: Calculate totals
    total_reactions = sum(p.get('reactions', 0) for p in processed_posts)
    total_comments = sum(p.get('comments', 0) for p in processed_posts)
    total_shares = sum(p.get('shares', 0) for p in processed_posts)
    total_engagement = total_reactions + total_comments + total_shares

    # Step 4: Save to files
    print("\n" + "=" * 60)
    print("SAVING DATA")
    print("=" * 60)

    # Save posts.json
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

    # Save posts_reactions_full.json for dashboard
    reactions_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_posts': len(processed_posts),
        'posts': [{
            'id': p['id'],
            'message': p['message'],
            'created_time': p['created_time'],
            'date': p['created_time'][:10] if p['created_time'] else '',
            'permalink_url': p['permalink_url'],
            'post_type': p['post_type'],
            'reactions': p['reactions'],
            'comments': p['comments'],
            'shares': p['shares'],
            'engagement': p['engagement'],
            'like': p['like'],
            'love': p['love'],
            'haha': p['haha'],
            'wow': p['wow'],
            'sad': p['sad'],
            'angry': p['angry']
        } for p in processed_posts]
    }

    with open(CACHE_DIR / 'posts_reactions_full.json', 'w', encoding='utf-8') as f:
        json.dump(reactions_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved posts_reactions_full.json")

    # Update all_api_data.json
    try:
        with open(CACHE_DIR / 'all_api_data.json', 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except:
        all_data = {}

    all_data['posts'] = processed_posts
    all_data['total_reactions'] = total_reactions
    all_data['total_comments'] = total_comments
    all_data['total_shares'] = total_shares
    all_data['total_engagement'] = total_engagement

    with open(CACHE_DIR / 'all_api_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"  Updated all_api_data.json")

    # Print summary
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"Total posts: {len(processed_posts)}")
    print(f"Date range: {dates[0]} to {dates[-1]}")
    print(f"\nEngagement totals:")
    print(f"  Reactions: {total_reactions:,}")
    print(f"  Comments: {total_comments:,}")
    print(f"  Shares: {total_shares:,}")
    print(f"  Total Engagement: {total_engagement:,}")

    # Reaction breakdown totals
    like_total = sum(p.get('like', 0) for p in processed_posts)
    love_total = sum(p.get('love', 0) for p in processed_posts)
    haha_total = sum(p.get('haha', 0) for p in processed_posts)
    wow_total = sum(p.get('wow', 0) for p in processed_posts)
    sad_total = sum(p.get('sad', 0) for p in processed_posts)
    angry_total = sum(p.get('angry', 0) for p in processed_posts)

    print(f"\nReaction breakdown:")
    print(f"  👍 Like: {like_total:,}")
    print(f"  ❤️ Love: {love_total:,}")
    print(f"  😆 Haha: {haha_total:,}")
    print(f"  😮 Wow: {wow_total:,}")
    print(f"  😢 Sad: {sad_total:,}")
    print(f"  😠 Angry: {angry_total:,}")

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
