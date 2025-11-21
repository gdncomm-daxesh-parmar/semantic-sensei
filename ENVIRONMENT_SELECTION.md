# Environment Selection in Visual Diff

## Overview
The Visual Diff now supports two environments: **Production** and **Lower Env**. This allows you to compare results between the production Blibli API and your local lower environment API.

---

## Environment Options

### 1. **Production** (Default)
- **API Endpoint:** `https://www.blibli.com/backend/search/products`
- **Use Case:** Compare control vs AI categories on live production data
- **Authentication:** Uses Blibli cookies and headers
- **Boost Params:** Not included (production doesn't support custom boost params)

### 2. **Lower Env**
- **API Endpoint:** `http://localhost:9090/search/products`
- **Use Case:** Test AI categories with custom boost values on local environment
- **Authentication:** No cookies required
- **Boost Params:** ✅ Included as `boostParam` query parameter

---

## Boost Parameter Format

When **Lower Env** is selected and AI categories are active, the system automatically builds a boost parameter string:

### Format
```
boostParam=code1:boost1,code2:boost2,code3:boost3
```

### Example
If you have these AI categories:
- Sepatu Sneaker Pria (SN-1000001) - Boost: 100
- Pakaian Lari Pria (PA-1000012) - Boost: 150
- Lifestyle Sporty (LI-1000049) - Boost: 120

The boost parameter will be:
```
boostParam=SN-1000001:100,PA-1000012:150,LI-1000049:120
```

---

## API Request Examples

### Production Environment

#### Control Request
```
GET https://www.blibli.com/backend/search/products?
  searchTerm=nike
  &page=1
  &start=0
  &merchantSearch=true
  &multiCategory=true
  &channelId=web
  ...
```

#### AI Categories Request (Boosting Mode)
```
GET https://www.blibli.com/backend/search/products?
  searchTerm=nike
  &category=SN-1000001
  &category=PA-1000012
  &category=LI-1000049
  &page=1
  ...
```

---

### Lower Env

#### Control Request
```
GET http://localhost:9090/search/products?
  searchTerm=nike
  &page=1
  &start=0
  &merchantSearch=true
  &multiCategory=true
  &channelId=web
  ...
```

#### AI Categories Request (Boosting Mode)
```
GET http://localhost:9090/search/products?
  searchTerm=nike
  &category=SN-1000001
  &category=PA-1000012
  &category=LI-1000049
  &boostParam=SN-1000001:100,PA-1000012:150,LI-1000049:120  ← NEW!
  &page=1
  ...
```

---

## UI Changes

### Environment Selector
A dropdown appears at the top of the Visual Diff dialog:

```
🌍 Environment: [Production ▼]
                [lowerEnv    ]
```

### Boost Parameter Display
When **Lower Env** is selected and categories are active, a blue info box shows:

```
📊 Boost Parameter: `SN-1000001:100,PA-1000012:150,LI-1000049:120`
```

### Column Headers Updated
Both columns now show the environment:

**Control:**
```
📦 Control Response
No category filters | 🌐 Production
```

**AI Categories:**
```
🤖 AI Category Response
With AI filters + Boost Params | 🧪 Lower Env
```

---

## Code Implementation

### UI Updates (`ui/app.py`)

```python
# Environment selector
environment = st.selectbox(
    "🌍 Environment",
    options=["production", "lowerEnv"],
    index=0,
    help="Production: Blibli API | Lower Env: localhost:9090 with boost params"
)

# Build boost parameter for lowerEnv
boost_param = None
if environment == "lowerEnv" and active_categories:
    boost_pairs = [f"{cat['code']}:{cat.get('boostValue', 100)}" 
                   for cat in active_categories]
    boost_param = ",".join(boost_pairs)

# Pass to fetch_products
control_products, control_error = fetch_products(
    term, 
    category_codes=None, 
    limit=40, 
    include_search_term=True,
    environment=environment,
    boost_param=None  # Control never uses boost params
)

ai_products, ai_error = fetch_products(
    term, 
    category_codes=category_codes, 
    limit=40, 
    include_search_term=include_search_term_in_ai,
    environment=environment,
    boost_param=boost_param  # Only for AI categories in lowerEnv
)
```

### Product Fetcher Updates (`utils/product_fetcher.py`)

```python
def fetch_products(search_term, category_codes=None, page=1, limit=20, 
                   include_search_term=True, environment="production", 
                   boost_param=None):
    # Choose base URL based on environment
    if environment == "lowerEnv":
        url = f"http://localhost:9090/search/products?..."
    else:
        url = f"https://www.blibli.com/backend/search/products?..."
    
    # Add searchTerm if needed
    if include_search_term:
        url += f"&searchTerm={encoded_term}"
    
    # Add category filters
    if category_codes:
        for code in category_codes:
            url += f"&category={code}"
    
    # Add boost parameter for lowerEnv
    if environment == "lowerEnv" and boost_param:
        url += f"&boostParam={boost_param}"
    
    # Make request (no cookies for lowerEnv)
    if environment == "lowerEnv":
        response = requests.get(url, headers=headers, timeout=10)
    else:
        response = requests.get(url, headers=headers, cookies=BLIBLI_COOKIES, timeout=10)
```

---

## Use Cases

### Use Case 1: Production Testing
**Scenario:** Compare live production results with AI categories  
**Environment:** Production  
**What happens:** Both requests go to Blibli API, boost params not sent

### Use Case 2: Local Development
**Scenario:** Test new boost values before deploying  
**Environment:** Lower Env  
**What happens:** Both requests go to localhost:9090, boost params included in AI request

### Use Case 3: Boost Value Tuning
**Scenario:** Adjust boost values in UI and immediately see results  
**Steps:**
1. Select "lowerEnv" environment
2. Edit category boost values in main UI
3. Click "Visualize diff" button
4. See results with new boost params applied
5. Iterate until satisfied

---

## Requirements

### For Lower Env to Work
You need a local API running at `http://localhost:9090` that:
1. Accepts the same query parameters as Blibli API
2. Supports the `boostParam` parameter
3. Returns products in the same JSON format

### Starting Lower Env API (Example)
```bash
# Assuming you have a local API server
cd /path/to/local-api
python server.py --port 9090
```

---

## Summary

| Feature | Production | Lower Env |
|---------|-----------|-----------|
| **API URL** | blibli.com | localhost:9090 |
| **Cookies** | ✅ Required | ❌ Not used |
| **Boost Params** | ❌ Not sent | ✅ Sent for AI request |
| **Use Case** | Live comparison | Development & testing |

The environment selection feature enables rapid iteration on boost values without touching production, while still allowing production validation when needed! 🚀

