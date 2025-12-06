"""Check current post date range"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'

posts = json.load(open(DATA_DIR / 'posts.json', encoding='utf-8'))['posts']
dates = sorted([p['created_time'][:10] for p in posts])

print(f"Earliest: {dates[0]}")
print(f"Latest: {dates[-1]}")
print(f"Total: {len(posts)} posts")
