"""
Fetch ALL Facebook Reels with engagement data
Reels are separate from regular posts and require the video_reels endpoint
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


def fetch_all_reels():
    """Fetch ALL reels from the page"""
    print("=" * 60)
    print("FETCHING ALL REELS")
    print("=" * 60)

    all_reels = []
    url = f"{BASE_URL}/{PAGE_ID}/video_reels"

    params = {
        'fields': 'id,description,created_time,permalink_url,updated_time',
        'limit': 25,
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
                break

            reels = data.get('data', [])
            all_reels.extend(reels)
            page_count += 1

            if reels:
                oldest = reels[-1].get('created_time', '')[:10]
                newest = reels[0].get('created_time', '')[:10]
                print(f"  Page {page_count}: {len(reels)} reels ({newest} to {oldest}) - Total: {len(all_reels)}")
            else:
                print(f"  Page {page_count}: No more reels")

            # Get next page URL
            paging = data.get('paging', {})
            url = paging.get('next')
            params = None

            time.sleep(0.3)

        except Exception as e:
            print(f"  Exception: {e}")
            break

    print(f"\nTotal reels fetched: {len(all_reels)}")
    return all_reels


def fetch_reel_engagement(reel_id):
    """Fetch engagement data for a single reel"""
    url = f"{BASE_URL}/{reel_id}"

    # Reels/Videos use 'likes' not 'reactions'
    params = {
        'access_token': PAGE_TOKEN,
        'fields': 'likes.summary(true),comments.summary(true)'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()

            likes_total = data.get('likes', {}).get('summary', {}).get('total_count', 0)
            comments_total = data.get('comments', {}).get('summary', {}).get('total_count', 0)

            return {
                'likes': likes_total,
                'comments': comments_total,
                'shares': 0,  # Shares not available for reels via API
                'like': likes_total,  # Use likes as the reaction count
                'love': 0,
                'haha': 0,
                'wow': 0,
                'sad': 0,
                'angry': 0
            }
    except Exception as e:
        pass

    return None


def process_reel(reel, engagement=None):
    """Process a single reel into clean format"""
    engagement = engagement or {}

    # Calculate total reactions from breakdown
    reactions_total = sum([
        engagement.get('like', 0),
        engagement.get('love', 0),
        engagement.get('haha', 0),
        engagement.get('wow', 0),
        engagement.get('sad', 0),
        engagement.get('angry', 0)
    ])

    # Use likes if reactions breakdown is 0
    if reactions_total == 0:
        reactions_total = engagement.get('likes', 0)

    comments_total = engagement.get('comments', 0)
    shares_total = engagement.get('shares', 0)

    return {
        'id': reel.get('id'),
        'message': (reel.get('description', '') or '')[:200],
        'created_time': reel.get('created_time'),
        'permalink_url': reel.get('permalink_url'),
        'post_type': 'Reel',
        'reactions': reactions_total,
        'comments': comments_total,
        'shares': shares_total,
        'engagement': reactions_total + comments_total + shares_total,
        'like': engagement.get('like', 0),
        'love': engagement.get('love', 0),
        'haha': engagement.get('haha', 0),
        'wow': engagement.get('wow', 0),
        'sad': engagement.get('sad', 0),
        'angry': engagement.get('angry', 0)
    }


def main():
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Fetch all reels
    raw_reels = fetch_all_reels()

    if not raw_reels:
        print("No reels fetched!")
        return

    # Check date range
    dates = sorted([r.get('created_time', '')[:10] for r in raw_reels if r.get('created_time')])
    print(f"\nDate range: {dates[0]} to {dates[-1]}")

    # Step 2: Fetch engagement for all reels
    print("\n" + "=" * 60)
    print("FETCHING ENGAGEMENT DATA FOR ALL REELS")
    print("=" * 60)

    processed_reels = []
    total = len(raw_reels)

    for i, reel in enumerate(raw_reels):
        reel_id = reel.get('id')

        if (i + 1) % 10 == 0 or i == 0:
            print(f"\rProcessing {i + 1}/{total}...", end='', flush=True)

        engagement = fetch_reel_engagement(reel_id)
        processed = process_reel(reel, engagement)
        processed_reels.append(processed)

        time.sleep(0.4)

    print(f"\rProcessed {total}/{total} reels")

    # Step 3: Calculate totals
    total_reactions = sum(r.get('reactions', 0) for r in processed_reels)
    total_comments = sum(r.get('comments', 0) for r in processed_reels)
    total_shares = sum(r.get('shares', 0) for r in processed_reels)
    total_engagement = total_reactions + total_comments + total_shares

    # Step 4: Save reels data
    print("\n" + "=" * 60)
    print("SAVING REELS DATA")
    print("=" * 60)

    reels_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_reels': len(processed_reels),
        'total_reactions': total_reactions,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'total_engagement': total_engagement,
        'reels': processed_reels
    }

    with open(DATA_DIR / 'reels.json', 'w', encoding='utf-8') as f:
        json.dump(reels_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved reels.json ({len(processed_reels)} reels)")

    # Step 5: Merge reels into posts.json and update cache files
    print("\n" + "=" * 60)
    print("MERGING REELS INTO POSTS DATA")
    print("=" * 60)

    # Load existing posts
    try:
        with open(DATA_DIR / 'posts.json', 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
        existing_posts = posts_data.get('posts', [])
    except:
        existing_posts = []

    # Get existing post IDs to avoid duplicates
    existing_ids = {p.get('id') for p in existing_posts}

    # Add reels that aren't already in posts
    new_reels_count = 0
    for reel in processed_reels:
        if reel['id'] not in existing_ids:
            existing_posts.append(reel)
            new_reels_count += 1

    # Sort all by date
    existing_posts.sort(key=lambda x: x.get('created_time', ''), reverse=True)

    # Recalculate totals
    all_reactions = sum(p.get('reactions', 0) for p in existing_posts)
    all_comments = sum(p.get('comments', 0) for p in existing_posts)
    all_shares = sum(p.get('shares', 0) for p in existing_posts)
    all_engagement = all_reactions + all_comments + all_shares

    # Save updated posts.json
    updated_posts_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_posts': len(existing_posts),
        'total_reactions': all_reactions,
        'total_comments': all_comments,
        'total_shares': all_shares,
        'total_engagement': all_engagement,
        'posts': existing_posts
    }

    with open(DATA_DIR / 'posts.json', 'w', encoding='utf-8') as f:
        json.dump(updated_posts_data, f, indent=2, ensure_ascii=False)
    print(f"  Updated posts.json (added {new_reels_count} new reels, total: {len(existing_posts)} posts)")

    # Update posts_reactions_full.json
    reactions_posts = [{
        'id': p.get('id', ''),
        'message': p.get('message', ''),
        'created_time': p.get('created_time', ''),
        'date': p.get('created_time', '')[:10] if p.get('created_time') else '',
        'permalink_url': p.get('permalink_url', ''),
        'post_type': p.get('post_type', 'Other'),
        'reactions': p.get('reactions', 0),
        'comments': p.get('comments', 0),
        'shares': p.get('shares', 0),
        'engagement': p.get('engagement', 0),
        'like': p.get('like', 0),
        'love': p.get('love', 0),
        'haha': p.get('haha', 0),
        'wow': p.get('wow', 0),
        'sad': p.get('sad', 0),
        'angry': p.get('angry', 0),
    } for p in existing_posts]

    reactions_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_posts': len(reactions_posts),
        'posts': reactions_posts
    }

    with open(CACHE_DIR / 'posts_reactions_full.json', 'w', encoding='utf-8') as f:
        json.dump(reactions_data, f, indent=2, ensure_ascii=False)
    print(f"  Updated posts_reactions_full.json")

    # Update all_api_data.json
    try:
        with open(CACHE_DIR / 'all_api_data.json', 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except:
        all_data = {}

    all_data['posts'] = existing_posts
    all_data['total_reactions'] = all_reactions
    all_data['total_comments'] = all_comments
    all_data['total_shares'] = all_shares
    all_data['total_engagement'] = all_engagement

    with open(CACHE_DIR / 'all_api_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"  Updated all_api_data.json")

    # Print summary
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"Total reels: {len(processed_reels)}")
    print(f"New reels added: {new_reels_count}")
    print(f"Total posts (including reels): {len(existing_posts)}")
    print(f"\nReels engagement:")
    print(f"  Reactions: {total_reactions:,}")
    print(f"  Comments: {total_comments:,}")
    print(f"  Shares: {total_shares:,}")
    print(f"  Total: {total_engagement:,}")

    # Post type breakdown
    types = {}
    for p in existing_posts:
        pt = p.get('post_type', 'Unknown')
        types[pt] = types.get(pt, 0) + 1

    print(f"\nPost type breakdown:")
    for pt, count in sorted(types.items(), key=lambda x: -x[1]):
        print(f"  {pt}: {count}")

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
