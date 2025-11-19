# 🚀 Quick Start Guide

## Launch the UI in 3 Steps

### Step 1: Ensure Dependencies
```bash
pip3 install streamlit pandas pymongo
```

### Step 2: Launch the Application
```bash
./run_ui.sh
```

Or directly:
```bash
streamlit run ui/app.py
```

### Step 3: Open Browser
The UI will automatically open at: **http://localhost:8501**

---

## 🎯 Using the UI

### **Search for a Term**
1. Type in the search box on the left sidebar
   - Example: `adidas`, `nike`, `iphone`
2. Click on any result to view details

### **View Categories**
- **Tab 1: View Categories**
  - See catalog categories (left) and model predictions (right)
  - Compare what's in the catalog vs what the model identified

### **Edit Boost Values**
- **Tab 2: Edit Boost Values**
  - Adjust boost values (0-1000) for model predictions
  - Higher boost = more weight in search results
  - Click Save to apply changes

### **Add or Remove Categories**
- **Tab 3: Add/Remove Categories**
  - **Left side**: Add new model categories
    - Select from dropdown (2,023 options)
    - Set score and boost value
    - Click Add
  - **Right side**: Remove existing categories
    - One-click removal
    - Instant updates

---

## 📊 UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 Search Term Category Manager                        🔄 Stats │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                   │
│  SIDEBAR     │              MAIN CONTENT AREA                   │
│              │                                                   │
│  🔎 Search   │  ┌─────────────────────────────────────────────┐│
│              │  │ Selected Term: "adidas"                     ││
│  ┌────────┐  │  └─────────────────────────────────────────────┘│
│  │adidas  │  │                                                   │
│  │nike    │  │  ┌──────────────┬──────────────┬──────────────┐ │
│  │asics   │  │  │ View         │ Edit Boost   │ Add/Remove   │ │
│  │iphone  │  │  │ Categories   │ Values       │ Categories   │ │
│  │...     │  │  └──────────────┴──────────────┴──────────────┘ │
│  └────────┘  │                                                   │
│              │  TAB CONTENT:                                     │
│  📊 Stats    │  - Catalog categories table (read-only)          │
│  ────────    │  - Model predictions table (editable)            │
│  Total: 3692 │  - Boost value editors                           │
│  Model: 60   │  - Add/Remove controls                           │
│  Catalog: 3630│                                                  │
│              │                                                   │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 💡 Tips

### Search Tips
- Use partial terms: `nik` finds `nike`, `nike official store`, etc.
- Search is case-insensitive
- Results limited to 50 for performance

### Boost Values
- **Default**: 100
- **Range**: 0-1000
- **Use case**: Control category ranking in search
- **Example**: Boost 200 = double weight vs boost 100

### Adding Categories
- Dropdown is searchable - start typing to filter
- Cannot add duplicates (system prevents this)
- Set appropriate score based on confidence

### Removing Categories
- Only removes from model predictions
- Catalog categories are read-only
- Changes are immediate

---

## 🔍 Example Workflows

### Workflow 1: Review Model Predictions
1. Search for `nike`
2. Go to **View Categories** tab
3. Compare catalog vs model categories
4. Identify any discrepancies

### Workflow 2: Boost Important Categories
1. Search for `adidas`
2. Go to **Edit Boost Values** tab
3. Find `Sepatu Lari` (Running Shoes)
4. Increase boost from 100 to 150
5. Click Save

### Workflow 3: Add Missing Category
1. Search for `nike`
2. Go to **Add/Remove Categories** tab
3. Select `SE-1000027 - Sepatu Sepakbola` from dropdown
4. Set score to 85, boost to 120
5. Click Add Category

### Workflow 4: Remove Incorrect Category
1. Search for term
2. Go to **Add/Remove Categories** tab
3. Find incorrect category on the right
4. Click Remove button
5. Confirm removal

---

## 🛠️ Troubleshooting

### UI won't start
```bash
# Check if port 8501 is in use
lsof -i :8501

# Kill existing process if needed
kill -9 <PID>

# Try different port
streamlit run ui/app.py --server.port 8502
```

### Can't connect to MongoDB
- Check `config/database.py` for correct URI
- Verify network connectivity
- Check VPN/firewall settings

### Changes not showing
- Click the 🔄 Refresh button
- Check MongoDB connection status
- Verify write permissions

---

## 📞 Need Help?

1. Check the console for error messages
2. Review `UI_README.md` for detailed documentation
3. Check `PROJECT_SUMMARY.md` for architecture overview

---

**Ready to Go!** 🎉

Your UI should now be running. Happy managing! 🚀

