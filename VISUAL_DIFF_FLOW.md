# Visual Diff - Search Term Flow Documentation

## Overview
The Visual Diff feature compares product results between two scenarios to show the impact of AI category predictions on search results.

---

## Two Scenarios Compared

### 1. **Control (Left Side)**
- **Purpose:** Show baseline results without AI intervention
- **Configuration:**
  - ✅ `searchTerm` is **ALWAYS included**
  - ❌ No category filters applied
  - 🎯 Represents: "What users see with current search"

**API Call:**
```
https://www.blibli.com/backend/search/products?
  searchTerm=nike          ← ALWAYS INCLUDED
  &page=1
  &start=0
  ...other params
```

---

### 2. **AI Categories (Right Side)**
- **Purpose:** Show results with AI-predicted categories applied
- **Configuration:** **DEPENDS ON TERM TYPE**

#### Case A: `boostingConfiguration` (Has Category Intersection)
**When:** Catalog categories ∩ Model categories ≠ ∅
- ✅ `searchTerm` is **INCLUDED** 
- ✅ Category filters applied
- 🎯 Represents: "Boost existing search results with category relevance"

**API Call:**
```
https://www.blibli.com/backend/search/products?
  searchTerm=nike          ← INCLUDED (boost mode)
  &category=SN-1000001
  &category=PA-1000012
  &page=1
  ...other params
```

#### Case B: `filterConfiguration` (No Category Intersection)
**When:** Catalog categories ∩ Model categories = ∅
- ❌ `searchTerm` is **EXCLUDED**
- ✅ Category filters applied
- 🎯 Represents: "Pure category filtering, ignore user's search term"

**API Call:**
```
https://www.blibli.com/backend/search/products?
  (NO searchTerm parameter)   ← EXCLUDED (filter mode)
  &category=PA-1000047
  &category=PA-1000048
  &page=1
  ...other params
```

---

## Code Implementation

### Where Term Type is Determined
**File:** `ui/app.py`
**Function:** `show_product_comparison_dialog(term)`

```python
# Line 889 - Get term type from database
term_type = term_data.get('termType', 'filterConfiguration')

# Line 893-894 - Control always includes searchTerm
control_products, control_error = fetch_products(
    term, 
    category_codes=None, 
    limit=40, 
    include_search_term=True  # ← ALWAYS TRUE for Control
)

# Line 896-900 - AI Categories behavior depends on termType
include_search_term_in_ai = (term_type == 'boostingConfiguration')
ai_products, ai_error = fetch_products(
    term, 
    category_codes=category_codes, 
    limit=40, 
    include_search_term=include_search_term_in_ai  # ← TRUE only if boosting
)
```

### Where searchTerm is Applied
**File:** `utils/product_fetcher.py`
**Function:** `fetch_products(..., include_search_term=True)`

```python
# Line 70-72 - Conditionally add searchTerm to URL
if include_search_term:
    encoded_term = urllib.parse.quote(search_term)
    url += f"&searchTerm={encoded_term}"
```

---

## Term Classification Logic

### When is a term classified as `boostingConfiguration`?

**File:** `ui/app.py`
**Function:** `reclassify_term_type(search_term)`

```python
# Extract category codes from both sources
catalog_codes = set(cat['code'] for cat in catalog_categories if 'code' in cat)
model_codes = set(cat['code'] for cat in model_categories if 'code' in cat)

# Check for intersection
intersection = catalog_codes & model_codes

if intersection:
    term_type = 'boostingConfiguration'  # Has overlap → boost mode
else:
    term_type = 'filterConfiguration'    # No overlap → filter mode
```

### Classification is Stored in MongoDB
- **Collection:** `search_term_categories`
- **Field:** `termType`
- **Values:** 
  - `"boostingConfiguration"` - searchTerm will be included in AI API call
  - `"filterConfiguration"` - searchTerm will be excluded in AI API call

---

## Examples

### Example 1: "nike" (Boosting Configuration)
**Catalog Categories:** Shoes, Sportswear  
**Model Categories:** Shoes, Apparel, Accessories  
**Intersection:** ✅ YES (Shoes is in both)  
**Result:** `termType = 'boostingConfiguration'`

**Visual Diff:**
- **Control:** `searchTerm=nike` (no categories)
- **AI Categories:** `searchTerm=nike` + `category=SN-1000001&category=PA-1000012`

---

### Example 2: "eser" (Filter Configuration)
**Catalog Categories:** (none found in product catalog)  
**Model Categories:** Parfum Wanita, Parfum Pria  
**Intersection:** ❌ NO  
**Result:** `termType = 'filterConfiguration'`

**Visual Diff:**
- **Control:** `searchTerm=eser` (no categories)
- **AI Categories:** (NO searchTerm) + `category=PA-1000047&category=PA-1000048`

---

## Why This Design?

### Boosting Configuration
- User's search intent is **clear and mappable** to existing catalog
- AI categories **enhance** existing results by adding relevance scoring
- Keep searchTerm to maintain user's original intent

### Filter Configuration  
- User's search term is **not found** in catalog (typo, brand name, slang)
- AI can infer correct category but catalog doesn't recognize the term
- **Ignore** searchTerm and use pure category filtering to find relevant products

---

## Visual Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                      VISUAL DIFF FLOW                           │
└─────────────────────────────────────────────────────────────────┘

User searches: "nike"
        ↓
MongoDB lookup: search_term_categories
        ↓
Read: termType = 'boostingConfiguration'
        ↓
┌───────────────────────────┬───────────────────────────────────┐
│    CONTROL (Left)         │    AI CATEGORIES (Right)          │
├───────────────────────────┼───────────────────────────────────┤
│ searchTerm = "nike" ✓     │ searchTerm = "nike" ✓             │
│ categories = None         │ categories = [SN-1000001, ...]    │
│                           │                                   │
│ Shows: Baseline results   │ Shows: Boosted results            │
└───────────────────────────┴───────────────────────────────────┘

User searches: "eser"
        ↓
MongoDB lookup: search_term_categories
        ↓
Read: termType = 'filterConfiguration'
        ↓
┌───────────────────────────┬───────────────────────────────────┐
│    CONTROL (Left)         │    AI CATEGORIES (Right)          │
├───────────────────────────┼───────────────────────────────────┤
│ searchTerm = "eser" ✓     │ searchTerm = (excluded) ✗         │
│ categories = None         │ categories = [PA-1000047, ...]    │
│                           │                                   │
│ Shows: No results         │ Shows: Perfume products           │
└───────────────────────────┴───────────────────────────────────┘
```

---

## Key Takeaways

1. **Control ALWAYS uses searchTerm** - This is the baseline for comparison
2. **AI Categories conditionally uses searchTerm** - Based on `termType` field in MongoDB
3. **termType is auto-calculated** - When categories are added/removed/saved
4. **Classification is persistent** - Stored in MongoDB, not calculated on-the-fly during visual diff
5. **Two distinct use cases:**
   - **Boosting:** searchTerm + categories (enhance existing results)
   - **Filtering:** categories only (find products when search fails)

