# 🔍 Search Term Category Manager UI

A web-based user interface for managing search term categories, including catalog categories and model-identified categories with boost values.

## 📋 Features

### 1. **Search Interface**
- Search for terms using partial matching
- View up to 50 matching results
- Click on any term to view its details

### 2. **View Categories**
- **Catalog Categories**: View all categories from the catalog API
  - Display: Code, Name
  - Read-only (cannot be modified)
  
- **Model Identified Categories**: View ML model predictions
  - Display: Code, Name, Score, Boost Value
  - Can be edited and modified

### 3. **Edit Boost Values**
- Modify boost values for model-identified categories
- Range: 0-1000 (default: 100)
- Adjustable in increments of 10
- Real-time save functionality

### 4. **Add/Remove Categories**
- **Add Categories**: 
  - Select from dropdown of ~2,000 C3 categories
  - Set custom score (0-100)
  - Set custom boost value (0-1000)
  - Prevents duplicate categories
  
- **Remove Categories**:
  - One-click removal of model-identified categories
  - Instant feedback and updates

## 🚀 Quick Start

### Prerequisites
```bash
# Install required packages
pip3 install streamlit pandas pymongo
```

### Launch the UI

**Option 1: Using the launch script**
```bash
./run_ui.sh
```

**Option 2: Direct command**
```bash
streamlit run ui/app.py
```

The UI will automatically open in your browser at `http://localhost:8501`

## 📊 Database Structure

### MongoDB Collection: `search_term_categories`

```json
{
  "searchTerm": "adidas",
  "catalogCategories": [
    {
      "code": "SE-1000019",
      "name": "Sepatu Lari"
    }
  ],
  "modelIdentifiedCategories": [
    {
      "code": "SE-1000019",
      "name": "Sepatu Lari",
      "score": 95,
      "boostValue": 100
    }
  ]
}
```

## 🎯 Usage Guide

### Searching for Terms

1. Type a search query in the left sidebar
2. Results will appear as clickable buttons
3. Click any term to view its full details

### Viewing Categories

The **View Categories** tab shows:
- Left column: Catalog categories (from API)
- Right column: Model-identified categories (from ML)

### Editing Boost Values

1. Go to the **Edit Boost Values** tab
2. Each model category shows:
   - Category name and code
   - Model score
   - Current boost value
3. Adjust the boost value using the number input
4. Click **Save** to update

### Adding a Category

1. Go to the **Add/Remove Categories** tab
2. Select a category from the dropdown (searchable)
3. Set the score (0-100)
4. Set the boost value (0-1000)
5. Click **Add Category**

### Removing a Category

1. Go to the **Add/Remove Categories** tab
2. Find the category you want to remove
3. Click the **Remove** button
4. Confirm the action

## 📈 Dashboard Statistics

The home screen displays:
- **Total Terms**: Total number of search terms in database
- **With Model Data**: Terms that have model predictions
- **With Catalog Data**: Terms that have catalog categories

## 🔧 Configuration

### MongoDB Connection
Edit `config/database.py` to change the MongoDB connection:
```python
MONGO_URI = "your_mongodb_uri"
DATABASE_NAME = "your_database"
```

### UI Port
To run on a different port:
```bash
streamlit run ui/app.py --server.port 8502
```

## 📁 File Structure

```
semantic-sensei/
├── ui/
│   ├── app.py              # Main Streamlit application
│   └── __init__.py
├── config/
│   └── database.py         # MongoDB configuration
├── utils/
│   └── db_connector.py     # Database connection utility
├── data/
│   └── c3_categories.csv   # All C3 categories (2K entries)
├── run_ui.sh               # Launch script
└── UI_README.md           # This file
```

## 🛠️ Troubleshooting

### Connection Issues
- Ensure MongoDB is accessible from your network
- Check firewall settings
- Verify credentials in `config/database.py`

### Performance
- Search results are limited to 50 for performance
- Large category lists use pagination in dropdowns

### Browser Issues
- If UI doesn't open automatically, manually navigate to `http://localhost:8501`
- Clear browser cache if experiencing display issues
- Recommended browsers: Chrome, Firefox, Safari

## 💡 Tips

- **Search Tips**: Use partial terms for broader results (e.g., "nike" finds "nike official store")
- **Boost Values**: Higher values give more weight to categories in search results
- **Score vs Boost**: Score is model confidence (0-100), Boost is manual weight adjustment
- **Category Selection**: The dropdown is searchable - start typing to filter options

## 📝 Notes

- Catalog categories are read-only and come from the API
- Only model-identified categories can be added/removed
- Changes are saved immediately to MongoDB
- Use the refresh button to reload data after external changes

## 🔐 Security

- The UI connects directly to MongoDB
- Ensure proper network security for production use
- Consider adding authentication for multi-user environments

## 📞 Support

For issues or questions:
1. Check the console for error messages
2. Verify MongoDB connection
3. Ensure all dependencies are installed

---

**Version**: 1.0.0  
**Last Updated**: November 2024

