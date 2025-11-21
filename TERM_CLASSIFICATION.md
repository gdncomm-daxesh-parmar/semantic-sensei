# 🔍 Search Term Classification System

## Overview

The system automatically classifies search terms into two types based on the relationship between **Catalog Categories** (from Blibli API) and **Model-Identified Categories** (from AI predictions).

---

## 🏷️ Classification Types

### **1. Boosting Configuration** 🎯

**Definition:** Terms where catalog and model categories have **overlapping categories**.

**Behavior:**
- Uses **searchTerm + category filters** in API calls
- Categories act as **boost signals** to improve existing results
- Enhances relevance of products already found by search term

**Example:**
```
Search Term: "nike shoes"
Catalog Categories: [SE-1000019, SE-1000027, SE-1000035]
Model Categories:   [SE-1000019, SE-1000050, SE-1000027]
Intersection:       [SE-1000019, SE-1000027] ✓
Result: boostingConfiguration
```

**API Call:**
```
GET /search/products?searchTerm=nike+shoes&category=SE-1000019&category=SE-1000027
```

---

### **2. Filter Configuration** 🔍

**Definition:** Terms where catalog and model categories have **no overlap**.

**Behavior:**
- Uses **only category filters** in API calls (no searchTerm)
- Categories act as **pure filters** to find products
- Discovers products outside the original search term scope

**Example:**
```
Search Term: "gift ideas"
Catalog Categories: [GF-1000001, GF-1000002]
Model Categories:   [TO-2000050, AC-3000100]
Intersection:       [] ✗
Result: filterConfiguration
```

**API Call:**
```
GET /search/products?category=TO-2000050&category=AC-3000100
(no searchTerm parameter)
```

---

## 🔄 Classification Logic

```python
def classify_term_type(term_doc):
    catalog_codes = {cat['code'] for cat in catalogCategories}
    model_codes = {cat['code'] for cat in modelIdentifiedCategories}
    
    intersection = catalog_codes & model_codes
    
    if intersection:
        return 'boostingConfiguration'  # Has overlap
    else:
        return 'filterConfiguration'    # No overlap
```

---

## 📊 Database Schema

Each term document includes:

```json
{
  "searchTerm": "nike shoes",
  "catalogCategories": [...],
  "modelIdentifiedCategories": [...],
  "termType": "boostingConfiguration",
  "termTypeClassifiedDate": "2024-11-20T15:30:00Z",
  "status": "in_progress",
  ...
}
```

**Fields:**
- `termType`: `"boostingConfiguration"` or `"filterConfiguration"`
- `termTypeClassifiedDate`: When the classification was computed

---

## 🚀 Running Classification

### **Classify All Terms (One-Time Setup)**

```bash
python scripts/classify_term_types.py --classify-all
```

**Output:**
```
======================================================================
Classifying Search Terms: Boosting vs Filter Configuration
======================================================================

Processing 3692 terms...
  Progress: 100/3692 terms processed...
  Progress: 200/3692 terms processed...
  ...

======================================================================
Classification Complete!
======================================================================

📊 Results:
  Total terms processed: 3692
  Updated terms: 3692
  🎯 Boosting Configuration: 2450 (66.4%)
  🔍 Filter Configuration: 1242 (33.6%)
```

### **Check Specific Term**

```bash
python scripts/classify_term_types.py --term "nike shoes"
```

**Output:**
```
======================================================================
Classification Details: 'nike shoes'
======================================================================

🏷️  Term Type: boostingConfiguration

📚 Catalog Categories (5):
    • SE-1000019 - Sepatu Lari
    • SE-1000027 - Sepatu Sepakbola
    • SE-1000035 - Sepatu Basket
    ... and 2 more

🤖 Model Identified Categories (4):
    • SE-1000019 - Sepatu Lari
    • SE-1000027 - Sepatu Sepakbola
    • SE-1000050 - Sepatu Training
    • AC-2000100 - Aksesoris Olahraga

🔗 Intersection (2):
    • SE-1000019 - Sepatu Lari
    • SE-1000027 - Sepatu Sepakbola
```

---

## 🔄 Automatic Re-classification

The system automatically re-classifies terms when categories change:

### **Triggers:**
1. ✅ **Adding a model category** (`add_model_category`)
2. ✅ **Removing a model category** (`remove_model_category`)
3. ✅ **Creating new live entries** (`save_live_entry`)

### **Process:**
```python
def reclassify_term_type(term):
    # Get current categories
    catalog_codes = set(...)
    model_codes = set(...)
    
    # Calculate new type
    intersection = catalog_codes & model_codes
    new_type = 'boostingConfiguration' if intersection else 'filterConfiguration'
    
    # Update if changed
    if current_type != new_type:
        update_database(term, new_type)
```

---

## 📈 Product Comparison Impact

### **In Product Comparison Dialog:**

**Control Side (Left):**
- Always uses `searchTerm` parameter
- Baseline behavior

**AI Categories Side (Right):**
- **If boostingConfiguration:** Uses `searchTerm + category filters`
- **If filterConfiguration:** Uses `only category filters` (no searchTerm)

**Code:**
```python
term_type = term_data.get('termType', 'filterConfiguration')
include_search_term = (term_type == 'boostingConfiguration')

ai_products = fetch_products(
    term, 
    category_codes=category_codes, 
    include_search_term=include_search_term
)
```

---

## 📝 Use Cases

### **Boosting Configuration Example**

**Search Term:** "samsung galaxy"
- Catalog has phone categories
- Model predicts phone categories  
- **Overlap exists** → Use searchTerm + categories
- **Result:** Better ranking of Samsung Galaxy phones

### **Filter Configuration Example**

**Search Term:** "birthday gift"
- Catalog has generic gift categories
- Model predicts specific product categories (toys, electronics)
- **No overlap** → Use only model categories
- **Result:** Discover relevant products beyond "birthday gift" term

---

## 🔧 Maintenance

### **Re-run Classification:**

If you bulk-update catalog or model categories:

```bash
python scripts/classify_term_types.py --classify-all
```

### **Verify Classification:**

Check distribution:
```bash
python scripts/classify_term_types.py --classify-all | grep "Boosting\|Filter"
```

---

## 🎯 Benefits

1. **⚡ Boosting:** Improves relevance for terms with good catalog coverage
2. **🔍 Filtering:** Discovers products for ambiguous/broad terms
3. **🤖 Automatic:** Classifies and re-classifies without manual intervention
4. **📊 Transparent:** Stored in database for analysis and debugging
5. **🚀 Optimized:** Different strategies for different term types

---

## 📌 Important Notes

- ✅ Classification runs **once** and is stored in database
- ✅ Automatically re-classifies when categories change
- ✅ **Not shown in UI** (internal logic only)
- ✅ Used in product comparison to optimize API calls
- ✅ New live entries are classified immediately

---

**Last Updated:** November 20, 2024

