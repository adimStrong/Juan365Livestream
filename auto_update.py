"""
Master Auto-Update Script for Juan365 Livestream Dashboard

This script orchestrates the complete data update workflow:
1. Fetch API data (posts, reactions, videos, reels)
2. Download CSV from Meta Business Suite (optional)
3. Merge CSV files
4. Commit and push to GitHub
5. Streamlit Cloud auto-deploys

Usage:
    python auto_update.py              # Full update (API + CSV + Git)
    python auto_update.py --api-only   # API data only (skip CSV)
    python auto_update.py --no-push    # Don't push to GitHub
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Project directory
PROJECT_DIR = Path(__file__).parent
LOGS_DIR = PROJECT_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Log file
LOG_FILE = LOGS_DIR / 'auto_update.log'


def log(message, level='INFO'):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] [{level}] {message}"
    print(log_message)

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')


def run_script(script_name, description=None):
    """Run a Python script and return success status"""
    script_path = PROJECT_DIR / script_name
    desc = description or script_name

    if not script_path.exists():
        log(f"Script not found: {script_path}", 'WARNING')
        return False

    log(f"Running: {desc}...")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per script
        )

        if result.returncode == 0:
            log(f"SUCCESS: {desc}")
            if result.stdout.strip():
                # Log last few lines of output
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines[-5:]:
                    log(f"  > {line}")
            return True
        else:
            log(f"FAILED: {desc} (exit code: {result.returncode})", 'ERROR')
            if result.stderr.strip():
                log(f"  Error: {result.stderr.strip()[:200]}", 'ERROR')
            return False

    except subprocess.TimeoutExpired:
        log(f"TIMEOUT: {desc} exceeded 10 minutes", 'ERROR')
        return False
    except Exception as e:
        log(f"EXCEPTION running {desc}: {str(e)}", 'ERROR')
        return False


def run_command(cmd, description=None):
    """Run a shell command and return success status"""
    desc = description or cmd[0]
    log(f"Running: {desc}...")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=120,
            shell=True if isinstance(cmd, str) else False
        )

        if result.returncode == 0:
            log(f"SUCCESS: {desc}")
            return True
        else:
            log(f"FAILED: {desc}", 'ERROR')
            if result.stderr.strip():
                log(f"  Error: {result.stderr.strip()[:200]}", 'ERROR')
            return False

    except Exception as e:
        log(f"EXCEPTION: {str(e)}", 'ERROR')
        return False


def fetch_api_data():
    """Fetch all API data"""
    log("=" * 60)
    log("STEP 1: FETCHING API DATA")
    log("=" * 60)

    success = True

    # Run API fetcher scripts in order
    scripts = [
        ('api_fetcher.py', 'Fetch page info, posts, videos'),
        ('refresh_api_cache.py', 'Refresh API cache'),
        ('fetch_all_historical.py', 'Fetch historical posts with reactions'),
        ('fetch_reels.py', 'Fetch reels'),
    ]

    for script, desc in scripts:
        if not run_script(script, desc):
            success = False
            log(f"Warning: {script} failed, continuing...", 'WARNING')

    return success


def download_csv():
    """Download CSV from Meta Business Suite"""
    log("=" * 60)
    log("STEP 2: DOWNLOADING CSV FROM META BUSINESS SUITE")
    log("=" * 60)

    # First check if there are recent manual downloads
    result = run_script('auto_download_csv.py', 'Download CSV (browser automation)')

    if not result:
        log("CSV download failed. Dashboard will use API data only.", 'WARNING')
        log("To fix: Run 'python auto_download_csv.py --setup' to set up browser session", 'WARNING')

    return result


def merge_csv():
    """Merge CSV files"""
    log("=" * 60)
    log("STEP 3: MERGING CSV FILES")
    log("=" * 60)

    return run_script('merge_exports.py', 'Merge CSV exports')


def git_push():
    """Commit and push changes to GitHub"""
    log("=" * 60)
    log("STEP 4: PUSHING TO GITHUB")
    log("=" * 60)

    # Check for changes
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True
    )

    if not result.stdout.strip():
        log("No changes to commit")
        return True

    # Stage changes
    files_to_add = [
        'api_cache/',
        'data/posts.json',
        'data/reels.json',
        'exports/',
    ]

    for file_pattern in files_to_add:
        run_command(['git', 'add', file_pattern], f'Stage {file_pattern}')

    # Create commit message
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    commit_message = f"Auto-update: {timestamp}"

    # Commit
    if not run_command(['git', 'commit', '-m', commit_message], 'Create commit'):
        log("Commit failed or nothing to commit")
        return False

    # Push
    if not run_command(['git', 'push', 'origin', 'main'], 'Push to GitHub'):
        log("Push failed. Will retry next cycle.", 'ERROR')
        return False

    log("Successfully pushed to GitHub!")
    log("Streamlit Cloud will auto-deploy in ~1-2 minutes")
    return True


def main():
    parser = argparse.ArgumentParser(description='Auto-update Juan365 Livestream Dashboard')
    parser.add_argument('--api-only', action='store_true', help='Skip CSV download')
    parser.add_argument('--no-push', action='store_true', help='Skip git push')
    parser.add_argument('--no-csv', action='store_true', help='Skip CSV download (alias for --api-only)')
    args = parser.parse_args()

    skip_csv = args.api_only or args.no_csv
    skip_push = args.no_push

    # Start
    log("")
    log("=" * 60)
    log("JUAN365 LIVESTREAM AUTO-UPDATE STARTED")
    log("=" * 60)
    log(f"Project: {PROJECT_DIR}")
    log(f"Options: API-only={skip_csv}, No-push={skip_push}")
    log("")

    start_time = datetime.now()
    results = {
        'api': False,
        'csv': False,
        'merge': False,
        'push': False
    }

    try:
        # Step 1: Fetch API data
        results['api'] = fetch_api_data()

        # Step 2: Download CSV (optional)
        if not skip_csv:
            results['csv'] = download_csv()
        else:
            log("Skipping CSV download (--api-only or --no-csv)")
            results['csv'] = True

        # Step 3: Merge CSV
        if results['csv'] or not skip_csv:
            results['merge'] = merge_csv()
        else:
            results['merge'] = True

        # Step 4: Git push (optional)
        if not skip_push:
            results['push'] = git_push()
        else:
            log("Skipping git push (--no-push)")
            results['push'] = True

    except Exception as e:
        log(f"FATAL ERROR: {str(e)}", 'ERROR')
        import traceback
        log(traceback.format_exc(), 'ERROR')

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    log("")
    log("=" * 60)
    log("AUTO-UPDATE COMPLETE")
    log("=" * 60)
    log(f"Duration: {duration:.1f} seconds")
    log(f"Results:")
    log(f"  API Data:    {'OK' if results['api'] else 'FAILED'}")
    log(f"  CSV Download: {'OK' if results['csv'] else 'FAILED'}")
    log(f"  CSV Merge:   {'OK' if results['merge'] else 'FAILED'}")
    log(f"  Git Push:    {'OK' if results['push'] else 'FAILED'}")
    log("")

    # Exit with appropriate code
    all_success = all(results.values())
    if all_success:
        log("All steps completed successfully!")
        sys.exit(0)
    else:
        log("Some steps failed. Check logs for details.", 'WARNING')
        sys.exit(1)


if __name__ == '__main__':
    main()
