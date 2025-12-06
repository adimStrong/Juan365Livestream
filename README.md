# Juan365 Social Media Dashboard

Professional social media analytics dashboard for Facebook pages. Features both **Streamlit Dashboard** (interactive) and **HTML Reports** (static).

## Features

### Streamlit Dashboard (Primary)
- **Page Overview** - Followers, rating, talking about count
- **KPI Cards** - Posts, engagement, reactions, comments, shares, views, reach
- **Reaction Breakdown** - Like, Love, Haha, Wow, Sad, Angry distribution with date range
- **Post Type Analysis** - Performance by Photo, Video, Reel, Live, Text
- **Daily/Monthly Trends** - Interactive charts with Views and Reach
- **Best Posting Times** - Day and time slot analysis
- **Top Posts** - Highest performing content
- **Video Performance** - Views tracking for all videos/reels

### Data Sources
- **CSV Export** (Primary) - Complete data with Views, Reach, Impressions from Meta Business Suite
- **Facebook API** (Secondary) - Page info, reaction breakdown, video views

---

## Quick Start

### First Time Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/adimStrong/Juan365-Socmed-Mainpage.git
   cd Juan365-Socmed-Mainpage
   ```

2. **Install dependencies**
   ```bash
   pip install pandas streamlit plotly requests jinja2
   ```

3. **Run SETUP.bat** (Windows)
   - Creates `config.py` from template
   - Creates required directories
   - Opens config file for editing

4. **Edit config.py** with your Facebook credentials:
   ```python
   PAGE_ID = "your_page_id_here"
   PAGE_TOKEN = "your_page_access_token_here"
   ```

5. **Get your Facebook credentials:**
   - Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
   - Select your App and Page
   - Generate Page Access Token
   - Get Page ID from your Facebook Page Settings

---

## Daily Usage

### Update Data

1. **Export CSV from Meta Business Suite**
   - Go to https://business.facebook.com/latest/insights/content
   - Click Export → Export table data → CSV
   - Download the file

2. **Run UPDATE_CSV.bat**
   - Select your downloaded CSV file
   - Choose "Replace" or "Merge"

3. **Run REFRESH_DATA.bat**
   - Fetches latest page info and reaction breakdown from API

### View Dashboard

**Option 1: Streamlit Dashboard (Recommended)**
```bash
# Double-click START_STREAMLIT.bat
# Or run:
python -m streamlit run streamlit_app.py
```
Opens at http://localhost:8501

**Option 2: Static HTML Report**
```bash
# Double-click START_REPORT_SERVER.bat
```
Opens at http://localhost:8080

---

## File Structure

```
juan365_engagement_project/
├── config.py                  # Facebook API credentials (NOT in git)
├── config.template.py         # Template for config.py
├── data/                      # API cached data (NOT in git)
├── exports/                   # CSV exports (NOT in git)
│   └── Juan365_MERGED_ALL.csv
│
├── streamlit_app.py           # Main Streamlit dashboard
├── api_fetcher.py             # Facebook Graph API fetcher
├── UPDATE_CSV.py              # GUI tool for CSV updates
│
├── SETUP.bat                  # First-time setup
├── START_STREAMLIT.bat        # Launch Streamlit dashboard
├── REFRESH_DATA.bat           # Fetch API data
├── UPDATE_CSV.bat             # Update CSV data
│
├── reports/                   # Static HTML report system
│   ├── generate_report.py
│   ├── serve_report.py
│   └── output/
│       └── Juan365_Report_LATEST.html
│
└── assets/                    # Logo and images
```

---

## Batch Files Reference

| File | Purpose |
|------|---------|
| `SETUP.bat` | First-time setup - creates config.py and directories |
| `START_STREAMLIT.bat` | Launch Streamlit dashboard at localhost:8501 |
| `REFRESH_DATA.bat` | Fetch latest data from Facebook API |
| `UPDATE_CSV.bat` | GUI tool to import Meta Business Suite CSV exports |
| `START_REPORT_SERVER.bat` | Launch static HTML report at localhost:8080 |
| `UPDATE_REPORT.bat` | Generate new HTML report from CSV |

---

## API Data vs CSV Data

| Metric | CSV (Meta Export) | API |
|--------|-------------------|-----|
| Views | ✅ All posts | ❌ |
| Reach | ✅ All posts | ❌ |
| Impressions | ✅ All posts | ❌ |
| Reactions | ✅ All posts | ✅ Last 100 |
| Reaction Breakdown | ❌ | ✅ Last 100 |
| Comments | ✅ All posts | ✅ Last 100 |
| Shares | ✅ All posts | ✅ Last 100 |
| Followers | ❌ | ✅ Current |
| Page Rating | ❌ | ✅ Current |
| Video Views | ❌ | ✅ All videos |

**Recommendation:** Use both! CSV for complete historical data, API for reaction breakdown and page metrics.

---

## Requirements

- Python 3.8+
- pandas
- streamlit
- plotly
- requests
- jinja2

```bash
pip install -r requirements.txt
```

---

## Security Notes

The following files contain sensitive data and are excluded from git:
- `config.py` - Facebook API token (use `config.template.py` as reference)
- `data/` - Cached API responses
- `exports/` - CSV data files

**Never commit your API tokens to git!**

---

## Troubleshooting

### Dashboard shows no data
1. Make sure you've imported CSV data via UPDATE_CSV.bat
2. Or run REFRESH_DATA.bat to fetch API data

### API errors
1. Check your PAGE_TOKEN in config.py
2. Token may have expired - regenerate from Graph API Explorer
3. Make sure your app has the required permissions

### Streamlit not starting
1. Make sure port 8501 is not in use
2. Try: `python -m streamlit run streamlit_app.py --server.port 8502`
