"""
Juan365 Facebook API Configuration Template

INSTRUCTIONS:
1. Copy this file and rename to: config.py
2. Replace the placeholder values with your actual Facebook credentials
3. Never commit config.py to git (it's in .gitignore)

HOW TO GET THESE VALUES:
1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app and page
3. Generate a Page Access Token
4. Convert to Long-Lived Token (lasts 60+ days)
"""

# Your Facebook Page ID
# Find it at: https://www.facebook.com/YOUR_PAGE/about (or in Page Settings)
PAGE_ID = "YOUR_PAGE_ID_HERE"

# Your Page Access Token (Long-Lived, never expires for page tokens)
# Get it from Graph API Explorer: https://developers.facebook.com/tools/explorer/
PAGE_TOKEN = "YOUR_PAGE_ACCESS_TOKEN_HERE"

# Facebook Graph API Base URL (don't change)
BASE_URL = "https://graph.facebook.com/v21.0"
