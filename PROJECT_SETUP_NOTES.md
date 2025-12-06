# Facebook Page Dashboard - Project Setup Notes

## Quick Reference for New Facebook Page Dashboard Projects

This document contains step-by-step instructions for setting up a new Facebook Page analytics dashboard. Use this as a template for future projects.

---

## PHASE 1: Facebook API Credentials

### Step 1.1: Get Page ID
1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app
3. Run query: `GET /me/accounts`
4. Find your page in results - note the `id` field

**Alternative:** Check page source at facebook.com/yourpage for `page_id`

### Step 1.2: Get Page Access Token
1. Go to Graph API Explorer: https://developers.facebook.com/tools/explorer/
2. Select your app
3. Click "Get User Access Token"
4. Select permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_read_user_content`
   - `read_insights`
5. Click "Generate Access Token"
6. Authorize and select your page

### Step 1.3: Convert to Permanent Page Token
1. Exchange short-lived token for long-lived:
```
GET /oauth/access_token?
  grant_type=fb_exchange_token&
  client_id={app_id}&
  client_secret={app_secret}&
  fb_exchange_token={short_lived_token}
```

2. Get permanent page token:
```
GET /me/accounts?access_token={long_lived_user_token}
```

3. Extract the `access_token` for your page (this is permanent)

### Step 1.4: Verify Token
- Go to https://developers.facebook.com/tools/debug/accesstoken/
- Paste the page token
- Confirm: Type = "Page", Expires = "Never"

---

## PHASE 2: Project Setup

### Step 2.1: Copy Base Project
```bash
# Copy from existing project
cp -r source_project/ new_project/

# Or clone from git
git clone <repo_url> new_project
```

### Step 2.2: Update config.py
```python
PAGE_ID = "YOUR_PAGE_ID"
PAGE_TOKEN = "YOUR_PAGE_TOKEN"
API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
```

### Step 2.3: Clear Data Folders
Delete contents of (keep folders):
- `api_cache/`
- `data/`
- `exports/`
- `output/`

### Step 2.4: Update Branding
Files to update:
- `streamlit_app.py` - page title, logo alt text
- `assets/` - replace logo image

---

## PHASE 3: Data Fetching

### IMPORTANT: Facebook API Endpoints

| Content Type | Endpoint | Fields |
|--------------|----------|--------|
| **Posts** | `/{PAGE_ID}/posts` | id,message,created_time,shares,permalink_url,status_type,reactions.summary(true),comments.summary(true) |
| **Videos** | `/{PAGE_ID}/videos` | id,title,description,created_time,permalink_url,likes.summary(true),comments.summary(true) |
| **Reels** | `/{PAGE_ID}/video_reels` | id,description,created_time,permalink_url |
| **Page Info** | `/{PAGE_ID}` | id,name,fan_count,followers_count |

### Key Differences by Content Type:

1. **Posts** - Use `reactions.type(LIKE/LOVE/HAHA/etc).summary(true)` for breakdown
2. **Videos** - Use `likes.summary(true)` (reactions doesn't work)
3. **Reels** - Use `likes.summary(true)` (reactions doesn't work), no shares field

### Step 3.1: Fetch All Historical Posts
Run: `python fetch_all_historical.py`

This fetches:
- All posts since page creation (check earliest post date first)
- Reaction breakdown (like, love, haha, wow, sad, angry) for each post
- Saves to `data/posts.json` and `api_cache/posts_reactions_full.json`

**Note:** Update the `since` timestamp in the script to match when your page was created.

### Step 3.2: Fetch Reels (SEPARATE ENDPOINT!)
Run: `python fetch_reels.py`

**CRITICAL:** Reels are NOT included in the /posts endpoint!
- Reels require the `/video_reels` endpoint
- Reels use `likes.summary(true)` not `reactions`
- Reels don't have `shares` field

### Step 3.3: Fetch Videos
Run: `python api_fetcher.py` or dedicated video script

---

## PHASE 4: Data Structure

### Required JSON Files in api_cache/

1. **page_info.json**
```json
{
  "id": "PAGE_ID",
  "name": "Page Name",
  "fan_count": 12345,
  "followers_count": 12345
}
```

2. **posts_reactions_full.json** (MAIN FILE FOR DASHBOARD)
```json
{
  "fetched_at": "2025-12-06T12:00:00",
  "total_posts": 591,
  "posts": [
    {
      "id": "POST_ID",
      "message": "Post text...",
      "created_time": "2025-12-06T10:00:00+0000",
      "date": "2025-12-06",
      "permalink_url": "https://facebook.com/...",
      "post_type": "Photo|Video|Reel|Text|Shared",
      "reactions": 100,
      "comments": 50,
      "shares": 25,
      "engagement": 175,
      "like": 60,
      "love": 30,
      "haha": 5,
      "wow": 3,
      "sad": 1,
      "angry": 1
    }
  ]
}
```

3. **videos.json**
```json
{
  "fetched_at": "2025-12-06T12:00:00",
  "total_videos": 91,
  "total_views": 500000,
  "videos": [...]
}
```

4. **reels.json** (optional, for separate reel analytics)
```json
{
  "fetched_at": "2025-12-06T12:00:00",
  "total_reels": 59,
  "reels": [...]
}
```

---

## PHASE 5: Running the Dashboard

### Start Dashboard
```bash
streamlit run streamlit_app.py --server.port 8502 --server.headless true
```

### Verify Data Loading
Check that dashboard shows:
- Total posts count
- Reaction breakdown chart
- Post type filter (should include "Reel" if reels fetched)
- Date range matches your data

---

## Common Issues & Solutions

### Issue 1: "No data" on dashboard
**Cause:** Missing or empty `posts_reactions_full.json`
**Solution:** Run `python fetch_all_historical.py` then `python fetch_reels.py`

### Issue 2: No Reels showing
**Cause:** Reels require separate API endpoint
**Solution:** Run `python fetch_reels.py` - reels are NOT in /posts endpoint

### Issue 3: API "reduce the amount of data" error
**Cause:** Batch size too large
**Solution:** Reduce `limit` parameter to 25 in API calls

### Issue 4: Unicode encoding errors on Windows
**Cause:** Console can't display emojis
**Solution:** Use `PYTHONIOENCODING=utf-8` or avoid printing emojis

### Issue 5: Zero reactions for Reels/Videos
**Cause:** Using `reactions` field instead of `likes`
**Solution:** Reels/Videos use `likes.summary(true)` not `reactions`

### Issue 6: Dashboard shows 0 Reels but data was fetched
**Cause:** `posts.json` and `posts_reactions_full.json` are out of sync
**Solution:** After running `fetch_reels.py`, both files must have the same data. The dashboard reads from `posts.json`. Sync the files:
```python
import json
with open('api_cache/posts_reactions_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
with open('api_cache/posts.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

### Issue 7: Post type filter shows singular (Photo) instead of plural (Photos)
**Cause:** Dashboard expects plural post types for display
**Solution:** Mapping in `streamlit_app.py` converts: Photo→Photos, Video→Videos, Reel→Reels

---

## Scripts Summary

| Script | Purpose |
|--------|---------|
| `fetch_all_historical.py` | Fetch ALL posts since August 2025 with reaction breakdown |
| `fetch_reels.py` | Fetch ALL reels (separate endpoint) with engagement |
| `api_fetcher.py` | Fetch recent data (posts, videos, page info) |
| `refresh_api_cache.py` | Refresh all cached data |
| `create_all_data.py` | Combine data into all_api_data.json |
| `create_reactions_full.py` | Create posts_reactions_full.json from posts.json |
| `check_dates.py` | Quick check of post date range |

---

## Post Types Mapping

| Facebook status_type | Dashboard post_type |
|---------------------|---------------------|
| added_photos | Photo |
| added_video | Video |
| shared_story | Shared |
| mobile_status_update | Text |
| (from video_reels endpoint) | Reel |

---

## Rate Limiting

- Posts endpoint: ~200 calls/hour
- Sleep 0.3-0.5 seconds between API calls
- For reaction breakdown: ~0.4 second delay per post

---

## Updating Data

### Daily/Regular Updates
```bash
python refresh_api_cache.py
python fetch_reels.py
```

### Full Historical Refresh
```bash
python fetch_all_historical.py
python fetch_reels.py
```

---

## File Locations

```
project/
├── api_cache/           # JSON data files for dashboard
│   ├── page_info.json
│   ├── posts_reactions_full.json  <-- MAIN DATA FILE
│   ├── all_api_data.json
│   └── videos.json
├── data/                # Backup/raw data
│   ├── posts.json
│   └── reels.json
├── assets/              # Logo, images
├── config.py            # API credentials
├── streamlit_app.py     # Dashboard app
├── fetch_all_historical.py
├── fetch_reels.py
└── PROJECT_SETUP_NOTES.md  <-- This file
```

---

## Checklist for New Project

- [ ] Get Facebook Page ID
- [ ] Get permanent Page Access Token
- [ ] Update config.py with credentials
- [ ] Clear old data folders
- [ ] Update branding (title, logo)
- [ ] Run fetch_all_historical.py
- [ ] Run fetch_reels.py (IMPORTANT!)
- [ ] Verify dashboard shows all data
- [ ] Check Post Type filter includes "Reel"

---

Last Updated: 2025-12-06
