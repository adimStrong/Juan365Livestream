# Juan365 Livestream Dashboard - Claude Code Reference

## Project Overview
- **Location**: `C:\Users\us\Desktop\juan365_livestream_project`
- **Streamlit Cloud**: https://adimstrong-juan365livestream-streamlit-app-iknjof.streamlit.app/
- **GitHub**: https://github.com/adimStrong/Juan365Livestream
- **Facebook Page**: Juan365 Live Stream (ID: 481447078389174)

---

## Key Files

| File | Purpose |
|------|---------|
| `config.py` | Facebook API credentials (PAGE_ID, PAGE_TOKEN, API_VERSION) - **GITIGNORED** |
| `streamlit_app.py` | Main dashboard app |
| `refresh_api_cache.py` | Fetches fresh data from Facebook API |
| `merge_exports.py` | Merges CSV exports from Meta Business Suite |
| `DAILY_UPDATE.bat` | One-click daily update workflow |
| `api_cache/` | Cached API data (pushed to GitHub) |
| `exports/` | CSV exports from Meta Business Suite |

---

## Token Management

### Two Types of Tokens
| Token Type | Description |
|------------|-------------|
| **User Access Token** | Short-lived (~1 hour), from Graph API Explorer |
| **Page Access Token** | Required for page endpoints (`/posts`, `/videos`) |

### How to Convert User Token to Page Token
```python
import requests
USER_TOKEN = "EAASZCkc1szf4BO..."  # User gives this
PAGE_ID = "481447078389174"

url = f'https://graph.facebook.com/v21.0/{PAGE_ID}?fields=access_token&access_token={USER_TOKEN}'
r = requests.get(url)
PAGE_TOKEN = r.json()['access_token']
print(PAGE_TOKEN)  # Use this in config.py
```

### Current Config Format
```python
# config.py
PAGE_ID = "481447078389174"
PAGE_TOKEN = "EAASZCkc1szf4BQ..."  # Page Access Token
API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
```

### Common Token Errors
| Error | Cause | Solution |
|-------|-------|----------|
| "Session has expired" | Token expired | Get new token from Graph API Explorer |
| "User Access Token Is Not Supported" | Using User Token instead of Page Token | Convert to Page Token (see above) |
| "Invalid OAuth 2.0 Access Token" | Token invalid or wrong type | Check token type and refresh |

---

## Data Sources

### 1. Facebook API (Real-time data)
- Fetched by `refresh_api_cache.py`
- Stored in `api_cache/` folder
- Contains: page_info, posts_with_reactions, videos

### 2. Meta Business Suite CSV (Historical data)
- Downloaded manually from: https://business.facebook.com/latest/insights/content
- Stored in `exports/` folder
- Merged by `merge_exports.py`

### Important: Page ID Filtering
There are TWO Facebook pages with similar names:
| Page Name | Page ID | Status |
|-----------|---------|--------|
| Juan365 Live Stream | 61569634500241 | **CORRECT** (for CSV) |
| Juan365 | 61572881214141 | WRONG (filter out) |

The `merge_exports.py` filters by `Page ID == 61569634500241` to avoid data mixing.

---

## Daily Update Workflow

### Option 1: Run DAILY_UPDATE.bat
```batch
@echo off
set GIT_PATH=C:\Users\us\AppData\Local\Programs\Git\cmd\git.exe
cd /d C:\Users\us\Desktop\juan365_livestream_project
python open_meta_export.py    # Opens Meta Business Suite
pause                          # Wait for CSV download
python merge_exports.py        # Merge CSVs
python api_fetcher.py          # Fetch API data
python refresh_api_cache.py    # Refresh cache
"%GIT_PATH%" add api_cache/ exports/
"%GIT_PATH%" commit -m "Daily update: %date%"
"%GIT_PATH%" push origin main
```

### Option 2: Manual Steps
```bash
cd C:\Users\us\Desktop\juan365_livestream_project
python refresh_api_cache.py
git add api_cache/
git commit -m "Update API cache"
git push origin main
```

---

## Troubleshooting

### Data Not Updating on Streamlit Cloud
1. Check if `api_cache/` was pushed to GitHub
2. Verify Streamlit Cloud auto-deployed (check GitHub commits)
3. Hard refresh browser (Ctrl+Shift+R)

### Wrong Data Showing (Mixed Pages)
1. Check `exports/` folder for CSVs from wrong page
2. Delete CSVs that don't have Page ID `61569634500241`
3. Re-run `merge_exports.py`

### Git Not Recognized in .bat Files
Use full path: `C:\Users\us\AppData\Local\Programs\Git\cmd\git.exe`

### Token Expired
1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app and page
3. Generate new User Access Token
4. Convert to Page Access Token (see above)
5. Update `config.py`

---

## API Endpoints Used

```python
# Page Info
GET /{PAGE_ID}?fields=name,fan_count,followers_count

# Posts with Reactions
GET /{PAGE_ID}/posts?fields=id,message,created_time,reactions.summary(true),comments.summary(true),shares

# Videos
GET /{PAGE_ID}/videos?fields=id,title,description,created_time,length,views
```

---

## File Structure
```
juan365_livestream_project/
├── streamlit_app.py          # Main dashboard
├── config.py                 # API credentials (gitignored)
├── refresh_api_cache.py      # Fetch API data
├── merge_exports.py          # Merge CSV files
├── api_fetcher.py            # Alternative API fetcher
├── DAILY_UPDATE.bat          # One-click update
├── open_meta_export.py       # Opens Meta Business Suite
├── api_cache/                # API data (pushed to git)
│   ├── page_info.json
│   ├── posts_with_reactions.json
│   └── videos.json
├── exports/                  # CSV exports
│   └── Juan365_MERGED_ALL.csv
├── requirements.txt
├── .gitignore
└── CLAUDE_PROMPT.md          # This file
```

---

## Quick Commands

```bash
# Refresh API data and push
cd /c/Users/us/Desktop/juan365_livestream_project
python refresh_api_cache.py
git add api_cache/ && git commit -m "Update cache" && git push

# Test token
python -c "from config import *; import requests; print(requests.get(f'{BASE_URL}/{PAGE_ID}?fields=name&access_token={PAGE_TOKEN}').json())"

# Convert User Token to Page Token
python -c "import requests; r=requests.get('https://graph.facebook.com/v21.0/481447078389174?fields=access_token&access_token=USER_TOKEN_HERE'); print(r.json()['access_token'])"
```

---

## Last Updated
- **Date**: December 10, 2025
- **Token Expires**: ~60 days from last refresh
- **Note**: config.py is gitignored - token stays local only
