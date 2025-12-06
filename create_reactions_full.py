"""Create posts_reactions_full.json from posts data"""
import json
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / 'data'
CACHE_DIR = PROJECT_DIR / 'api_cache'

# Load posts
posts_data = json.load(open(DATA_DIR / 'posts.json', encoding='utf-8'))
posts = posts_data.get('posts', [])

# Extract reaction data - keep full post data for dashboard
reactions_posts = []
for post in posts:
    reactions_posts.append({
        'id': post.get('id', ''),
        'message': post.get('message', ''),
        'created_time': post.get('created_time', ''),
        'date': post.get('created_time', '')[:10] if post.get('created_time') else '',
        'permalink_url': post.get('permalink_url', ''),
        'post_type': post.get('post_type', 'Other'),
        'reactions': post.get('reactions', 0),
        'comments': post.get('comments', 0),
        'shares': post.get('shares', 0),
        'engagement': post.get('engagement', 0),
        'like': post.get('like', 0),
        'love': post.get('love', 0),
        'haha': post.get('haha', 0),
        'wow': post.get('wow', 0),
        'sad': post.get('sad', 0),
        'angry': post.get('angry', 0),
    })

# Save in expected format (dict with 'posts' key)
output_data = {
    'fetched_at': datetime.now().isoformat(),
    'total_posts': len(reactions_posts),
    'posts': reactions_posts
}

with open(CACHE_DIR / 'posts_reactions_full.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"Created posts_reactions_full.json with {len(reactions_posts)} posts")
