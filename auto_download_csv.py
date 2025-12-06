"""
Auto-download CSV from Meta Business Suite using Playwright browser automation.

PYAUTOGUI MOUSE CLICK APPROACH: Uses OS-level mouse clicks via pyautogui to bypass
Meta's overlay protection that intercepts DOM events (clicks, keyboard).

The strategy:
1. Opens browser and navigates to Meta Business Suite Content Insights
2. Uses Playwright to locate elements and get their screen coordinates
3. Uses pyautogui to perform OS-level mouse clicks at those coordinates
4. This bypasses React's event system completely - pyautogui clicks are real mouse events
5. Waits for the CSV file to appear in Downloads folder
6. Copies the CSV to the exports/ folder

Usage:
    python auto_download_csv.py --setup    # First-time setup - manual login to save session
    python auto_download_csv.py --test     # Test CSV download (visible browser)
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

# Page name to select (case-insensitive match)
TARGET_PAGE_NAME = "Juan365 Live Stream"


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
        'export_days': 90,
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
            headless=False,
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


def get_element_screen_coords(page, element, log_func=None):
    """
    Get the screen coordinates of an element for pyautogui clicking.
    Returns (x, y) center of the element in screen coordinates.

    Uses CDP to get the exact content offset within the browser window.
    """
    # Get the element's bounding box relative to viewport
    bbox = element.bounding_box()
    if not bbox:
        return None

    # Get the browser window position and calculate viewport offset
    # The key is to get the ACTUAL content area position on screen
    window_info = page.evaluate('''() => {
        return {
            screenX: window.screenX || window.screenLeft || 0,
            screenY: window.screenY || window.screenTop || 0,
            outerWidth: window.outerWidth,
            outerHeight: window.outerHeight,
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight,
            // These give us the viewport offset within the window
            scrollX: window.scrollX || window.pageXOffset || 0,
            scrollY: window.scrollY || window.pageYOffset || 0,
            devicePixelRatio: window.devicePixelRatio || 1
        }
    }''')

    if log_func:
        log_func(f"Window info: screenX={window_info['screenX']}, screenY={window_info['screenY']}, "
                f"outer={window_info['outerWidth']}x{window_info['outerHeight']}, "
                f"inner={window_info['innerWidth']}x{window_info['innerHeight']}")

    # Calculate the browser chrome heights
    # Title bar + address bar + tabs + bookmarks bar is typically ~88-120px on Windows
    chrome_height = window_info['outerHeight'] - window_info['innerHeight']
    chrome_width = window_info['outerWidth'] - window_info['innerWidth']  # Usually small (border width)

    if log_func:
        log_func(f"Chrome offset: width={chrome_width}, height={chrome_height}")
        log_func(f"Element bbox: x={bbox['x']:.0f}, y={bbox['y']:.0f}, w={bbox['width']:.0f}, h={bbox['height']:.0f}")

    # Calculate screen coordinates
    # The element's bbox is relative to the viewport, so we need to add:
    # 1. Window screen position (where window starts on screen)
    # 2. Chrome width/height (offset from window edge to content area)
    # 3. Element position within viewport + half size to get center
    screen_x = window_info['screenX'] + (chrome_width // 2) + bbox['x'] + bbox['width'] / 2
    screen_y = window_info['screenY'] + chrome_height + bbox['y'] + bbox['height'] / 2

    if log_func:
        log_func(f"Calculated screen coords: ({int(screen_x)}, {int(screen_y)})")

    return (int(screen_x), int(screen_y))


def download_csv_pyautogui_method(headless=False, test_mode=False):
    """
    Download CSV using pyautogui OS-level mouse clicks to bypass overlay protection.

    IMPORTANT: This method requires headless=False because we need actual screen coordinates.
    pyautogui clicks at real screen positions, so the browser must be visible.

    Strategy:
    1. Use Playwright to navigate and locate elements (get their bounding boxes)
    2. Use pyautogui to perform OS-level mouse clicks at those screen coordinates
    3. This completely bypasses Meta's React event interception

    Returns path to downloaded CSV or None if failed.
    """
    try:
        from playwright.sync_api import sync_playwright
        import pyautogui
        # Disable pyautogui's fail-safe (moving mouse to corner stops script)
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1  # Small pause between actions
    except ImportError as e:
        log(f"ERROR: Missing dependency: {e}")
        log("Run: pip install playwright pyautogui && playwright install chromium")
        return None

    config = load_config()
    log("Starting CSV download using PYAUTOGUI mouse click method...")
    log("NOTE: Browser will be VISIBLE because pyautogui needs screen coordinates")

    # pyautogui requires visible browser - force headless=False
    if headless:
        log("WARNING: Forcing headless=False for pyautogui method")
        headless = False

    with sync_playwright() as p:
        # Launch browser with saved session - MUST be visible
        # Position window at top-left (0,0) for predictable coordinates
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_DATA_DIR),
            headless=False,  # MUST be visible for pyautogui
            viewport={'width': 1280, 'height': 900},
            accept_downloads=True,
            args=['--window-position=0,0']  # Position at top-left of screen
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

            log(f"Current URL: {page.url}")

            # Bring browser to foreground and ensure it's at top-left for pyautogui
            page.bring_to_front()
            time.sleep(0.5)

            # Move mouse to a neutral position first
            pyautogui.moveTo(100, 100)
            time.sleep(0.5)

            # Take screenshot for debugging
            if test_mode:
                screenshot_path = LOGS_DIR / f'pyag_step0_loaded_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path))
                log(f"Screenshot: {screenshot_path}")

            # Get list of existing CSVs before we trigger download
            existing_csvs = set(f.name for f in DOWNLOADS_DIR.glob('*.csv'))
            log(f"Existing CSVs in Downloads: {len(existing_csvs)}")

            # ============================================
            # STEP 1: Click the Export dropdown button using pyautogui
            # ============================================
            log("Step 1: Finding Export dropdown button...")

            dropdown_opened = False

            try:
                # Find all "Open Dropdown" buttons
                buttons = page.get_by_role("button", name="Open Dropdown").all()
                log(f"Found {len(buttons)} 'Open Dropdown' buttons")

                # Find the one near "Export data"
                target_btn = None
                for btn in buttons:
                    try:
                        # Check if this button is in a group with "Export data"
                        parent_group = btn.locator('xpath=ancestor::div[@role="group"]').first
                        if parent_group.count() > 0:
                            group_text = parent_group.text_content(timeout=1000) or ""
                            if "Export data" in group_text:
                                target_btn = btn
                                log("Found Export dropdown button!")
                                break
                    except:
                        continue

                if target_btn and target_btn.is_visible(timeout=3000):
                    # Get element bounding box for CDP click
                    bbox = target_btn.bounding_box()
                    if bbox:
                        center_x = bbox['x'] + bbox['width'] / 2
                        center_y = bbox['y'] + bbox['height'] / 2
                        log(f"Element center in viewport: ({center_x:.0f}, {center_y:.0f})")

                        # METHOD A: Use CDP Input.dispatchMouseEvent for raw input simulation
                        log("Trying CDP raw mouse input...")
                        try:
                            cdp = page.context.new_cdp_session(page)

                            # Dispatch mousePressed event
                            cdp.send('Input.dispatchMouseEvent', {
                                'type': 'mousePressed',
                                'x': center_x,
                                'y': center_y,
                                'button': 'left',
                                'clickCount': 1
                            })
                            time.sleep(0.1)

                            # Dispatch mouseReleased event
                            cdp.send('Input.dispatchMouseEvent', {
                                'type': 'mouseReleased',
                                'x': center_x,
                                'y': center_y,
                                'button': 'left',
                                'clickCount': 1
                            })
                            time.sleep(1.5)

                            # Check if menu opened
                            menu = page.locator('div[role="menu"]')
                            if menu.is_visible(timeout=3000):
                                dropdown_opened = True
                                log("SUCCESS: Menu opened with CDP mouse event!")
                        except Exception as e:
                            log(f"CDP method error: {str(e)[:60]}")

                        # METHOD B: Try pyautogui if CDP didn't work
                        if not dropdown_opened:
                            log("CDP didn't work, trying pyautogui...")
                            coords = get_element_screen_coords(page, target_btn, log_func=log)
                            if coords:
                                log(f"Pyautogui coords: {coords}")

                                # Ensure window is focused
                                page.bring_to_front()
                                time.sleep(0.3)

                                # Move to position first, then click
                                pyautogui.moveTo(coords[0], coords[1], duration=0.2)
                                time.sleep(0.2)
                                pyautogui.click()
                                time.sleep(1.5)

                                menu = page.locator('div[role="menu"]')
                                if menu.is_visible(timeout=3000):
                                    dropdown_opened = True
                                    log("SUCCESS: Menu opened with pyautogui!")
                                else:
                                    log("pyautogui click didn't open menu")
                    else:
                        log("Could not get bounding box for dropdown button")
                else:
                    log("Could not find visible Export dropdown button")

            except Exception as e:
                log(f"Step 1 error: {str(e)[:80]}")

            if test_mode:
                screenshot_path = LOGS_DIR / f'pyag_step1_dropdown_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path))
                log(f"Screenshot: {screenshot_path}")

            if not dropdown_opened:
                log("ERROR: Could not open the dropdown menu")
                browser.close()
                return None

            # ============================================
            # STEP 2: Click on completed export using pyautogui
            # ============================================
            log("Step 2: Finding and clicking completed export...")

            download_triggered = False

            try:
                time.sleep(0.5)

                # Find menu items
                menu_items = page.locator('div[role="menuitem"]').all()
                log(f"Found {len(menu_items)} menu items")

                # Look for completed export
                for i, item in enumerate(menu_items):
                    try:
                        text = item.text_content(timeout=1000) or ""
                        log(f"Menu item {i}: {text[:60]}...")

                        if 'Completed' in text and '100%' in text:
                            log(f"Found completed export at index {i}!")

                            # Get bounding box for CDP click
                            item_bbox = item.bounding_box()
                            if item_bbox:
                                # Click on the LEFT side where the download icon is (not center)
                                # The download icon is typically 20-30px from the left edge
                                item_click_x = item_bbox['x'] + 25  # Click on download icon area
                                item_center_y = item_bbox['y'] + item_bbox['height'] / 2
                                log(f"Menu item bbox: x={item_bbox['x']:.0f}, y={item_bbox['y']:.0f}, w={item_bbox['width']:.0f}")
                                log(f"Click position (left side for icon): ({item_click_x:.0f}, {item_center_y:.0f})")

                                # Use CDP to click the menu item (same method that worked for dropdown)
                                log("Clicking menu item with CDP...")
                                try:
                                    cdp = page.context.new_cdp_session(page)

                                    # Dispatch mousePressed event
                                    cdp.send('Input.dispatchMouseEvent', {
                                        'type': 'mousePressed',
                                        'x': item_click_x,
                                        'y': item_center_y,
                                        'button': 'left',
                                        'clickCount': 1
                                    })
                                    time.sleep(0.1)

                                    # Dispatch mouseReleased event
                                    cdp.send('Input.dispatchMouseEvent', {
                                        'type': 'mouseReleased',
                                        'x': item_click_x,
                                        'y': item_center_y,
                                        'button': 'left',
                                        'clickCount': 1
                                    })
                                    time.sleep(2)

                                    download_triggered = True
                                    log("CDP click sent on menu item (left side for icon)!")
                                except Exception as e:
                                    log(f"CDP menu click error: {str(e)[:60]}")
                                break
                            else:
                                log("Could not get bounding box for menu item")
                    except Exception as e:
                        log(f"Menu item {i} error: {str(e)[:40]}")
                        continue

            except Exception as e:
                log(f"Step 2 error: {str(e)[:80]}")

            if test_mode:
                screenshot_path = LOGS_DIR / f'pyag_step2_after_click_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path))
                log(f"Screenshot: {screenshot_path}")

            # ============================================
            # STEP 3: Wait for download
            # ============================================
            log("Step 3: Waiting for CSV file to download...")

            csv_path = None
            max_wait = 60  # seconds
            poll_interval = 2  # seconds

            for i in range(max_wait // poll_interval):
                time.sleep(poll_interval)

                # Check for new CSVs
                current_csvs = set(f.name for f in DOWNLOADS_DIR.glob('*.csv'))
                new_csvs = current_csvs - existing_csvs

                if new_csvs:
                    # Found new CSV file(s)
                    for new_csv in new_csvs:
                        csv_file = DOWNLOADS_DIR / new_csv
                        # Check if it looks like a Meta export
                        name_lower = new_csv.lower()
                        if any(month in name_lower for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                                                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']) or \
                           '_' in new_csv:
                            log(f"Found new CSV: {new_csv}")
                            csv_path = csv_file
                            break

                if csv_path:
                    break

                log(f"Waiting for download... ({(i+1) * poll_interval}s)")

            if not csv_path:
                log("WARNING: No new CSV in Downloads folder")
                log("Checking browser's download location...")

                # Try checking the browser's default download path
                # Also check .playwright-mcp folder
                playwright_downloads = Path.home() / 'AppData' / 'Local' / 'Programs' / 'Git' / '.playwright-mcp'
                if playwright_downloads.exists():
                    pw_csvs = set(f.name for f in playwright_downloads.glob('*.csv'))
                    for csv_name in pw_csvs:
                        csv_file = playwright_downloads / csv_name
                        mod_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
                        if datetime.now() - mod_time < timedelta(minutes=5):
                            log(f"Found recent CSV in playwright folder: {csv_name}")
                            csv_path = csv_file
                            break

            if not csv_path:
                log("ERROR: No new CSV file found")
                screenshot_path = LOGS_DIR / f'pyag_error_no_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path))
                browser.close()
                return None

            # ============================================
            # STEP 4: Copy to exports folder
            # ============================================
            log("Step 4: Copying CSV to exports folder...")

            dest_filename = csv_path.name.replace('-', '_')
            dest_path = EXPORTS_DIR / dest_filename

            if dest_path.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                stem = dest_path.stem
                dest_path = EXPORTS_DIR / f"{stem}_{timestamp}.csv"

            shutil.copy(str(csv_path), str(dest_path))
            log(f"CSV copied to: {dest_path}")

            # Update config
            config['last_export_date'] = datetime.now().isoformat()
            save_config(config)

            browser.close()
            return dest_path

        except Exception as e:
            log(f"ERROR during CSV download: {str(e)}")
            try:
                screenshot_path = LOGS_DIR / f'pyag_error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                page.screenshot(path=str(screenshot_path), full_page=True)
                log(f"Error screenshot saved: {screenshot_path}")
            except:
                pass
            browser.close()
            return None


def check_for_recent_downloads():
    """Check if there are recent CSV files in Downloads folder and move them"""
    log("Checking for recent CSV downloads...")

    recent_csvs = []

    # Check standard Downloads folder
    for csv_file in DOWNLOADS_DIR.glob('*.csv'):
        mod_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
        if datetime.now() - mod_time < timedelta(hours=1):
            name_lower = csv_file.name.lower()
            if any(x in name_lower for x in ['export', 'insight', 'content', 'juan365',
                                              'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                recent_csvs.append(csv_file)

    # Also check playwright downloads folder
    playwright_downloads = Path.home() / 'AppData' / 'Local' / 'Programs' / 'Git' / '.playwright-mcp'
    if playwright_downloads.exists():
        for csv_file in playwright_downloads.glob('*.csv'):
            mod_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
            if datetime.now() - mod_time < timedelta(hours=1):
                recent_csvs.append(csv_file)

    if recent_csvs:
        log(f"Found {len(recent_csvs)} recent CSV file(s)")
        for csv_file in recent_csvs:
            dest_name = csv_file.name.replace('-', '_')
            dest_path = EXPORTS_DIR / dest_name
            if not dest_path.exists():
                shutil.copy(str(csv_file), str(dest_path))
                log(f"Copied: {csv_file.name} -> exports/{dest_name}")
            else:
                log(f"Already exists: {dest_name}")
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

    # Use pyautogui method (always visible browser - required for coordinate-based clicking)
    if args.test:
        log("=== TEST MODE (pyautogui mouse clicks) ===")
    else:
        log("=== PYAUTOGUI METHOD (browser will be visible) ===")

    csv_path = download_csv_pyautogui_method(headless=False, test_mode=args.test)

    if csv_path:
        log(f"SUCCESS: CSV downloaded to {csv_path}")
        sys.exit(0)
    else:
        log("FAILED: pyautogui method did not work")
        log("Checking for recent downloads as fallback...")
        if check_for_recent_downloads():
            log("Found and moved recent CSV exports")
            sys.exit(0)
        sys.exit(1)


if __name__ == '__main__':
    main()
