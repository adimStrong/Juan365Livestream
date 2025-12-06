# Juan365 Social Media Dashboard - Project Context

> **Use this file to provide context to Claude in new sessions.**
> Copy and paste this content when starting a new conversation about this project.

---

## Project Overview

**Name:** Juan365 Social Media Dashboard
**Type:** Streamlit web dashboard for Facebook page analytics
**Location:** `C:\Users\us\Desktop\juan365_engagement_project`
**GitHub:** https://github.com/adimStrong/Juan365-Socmed-Mainpage.git
**Live URL:** https://juan365-socmed-mainpage.streamlit.app
**Local URL:** http://localhost:8501

---

## Facebook Page Info

- **Page Name:** Juan365
- **Page ID:** `580104038511364`
- **Followers:** 2,177,005+
- **Rating:** 4.6/5 (802 ratings)
- **Content:** Daily posts (photos, videos, reels, text)

---

## API Configuration

```python
# config.py
PAGE_ID = "580104038511364"
PAGE_TOKEN = "EAASZCkc1szf4BQGTviUebyDUZCVbO2tLUSZBtUNYRLAjSGon6m8qkjLo2w9IOTZCxHh4x4tKw8yr18GGWu8NLMQemGsCsWvZBhXxleAyhaV4giLoRQyU5qspoTPKTwhtKPzdtePVBSZA936rGmsp3BP1DTyG7rYbUZAeoHDxG45Y3YkG8e1xmoAhMijNUj8LY3ofZB3IIciv"
BASE_URL = "https://graph.facebook.com/v21.0"
```

**Token Type:** Permanent Page Token (never expires)

---

## Data Sources

| Data | Source | How to Update |
|------|--------|---------------|
| Reactions, Comments, Shares | Facebook Graph API | `REFRESH_DATA.bat` |
| Reaction Breakdown (Like/Love/Haha/Wow/Sad/Angry) | Facebook Graph API | `REFRESH_DATA.bat` |
| Video Views | Facebook Graph API (`/videos` endpoint) | `REFRESH_DATA.bat` |
| Page Followers, Rating | Facebook Graph API | `REFRESH_DATA.bat` |
| Post Reach, Post Views | CSV from Meta Business Suite | `MERGE_CSV.bat` |

**Note:** Reach and Post Views require manual CSV export from Meta Business Suite because Facebook API doesn't provide post-level reach without special approval.

---

## Project Structure

```
juan365_engagement_project/
├── streamlit_app.py              # Main dashboard (Streamlit)
├── api_fetcher.py                # Fetches posts, videos, page info from API
├── fetch_historical_reactions.py # Fetches Like/Love/Haha/Wow/Sad/Angry breakdown
├── refresh_api_cache.py          # Combines API data into all_api_data.json
├── merge_exports.py              # Merges multiple CSV files into one
├── config.py                     # API credentials (PAGE_ID, PAGE_TOKEN)
│
├── REFRESH_DATA.bat              # One-click: Fetch API data
├── MERGE_CSV.bat                 # One-click: Merge CSV files
│
├── api_cache/                    # Cached API data
│   ├── posts.json                # Recent posts with engagement
│   ├── videos.json               # Video/reel views
│   ├── stories.json              # Stories data
│   ├── page_info.json            # Followers, rating
│   ├── posts_reactions_full.json # Historical reaction breakdown (801+ posts)
│   └── all_api_data.json         # Combined data for dashboard
│
├── exports/                      # CSV exports from Meta Business Suite
│   ├── Jun-01-2025_Aug-31-2025_xxx.csv
│   ├── Sep-01-2025_Sep-30-2025_xxx.csv
│   ├── Oct-01-2025_Oct-31-2025_xxx.csv
│   ├── Nov-01-2025_Dec-03-2025_xxx.csv
│   └── Juan365_MERGED_ALL.csv    # Auto-generated merged file
│
├── assets/
│   └── juan365_logo.jpg          # Page logo
│
├── requirements.txt              # Python dependencies
├── HOW_TO_UPDATE_REPORT.md       # User instructions
└── PROJECT_CONTEXT.md            # This file
```

---

## Dashboard Features

### KPI Cards (Top Row)
- Total Posts
- Total Reactions
- Total Comments
- Total Shares
- Video Views
- Avg Engagement Rate

### Page Overview Section
- Followers count with growth indicator
- Page rating (stars)
- Weekly active engagers

### Filters (Sidebar)
- **Time Period:** All Time, Yesterday, Last 7/14/30/60/90 Days, Custom
- **Post Type:** All, Photos, Videos, Reels, Live, Text

### Charts & Tables
1. **Reaction Breakdown** - Pie chart (Like/Love/Haha/Wow/Sad/Angry)
2. **Daily Reaction Trend** - Line chart with all 6 reaction types
3. **Daily Engagement Trend** - Reactions, Comments, Shares over time
4. **Post Type Performance** - Bar chart by content type
5. **Top Performing Posts** - Table with thumbnails and metrics
6. **All Posts Table** - Searchable/sortable data table

---

## Key Technical Details

### Data Loading Priority
1. **Primary:** CSV data (has Reach, Views)
2. **Fallback:** API data (if no CSV)
3. **Merge:** Reaction breakdown from API merged into CSV data

### Reaction Breakdown
- Filters by **time period only** (not post type)
- Shows all 6 reactions: Like, Love, Haha, Wow, Sad, Angry
- Data stored in `api_cache/posts_reactions_full.json`

### Time Period Filter
- Options: All Time, Yesterday, Last 7/14/30/60/90 Days, Custom
- "Today" was removed (not useful for reporting)

---

## Update Workflow

### Daily Update (API Data)
```batch
Double-click REFRESH_DATA.bat
```
Or manually:
```
python api_fetcher.py
python refresh_api_cache.py
python fetch_historical_reactions.py
```

### Monthly Update (CSV for Reach/Views)
1. Export from https://business.facebook.com/latest/insights/content
2. Save CSV to `exports/` folder
3. Double-click `MERGE_CSV.bat`

### Deploy to Streamlit Cloud
```
git add .
git commit -m "Update data"
git push
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "No module named 'requests'" | `pip install requests` |
| Rate limit exceeded | Wait 1 hour, try again |
| Token expired | Token is permanent, check config.py |
| Data not updating on cloud | Run `git push` after updating |
| Streamlit not running | `python -m streamlit run streamlit_app.py` |

---

## API Endpoints Used

```python
# Page info
GET /{page_id}?fields=name,fan_count,followers_count,talking_about_count,overall_star_rating,rating_count

# Posts with engagement
GET /{page_id}/posts?fields=id,message,created_time,shares,reactions.summary(true),comments.summary(true),full_picture,permalink_url,status_type

# Reaction breakdown per post
GET /{post_id}?fields=reactions.type(LIKE).summary(true).limit(0).as(like),reactions.type(LOVE).summary(true).limit(0).as(love),...

# Video views
GET /{page_id}/videos?fields=id,description,created_time,views,length,permalink_url
```

---

## Recent Changes (December 2025)

1. **Added historical reaction breakdown** - 801 posts from June-Dec 2025
2. **Daily Reaction Trend chart** - Line chart with all 6 reaction types
3. **Reaction Breakdown filters** - Time period only (not post type)
4. **Removed "Today"** from time period filter
5. **Created batch files** - REFRESH_DATA.bat, MERGE_CSV.bat
6. **Documentation** - HOW_TO_UPDATE_REPORT.md, PROJECT_CONTEXT.md

---

## For Similar Projects (Other Facebook Pages)

To create a similar dashboard for another Facebook page:

1. **Copy this project folder**
2. **Update config.py** with new Page ID and Page Token
3. **Clear api_cache/** folder
4. **Clear exports/** folder
5. **Update logo** in assets/
6. **Run REFRESH_DATA.bat** to fetch new page data
7. **Update GitHub repo** (create new repo or rename)
8. **Deploy to Streamlit Cloud** with new repo

---

## Contact / Notes

- Project created: December 2025
- Framework: Streamlit + Plotly
- Data: Facebook Graph API v21.0
- Python: 3.x with pandas, plotly, requests
