# Juan365 Token Update Guide (5 minutes)

## When Token Expires
Token expires ~every 60 days. You'll see error: "Session has expired"

---

## QUICK STEPS (5 min total)

### Step 1: Get New User Token (2 min)
1. Go to: https://developers.facebook.com/tools/explorer/
2. Select App: **Juan365 Livestream**
3. Click **Generate Access Token**
4. Permissions needed: `pages_show_list`, `pages_read_engagement`, `pages_read_user_content`
5. Copy the token

### Step 2: Convert to Page Token (1 min)
Run this in browser console or give to Claude:
```
GET https://graph.facebook.com/v21.0/481447078389174?fields=access_token&access_token={USER_TOKEN}
```
Copy the `access_token` from response.

### Step 3: Update config.py (30 sec)
```python
PAGE_TOKEN = "paste_new_token_here"
```

### Step 4: Fetch Fresh Data (10 min)
```bash
cd C:\Users\us\Desktop\juan365_livestream_project
python fetch_all_historical.py
```

### Step 5: Push to GitHub (30 sec)
```bash
git add api_cache/
git commit -m "Update engagement data"
git push
```

---

## ONE-LINER FOR CLAUDE

```
Update Juan365 token. New user token: [PASTE TOKEN]
Project: C:\Users\us\Desktop\juan365_livestream_project
Page ID: 481447078389174
```

---

## Files Reference
| File | Purpose |
|------|---------|
| `config.py` | Contains PAGE_TOKEN |
| `fetch_all_historical.py` | Fetches all posts + reactions |
| `api_cache/posts.json` | Cached post data |

---

## Token Expiry Dates
| Date Updated | Expires (~60 days) |
|--------------|-------------------|
| 2025-12-09 | ~Feb 7, 2026 |

---

## Streamlit Cloud
- URL: https://juan365livestream.streamlit.app
- Auto-deploys from GitHub (no manual action needed)
- Secrets: Update PAGE_TOKEN in Streamlit Cloud Settings if using secrets
