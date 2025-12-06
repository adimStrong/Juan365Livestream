@echo off
echo ============================================================
echo           JUAN365 DATA REFRESH (Facebook API)
echo ============================================================
echo.
cd /d "%~dp0"

echo [1/3] Fetching latest posts, videos, stories...
python api_fetcher.py
python refresh_api_cache.py

echo.
echo [2/3] Updating historical reaction breakdown...
echo       (This fetches like/love/haha/wow/sad/angry for new posts)
python fetch_historical_reactions.py

echo.
echo ============================================================
echo [3/3] DATA REFRESH COMPLETE!
echo ============================================================
echo.
echo Files updated:
echo   - api_cache/posts.json (all posts)
echo   - api_cache/videos.json (video views)
echo   - api_cache/stories.json (stories)
echo   - api_cache/page_info.json (followers, rating)
echo   - api_cache/posts_reactions_full.json (reaction breakdown)
echo.
echo To deploy to Streamlit Cloud:
echo   git add api_cache/ && git commit -m "Update data" && git push
echo.
echo Refresh browser: http://localhost:8501
echo.
pause
