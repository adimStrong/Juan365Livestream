"""
Juan365 Live Stream Dashboard - Streamlit App
Professional analytics dashboard powered by Facebook Graph API
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import base64
import json
import requests

# Try to load config - supports both local config.py and Streamlit secrets
def get_credentials():
    """Get API credentials from config.py or Streamlit secrets"""
    try:
        from config import PAGE_ID, PAGE_TOKEN, BASE_URL
        return PAGE_ID, PAGE_TOKEN, BASE_URL
    except ImportError:
        # Running on Streamlit Cloud - use secrets
        try:
            page_id = st.secrets["PAGE_ID"]
            page_token = st.secrets["PAGE_TOKEN"]
            base_url = st.secrets.get("BASE_URL", "https://graph.facebook.com/v21.0")
            return page_id, page_token, base_url
        except Exception as e:
            st.warning(f"No credentials found. Please add secrets in Streamlit Cloud settings.")
            return None, None, "https://graph.facebook.com/v21.0"

# These will be set when needed
PAGE_ID, PAGE_TOKEN, BASE_URL = None, None, "https://graph.facebook.com/v21.0"

# Page config
st.set_page_config(
    page_title="Juan365 Live Stream Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load logo as base64 for embedding
def get_logo_base64():
    logo_path = Path(__file__).parent / 'assets' / 'juan365_logo.jpg'
    if logo_path.exists():
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_base64 = get_logo_base64()

# Custom CSS
st.markdown("""
<style>
    .post-type-card {
        background: #F3F4F6;
        padding: 1rem;
        border-radius: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid #E5E7EB;
    }
    .post-type-card h3 { margin: 0; color: #1F2937; }
    .post-type-card p { margin: 0.25rem 0; color: #4B5563; }
    .post-type-card .subtitle { color: #6B7280; }

    .page-overview-card {
        background: linear-gradient(135deg, #4361EE 0%, #8B5CF6 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .page-overview-card h2 { margin: 0; font-size: 2.5rem; }
    .page-overview-card p { margin: 0.5rem 0 0 0; opacity: 0.9; }

    .main-header {
        background: linear-gradient(135deg, #4361EE 0%, #8B5CF6 100%);
        padding: 1.5rem 2rem;
        border-radius: 1rem;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .main-header .logo {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid rgba(255,255,255,0.3);
    }
    .main-header .header-text { text-align: left; }
    .main-header h1 { margin: 0; font-size: 2rem; font-weight: 800; }
    .main-header p { margin: 0.25rem 0 0 0; opacity: 0.9; font-size: 0.9rem; }
    .footer-text { text-align: center; color: #6B7280; padding: 1rem; }

    @media (prefers-color-scheme: dark) {
        .post-type-card {
            background: #262730 !important;
            border-color: #4B5563 !important;
        }
        .post-type-card h3 { color: #F9FAFB !important; }
        .post-type-card p { color: #E5E7EB !important; }
        .post-type-card .subtitle { color: #9CA3AF !important; }
        .footer-text { color: #9CA3AF !important; }
    }
</style>
""", unsafe_allow_html=True)


def get_highlight_color():
    return '#0D9488'


# ===== API FETCH FUNCTIONS (for Streamlit Cloud) =====
# Cache TTL: 3600 seconds = 1 hour
@st.cache_data(ttl=3600)
def fetch_page_info_api():
    """Fetch page-level metrics from Facebook API"""
    page_id, page_token, base_url = get_credentials()
    if not page_id or not page_token:
        return {}

    url = f"{base_url}/{page_id}"
    params = {
        'fields': 'name,fan_count,followers_count,talking_about_count,overall_star_rating,rating_count',
        'access_token': page_token
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if 'error' not in data:
            data['fetched_at'] = datetime.now().isoformat()
            return data
    except Exception:
        pass
    return {}


@st.cache_data(ttl=3600)
def fetch_posts_api(limit=30):
    """Fetch recent posts with engagement and reaction breakdown from Facebook API.
    Note: limit=30 is the max for reaction breakdown due to API data limits.
    """
    page_id, page_token, base_url = get_credentials()
    if not page_id or not page_token:
        return {'posts': [], 'total_posts': 0, 'error': 'No credentials'}

    posts = []
    error_msg = None

    # Fetch posts with reaction breakdown (limit 30 due to API data size limits)
    url = f"{base_url}/{page_id}/posts"
    params = {
        'fields': 'id,message,created_time,shares,permalink_url,status_type,'
                  'reactions.summary(true),comments.summary(true),'
                  'reactions.type(LIKE).summary(true).as(like_count),'
                  'reactions.type(LOVE).summary(true).as(love_count),'
                  'reactions.type(HAHA).summary(true).as(haha_count),'
                  'reactions.type(WOW).summary(true).as(wow_count),'
                  'reactions.type(SAD).summary(true).as(sad_count),'
                  'reactions.type(ANGRY).summary(true).as(angry_count)',
        'limit': min(limit, 30),  # Max 30 for reaction breakdown
        'access_token': page_token
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        data = response.json()

        if 'error' in data:
            error_msg = data['error'].get('message', 'Unknown API error')
        else:
            for post in data.get('data', []):
                processed = {
                    'id': post.get('id'),
                    'message': post.get('message', '')[:200] if post.get('message') else '',
                    'created_time': post.get('created_time'),
                    'permalink_url': post.get('permalink_url'),
                    'post_type': post.get('status_type', 'unknown'),
                    'reactions': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
                    'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0),
                    'shares': post.get('shares', {}).get('count', 0) if post.get('shares') else 0,
                    # Get reaction breakdown directly from the same API call
                    'like': post.get('like_count', {}).get('summary', {}).get('total_count', 0),
                    'love': post.get('love_count', {}).get('summary', {}).get('total_count', 0),
                    'haha': post.get('haha_count', {}).get('summary', {}).get('total_count', 0),
                    'wow': post.get('wow_count', {}).get('summary', {}).get('total_count', 0),
                    'sad': post.get('sad_count', {}).get('summary', {}).get('total_count', 0),
                    'angry': post.get('angry_count', {}).get('summary', {}).get('total_count', 0),
                }
                processed['engagement'] = processed['reactions'] + processed['comments'] + processed['shares']
                posts.append(processed)

    except requests.exceptions.Timeout:
        error_msg = 'API request timed out'
    except requests.exceptions.RequestException as e:
        error_msg = f'Request error: {str(e)}'
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'

    return {
        'fetched_at': datetime.now().isoformat(),
        'total_posts': len(posts),
        'posts': posts,
        'error': error_msg
    }


@st.cache_data(ttl=3600)
def fetch_videos_api(limit=100):
    """Fetch videos with view counts from Facebook API"""
    page_id, page_token, base_url = get_credentials()
    if not page_id or not page_token:
        return {'videos': [], 'total_videos': 0, 'total_views': 0}

    videos = []
    url = f"{base_url}/{page_id}/videos"
    params = {
        'fields': 'id,title,description,created_time,length,views,permalink_url',
        'limit': limit,
        'access_token': page_token
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if 'error' not in data:
            videos = data.get('data', [])
    except Exception:
        pass

    total_views = sum(v.get('views', 0) for v in videos)
    return {
        'fetched_at': datetime.now().isoformat(),
        'total_videos': len(videos),
        'total_views': total_views,
        'videos': videos
    }


def get_cache_key():
    """Get file modification times for cache invalidation."""
    base_dir = Path(__file__).parent
    api_cache_dir = base_dir / 'api_cache'
    posts_file = api_cache_dir / 'posts.json'
    csv_file = base_dir / 'exports' / 'Juan365_MERGED_ALL.csv'
    mtime = 0
    if posts_file.exists():
        mtime = int(posts_file.stat().st_mtime)
    if csv_file.exists():
        mtime = max(mtime, int(csv_file.stat().st_mtime))
    return mtime

@st.cache_data(ttl=3600)
def load_api_data(_cache_key=None):
    """Load data from cached JSON files (committed to git) or fetch from API.

    Priority:
    1. api_cache/ folder (committed to git, works on Streamlit Cloud)
    2. data/ folder (local only, in .gitignore)
    3. Fetch from API directly

    Returns:
    - page_info: Page-level metrics
    - posts_data: Recent 30 posts with reaction breakdown
    - videos_data: Videos with views
    - all_posts_data: All posts from June 2025 (for historical charts)
    """
    base_dir = Path(__file__).parent
    api_cache_dir = base_dir / 'api_cache'  # Committed to git
    data_dir = base_dir / 'data'  # Local only (.gitignore)

    # Load page info - try api_cache first, then data folder
    page_info = {}
    for cache_dir in [api_cache_dir, data_dir]:
        page_info_file = cache_dir / 'page_info.json'
        if page_info_file.exists():
            with open(page_info_file, 'r', encoding='utf-8') as f:
                page_info = json.load(f)
            break

    # Load posts with reactions (historical data from June 2025 for reaction breakdown)
    posts_data = {'posts': [], 'total_posts': 0}
    for cache_dir in [api_cache_dir, data_dir]:
        # Try historical full data first, then fall back to recent 30
        posts_file = cache_dir / 'posts_reactions_full.json'
        if posts_file.exists():
            with open(posts_file, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            break
        # Fallback to posts_with_reactions.json if full data not available
        posts_file = cache_dir / 'posts_with_reactions.json'
        if posts_file.exists():
            with open(posts_file, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            break

    # Load ALL posts (from June 2025 - for historical charts)
    all_posts_data = {'posts': [], 'total_posts': 0}
    for cache_dir in [api_cache_dir, data_dir]:
        all_posts_file = cache_dir / 'posts.json'
        if all_posts_file.exists():
            with open(all_posts_file, 'r', encoding='utf-8') as f:
                all_posts_data = json.load(f)
            break

    # Load videos - try api_cache first, then data folder
    videos_data = {'videos': [], 'total_videos': 0, 'total_views': 0}
    for cache_dir in [api_cache_dir, data_dir]:
        videos_file = cache_dir / 'videos.json'
        if videos_file.exists():
            with open(videos_file, 'r', encoding='utf-8') as f:
                videos_data = json.load(f)
            break

    # Load stories data
    stories_data = {'stories': [], 'total_stories': 0}
    for cache_dir in [api_cache_dir, data_dir]:
        stories_file = cache_dir / 'stories.json'
        if stories_file.exists():
            with open(stories_file, 'r', encoding='utf-8') as f:
                stories_data = json.load(f)
            break

    # Only fetch from API if no cached data found
    page_id, page_token, _ = get_credentials()

    if page_id and page_token:
        # Fetch page info if empty
        if not page_info:
            page_info = fetch_page_info_api()

        # Fetch posts if no posts or no reaction data
        if not posts_data.get('posts'):
            posts_data = fetch_posts_api(limit=30)
        elif not any(p.get('like', 0) > 0 for p in posts_data.get('posts', [])):
            posts_data = fetch_posts_api(limit=30)

        # Fetch videos if empty
        if not videos_data.get('videos'):
            videos_data = fetch_videos_api(limit=100)

    return page_info, posts_data, videos_data, all_posts_data, stories_data


@st.cache_data(ttl=3600)
def load_csv_data(_cache_key=None):
    """Load data from CSV exports (fallback)"""
    exports_dir = Path(__file__).parent / 'exports'

    merged_file = exports_dir / 'Juan365_MERGED_ALL.csv'
    if merged_file.exists():
        csv_path = merged_file
    else:
        csv_files = list(exports_dir.glob('*.csv'))
        if not csv_files:
            return None
        csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        csv_path = csv_files[0]

    df = pd.read_csv(csv_path)

    # Filter to only Juan365 Live Stream page (ID: 61569634500241)
    if 'Page ID' in df.columns:
        df['Page ID'] = df['Page ID'].astype(str)
        df = df[df['Page ID'] == '61569634500241']

    column_mapping = {
        'Post ID': 'post_id', 'Title': 'message', 'Publish time': 'publish_time',
        'Post type': 'post_type', 'Permalink': 'permalink',
        'Reactions': 'reactions', 'Comments': 'comments', 'Shares': 'shares',
        'Views': 'views', 'Reach': 'reach'
    }
    df = df.rename(columns=column_mapping)

    df['publish_datetime'] = pd.to_datetime(df['publish_time'], format='%m/%d/%Y %H:%M', errors='coerce')
    df['publish_datetime'] = df['publish_datetime'] + pd.Timedelta(hours=16)
    df['date'] = df['publish_datetime'].dt.date
    df['hour'] = df['publish_datetime'].dt.hour

    for col in ['reactions', 'comments', 'shares', 'views', 'reach']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df['engagement'] = df['reactions'] + df['comments'] + df['shares']

    # Add Total Clicks if available
    if 'Total clicks' in df.columns:
        df['total_clicks'] = pd.to_numeric(df['Total clicks'], errors='coerce').fillna(0).astype(int)

    # Clean post type for filtering
    if 'post_type' in df.columns:
        df['post_type_clean'] = df['post_type'].fillna('Unknown').str.strip()
    else:
        df['post_type_clean'] = 'Unknown'

    # Add month column for grouping
    df['month'] = df['publish_datetime'].dt.to_period('M').astype(str)

    # Add day_of_week for best posting time analysis
    df['day_of_week'] = df['publish_datetime'].dt.day_name()

    # Add time_slot for hourly analysis
    def get_time_slot(hour):
        if 6 <= hour < 12:
            return 'Morning (6AM-12PM)'
        elif 12 <= hour < 18:
            return 'Afternoon (12PM-6PM)'
        elif 18 <= hour < 22:
            return 'Evening (6PM-10PM)'
        else:
            return 'Night (10PM-6AM)'
    df['time_slot'] = df['hour'].apply(get_time_slot)

    return df


def prepare_posts_dataframe(posts_data):
    """Convert API posts data to DataFrame"""
    posts = posts_data.get('posts', [])
    if not posts:
        return None

    df = pd.DataFrame(posts)

    # Parse datetime (API returns UTC)
    df['publish_datetime'] = pd.to_datetime(df['created_time'], errors='coerce')
    df['publish_datetime'] = df['publish_datetime'] + pd.Timedelta(hours=8)  # Convert to PHT
    df['date'] = df['publish_datetime'].dt.date
    df['hour'] = df['publish_datetime'].dt.hour
    df['day_of_week'] = df['publish_datetime'].dt.day_name()
    df['month'] = df['publish_datetime'].dt.to_period('M').astype(str)

    # Time slots
    def get_time_slot(hour):
        if 6 <= hour < 12: return 'Morning (6AM-12PM)'
        elif 12 <= hour < 18: return 'Afternoon (12PM-6PM)'
        elif 18 <= hour < 22: return 'Evening (6PM-10PM)'
        else: return 'Night (10PM-6AM)'

    df['time_slot'] = df['hour'].apply(get_time_slot)

    # Clean post types - detect from permalink_url if status_type not available
    type_mapping = {
        'added_photos': 'Photos',
        'added_video': 'Videos',
        'mobile_status_update': 'Text',
        'shared_story': 'Shared',
        'created_event': 'Event',
        'unknown': 'Other'
    }
    if 'status_type' in df.columns:
        df['post_type_clean'] = df['status_type'].map(type_mapping).fillna('Other')
    elif 'post_type' in df.columns:
        # Map singular to plural for consistency
        post_type_mapping = {
            'Photo': 'Photos',
            'Video': 'Videos',
            'Reel': 'Reels',
            'Text': 'Text',
            'Shared': 'Shared',
            'Unknown': 'Other'
        }
        df['post_type_clean'] = df['post_type'].map(post_type_mapping).fillna(df['post_type'])
    else:
        # Detect post type from permalink_url
        def detect_post_type(row):
            url = str(row.get('permalink_url', '') or row.get('permalink', ''))
            if '/videos/' in url or '/reel/' in url:
                return 'Videos'
            elif '/photos/' in url:
                return 'Photos'
            else:
                return 'Posts'  # Default to Posts for all content
        df['post_type_clean'] = df.apply(detect_post_type, axis=1)

    # Add post_id column if not present (for compatibility)
    if 'post_id' not in df.columns and 'id' in df.columns:
        df['post_id'] = df['id']

    # Add permalink column if not present (API uses permalink_url)
    if 'permalink' not in df.columns and 'permalink_url' in df.columns:
        df['permalink'] = df['permalink_url']

    # Calculate accurate reactions from breakdown (like, love, haha, wow, sad, angry)
    reaction_cols = ['like', 'love', 'haha', 'wow', 'sad', 'angry']
    for col in reaction_cols:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = df[col].fillna(0).astype(int)

    # Calculate total reactions from breakdown (more accurate than stored 'reactions' field)
    df['reactions'] = df[reaction_cols].sum(axis=1)

    # Ensure comments and shares columns exist and are integers
    if 'comments' not in df.columns:
        df['comments'] = 0
    else:
        df['comments'] = df['comments'].fillna(0).astype(int)

    if 'shares' not in df.columns:
        df['shares'] = 0
    else:
        df['shares'] = df['shares'].fillna(0).astype(int)

    # Calculate total engagement
    df['engagement'] = df['reactions'] + df['comments'] + df['shares']

    # Add content_category for 4-type classification (Photos, Livestreams, Reels, Videos)
    def categorize_content(row):
        msg = str(row.get('message', '') or '').lower()
        ptype = row.get('post_type', '')

        if ptype in ['Video', 'Reel'] and 'live' in msg:
            return 'Livestreams'
        elif ptype == 'Reel':
            return 'Reels'
        elif ptype == 'Video':
            return 'Videos'
        elif ptype == 'Photo':
            return 'Photos'
        else:
            return 'Other'

    df['content_category'] = df.apply(categorize_content, axis=1)

    return df


def format_number(num):
    """Format numbers with commas"""
    return f"{int(num):,}"


def main():
    # Load API data (for page-level info: followers, rating, video views, reaction breakdown)
    # Pass cache_key to invalidate cache when files change
    page_info, posts_data, videos_data, all_posts_data, stories_data = load_api_data(_cache_key=get_cache_key())

    # PRIMARY: Use API data for posts (most complete, real-time engagement data)
    # API has 552 posts with reactions, comments, shares breakdown
    if all_posts_data.get('posts'):
        df = prepare_posts_dataframe(all_posts_data)
    else:
        df = prepare_posts_dataframe(posts_data)

    # SECONDARY: Load CSV only for Reach and Views (Meta Business Suite has these)
    # Pass cache_key to invalidate cache when CSV changes
    csv_df = load_csv_data(_cache_key=get_cache_key())

    # Merge Reach and Views from CSV into API data
    if csv_df is not None and not csv_df.empty:
        # Create mapping of post_id to reach/views from CSV
        csv_metrics = {}
        for idx, row in csv_df.iterrows():
            csv_post_id = str(row.get('post_id', ''))
            csv_metrics[csv_post_id] = {
                'reach': row.get('reach', 0),
                'views': row.get('views', 0)
            }

        # Add reach/views columns to df if not present
        if 'reach' not in df.columns:
            df['reach'] = 0
        if 'views' not in df.columns:
            df['views'] = 0

        # Match and merge reach/views from CSV into API data
        for idx, row in df.iterrows():
            api_post_id = str(row.get('post_id', ''))
            # Try both full ID and short ID
            short_id = api_post_id.split('_')[-1] if '_' in api_post_id else api_post_id

            if api_post_id in csv_metrics:
                df.at[idx, 'reach'] = csv_metrics[api_post_id].get('reach', 0)
                df.at[idx, 'views'] = csv_metrics[api_post_id].get('views', 0)
            elif short_id in csv_metrics:
                df.at[idx, 'reach'] = csv_metrics[short_id].get('reach', 0)
                df.at[idx, 'views'] = csv_metrics[short_id].get('views', 0)

    # Header
    if logo_base64:
        st.markdown(f"""
        <div class="main-header">
            <img src="data:image/jpeg;base64,{logo_base64}" class="logo" alt="Juan365 Live Stream Logo">
            <div class="header-text">
                <h1>Juan365 Live Stream Dashboard</h1>
                <p>Social Media Performance Analytics (API Powered)</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="main-header">
            <div class="header-text">
                <h1>📊 Juan365 Live Stream Dashboard</h1>
                <p>Social Media Performance Analytics</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ===== PAGE OVERVIEW SECTION =====
    st.markdown("### 🏠 Page Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        followers = page_info.get('fan_count', 0)
        st.markdown(f'''<div class="page-overview-card">
            <h2>{format_number(followers)}</h2>
            <p>👥 Followers</p>
        </div>''', unsafe_allow_html=True)

    with col2:
        rating = page_info.get('overall_star_rating', 0)
        rating_count = page_info.get('rating_count', 0)
        st.markdown(f'''<div class="page-overview-card">
            <h2>{rating}/5 ⭐</h2>
            <p>📊 Rating ({rating_count:,} reviews)</p>
        </div>''', unsafe_allow_html=True)

    with col3:
        talking_about = page_info.get('talking_about_count', 0)
        st.markdown(f'''<div class="page-overview-card">
            <h2>{format_number(talking_about)}</h2>
            <p>🔥 Talking About (Weekly)</p>
        </div>''', unsafe_allow_html=True)

    with col4:
        total_video_views = videos_data.get('total_views', 0)
        st.markdown(f'''<div class="page-overview-card">
            <h2>{format_number(total_video_views)}</h2>
            <p>🎬 Total Video Views</p>
        </div>''', unsafe_allow_html=True)

    st.markdown("---")

    # Check if we have data
    if df is None or df.empty:
        st.warning("No data available. Please run fetch_all_api_data.py to fetch data from Facebook API.")
        return

    # Show data source info
    data_source = "API Cache" if all_posts_data.get('posts') else "CSV"
    st.sidebar.success(f"📊 Loaded {len(df):,} posts from {data_source}")

    # Sidebar filters
    st.sidebar.markdown("## 🎛️ Filters")

    today = datetime.now().date()
    min_date = df['date'].min()
    max_date = df['date'].max()

    time_periods = {
        'All Time': (min_date, max_date),
        'Yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
        'Last 7 Days': (today - timedelta(days=7), today),
        'Last 14 Days': (today - timedelta(days=14), today),
        'Last 30 Days': (today - timedelta(days=30), today),
        'Last 60 Days': (today - timedelta(days=60), today),
        'Last 90 Days': (today - timedelta(days=90), today),
        'Custom': None
    }

    selected_period = st.sidebar.selectbox("📅 Time Period", list(time_periods.keys()))

    if selected_period == 'Custom':
        date_range = st.sidebar.date_input("Custom Date Range", value=(min_date, max_date))
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
    else:
        start_date, end_date = time_periods[selected_period]
        start_date = max(start_date, min_date)
        end_date = min(end_date, max_date)

    # Post type filter
    post_types = ['All'] + sorted(df['post_type_clean'].unique().tolist())
    selected_type = st.sidebar.selectbox("Post Type", post_types)

    # Apply filters
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['post_type_clean'] == selected_type]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Showing:** {len(filtered_df):,} posts")
    st.sidebar.markdown(f"**Period:** {start_date} to {end_date}")

    # Data last updated
    fetched_at = all_posts_data.get('fetched_at') or posts_data.get('fetched_at', 'Unknown')
    if fetched_at != 'Unknown':
        try:
            # Try ISO format first
            fetched_dt = datetime.fromisoformat(fetched_at)
        except ValueError:
            try:
                # Try HTTP header format: "Tue, 09 Dec 2025 04:58:09 GMT"
                from email.utils import parsedate_to_datetime
                fetched_dt = parsedate_to_datetime(fetched_at)
            except:
                fetched_dt = None
        if fetched_dt:
            st.sidebar.markdown(f"**Updated:** {fetched_dt.strftime('%Y-%m-%d %H:%M')}")

    # Show date range if available
    date_range = all_posts_data.get('date_range', {})
    if date_range:
        st.sidebar.markdown(f"**Data Range:** {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}")

    # ===== MAIN KPIs =====
    st.markdown("### 📈 Performance Metrics")

    total_posts = len(filtered_df)
    total_engagement = filtered_df['engagement'].sum()
    total_reactions = filtered_df['reactions'].sum()
    total_comments = filtered_df['comments'].sum()
    total_shares = filtered_df['shares'].sum()
    avg_engagement = filtered_df['engagement'].mean() if total_posts > 0 else 0

    # Get Views and Reach from CSV if available
    total_views = filtered_df['views'].sum() if 'views' in filtered_df.columns else 0
    total_reach = filtered_df['reach'].sum() if 'reach' in filtered_df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''<div class="post-type-card">
            <p class="subtitle">📊 Total Posts</p>
            <h3>{total_posts:,}</h3>
        </div>''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''<div class="post-type-card">
            <p class="subtitle">👁️ Total Views</p>
            <h3>{format_number(total_views)}</h3>
        </div>''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''<div class="post-type-card">
            <p class="subtitle">📣 Total Reach</p>
            <h3>{format_number(total_reach)}</h3>
        </div>''', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''<div class="post-type-card">
            <p class="subtitle">💬 Total Engagement</p>
            <h3>{format_number(total_engagement)}</h3>
        </div>''', unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.markdown(f'''<div class="post-type-card">
            <p class="subtitle">❤️ Total Reactions</p>
            <h3>{format_number(total_reactions)}</h3>
        </div>''', unsafe_allow_html=True)
    with col6:
        st.markdown(f'''<div class="post-type-card">
            <p class="subtitle">💭 Total Comments</p>
            <h3>{format_number(total_comments)}</h3>
        </div>''', unsafe_allow_html=True)
    with col7:
        st.markdown(f'''<div class="post-type-card">
            <p class="subtitle">🔄 Total Shares</p>
            <h3>{format_number(total_shares)}</h3>
        </div>''', unsafe_allow_html=True)
    with col8:
        st.markdown(f'''<div class="post-type-card">
            <p class="subtitle">📈 Avg Engagement</p>
            <h3>{format_number(avg_engagement)}</h3>
        </div>''', unsafe_allow_html=True)

    st.markdown("---")

    # ===== REACTION BREAKDOWN (from API data) =====
    # Get reaction data directly from API posts (more reliable than CSV merge)
    api_posts = posts_data.get('posts', [])

    # Show API error if any
    if posts_data.get('error'):
        st.error(f"⚠️ API Error: {posts_data.get('error')}")

    # Calculate totals from API posts
    total_like = sum(p.get('like', 0) for p in api_posts)
    total_love = sum(p.get('love', 0) for p in api_posts)
    total_haha = sum(p.get('haha', 0) for p in api_posts)
    total_wow = sum(p.get('wow', 0) for p in api_posts)
    total_sad = sum(p.get('sad', 0) for p in api_posts)
    total_angry = sum(p.get('angry', 0) for p in api_posts)
    total_all_reactions = total_like + total_love + total_haha + total_wow + total_sad + total_angry

    # Debug: Show API fetch status
    st.sidebar.markdown("---")
    st.sidebar.markdown("**API Status:**")
    st.sidebar.markdown(f"Posts from API: {len(api_posts)}")
    st.sidebar.markdown(f"Total reactions: {total_all_reactions:,}")

    if total_all_reactions > 0:
        st.markdown("### 😊 Reaction Breakdown")

        # Create DataFrame from API posts for filtering
        reaction_posts_df = pd.DataFrame(api_posts)
        if 'created_time' in reaction_posts_df.columns:
            reaction_posts_df['date'] = pd.to_datetime(reaction_posts_df['created_time']).dt.date
        elif 'date' in reaction_posts_df.columns:
            reaction_posts_df['date'] = pd.to_datetime(reaction_posts_df['date']).dt.date

        # Apply only time period filter (not post type) for reaction breakdown
        filtered_reaction_df = reaction_posts_df[
            (reaction_posts_df['date'] >= start_date) &
            (reaction_posts_df['date'] <= end_date)
        ]

        # Calculate filtered totals
        filtered_like = filtered_reaction_df['like'].sum() if 'like' in filtered_reaction_df.columns else 0
        filtered_love = filtered_reaction_df['love'].sum() if 'love' in filtered_reaction_df.columns else 0
        filtered_haha = filtered_reaction_df['haha'].sum() if 'haha' in filtered_reaction_df.columns else 0
        filtered_wow = filtered_reaction_df['wow'].sum() if 'wow' in filtered_reaction_df.columns else 0
        filtered_sad = filtered_reaction_df['sad'].sum() if 'sad' in filtered_reaction_df.columns else 0
        filtered_angry = filtered_reaction_df['angry'].sum() if 'angry' in filtered_reaction_df.columns else 0
        filtered_total = filtered_like + filtered_love + filtered_haha + filtered_wow + filtered_sad + filtered_angry

        # Show filter info (time period only, all post types)
        filter_info = f"📊 **{len(filtered_reaction_df):,}** posts (All Types) from **{start_date}** to **{end_date}**"
        st.markdown(filter_info)

        col1, col2 = st.columns(2)

        with col1:
            # Reaction counts pie chart
            reaction_df = pd.DataFrame({
                'Reaction': ['👍 Like', '❤️ Love', '😆 Haha', '😮 Wow', '😢 Sad', '😠 Angry'],
                'Count': [filtered_like, filtered_love, filtered_haha, filtered_wow, filtered_sad, filtered_angry]
            })

            fig = px.pie(
                reaction_df,
                values='Count',
                names='Reaction',
                title=f'Reaction Distribution (Total: {format_number(filtered_total)})',
                color_discrete_sequence=['#4267B2', '#F02849', '#F7B928', '#F7B928', '#F7B928', '#E9573F'],
                hole=0.4
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Daily Reaction Trend chart
            if len(filtered_reaction_df) > 0:
                daily_reactions = filtered_reaction_df.groupby('date').agg({
                    'like': 'sum',
                    'love': 'sum',
                    'haha': 'sum',
                    'wow': 'sum',
                    'sad': 'sum',
                    'angry': 'sum'
                }).reset_index()
                daily_reactions['date'] = pd.to_datetime(daily_reactions['date'])
                daily_reactions = daily_reactions.sort_values('date')

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=daily_reactions['date'], y=daily_reactions['like'],
                    name='👍 Like', mode='lines', line=dict(width=2, color='#4267B2'),
                    hovertemplate='%{y:,}<extra></extra>'))
                fig.add_trace(go.Scatter(x=daily_reactions['date'], y=daily_reactions['love'],
                    name='❤️ Love', mode='lines', line=dict(width=2, color='#F02849'),
                    hovertemplate='%{y:,}<extra></extra>'))
                fig.add_trace(go.Scatter(x=daily_reactions['date'], y=daily_reactions['haha'],
                    name='😆 Haha', mode='lines', line=dict(width=1.5, color='#F7B928'),
                    hovertemplate='%{y:,}<extra></extra>'))
                fig.add_trace(go.Scatter(x=daily_reactions['date'], y=daily_reactions['wow'],
                    name='😮 Wow', mode='lines', line=dict(width=1.5, color='#8B5CF6'),
                    hovertemplate='%{y:,}<extra></extra>'))
                fig.add_trace(go.Scatter(x=daily_reactions['date'], y=daily_reactions['sad'],
                    name='😢 Sad', mode='lines', line=dict(width=1.5, color='#6B7280'),
                    hovertemplate='%{y:,}<extra></extra>'))
                fig.add_trace(go.Scatter(x=daily_reactions['date'], y=daily_reactions['angry'],
                    name='😠 Angry', mode='lines', line=dict(width=1.5, color='#E9573F'),
                    hovertemplate='%{y:,}<extra></extra>'))

                fig.update_layout(
                    title='Daily Reaction Trend',
                    xaxis_title='Date',
                    yaxis_title='Reactions',
                    height=400,
                    hovermode='x unified',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No reaction data for selected period")
        st.markdown("---")

    # Note: Reaction breakdown is only available when API data is loaded

    # Content Distribution and Growth Rate Charts
    st.markdown("### 🎯 Content Distribution & Growth")

    col1, col2 = st.columns(2)

    with col1:
        # Content Distribution Pie Chart
        type_counts = filtered_df['post_type_clean'].value_counts().reset_index()
        type_counts.columns = ['Post Type', 'Count']

        fig = px.pie(
            type_counts,
            values='Count',
            names='Post Type',
            title='Posts by Type',
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Growth Rate by Engagement (Weekly with ISO week numbers)
        filtered_df_copy = filtered_df.copy()
        filtered_df_copy['date_dt'] = pd.to_datetime(filtered_df_copy['date'])
        filtered_df_copy['iso_year'] = filtered_df_copy['date_dt'].dt.isocalendar().year
        filtered_df_copy['iso_week'] = filtered_df_copy['date_dt'].dt.isocalendar().week
        filtered_df_copy['week_key'] = filtered_df_copy['iso_year'].astype(str) + '-W' + filtered_df_copy['iso_week'].astype(str).str.zfill(2)

        weekly_engagement = filtered_df_copy.groupby('week_key').agg({
            'engagement': 'sum',
            'reactions': 'sum',
            'comments': 'sum',
            'shares': 'sum',
            'date_dt': ['min', 'max']
        }).reset_index()
        weekly_engagement.columns = ['week_key', 'engagement', 'reactions', 'comments', 'shares', 'week_start', 'week_end']

        # Sort by week_key to ensure proper order
        weekly_engagement = weekly_engagement.sort_values('week_key')

        # Calculate week-over-week growth rate
        if len(weekly_engagement) > 1:
            weekly_engagement['growth_rate'] = weekly_engagement['engagement'].pct_change() * 100
            weekly_engagement['growth_rate'] = weekly_engagement['growth_rate'].fillna(0)

            # Create ISO week labels for x-axis (e.g., "W23", "W24")
            weekly_engagement['iso_week_label'] = weekly_engagement['week_key'].str.split('-W').str[1].astype(int).apply(lambda x: f"W{x}")

            # Create date range for tooltip
            weekly_engagement['date_range'] = weekly_engagement.apply(
                lambda row: f"{row['week_start'].strftime('%b %d')} - {row['week_end'].strftime('%b %d, %Y')}", axis=1
            )

            # Create bar chart with color based on positive/negative growth
            colors = ['#10B981' if x >= 0 else '#EF4444' for x in weekly_engagement['growth_rate']]

            # Pre-format growth rate for tooltip
            weekly_engagement['growth_formatted'] = weekly_engagement['growth_rate'].apply(lambda x: f"{x:+.1f}%")

            fig_growth = go.Figure()
            fig_growth.add_trace(go.Bar(
                x=weekly_engagement['iso_week_label'],
                y=weekly_engagement['growth_rate'],
                marker_color=colors,
                name='Growth Rate',
                text=[f"{x:+.1f}%" for x in weekly_engagement['growth_rate']],
                textposition='outside',
                customdata=weekly_engagement[['week_key', 'date_range', 'engagement', 'growth_formatted']].values,
                hovertemplate='<b>%{customdata[0]}</b><br>' +
                              '%{customdata[1]}<br>' +
                              'Growth: %{customdata[3]}<br>' +
                              'Engagement: %{customdata[2]:,}<extra></extra>'
            ))

            # Add a reference line at 0
            fig_growth.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

            fig_growth.update_layout(
                title='Weekly Engagement Growth Rate',
                xaxis_title='ISO Week',
                yaxis_title='Growth Rate (%)',
                height=400,
                showlegend=False,
                hovermode='closest'
            )
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("Not enough data to calculate growth rate. Need at least 2 weeks of data.")

    st.markdown("---")

    # ===== DAILY CONTENT PERFORMANCE (4 Charts with Engagement Breakdown) =====
    st.markdown("### 📊 Daily Content Performance")

    # Prepare daily data with engagement breakdown and post count
    daily_all = filtered_df.groupby('date').agg({
        'reactions': 'sum',
        'comments': 'sum',
        'shares': 'sum',
        'post_id': 'count'  # Count posts per day
    }).reset_index()
    daily_all.rename(columns={'post_id': 'post_count'}, inplace=True)

    # All Videos (for reference)
    all_videos_df = filtered_df[filtered_df['post_type_clean'].isin(['Videos', 'Reels'])]

    # Livestreams - videos with "live" in message
    is_livestream = all_videos_df['message'].fillna('').str.lower().str.contains('live')
    livestream_df = all_videos_df[is_livestream]
    daily_livestream = livestream_df.groupby('date').agg({
        'reactions': 'sum',
        'comments': 'sum',
        'shares': 'sum',
        'post_id': 'count'
    }).reset_index() if not livestream_df.empty else pd.DataFrame({'date': [], 'reactions': [], 'comments': [], 'shares': [], 'post_count': []})
    if not daily_livestream.empty:
        daily_livestream.rename(columns={'post_id': 'post_count'}, inplace=True)

    # Other Videos - videos without "live" in message (reels, regular videos)
    other_videos_df = all_videos_df[~is_livestream]
    daily_other_videos = other_videos_df.groupby('date').agg({
        'reactions': 'sum',
        'comments': 'sum',
        'shares': 'sum',
        'post_id': 'count'
    }).reset_index() if not other_videos_df.empty else pd.DataFrame({'date': [], 'reactions': [], 'comments': [], 'shares': [], 'post_count': []})
    if not daily_other_videos.empty:
        daily_other_videos.rename(columns={'post_id': 'post_count'}, inplace=True)

    # Filter by content type - Photos/Images
    photos_df = filtered_df[filtered_df['post_type_clean'] == 'Photos']
    daily_photos = photos_df.groupby('date').agg({
        'reactions': 'sum',
        'comments': 'sum',
        'shares': 'sum',
        'post_id': 'count'
    }).reset_index() if not photos_df.empty else pd.DataFrame({'date': [], 'reactions': [], 'comments': [], 'shares': [], 'post_count': []})
    if not daily_photos.empty:
        daily_photos.rename(columns={'post_id': 'post_count'}, inplace=True)

    # Create 4 charts in 2x2 grid
    col1, col2 = st.columns(2)

    with col1:
        # Chart 1: Content Overview (All) - Reactions, Comments, Shares with post count
        total_all_posts = len(filtered_df)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=daily_all['date'], y=daily_all['reactions'],
            name='Reactions', mode='lines',
            line=dict(width=2, color='#F02849'),
            customdata=daily_all['post_count'],
            hovertemplate='%{y:,}<extra></extra>'
        ))
        fig1.add_trace(go.Scatter(
            x=daily_all['date'], y=daily_all['comments'],
            name='Comments', mode='lines',
            line=dict(width=2, color='#4361EE'),
            hovertemplate='%{y:,}<extra></extra>'
        ))
        fig1.add_trace(go.Scatter(
            x=daily_all['date'], y=daily_all['shares'],
            name='Shares', mode='lines',
            line=dict(width=2, color='#10B981'),
            hovertemplate='%{y:,}<extra></extra>'
        ))
        # Add invisible trace for post count in tooltip
        fig1.add_trace(go.Scatter(
            x=daily_all['date'], y=[0] * len(daily_all),
            name='Posts', mode='lines',
            line=dict(width=0, color='rgba(0,0,0,0)'),
            customdata=daily_all['post_count'],
            hovertemplate='📊 Posts: %{customdata}<extra></extra>',
            showlegend=False
        ))
        fig1.update_layout(
            title=f'📈 Content Overview ({total_all_posts:,} posts)',
            xaxis_title='Date',
            yaxis_title='Count',
            height=350,
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Chart 2: Photos/Images
        total_photos_count = len(photos_df)
        fig2 = go.Figure()
        if not daily_photos.empty and len(daily_photos) > 0:
            fig2.add_trace(go.Scatter(
                x=daily_photos['date'], y=daily_photos['reactions'],
                name='Reactions', mode='lines',
                line=dict(width=2, color='#F02849'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            fig2.add_trace(go.Scatter(
                x=daily_photos['date'], y=daily_photos['comments'],
                name='Comments', mode='lines',
                line=dict(width=2, color='#4361EE'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            fig2.add_trace(go.Scatter(
                x=daily_photos['date'], y=daily_photos['shares'],
                name='Shares', mode='lines',
                line=dict(width=2, color='#10B981'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            # Add invisible trace for post count in tooltip
            fig2.add_trace(go.Scatter(
                x=daily_photos['date'], y=[0] * len(daily_photos),
                name='Photos', mode='lines',
                line=dict(width=0, color='rgba(0,0,0,0)'),
                customdata=daily_photos['post_count'],
                hovertemplate='Photos: %{customdata}<extra></extra>',
                showlegend=False
            ))
        fig2.update_layout(
            title=f'Photos/Images ({total_photos_count:,})',
            xaxis_title='Date',
            yaxis_title='Count',
            height=350,
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Chart 3: Livestreams (videos with "live" in message)
        total_livestream_count = len(livestream_df)
        fig3 = go.Figure()
        if not daily_livestream.empty and len(daily_livestream) > 0:
            fig3.add_trace(go.Scatter(
                x=daily_livestream['date'], y=daily_livestream['reactions'],
                name='Reactions', mode='lines',
                line=dict(width=2, color='#F02849'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            fig3.add_trace(go.Scatter(
                x=daily_livestream['date'], y=daily_livestream['comments'],
                name='Comments', mode='lines',
                line=dict(width=2, color='#4361EE'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            fig3.add_trace(go.Scatter(
                x=daily_livestream['date'], y=daily_livestream['shares'],
                name='Shares', mode='lines',
                line=dict(width=2, color='#10B981'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            fig3.add_trace(go.Scatter(
                x=daily_livestream['date'], y=[0] * len(daily_livestream),
                name='Livestreams', mode='lines',
                line=dict(width=0, color='rgba(0,0,0,0)'),
                customdata=daily_livestream['post_count'],
                hovertemplate='Livestreams: %{customdata}<extra></extra>',
                showlegend=False
            ))
        fig3.update_layout(
            title=f'Livestreams ({total_livestream_count:,})',
            xaxis_title='Date',
            yaxis_title='Count',
            height=350,
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # Chart 4: Other Videos (non-livestream videos/reels)
        total_other_videos_count = len(other_videos_df)
        fig4 = go.Figure()
        if not daily_other_videos.empty and len(daily_other_videos) > 0:
            fig4.add_trace(go.Scatter(
                x=daily_other_videos['date'], y=daily_other_videos['reactions'],
                name='Reactions', mode='lines',
                line=dict(width=2, color='#F02849'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            fig4.add_trace(go.Scatter(
                x=daily_other_videos['date'], y=daily_other_videos['comments'],
                name='Comments', mode='lines',
                line=dict(width=2, color='#4361EE'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            fig4.add_trace(go.Scatter(
                x=daily_other_videos['date'], y=daily_other_videos['shares'],
                name='Shares', mode='lines',
                line=dict(width=2, color='#10B981'),
                hovertemplate='%{y:,}<extra></extra>'
            ))
            fig4.add_trace(go.Scatter(
                x=daily_other_videos['date'], y=[0] * len(daily_other_videos),
                name='Other Videos', mode='lines',
                line=dict(width=0, color='rgba(0,0,0,0)'),
                customdata=daily_other_videos['post_count'],
                hovertemplate='Other Videos: %{customdata}<extra></extra>',
                showlegend=False
            ))
        fig4.update_layout(
            title=f'Other Videos/Reels ({total_other_videos_count:,})',
            xaxis_title='Date',
            yaxis_title='Count',
            height=350,
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Charts row 2
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📅 Daily Performance Trend")
        agg_dict = {
            'engagement': 'sum',
            'reactions': 'sum',
            'comments': 'sum'
        }
        # Add views and reach if available
        if 'views' in filtered_df.columns:
            agg_dict['views'] = 'sum'
        if 'reach' in filtered_df.columns:
            agg_dict['reach'] = 'sum'

        daily_stats = filtered_df.groupby('date').agg(agg_dict).reset_index()

        fig = go.Figure()
        # Add Views line (primary - most important)
        if 'views' in daily_stats.columns:
            fig.add_trace(go.Scatter(
                x=daily_stats['date'], y=daily_stats['views'],
                name='Views', line=dict(color='#10B981', width=2),
                fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
            ))
        # Add Reach line
        if 'reach' in daily_stats.columns:
            fig.add_trace(go.Scatter(
                x=daily_stats['date'], y=daily_stats['reach'],
                name='Reach', line=dict(color='#F59E0B', width=2)
            ))
        # Add Engagement line
        fig.add_trace(go.Scatter(
            x=daily_stats['date'], y=daily_stats['engagement'],
            name='Engagement', line=dict(color='#4361EE', width=2)
        ))
        fig.update_layout(title='Daily Views, Reach & Engagement', height=400, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📆 Monthly Engagement")
        # Group by month and calculate engagement breakdown
        monthly_stats = filtered_df.groupby('month').agg({
            'reactions': 'sum',
            'comments': 'sum',
            'shares': 'sum',
            'engagement': 'sum',
            'post_id': 'count'
        }).rename(columns={'post_id': 'posts'}).reset_index()

        # Sort by month
        monthly_stats = monthly_stats.sort_values('month')

        # Create stacked bar chart showing breakdown
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Reactions', x=monthly_stats['month'], y=monthly_stats['reactions'], marker_color='#4361EE'))
        fig.add_trace(go.Bar(name='Comments', x=monthly_stats['month'], y=monthly_stats['comments'], marker_color='#7209B7'))
        fig.add_trace(go.Bar(name='Shares', x=monthly_stats['month'], y=monthly_stats['shares'], marker_color='#F72585'))

        fig.update_layout(
            title='Monthly Engagement by Type',
            barmode='stack',
            xaxis_title='Month',
            yaxis_title='Total Engagement',
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ===== DISTRIBUTION STATISTICS BY CONTENT TYPE =====
    with st.expander("📊 Post Distribution by Content Type", expanded=False):
        st.markdown("**Engagement statistics broken down by content category**")

        # Check if content_category column exists
        if 'content_category' in filtered_df.columns:
            # Calculate distribution stats
            content_stats = filtered_df.groupby('content_category')['engagement'].agg([
                ('Posts', 'count'),
                ('Median', 'median'),
                ('Mean', 'mean'),
                ('Min', 'min'),
                ('Max', 'max'),
                ('Std Dev', 'std')
            ]).round(0).astype(int)

            # Sort by median engagement descending
            content_stats = content_stats.sort_values('Median', ascending=False)

            # Reset index to make content_category a column
            content_stats = content_stats.reset_index()
            content_stats.columns = ['Content Type', 'Posts', 'Median', 'Mean', 'Min', 'Max', 'Std Dev']

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("##### Statistics Table")
                st.dataframe(
                    content_stats.style.highlight_max(subset=['Median'], color=get_highlight_color()),
                    use_container_width=True,
                    hide_index=True
                )

                # Best performer insight
                best_type = content_stats.iloc[0]['Content Type']
                best_median = content_stats.iloc[0]['Median']
                overall_median = filtered_df['engagement'].median()
                pct_better = ((best_median - overall_median) / overall_median * 100) if overall_median > 0 else 0
                st.success(f"⭐ **{best_type}** has highest median engagement ({best_median:,.0f}) - {pct_better:.0f}% above overall median")

            with col2:
                st.markdown("##### Engagement Distribution")
                # Create box plot
                fig_box = go.Figure()

                colors = {'Livestreams': '#E91E63', 'Photos': '#4361EE', 'Reels': '#7209B7', 'Videos': '#F72585', 'Other': '#9CA3AF'}

                for content_type in ['Livestreams', 'Reels', 'Videos', 'Photos', 'Other']:
                    type_data = filtered_df[filtered_df['content_category'] == content_type]['engagement']
                    if len(type_data) > 0:
                        fig_box.add_trace(go.Box(
                            y=type_data,
                            name=content_type,
                            marker_color=colors.get(content_type, '#9CA3AF'),
                            boxpoints='outliers'
                        ))

                fig_box.update_layout(
                    title='Engagement by Content Type',
                    yaxis_title='Engagement',
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.warning("Content category data not available. Please refresh data.")

    # ===== CORRELATION ANALYSIS SECTION =====
    with st.expander("📈 Correlation Analysis", expanded=False):
        st.markdown("**Engagement metric correlations and content type performance**")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("##### Engagement Metric Correlations")
            # Calculate correlation matrix for engagement metrics
            corr_cols = ['reactions', 'comments', 'shares']
            if all(col in filtered_df.columns for col in corr_cols):
                corr_matrix = filtered_df[corr_cols].corr()

                # Create heatmap
                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=['Reactions', 'Comments', 'Shares'],
                    y=['Reactions', 'Comments', 'Shares'],
                    colorscale='RdBu',
                    zmid=0,
                    text=corr_matrix.round(2).values,
                    texttemplate='%{text}',
                    textfont={"size": 14},
                    hovertemplate='%{x} vs %{y}: %{z:.2f}<extra></extra>'
                ))
                fig_corr.update_layout(
                    title='Correlation Heatmap',
                    height=350
                )
                st.plotly_chart(fig_corr, use_container_width=True)

                # Find strongest and weakest correlations (excluding diagonal)
                corr_pairs = []
                for i, col1_name in enumerate(corr_cols):
                    for j, col2_name in enumerate(corr_cols):
                        if i < j:
                            corr_pairs.append((col1_name.title(), col2_name.title(), corr_matrix.iloc[i, j]))

                if corr_pairs:
                    strongest = max(corr_pairs, key=lambda x: abs(x[2]))
                    st.info(f"💡 Strongest correlation: **{strongest[0]}** ↔ **{strongest[1]}** ({strongest[2]:.2f})")
            else:
                st.warning("Correlation data not available.")

        with col2:
            st.markdown("##### Content Type Performance")
            if 'content_category' in filtered_df.columns:
                # Calculate average engagement by content type
                type_perf = filtered_df.groupby('content_category')['engagement'].mean().sort_values(ascending=True)

                # Create horizontal bar chart
                colors = {'Livestreams': '#E91E63', 'Photos': '#4361EE', 'Reels': '#7209B7', 'Videos': '#F72585', 'Other': '#9CA3AF'}
                bar_colors = [colors.get(t, '#9CA3AF') for t in type_perf.index]

                fig_perf = go.Figure(go.Bar(
                    x=type_perf.values,
                    y=type_perf.index,
                    orientation='h',
                    marker_color=bar_colors,
                    text=[f'{v:,.0f}' for v in type_perf.values],
                    textposition='outside'
                ))
                fig_perf.update_layout(
                    title='Avg Engagement by Content Type',
                    xaxis_title='Average Engagement',
                    height=350
                )
                st.plotly_chart(fig_perf, use_container_width=True)

                # Best performer insight
                overall_avg = filtered_df['engagement'].mean()
                best_type = type_perf.idxmax()
                best_avg = type_perf.max()
                pct_above = ((best_avg - overall_avg) / overall_avg * 100) if overall_avg > 0 else 0
                st.success(f"🏆 **{best_type}** performs {pct_above:.0f}% better than average ({best_avg:,.0f} vs {overall_avg:,.0f})")
            else:
                st.warning("Content type performance data not available.")

    st.markdown("---")

    # ===== TOP VIDEOS SECTION (NEW!) =====
    st.markdown("### 🎬 Top 10 Videos by Views")

    videos = videos_data.get('videos', [])
    if videos:
        videos_df = pd.DataFrame(videos)
        videos_df = videos_df.sort_values('views', ascending=False).head(10)

        # Format for display (API returns 'description' not 'title')
        display_videos = videos_df[['description', 'views', 'length', 'created_time', 'permalink_url']].copy()
        display_videos.columns = ['Title', 'Views', 'Duration (sec)', 'Created', 'Link']
        display_videos['Title'] = display_videos['Title'].fillna('Untitled').str[:50]
        display_videos['Views'] = display_videos['Views'].apply(lambda x: f"{int(x):,}")
        display_videos['Created'] = pd.to_datetime(display_videos['Created']).dt.strftime('%Y-%m-%d')

        # Fix relative URLs - add Facebook base URL
        display_videos['Link'] = display_videos['Link'].apply(
            lambda x: f"https://www.facebook.com{x}" if x and x.startswith('/') else x
        )

        st.dataframe(
            display_videos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Link": st.column_config.LinkColumn("Link", display_text="View →")
            }
        )
    else:
        st.info("No video data available.")

    st.markdown("---")

    # Best posting times
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📆 Best Posting Days")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_stats = filtered_df.groupby('day_of_week').agg({
            'engagement': ['count', 'sum', 'mean'],
            'reactions': 'mean',
            'comments': 'mean'
        })
        day_stats.columns = ['Posts', 'Total Engagement', 'Avg Engagement', 'Avg Reactions', 'Avg Comments']
        day_stats = day_stats.reindex(day_order).reset_index()

        for col in ['Posts', 'Total Engagement', 'Avg Engagement', 'Avg Reactions', 'Avg Comments']:
            day_stats[col] = day_stats[col].fillna(0).astype(int)

        best_day = day_stats.loc[day_stats['Avg Engagement'].idxmax(), 'day_of_week']

        st.dataframe(
            day_stats.style.highlight_max(subset=['Avg Engagement'], color=get_highlight_color()),
            use_container_width=True, hide_index=True
        )
        st.success(f"⭐ Best day: **{best_day}**")

    with col2:
        st.markdown("### ⏰ Best Posting Times")
        slot_order = ['Morning (6AM-12PM)', 'Afternoon (12PM-6PM)', 'Evening (6PM-10PM)', 'Night (10PM-6AM)']
        slot_stats = filtered_df.groupby('time_slot').agg({
            'engagement': ['count', 'sum', 'mean'],
            'reactions': 'mean',
            'comments': 'mean'
        })
        slot_stats.columns = ['Posts', 'Total Engagement', 'Avg Engagement', 'Avg Reactions', 'Avg Comments']
        slot_stats = slot_stats.reindex(slot_order).reset_index()

        for col in ['Posts', 'Total Engagement', 'Avg Engagement', 'Avg Reactions', 'Avg Comments']:
            slot_stats[col] = slot_stats[col].fillna(0).astype(int)

        best_slot = slot_stats.loc[slot_stats['Avg Engagement'].idxmax(), 'time_slot']

        st.dataframe(
            slot_stats.style.highlight_max(subset=['Avg Engagement'], color=get_highlight_color()),
            use_container_width=True, hide_index=True
        )
        st.success(f"⭐ Best time: **{best_slot}**")

    st.markdown("---")

    # Top Posts
    st.markdown("### 🏆 Top 15 Performing Posts")

    # Use permalink (from CSV) or permalink_url (from API)
    link_col = 'permalink' if 'permalink' in filtered_df.columns else 'permalink_url'

    top_posts = filtered_df.nlargest(15, 'engagement')[
        ['date', 'post_type_clean', 'message', 'reactions', 'comments', 'shares', 'engagement', link_col]
    ].copy()
    top_posts['message'] = top_posts['message'].fillna('').str[:80]
    top_posts.columns = ['Date', 'Type', 'Message', 'Reactions', 'Comments', 'Shares', 'Engagement', 'Link']

    for col in ['Reactions', 'Comments', 'Shares', 'Engagement']:
        top_posts[col] = top_posts[col].apply(lambda x: f"{int(x):,}")

    st.dataframe(
        top_posts,
        use_container_width=True,
        hide_index=True,
        column_config={"Link": st.column_config.LinkColumn("Link", display_text="View →")}
    )

    st.markdown("---")

    # All Posts Table
    st.markdown("### 📋 All Posts")

    all_posts = filtered_df.sort_values('date', ascending=False)[
        ['date', 'post_type_clean', 'message', 'reactions', 'comments', 'shares', 'engagement', link_col]
    ].copy()
    all_posts['message'] = all_posts['message'].fillna('').str[:60]
    all_posts.columns = ['Date', 'Type', 'Message', 'Reactions', 'Comments', 'Shares', 'Engagement', 'Link']

    st.dataframe(
        all_posts,
        use_container_width=True,
        height=600,
        column_config={"Link": st.column_config.LinkColumn("Link", display_text="View →")}
    )

    # Footer - use yesterday's date since today might not have complete data
    st.markdown("---")
    report_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    st.markdown(
        f"<p class='footer-text'>Report Date: {report_date} • Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} • Data from Facebook Graph API</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
