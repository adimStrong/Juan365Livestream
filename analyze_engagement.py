"""
Juan365 Engagement Data Analyzer
Analyzes exported data from Meta Business Suite
"""

import pandas as pd
import json
from datetime import datetime
import os

# Configuration
EXPORT_FILE = "C:/Users/us/Desktop/juan365_engagement_project/exports/Juan365_full_export_20251204.csv"
OUTPUT_DIR = "C:/Users/us/Desktop/juan365_engagement_project/output"


def load_data(filepath):
    """Load the CSV export file"""
    print(f"[INFO] Loading data from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"[OK] Loaded {len(df)} posts")
    return df


def analyze_by_post_type(df):
    """Analyze engagement breakdown by post type"""
    print("\n[INFO] Analyzing by post type...")

    # Group by Post type
    type_stats = df.groupby('Post type').agg({
        'Post ID': 'count',
        'Reactions': 'sum',
        'Comments': 'sum',
        'Shares': 'sum',
        'Views': 'sum',
        'Reach': 'sum'
    }).rename(columns={'Post ID': 'Count'})

    # Calculate totals
    type_stats['Total Engagement'] = type_stats['Reactions'] + type_stats['Comments'] + type_stats['Shares']
    type_stats['Avg Engagement'] = (type_stats['Total Engagement'] / type_stats['Count']).round(1)
    type_stats['Avg Reactions'] = (type_stats['Reactions'] / type_stats['Count']).round(1)
    type_stats['Avg Comments'] = (type_stats['Comments'] / type_stats['Count']).round(1)
    type_stats['Avg Shares'] = (type_stats['Shares'] / type_stats['Count']).round(1)

    return type_stats


def get_top_posts(df, n=20):
    """Get top N posts by engagement"""
    print(f"\n[INFO] Finding top {n} posts...")

    # Calculate total engagement
    df['Total Engagement'] = df['Reactions'].fillna(0) + df['Comments'].fillna(0) + df['Shares'].fillna(0)

    # Sort by total engagement
    top = df.nlargest(n, 'Total Engagement')

    # Select relevant columns
    result = top[['Publish time', 'Post type', 'Title', 'Reactions', 'Comments',
                  'Shares', 'Total Engagement', 'Reach', 'Views', 'Permalink']].copy()

    return result


def generate_summary(df):
    """Generate overall summary statistics"""
    print("\n[INFO] Generating summary statistics...")

    total_reactions = df['Reactions'].fillna(0).sum()
    total_comments = df['Comments'].fillna(0).sum()
    total_shares = df['Shares'].fillna(0).sum()
    total_reach = df['Reach'].fillna(0).sum()
    total_views = df['Views'].fillna(0).sum()

    total_engagement = total_reactions + total_comments + total_shares

    summary = {
        "collection_date": datetime.now().isoformat(),
        "data_source": "Meta Business Suite Export",
        "page_name": "Juan365",
        "date_range": {
            "start": df['Publish time'].min() if 'Publish time' in df.columns else "N/A",
            "end": df['Publish time'].max() if 'Publish time' in df.columns else "N/A"
        },
        "total_posts": len(df),
        "post_type_counts": df['Post type'].value_counts().to_dict(),
        "engagement_totals": {
            "reactions": int(total_reactions),
            "comments": int(total_comments),
            "shares": int(total_shares),
            "total": int(total_engagement)
        },
        "engagement_averages": {
            "reactions": round(total_reactions / len(df), 1),
            "comments": round(total_comments / len(df), 1),
            "shares": round(total_shares / len(df), 1),
            "total": round(total_engagement / len(df), 1)
        },
        "reach_totals": {
            "total_reach": int(total_reach),
            "total_views": int(total_views),
            "avg_reach_per_post": round(total_reach / len(df), 1)
        }
    }

    return summary


def save_results(summary, type_stats, top_posts, df, output_dir):
    """Save all analysis results"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save summary JSON
    json_file = f"{output_dir}/Juan365_analysis_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"[OK] Saved summary: {json_file}")

    # Save type breakdown CSV
    type_file = f"{output_dir}/Juan365_by_type_{timestamp}.csv"
    type_stats.to_csv(type_file)
    print(f"[OK] Saved type breakdown: {type_file}")

    # Save top posts CSV
    top_file = f"{output_dir}/Juan365_top_posts_{timestamp}.csv"
    top_posts.to_csv(top_file, index=False)
    print(f"[OK] Saved top posts: {top_file}")

    # Save posts with links (clean format)
    links_file = f"{output_dir}/Juan365_posts_with_links_{timestamp}.csv"
    df['Total Engagement'] = df['Reactions'].fillna(0) + df['Comments'].fillna(0) + df['Shares'].fillna(0)
    posts_links = df[['Publish time', 'Post type', 'Title', 'Reactions', 'Comments',
                      'Shares', 'Total Engagement', 'Reach', 'Permalink']].copy()
    posts_links = posts_links.sort_values('Total Engagement', ascending=False)
    posts_links.to_csv(links_file, index=False)
    print(f"[OK] Saved posts with links: {links_file}")

    return json_file, type_file, top_file, links_file


def print_report(summary, type_stats, top_posts):
    """Print formatted report to console"""
    print("\n" + "=" * 70)
    print("JUAN365 ENGAGEMENT ANALYSIS REPORT")
    print("=" * 70)
    print(f"Data Source: {summary['data_source']}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")

    print("\n" + "-" * 70)
    print("OVERALL SUMMARY")
    print("-" * 70)
    print(f"Total Posts: {summary['total_posts']:,}")
    print(f"\nPost Types:")
    for ptype, count in summary['post_type_counts'].items():
        print(f"  {ptype}: {count:,}")

    print(f"\nEngagement Totals:")
    print(f"  Reactions: {summary['engagement_totals']['reactions']:,}")
    print(f"  Comments: {summary['engagement_totals']['comments']:,}")
    print(f"  Shares: {summary['engagement_totals']['shares']:,}")
    print(f"  TOTAL: {summary['engagement_totals']['total']:,}")

    print(f"\nEngagement Averages (per post):")
    print(f"  Reactions: {summary['engagement_averages']['reactions']}")
    print(f"  Comments: {summary['engagement_averages']['comments']}")
    print(f"  Shares: {summary['engagement_averages']['shares']}")
    print(f"  TOTAL: {summary['engagement_averages']['total']}")

    print(f"\nReach:")
    print(f"  Total Reach: {summary['reach_totals']['total_reach']:,}")
    print(f"  Total Views: {summary['reach_totals']['total_views']:,}")
    print(f"  Avg Reach/Post: {summary['reach_totals']['avg_reach_per_post']:,}")

    print("\n" + "-" * 70)
    print("BREAKDOWN BY POST TYPE")
    print("-" * 70)
    print(type_stats[['Count', 'Total Engagement', 'Avg Engagement', 'Avg Reactions', 'Avg Comments', 'Avg Shares']].to_string())

    print("\n" + "-" * 70)
    print("TOP 10 POSTS BY ENGAGEMENT")
    print("-" * 70)
    for i, (_, row) in enumerate(top_posts.head(10).iterrows(), 1):
        title = str(row['Title'])[:50] + "..." if len(str(row['Title'])) > 50 else str(row['Title'])
        print(f"\n{i}. {row['Post type']} | {row['Publish time']}")
        print(f"   Engagement: {int(row['Total Engagement']):,} (R:{int(row['Reactions'])} C:{int(row['Comments'])} S:{int(row['Shares'])})")
        print(f"   Title: {title}")
        print(f"   Link: {row['Permalink']}")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)


def main():
    print("=" * 70)
    print("JUAN365 ENGAGEMENT DATA ANALYZER")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load data
    df = load_data(EXPORT_FILE)

    # Analyze
    summary = generate_summary(df)
    type_stats = analyze_by_post_type(df)
    top_posts = get_top_posts(df, n=20)

    # Save results
    files = save_results(summary, type_stats, top_posts, df, OUTPUT_DIR)

    # Print report
    print_report(summary, type_stats, top_posts)

    print(f"\nOutput Files:")
    for f in files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
