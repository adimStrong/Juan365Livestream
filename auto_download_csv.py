"""
Auto-download CSV from Meta Business Suite using Playwright browser automation.

Usage:
    python auto_download_csv.py --setup    # First-time setup - manual login to save session
    python auto_download_csv.py --test     # Test CSV download
    python auto_download_csv.py            # Normal run (used by auto_update.py)
"""
import sys
import os
import shutil
import time
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# Directories
AUTOMATION_DIR = PROJECT_DIR / 'automation'
BROWSER_DATA_DIR = AUTOMATION_DIR / 'browser_data'
EXPORTS_DIR = PROJECT_DIR / 'exports'
LOGS_DIR = PROJECT_DIR / 'logs'
DOWNLOADS_DIR = Path.home() / 'Downloads'

# Ensure directories exist
AUTOMATION_DIR.mkdir(exist_ok=True)
BROWSER_DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Config file
CONFIG_FILE = AUTOMATION_DIR / 'config.json'

# Meta Business Suite URL - Content insights page
META_INSIGHTS_URL = "https://business.facebook.com/latest/insights/content"

# Page ID from config.py
try:
    from config import PAGE_ID
except ImportError:
    PAGE_ID = None


def log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    print(log_message)

    # Also write to log file
    log_file = LOGS_DIR / 'auto_update.log'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')


def load_config():
    """Load automation config"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_export_date': None,
        'export_days': 90,  # Default export range
        'page_id': PAGE_ID
    }


def save_config(config):
    """Save automation config"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def setup_browser_session():
    """
    First-time setup: Open browser for manual login.
    User logs in manually, session is saved for future automation.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("ERROR: Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    log("=== BROWSER SESSION SETUP ===")
    log("A browser window will open. Please:")
    log("1. Log in to your Facebook account")
    log("2. Navigate to Meta Business Suite")
    log("3. Make sure you can access the Insights page")
    log("4. Close the browser when done")
    log("")

    with sync_playwright() as p:
        # Launch browser with persistent context (saves session)
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_DATA_DIR),
            headless=False,  # Show browser for manual login
            viewport={'width': 1280, 'height': 800}
        )

        page = browser.new_page()

        # Navigate to Meta Business Suite
        log("Opening Meta Business Suite...")
        page.goto(META_INSIGHTS_URL)

        # Wait for user to log in and close browser
        log("Waiting for you to log in and close the browser...")
        try:
            page.wait_for_event('close', timeout=300000)  # 5 minute timeout
        except:
            pass

        browser.close()

    log("Session saved! You can now run the automation.")
    return True


def download_csv(headless=True, test_mode=False):
    """
    Download CSV from Meta Business Suite.
    Returns path to downloaded CSV or None if failed.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("ERROR: Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None

    config = load_config()

    log("Starting CSV download from Meta Business Suite...")

    with sync_playwright() as p:
        # Launch browser with saved session
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_DATA_DIR),
            headless=headless,
            viewport={'width': 1280, 'height': 900},
            downloads_path=str(DOWNLOADS_DIR)
        )

        page = browser.new_page()

        try:
            # Navigate to Meta Business Suite Content Insights
            log(f"Navigating to: {META_INSIGHTS_URL}")
            page.goto(META_INSIGHTS_URL, wait_until='networkidle', timeout=60000)

            # Wait for page to fully load
            time.sleep(5)

            # Check if we need to log in
            if 'login' in page.url.lower() or 'facebook.com/login' in page.url:
                log("ERROR: Not logged in. Run 'python auto_download_csv.py --setup' first.")
                browser.close()
                return None

            # Check if we're on the right page
            log(f"Current URL: {page.url}")

            # Wait for the content to load
            time.sleep(3)

            # Take screenshot for debugging
            if test_mode:
                screenshot_path = LOGS_DIR / f'meta_page_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path))
                log(f"Screenshot saved: {screenshot_path}")

            # Look for Export button - Meta Business Suite UI
            # The export button is usually in the top right area
            export_button = None

            # Try different selectors for the Export button
            export_selectors = [
                'button:has-text("Export")',
                '[aria-label="Export"]',
                'div[role="button"]:has-text("Export")',
                'span:has-text("Export")',
                '[data-testid="export-button"]',
            ]

            for selector in export_selectors:
                try:
                    export_button = page.locator(selector).first
                    if export_button.is_visible(timeout=3000):
                        log(f"Found Export button with selector: {selector}")
                        break
                except:
                    continue

            if not export_button or not export_button.is_visible(timeout=5000):
                log("WARNING: Could not find Export button. The UI may have changed.")
                log("Taking screenshot for debugging...")
                screenshot_path = LOGS_DIR / f'export_not_found_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path), full_page=True)
                log(f"Screenshot saved: {screenshot_path}")
                browser.close()
                return None

            # Click Export button
            log("Clicking Export button...")
            export_button.click()
            time.sleep(2)

            # Wait for export dialog/dropdown
            # Look for CSV option or Download button
            csv_selectors = [
                'button:has-text("Download")',
                'div[role="menuitem"]:has-text("CSV")',
                'span:has-text("Download")',
                '[data-testid="download-csv"]',
            ]

            download_button = None
            for selector in csv_selectors:
                try:
                    download_button = page.locator(selector).first
                    if download_button.is_visible(timeout=3000):
                        log(f"Found Download button with selector: {selector}")
                        break
                except:
                    continue

            if download_button and download_button.is_visible(timeout=5000):
                # Set up download listener
                with page.expect_download(timeout=60000) as download_info:
                    download_button.click()
                    log("Waiting for download to start...")

                download = download_info.value

                # Save the downloaded file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_filename = f'meta_export_{timestamp}.csv'
                csv_path = EXPORTS_DIR / csv_filename

                download.save_as(str(csv_path))
                log(f"CSV downloaded successfully: {csv_path}")

                # Update config
                config['last_export_date'] = datetime.now().isoformat()
                save_config(config)

                browser.close()
                return csv_path
            else:
                log("WARNING: Could not find Download/CSV button in export dialog.")
                screenshot_path = LOGS_DIR / f'download_not_found_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path), full_page=True)
                log(f"Screenshot saved: {screenshot_path}")
                browser.close()
                return None

        except Exception as e:
            log(f"ERROR during CSV download: {str(e)}")
            try:
                screenshot_path = LOGS_DIR / f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path), full_page=True)
                log(f"Error screenshot saved: {screenshot_path}")
            except:
                pass
            browser.close()
            return None


def check_for_recent_downloads():
    """Check if there are recent CSV files in Downloads folder and move them"""
    log("Checking for recent CSV downloads in Downloads folder...")

    # Look for Meta Business Suite CSV files in Downloads
    recent_csvs = []
    for csv_file in DOWNLOADS_DIR.glob('*.csv'):
        # Check if file was modified in the last hour
        mod_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
        if datetime.now() - mod_time < timedelta(hours=1):
            # Check if it looks like a Meta export (contains date range in name)
            if any(x in csv_file.name.lower() for x in ['export', 'insight', 'content', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                recent_csvs.append(csv_file)

    if recent_csvs:
        log(f"Found {len(recent_csvs)} recent CSV file(s)")
        for csv_file in recent_csvs:
            dest_path = EXPORTS_DIR / csv_file.name
            if not dest_path.exists():
                shutil.move(str(csv_file), str(dest_path))
                log(f"Moved: {csv_file.name} -> exports/")
            else:
                log(f"Already exists: {csv_file.name}")
        return True

    return False


def main():
    parser = argparse.ArgumentParser(description='Auto-download CSV from Meta Business Suite')
    parser.add_argument('--setup', action='store_true', help='First-time setup - manual login')
    parser.add_argument('--test', action='store_true', help='Test mode - show browser')
    parser.add_argument('--check-downloads', action='store_true', help='Check Downloads folder for recent CSVs')
    args = parser.parse_args()

    if args.setup:
        success = setup_browser_session()
        sys.exit(0 if success else 1)

    if args.check_downloads:
        found = check_for_recent_downloads()
        sys.exit(0 if found else 1)

    if args.test:
        log("=== TEST MODE ===")
        csv_path = download_csv(headless=False, test_mode=True)
    else:
        csv_path = download_csv(headless=True, test_mode=False)

    if csv_path:
        log(f"SUCCESS: CSV downloaded to {csv_path}")
        sys.exit(0)
    else:
        log("FAILED: Could not download CSV")
        # Try checking downloads folder as fallback
        log("Checking Downloads folder for manual exports...")
        if check_for_recent_downloads():
            log("Found and moved manual CSV exports")
            sys.exit(0)
        sys.exit(1)


if __name__ == '__main__':
    main()
