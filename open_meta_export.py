"""
Open Meta Business Suite Export Page

This script opens the Meta Business Suite Insights page in your default browser.
You just need to:
1. Click "Export" button
2. Either download existing export OR generate new one with latest dates
3. The CSV will be saved to Downloads folder

Run this manually or schedule it with Windows Task Scheduler.
"""
import webbrowser
from datetime import datetime, timedelta

# Meta Business Suite Insights - Content page
META_URL = "https://business.facebook.com/latest/insights/content"

def get_date_range():
    """Calculate recommended date range (last 90 days)"""
    today = datetime.now()
    end_date = today.strftime("%b %d, %Y")  # e.g., "Dec 06, 2025"
    start_date = (today - timedelta(days=90)).strftime("%b %d, %Y")
    return start_date, end_date

def open_meta_page():
    start_date, end_date = get_date_range()

    print("=" * 60)
    print("OPENING META BUSINESS SUITE - CSV EXPORT")
    print("=" * 60)
    print()
    print("The page will open in your browser.")
    print()
    print("-" * 60)
    print("OPTION 1: Download Existing Export (Quick)")
    print("-" * 60)
    print("  1. Click 'Export' button (top right)")
    print("  2. Click on any completed export to download")
    print()
    print("-" * 60)
    print("OPTION 2: Generate NEW Export (Latest Data)")
    print("-" * 60)
    print("  1. Click 'Export' button (top right)")
    print("  2. Click 'Export new data'")
    print("  3. Set date range:")
    print(f"     FROM: {start_date}")
    print(f"     TO:   {end_date} (today)")
    print("  4. Click 'Export'")
    print("  5. Wait for export to complete (~1-2 min)")
    print("  6. Click on completed export to download")
    print()
    print("-" * 60)
    print("After downloading CSV, run:")
    print("  python merge_exports.py")
    print("=" * 60)
    print()

    # Open in default browser
    webbrowser.open(META_URL)
    print(f"Opened: {META_URL}")
    print()
    print("If page shows error, make sure you're logged into Facebook")
    print("and have access to Juan365 Live Stream page.")

if __name__ == "__main__":
    open_meta_page()
    input("\nPress Enter to close...")
