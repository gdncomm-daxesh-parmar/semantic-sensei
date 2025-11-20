# Configuration Files

## Blibli API Configuration

### File: `blibli_api.py`

This file contains the headers and cookies required for accessing Blibli.com APIs.

### When to Update

Update this file when you see errors like:
- `403 Forbidden`
- `401 Unauthorized`
- API returns empty responses

These usually indicate that cookies have expired.

### How to Update Cookies

#### Step 1: Open Browser
Open Chrome or Brave browser and go to https://www.blibli.com

#### Step 2: Open Developer Tools
- Press `F12` or `Cmd+Option+I` (Mac)
- Go to the **Network** tab

#### Step 3: Search for Something
- Type any search term in Blibli's search box
- Press Enter to search

#### Step 4: Find the API Request
- In Network tab, filter by "Fetch/XHR"
- Look for request to `/backend/search/products`
- Click on it

#### Step 5: Copy as cURL
- Right-click on the request
- Select **Copy → Copy as cURL**

#### Step 6: Extract Cookies
The cURL command will look like:
```bash
curl 'https://www.blibli.com/backend/search/products?...' \
  -H 'accept: application/json' \
  --cookie 'Blibli-User-Id=xxx; Blibli-Session-Id=yyy; ...'
```

#### Step 7: Update blibli_api.py
Copy the cookies from the `--cookie` line and update `BLIBLI_COOKIES` dictionary:

```python
BLIBLI_COOKIES = {
    'Blibli-User-Id': 'xxx',
    'Blibli-Session-Id': 'yyy',
    'Blibli-Signature': 'zzz',
    # ... rest of cookies
}
```

### Files Using This Config

All these files will automatically use the updated cookies:
- `utils/product_fetcher.py` - Product fetching for UI
- `scrapper/fetchTermToCategoryMapping.py` - Category mapping scraper
- `preprocess/fetchC3Categories.py` - C3 category fetcher

### Need Help?

If you're still getting errors after updating:
1. Make sure you're logged out of Blibli (cookies work better for guest users)
2. Clear browser cache
3. Try from an incognito/private window
4. Get fresh cookies using the steps above

