"""
Fetch historical reaction breakdown for all posts from June 2025
This script fetches like/love/haha/wow/sad/angry for each post
"""

import requests
import json
import time
from datetime import datetime
from config import PAGE_ID, PAGE_TOKEN, BASE_URL

def fetch_reaction_breakdown(post_id):
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
        else:
            print(f"Error fetching {post_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception fetching {post_id}: {e}")
        return None

def main():
    print("=" * 60)
    print("FETCHING HISTORICAL REACTION BREAKDOWN")
    print("=" * 60)

    # Load existing posts from all_api_data.json
    with open('api_cache/all_api_data.json', 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    posts = all_data.get('posts', [])
    total_posts = len(posts)
    print(f"\nFound {total_posts} posts to process")

    # Check if we have existing reaction data to resume from
    try:
        with open('api_cache/posts_reactions_full.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            processed_ids = {p['id'] for p in existing_data.get('posts', [])}
            print(f"Resuming from existing data: {len(processed_ids)} posts already processed")
    except FileNotFoundError:
        existing_data = {'posts': []}
        processed_ids = set()
        print("Starting fresh - no existing data found")

    # Process posts
    posts_with_reactions = existing_data.get('posts', [])
    batch_size = 50  # Save every 50 posts
    processed_count = len(processed_ids)

    for i, post in enumerate(posts):
        post_id = post['id']

        # Skip if already processed
        if post_id in processed_ids:
            continue

        print(f"\rProcessing {processed_count + 1}/{total_posts}: {post_id[:30]}...", end='', flush=True)

        # Fetch reaction breakdown
        reactions = fetch_reaction_breakdown(post_id)

        if reactions:
            # Create enhanced post with reaction breakdown
            enhanced_post = post.copy()
            enhanced_post.update(reactions)
            posts_with_reactions.append(enhanced_post)
            processed_ids.add(post_id)
            processed_count += 1

        # Save checkpoint every batch_size posts
        if processed_count % batch_size == 0:
            save_data(posts_with_reactions, processed_count, total_posts)

        # Rate limiting - Facebook allows ~200 calls/hour for reactions
        # Sleep 0.5 seconds between calls to be safe
        time.sleep(0.5)

    # Final save
    save_data(posts_with_reactions, processed_count, total_posts)

    print(f"\n\n{'=' * 60}")
    print("COMPLETE!")
    print(f"{'=' * 60}")
    print(f"Total posts with reaction breakdown: {len(posts_with_reactions)}")

    # Calculate totals
    totals = {
        'like': sum(p.get('like', 0) for p in posts_with_reactions),
        'love': sum(p.get('love', 0) for p in posts_with_reactions),
        'haha': sum(p.get('haha', 0) for p in posts_with_reactions),
        'wow': sum(p.get('wow', 0) for p in posts_with_reactions),
        'sad': sum(p.get('sad', 0) for p in posts_with_reactions),
        'angry': sum(p.get('angry', 0) for p in posts_with_reactions)
    }

    print(f"\nReaction Totals:")
    for reaction, count in totals.items():
        print(f"  {reaction.upper()}: {count:,}")
    print(f"  TOTAL: {sum(totals.values()):,}")

def save_data(posts, processed, total):
    """Save data to file"""
    output = {
        'fetched_at': datetime.now().isoformat(),
        'total_posts': len(posts),
        'progress': f"{processed}/{total}",
        'posts': posts
    }

    with open('api_cache/posts_reactions_full.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  [Saved checkpoint: {processed}/{total} posts]")

if __name__ == '__main__':
    main()
