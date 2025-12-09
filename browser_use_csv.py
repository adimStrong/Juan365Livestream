"""
Browser-Use AI-powered CSV Download from Meta Business Suite

This script uses browser-use with Claude to intelligently navigate
Meta Business Suite and download the CSV export.

Usage:
    python browser_use_csv.py
"""
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Set up paths
PROJECT_DIR = Path(__file__).parent
LOGS_DIR = PROJECT_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
BROWSER_DATA_DIR = PROJECT_DIR / 'automation' / 'browser_data'
DOWNLOADS_DIR = Path.home() / 'Downloads'

# Meta Business Suite URL
META_INSIGHTS_URL = "https://business.facebook.com/latest/insights/content"


async def download_csv_with_ai():
    """Use browser-use AI agent to download CSV from Meta Business Suite"""

    try:
        from browser_use import Agent
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install browser-use langchain-anthropic")
        return False

    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: set ANTHROPIC_API_KEY=your-key-here")
        return False

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting browser-use AI agent...")

    # Initialize the LLM
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=api_key,
        timeout=120,
        max_tokens=4096
    )

    # Create the task description
    task = f"""
    Navigate to Meta Business Suite Content Insights and download a CSV export.

    Steps:
    1. Go to: {META_INSIGHTS_URL}
    2. Wait for the page to load completely
    3. Click on "Export data" or "Export" button (usually in the top right area)
    4. In the Export dialog:
       - Select "Facebook" tab if not already selected
       - Click on the "Pages" dropdown and select "Juan365 Live Stream" (or similar page name)
       - Make sure "Metric presets" shows "Published" or similar
       - Select "Post" under "Content level"
       - Click the "Generate" button
    5. Wait for the CSV to be generated and downloaded
    6. Report success or any errors encountered

    Important:
    - The page may have overlay elements - you may need to click directly on dropdowns
    - The "Pages" dropdown is required - the Generate button stays disabled without a page selected
    - Take your time and verify each step before proceeding
    """

    try:
        # Create the agent
        agent = Agent(
            task=task,
            llm=llm,
            use_vision=True,  # Use vision to understand the page
        )

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running AI agent...")

        # Run the agent
        result = await agent.run()

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Agent completed!")
        print(f"Result: {result}")

        return True

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    print("=" * 60)
    print("Browser-Use AI CSV Download")
    print("=" * 60)
    print()

    # Check if we have the API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        # Try to load from .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except:
            pass

    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("ANTHROPIC_API_KEY not found!")
        print()
        print("Please set your Anthropic API key:")
        print("  Windows CMD:   set ANTHROPIC_API_KEY=sk-ant-...")
        print("  PowerShell:    $env:ANTHROPIC_API_KEY='sk-ant-...'")
        print("  Or add to .env file: ANTHROPIC_API_KEY=sk-ant-...")
        return

    # Run the async function
    success = asyncio.run(download_csv_with_ai())

    if success:
        print("\nCSV download completed successfully!")
    else:
        print("\nCSV download failed. Check the logs above for details.")


if __name__ == "__main__":
    main()
