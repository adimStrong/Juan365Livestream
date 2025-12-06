"""Quick script to create all_api_data.json from fetched data"""
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / 'data'
CACHE_DIR = PROJECT_DIR / 'api_cache'

# Load data
page_info = json.load(open(DATA_DIR / 'page_info.json', encoding='utf-8'))
posts_data = json.load(open(DATA_DIR / 'posts.json', encoding='utf-8'))
videos_data = json.load(open(DATA_DIR / 'videos.json', encoding='utf-8'))

# Combine
all_data = {
    'page_info': page_info,
    'posts': posts_data.get('posts', []),
    'videos': videos_data.get('videos', []),
    'total_reactions': posts_data.get('total_reactions', 0),
    'total_comments': posts_data.get('total_comments', 0),
    'total_shares': posts_data.get('total_shares', 0),
    'total_engagement': posts_data.get('total_engagement', 0),
}

# Save
CACHE_DIR.mkdir(exist_ok=True)
with open(CACHE_DIR / 'all_api_data.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"Created all_api_data.json")
print(f"  Posts: {len(all_data['posts'])}")
print(f"  Videos: {len(all_data['videos'])}")
print(f"  Total Reactions: {all_data['total_reactions']:,}")
print(f"  Total Comments: {all_data['total_comments']:,}")
print(f"  Total Shares: {all_data['total_shares']:,}")
