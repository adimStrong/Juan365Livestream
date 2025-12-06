"""
Juan365 Live Stream Report Generator
Generates professional minimalist HTML reports from Meta Business Suite exports

Usage:
    python generate_report.py              # All data
    python generate_report.py --days 60    # Last 60 days
"""

import pandas as pd
import os
import argparse
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Configuration
PROJECT_DIR = Path(__file__).parent.parent  # juan365_engagement_project
REPORTS_DIR = Path(__file__).parent         # reports/
EXPORTS_DIR = PROJECT_DIR / 'exports'
TEMPLATE_DIR = REPORTS_DIR / 'templates'
OUTPUT_DIR = REPORTS_DIR / 'output'

PAGE_NAME = "Juan365 Live Stream"


def find_latest_csv():
    """Find the most recent CSV file in exports folder."""
    csv_files = list(EXPORTS_DIR.glob('*.csv'))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {EXPORTS_DIR}")

    # Sort by modification time, newest first
    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return csv_files[0]


def clean_post_type(pt):
    """Normalize post type names from Meta export."""
    if pd.isna(pt):
        return 'Other'
    pt = str(pt).strip().lower()

    type_map = {
        'photos': 'Photo',
        'photo': 'Photo',
        'videos': 'Video',
        'video': 'Video',
        'reels': 'Reel',
        'reel': 'Reel',
        'live': 'Live',
        'live stream': 'Live',
        'live_video': 'Live',
        'text': 'Text',
        'status': 'Text'
    }

    return type_map.get(pt, pt.title() if pt else 'Other')


def get_time_slot(hour):
    """Get time slot from hour (0-23)."""
    if 6 <= hour < 12:
        return 'Morning (6AM-12PM)'
    elif 12 <= hour < 18:
        return 'Afternoon (12PM-6PM)'
    elif 18 <= hour < 24:
        return 'Evening (6PM-12AM)'
    else:
        return 'Night (12AM-6AM)'


def load_data(csv_path, days=None):
    """Load and prepare post data from Meta Business Suite export."""
    print(f"[INFO] Loading data from {csv_path.name}...")
    df = pd.read_csv(csv_path)
    print(f"[OK] Loaded {len(df)} total posts")

    # Rename Meta Business Suite columns to standard format
    column_mapping = {
        'Post ID': 'post_id',
        'Title': 'message',
        'Publish time': 'publish_time',
        'Post type': 'post_type',
        'Permalink': 'permalink',
        'Reactions': 'reactions',
        'Comments': 'comments',
        'Shares': 'shares',
        'Views': 'views',
        'Reach': 'reach'
    }
    df = df.rename(columns=column_mapping)

    # Parse publish time (format: "MM/DD/YYYY H:MM" or "M/D/YYYY H:MM")
    df['publish_datetime'] = pd.to_datetime(df['publish_time'], format='%m/%d/%Y %H:%M', errors='coerce')
    df['created_date'] = df['publish_datetime'].dt.strftime('%Y-%m-%d')
    df['created_time'] = df['publish_datetime'].dt.strftime('%H:%M')
    df['hour'] = df['publish_datetime'].dt.hour

    # Fill NaN values for engagement metrics
    df['reactions'] = df['reactions'].fillna(0).astype(int)
    df['comments'] = df['comments'].fillna(0).astype(int)
    df['shares'] = df['shares'].fillna(0).astype(int)
    df['engagement'] = df['reactions'] + df['comments'] + df['shares']

    # Filter by date range if specified
    if days:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        df = df[df['created_date'] >= cutoff_date]
        print(f"[INFO] Filtered to last {days} days: {len(df)} posts")

    # Clean post types
    df['post_type_clean'] = df['post_type'].apply(clean_post_type)

    # Add derived columns
    df['time_slot'] = df['hour'].apply(get_time_slot)
    df['day_of_week'] = df['publish_datetime'].dt.strftime('%A')

    # Fill message if empty
    df['message'] = df['message'].fillna('')

    print(f"[OK] Date range: {df['created_date'].min()} to {df['created_date'].max()}")

    type_counts = df['post_type_clean'].value_counts().to_dict()
    type_str = ', '.join([f"{k} ({v})" for k, v in type_counts.items()])
    print(f"[OK] Post types: {type_str}")

    return df


def calculate_metrics(df):
    """Calculate all report metrics."""
    metrics = {}

    # Executive Summary
    metrics['page_name'] = PAGE_NAME
    metrics['total_posts'] = len(df)
    metrics['total_engagement'] = int(df['engagement'].sum())
    metrics['avg_engagement'] = round(df['engagement'].mean(), 1) if len(df) > 0 else 0
    metrics['total_reactions'] = int(df['reactions'].sum())
    metrics['total_comments'] = int(df['comments'].sum())
    metrics['total_shares'] = int(df['shares'].sum())
    metrics['date_range_start'] = df['created_date'].min()
    metrics['date_range_end'] = df['created_date'].max()

    # Post Type Analysis
    post_type_stats = df.groupby('post_type_clean').agg({
        'engagement': ['count', 'sum', 'mean'],
        'reactions': 'sum',
        'comments': 'sum',
        'shares': 'sum'
    }).round(1)

    metrics['post_types'] = []
    for post_type in post_type_stats.index:
        stats = post_type_stats.loc[post_type]
        metrics['post_types'].append({
            'type': post_type,
            'count': int(stats[('engagement', 'count')]),
            'total_engagement': int(stats[('engagement', 'sum')]),
            'avg_engagement': round(stats[('engagement', 'mean')], 1),
            'reactions': int(stats[('reactions', 'sum')]),
            'comments': int(stats[('comments', 'sum')]),
            'shares': int(stats[('shares', 'sum')])
        })

    # Sort by total engagement
    metrics['post_types'] = sorted(metrics['post_types'], key=lambda x: x['total_engagement'], reverse=True)

    # Day of Week Analysis
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_stats = df.groupby('day_of_week').agg({
        'engagement': ['count', 'sum', 'mean']
    }).round(1)

    metrics['day_of_week'] = []
    for day in day_order:
        if day in day_stats.index:
            stats = day_stats.loc[day]
            metrics['day_of_week'].append({
                'day': day,
                'count': int(stats[('engagement', 'count')]),
                'total_engagement': int(stats[('engagement', 'sum')]),
                'avg_engagement': round(stats[('engagement', 'mean')], 1)
            })
        else:
            metrics['day_of_week'].append({
                'day': day, 'count': 0, 'total_engagement': 0, 'avg_engagement': 0
            })

    # Find best day by average engagement
    best_day = max(metrics['day_of_week'], key=lambda x: x['avg_engagement'])
    metrics['best_day'] = best_day['day']

    # Time Slot Analysis
    time_slot_order = ['Morning (6AM-12PM)', 'Afternoon (12PM-6PM)', 'Evening (6PM-12AM)', 'Night (12AM-6AM)']
    time_stats = df.groupby('time_slot').agg({
        'engagement': ['count', 'sum', 'mean']
    }).round(1)

    metrics['time_slots'] = []
    for slot in time_slot_order:
        if slot in time_stats.index:
            stats = time_stats.loc[slot]
            metrics['time_slots'].append({
                'slot': slot,
                'count': int(stats[('engagement', 'count')]),
                'total_engagement': int(stats[('engagement', 'sum')]),
                'avg_engagement': round(stats[('engagement', 'mean')], 1)
            })
        else:
            metrics['time_slots'].append({
                'slot': slot, 'count': 0, 'total_engagement': 0, 'avg_engagement': 0
            })

    # Find best time slot
    best_slot = max(metrics['time_slots'], key=lambda x: x['avg_engagement'])
    metrics['best_time_slot'] = best_slot['slot']

    # Top 15 Posts
    top_posts = df.nlargest(15, 'engagement')
    metrics['top_posts'] = []
    for _, row in top_posts.iterrows():
        message = str(row.get('message', '')) if pd.notna(row.get('message')) else ''
        metrics['top_posts'].append({
            'date': row['created_date'],
            'type': row['post_type_clean'],
            'message': message[:100],
            'reactions': int(row['reactions']),
            'comments': int(row['comments']),
            'shares': int(row['shares']),
            'engagement': int(row['engagement']),
            'permalink': row.get('permalink', '#')
        })

    # All Posts (sorted by date desc)
    all_posts_df = df.sort_values('created_date', ascending=False)
    metrics['all_posts'] = []
    for _, row in all_posts_df.iterrows():
        message = str(row.get('message', '')) if pd.notna(row.get('message')) else ''
        metrics['all_posts'].append({
            'date': row['created_date'],
            'type': row['post_type_clean'],
            'message': message[:80],
            'reactions': int(row['reactions']),
            'comments': int(row['comments']),
            'shares': int(row['shares']),
            'engagement': int(row['engagement']),
            'permalink': row.get('permalink', '#')
        })

    # Chart Data - Daily engagement (last 30 days)
    df_sorted = df.sort_values('created_date')
    daily_engagement = df_sorted.groupby('created_date')['engagement'].sum().tail(30)
    metrics['chart_dates'] = [str(d) for d in daily_engagement.index]
    metrics['chart_engagement'] = [int(v) for v in daily_engagement.values]

    # Post type distribution for chart
    metrics['post_type_labels'] = [pt['type'] for pt in metrics['post_types']]
    metrics['post_type_values'] = [pt['count'] for pt in metrics['post_types']]

    # Weekly Metrics using ISO weeks (last 8 weeks)
    df['iso_year'] = df['publish_datetime'].dt.isocalendar().year
    df['iso_week'] = df['publish_datetime'].dt.isocalendar().week
    df['iso_year_week'] = df['iso_year'].astype(str) + '-W' + df['iso_week'].astype(str).str.zfill(2)

    # Get actual date range for each ISO week
    weekly_stats = df.groupby('iso_year_week').agg({
        'engagement': ['count', 'sum', 'mean'],
        'publish_datetime': ['min', 'max']
    }).round(1)

    metrics['weekly_metrics'] = []
    week_num = 1
    for year_week in sorted(weekly_stats.index, reverse=True)[:8]:
        stats = weekly_stats.loc[year_week]
        # Get actual first and last post dates for this week
        actual_start = stats[('publish_datetime', 'min')]
        actual_end = stats[('publish_datetime', 'max')]

        # Parse ISO week number
        iso_week_num = int(year_week.split('-W')[1])

        metrics['weekly_metrics'].append({
            'week_num': iso_week_num,
            'start_date': actual_start.strftime('%b %d'),
            'end_date': actual_end.strftime('%b %d'),
            'year': actual_start.strftime('%Y'),
            'posts': int(stats[('engagement', 'count')]),
            'engagement': int(stats[('engagement', 'sum')]),
            'avg': round(stats[('engagement', 'mean')], 1)
        })
        week_num += 1

    # Weekly chart data (last 12 weeks) with ISO week labels
    weekly_chart_data = df.groupby('iso_year_week').agg({
        'engagement': 'sum',
        'publish_datetime': 'min'
    }).tail(12)
    metrics['weekly_chart_labels'] = [f"W{row.name.split('-W')[1]}" for _, row in weekly_chart_data.iterrows()]
    metrics['weekly_chart_values'] = [int(row['engagement']) for _, row in weekly_chart_data.iterrows()]

    # Monthly Metrics
    df['month'] = df['publish_datetime'].dt.to_period('M')
    monthly_stats = df.groupby('month').agg({
        'engagement': ['count', 'sum', 'mean']
    }).round(1)

    metrics['monthly_metrics'] = []
    for month in sorted(monthly_stats.index, reverse=True)[:6]:
        stats = monthly_stats.loc[month]
        metrics['monthly_metrics'].append({
            'month_name': month.strftime('%B'),
            'year': month.strftime('%Y'),
            'posts': int(stats[('engagement', 'count')]),
            'engagement': int(stats[('engagement', 'sum')]),
            'avg': round(stats[('engagement', 'mean')], 1)
        })

    # Monthly chart data
    monthly_chart = df.groupby('month')['engagement'].sum()
    metrics['monthly_chart_labels'] = [m.strftime('%b %Y') for m in monthly_chart.index]
    metrics['monthly_chart_values'] = [int(v) for v in monthly_chart.values]

    return metrics


def generate_report(metrics):
    """Generate HTML report from metrics."""
    print("[INFO] Generating HTML report...")

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('report_template.html')

    metrics['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html_content = template.render(**metrics)

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / f'Juan365_Report_{datetime.now().strftime("%Y-%m-%d")}.html'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[OK] Report saved to: {output_file}")
    return output_file


def copy_to_latest(output_file):
    """Copy report to a fixed 'latest' filename."""
    latest_file = OUTPUT_DIR / 'Juan365_Report_LATEST.html'
    shutil.copy(output_file, latest_file)
    print(f"[OK] Copied to: {latest_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate Juan365 Social Media Report')
    parser.add_argument('--days', type=int, default=None,
                        help='Number of days to include (default: all data)')
    args = parser.parse_args()

    print("=" * 60)
    print("JUAN365 SOCIAL MEDIA REPORT GENERATOR")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Find latest CSV
    try:
        csv_path = find_latest_csv()
        print(f"[INFO] Using CSV: {csv_path.name}")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return

    # Load data
    df = load_data(csv_path, days=args.days)

    if len(df) == 0:
        print("[ERROR] No posts found!")
        return

    # Calculate metrics
    print("\n[INFO] Calculating metrics...")
    metrics = calculate_metrics(df)

    # Print summary
    print("\n" + "-" * 60)
    print("REPORT SUMMARY")
    print("-" * 60)
    print(f"Total Posts: {metrics['total_posts']:,}")
    print(f"Total Engagement: {metrics['total_engagement']:,}")
    print(f"Average per Post: {metrics['avg_engagement']:.1f}")
    print(f"Date Range: {metrics['date_range_start']} to {metrics['date_range_end']}")

    pt_str = ', '.join([f"{pt['type']} ({pt['count']})" for pt in metrics['post_types']])
    print(f"Post Types: {pt_str}")
    print(f"Best Day: {metrics['best_day']}")
    print(f"Best Time: {metrics['best_time_slot']}")

    # Generate report
    output_file = generate_report(metrics)
    copy_to_latest(output_file)

    print("\n" + "=" * 60)
    print("REPORT COMPLETE!")
    print("=" * 60)
    print(f"\nFiles:")
    print(f"  - {output_file}")
    print(f"  - {OUTPUT_DIR / 'Juan365_Report_LATEST.html'}")
    print(f"\nTo view: python serve_report.py")


if __name__ == '__main__':
    main()
