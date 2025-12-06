"""
Juan365 Facebook Page Engagement Scraper
Fetches engagement data (likes, comments, shares, reactions) from posts
"""

import requests
import json
import csv
from datetime import datetime

# Configuration
APP_ID = "1336532844465662"
APP_SECRET = "11a845fa8ef8b3a50835546b145788a9"
PAGE_ID = "580104038511364"
PAGE_NAME = "Juan365"

# Page Access Token (from Graph API Explorer me/accounts)
PAGE_ACCESS_TOKEN = "EAASZCkc1szf4BQOClULZCB1xE6HdZAGYibjRp8hh8V6W7ed9XDAfaKi9QHnHb8kWFkrgcor4ZAhYW5IdTSs1k1xkZARZBKLR2Ur357ayAGuAwt0YDu2vuXD0aYKZCB7pHVlbsajRDvQFMKZCvY2G6Ss5y6Bkz46WIHZBWop8ShQbpHDWBlZA7Ads2vjx5lN2ZB8OGVkG2wJ5AMZCWqkowc7FOi1G3inv06b3TIppX4ZBmP8dBeEgZD"

BASE_URL = "https://graph.facebook.com/v24.0"
OUTPUT_DIR = "C:/Users/us/Desktop/juan365_engagement_project/output"


def exchange_for_long_lived_token(short_lived_token):
    """Exchange short-lived token for long-lived token (60 days)"""
    print("\n[1/4] Exchanging for long-lived token...")

    url = f"{BASE_URL}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_lived_token
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "access_token" in data:
        print("[OK] Got long-lived token!")
        print(f"[OK] Expires in: {data.get('expires_in', 'unknown')} seconds (~60 days)")
        return data["access_token"]
    else:
        print(f"[WARNING] Could not exchange token: {data.get('error', {}).get('message', 'Unknown error')}")
        print("[INFO] Using original token instead")
        return short_lived_token


def get_page_info(access_token):
    """Get basic page information"""
    print("\n[2/4] Fetching page information...")

    url = f"{BASE_URL}/{PAGE_ID}"
    params = {
        "fields": "id,name,fan_count,followers_count,about,category",
        "access_token": access_token
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data:
        print(f"[ERROR] {data['error']['message']}")
        return None

    print(f"[OK] Page: {data.get('name')}")
    print(f"[OK] Followers: {data.get('followers_count', 'N/A'):,}")
    print(f"[OK] Fans: {data.get('fan_count', 'N/A'):,}")

    return data


def get_page_posts(access_token, limit=100):
    """Get posts with engagement data"""
    print(f"\n[3/4] Fetching posts with engagement data...")

    url = f"{BASE_URL}/{PAGE_ID}/feed"
    params = {
        "fields": "id,message,created_time,permalink_url,shares",
        "limit": 50,
        "access_token": access_token
    }

    all_posts = []
    page_count = 0

    while url and page_count < 20:  # Max 20 pages (2000 posts)
        response = requests.get(url, params=params)
        data = response.json()

        if "error" in data:
            print(f"[ERROR] {data['error']['message']}")
            break

        posts = data.get("data", [])
        all_posts.extend(posts)

        page_count += 1
        print(f"[INFO] Fetched {len(all_posts)} posts (page {page_count})...")

        # Get next page
        url = data.get("paging", {}).get("next")
        params = {}  # Next page URL has all params

    print(f"[OK] Total posts collected: {len(all_posts)}")
    return all_posts


def get_post_engagement(post_id, access_token):
    """Get engagement details for a single post"""
    url = f"{BASE_URL}/{post_id}"
    params = {
        "fields": "likes.summary(true),comments.summary(true),reactions.summary(true)",
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if "error" not in data:
            return {
                "likes": data.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
                "reactions": data.get("reactions", {}).get("summary", {}).get("total_count", 0)
            }
    except:
        pass

    return {"likes": 0, "comments": 0, "reactions": 0}


def parse_posts(raw_posts, access_token=None, fetch_engagement=True):
    """Parse posts into clean format"""
    import time
    parsed = []
    total = len(raw_posts)

    for i, post in enumerate(raw_posts):
        shares = post.get("shares", {}).get("count", 0)

        # Fetch engagement details if token provided
        if fetch_engagement and access_token:
            if i % 50 == 0:
                print(f"[INFO] Fetching engagement for posts {i+1}-{min(i+50, total)} of {total}...")
            engagement = get_post_engagement(post.get("id"), access_token)
            likes = engagement["likes"]
            comments = engagement["comments"]
            reactions = engagement["reactions"]
            time.sleep(0.1)  # Rate limiting
        else:
            likes = post.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)
            reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)

        parsed.append({
            "post_id": post.get("id", ""),
            "created_time": post.get("created_time", ""),
            "date": post.get("created_time", "")[:10] if post.get("created_time") else "",
            "message": (post.get("message", "") or "")[:200],  # First 200 chars
            "permalink": post.get("permalink_url", ""),
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "reactions": reactions,
            "total_engagement": likes + comments + shares
        })

    return parsed


def calculate_stats(posts):
    """Calculate engagement statistics"""
    if not posts:
        return {}

    total_likes = sum(p["likes"] for p in posts)
    total_comments = sum(p["comments"] for p in posts)
    total_shares = sum(p["shares"] for p in posts)
    total_reactions = sum(p["reactions"] for p in posts)

    return {
        "total_posts": len(posts),
        "totals": {
            "likes": total_likes,
            "comments": total_comments,
            "shares": total_shares,
            "reactions": total_reactions,
            "engagement": total_likes + total_comments + total_shares
        },
        "averages": {
            "likes": round(total_likes / len(posts), 1),
            "comments": round(total_comments / len(posts), 1),
            "shares": round(total_shares / len(posts), 1),
            "reactions": round(total_reactions / len(posts), 1),
            "engagement": round((total_likes + total_comments + total_shares) / len(posts), 1)
        },
        "top_post": max(posts, key=lambda p: p["total_engagement"]) if posts else None
    }


def save_to_json(data, filename):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved to: {filename}")


def save_to_csv(posts, filename):
    """Save posts to CSV file"""
    if not posts:
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=posts[0].keys())
        writer.writeheader()
        writer.writerows(posts)
    print(f"[OK] Saved to: {filename}")


def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("JUAN365 FACEBOOK ENGAGEMENT SCRAPER")
    print("=" * 60)
    print(f"Page: {PAGE_NAME}")
    print(f"Page ID: {PAGE_ID}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Exchange for long-lived token
    long_lived_token = exchange_for_long_lived_token(PAGE_ACCESS_TOKEN)

    # Step 2: Get page info
    page_info = get_page_info(long_lived_token)

    # Step 3: Get posts
    raw_posts = get_page_posts(long_lived_token)

    if not raw_posts:
        print("\n[ERROR] No posts retrieved. Check your access token.")
        return

    # Step 4: Parse and analyze
    print("\n[4/4] Processing and saving data...")
    posts = parse_posts(raw_posts, access_token=long_lived_token, fetch_engagement=True)
    stats = calculate_stats(posts)

    # Print summary
    print("\n" + "=" * 60)
    print("ENGAGEMENT SUMMARY")
    print("=" * 60)
    print(f"Total Posts: {stats['total_posts']}")
    print(f"\nTotals:")
    print(f"  Likes: {stats['totals']['likes']:,}")
    print(f"  Comments: {stats['totals']['comments']:,}")
    print(f"  Shares: {stats['totals']['shares']:,}")
    print(f"  Reactions: {stats['totals']['reactions']:,}")
    print(f"\nAverages per Post:")
    print(f"  Likes: {stats['averages']['likes']}")
    print(f"  Comments: {stats['averages']['comments']}")
    print(f"  Shares: {stats['averages']['shares']}")
    print(f"  Engagement: {stats['averages']['engagement']}")

    if stats.get('top_post'):
        print(f"\nTop Performing Post:")
        print(f"  Date: {stats['top_post']['date']}")
        print(f"  Engagement: {stats['top_post']['total_engagement']:,}")
        print(f"  Link: {stats['top_post']['permalink']}")

    # Save data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Full data as JSON
    full_data = {
        "page_info": page_info,
        "collection_date": datetime.now().isoformat(),
        "statistics": stats,
        "posts": posts,
        "long_lived_token": long_lived_token  # Save for future use
    }

    json_file = f"{OUTPUT_DIR}/Juan365_engagement_{timestamp}.json"
    csv_file = f"{OUTPUT_DIR}/Juan365_posts_{timestamp}.csv"

    save_to_json(full_data, json_file)
    save_to_csv(posts, csv_file)

    # Save token separately for easy access
    token_file = f"{OUTPUT_DIR}/long_lived_token.txt"
    with open(token_file, 'w') as f:
        f.write(f"# Juan365 Long-Lived Page Access Token\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Valid for: ~60 days\n\n")
        f.write(long_lived_token)
    print(f"[OK] Token saved to: {token_file}")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"\nFiles saved:")
    print(f"  JSON: {json_file}")
    print(f"  CSV: {csv_file}")
    print(f"  Token: {token_file}")
    print(f"\nLong-lived token valid for ~60 days")


if __name__ == "__main__":
    main()
