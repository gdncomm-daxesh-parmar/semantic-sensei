"""
Streamlit UI for Search Term Category Management
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_connector import get_db_connection
from utils.product_fetcher import fetch_products
import requests
import json


# Set page config
st.set_page_config(
    page_title="Semantic Sensei - AI Category Intelligence",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state
if 'db_connector' not in st.session_state:
    st.session_state.db_connector = None
if 'c3_categories' not in st.session_state:
    st.session_state.c3_categories = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""


@st.cache_data
def load_c3_categories():
    """Load all C3 categories from CSV"""
    csv_path = "/Users/daxeshparmar/PycharmProjects/semantic-sensei/data/c3_categories.csv"
    df = pd.read_csv(csv_path)
    # Create a dict for easy lookup
    categories = {}
    for _, row in df.iterrows():
        categories[row['C3Code']] = row['C3Name']
    return categories


def get_db():
    """Get database connection"""
    if st.session_state.db_connector is None:
        st.session_state.db_connector = get_db_connection()
    return st.session_state.db_connector


def get_terms(skip=0, limit=10, query="", status_filter="in_progress", trend_filter="all"):
    """Get terms from database with pagination"""
    connector = get_db()
    if not connector:
        return [], 0
    
    collection = connector.get_collection('search_term_categories')
    trends_collection = connector.get_collection('search_term_trends')
    
    # Build filter query for search terms
    filter_query = {}
    
    if query:
        # Case-insensitive search
        filter_query['searchTerm'] = {'$regex': query, '$options': 'i'}
    
    # Add status filter
    if status_filter:
        filter_query['status'] = status_filter
    
    # Optimize: If trend filter is specified, get matching terms from trends collection first
    if trend_filter != "all":
        # Get all terms with the specified trend type
        trend_query = {'trendType': trend_filter}
        matching_trend_terms = trends_collection.find(trend_query, {'searchTerm': 1})
        trend_term_list = [doc['searchTerm'] for doc in matching_trend_terms]
        
        # Add to filter query
        if trend_term_list:
            filter_query['searchTerm'] = {'$in': trend_term_list}
            if query:
                # Combine with search query using $and
                filter_query = {
                    '$and': [
                        {'searchTerm': {'$in': trend_term_list}},
                        {'searchTerm': {'$regex': query, '$options': 'i'}}
                    ]
                }
                if status_filter:
                    filter_query['$and'].append({'status': status_filter})
        else:
            # No matching trends, return empty
            return [], 0
    
    # Get total count efficiently
    total = collection.count_documents(filter_query)
    
    # Get only the required page of results
    results = list(collection.find(filter_query).sort('updatedDate', -1).skip(skip).limit(limit))
    
    return results, total


def get_term_data(term):
    """Get full data for a specific term"""
    connector = get_db()
    if not connector:
        return None
    
    collection = connector.get_collection('search_term_categories')
    return collection.find_one({'searchTerm': term})


def log_edit_history(term, action_type, details):
    """Log an edit to the term's history"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    edit_entry = {
        'timestamp': datetime.utcnow(),
        'action': action_type,
        'details': details
    }
    
    collection.update_one(
        {'searchTerm': term},
        {'$push': {'editHistory': edit_entry}}
    )
    
    return True


def update_boost_value(term, category_code, new_boost):
    """Update boost value for a model category"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    # Get current boost value for logging
    term_data = collection.find_one({'searchTerm': term})
    old_boost = None
    category_name = None
    for cat in term_data.get('modelIdentifiedCategories', []):
        if cat['code'] == category_code:
            old_boost = cat.get('boostValue', 100)
            category_name = cat['name']
            break
    
    result = collection.update_one(
        {
            'searchTerm': term,
            'modelIdentifiedCategories.code': category_code
        },
        {
            '$set': {
                'modelIdentifiedCategories.$.boostValue': new_boost,
                'updatedDate': datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        # Log the edit
        log_edit_history(term, 'boost_update', 
                        f"Updated boost for '{category_name}' from {old_boost} to {new_boost}")
        # Check if term should be auto-locked
        check_and_auto_lock(term)
    
    return result.modified_count > 0


def add_model_category(term, category_code, category_name, boost_value):
    """Add a new model category to a term"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    new_category = {
        'code': category_code,
        'name': category_name,
        'score': 0,  # Manual entries have 0 score
        'boostValue': boost_value
    }
    
    result = collection.update_one(
        {'searchTerm': term},
        {
            '$push': {'modelIdentifiedCategories': new_category},
            '$set': {'updatedDate': datetime.utcnow()}
        }
    )
    
    if result.modified_count > 0:
        # Log the edit
        log_edit_history(term, 'category_added', 
                        f"Added category '{category_name}' (boost: {boost_value})")
        # Check if term should be auto-locked
        check_and_auto_lock(term)
    
    return result.modified_count > 0


def remove_model_category(term, category_code):
    """Remove a model category from a term"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    # Get category name for logging
    term_data = collection.find_one({'searchTerm': term})
    category_name = None
    for cat in term_data.get('modelIdentifiedCategories', []):
        if cat['code'] == category_code:
            category_name = cat['name']
            break
    
    result = collection.update_one(
        {'searchTerm': term},
        {
            '$pull': {'modelIdentifiedCategories': {'code': category_code}},
            '$set': {'updatedDate': datetime.utcnow()}
        }
    )
    
    if result.modified_count > 0 and category_name:
        # Log the edit
        log_edit_history(term, 'category_removed', 
                        f"Removed category '{category_name}'")
        # Check if term should be auto-locked
        check_and_auto_lock(term)
    
    return result.modified_count > 0


def delete_term(term):
    """Delete entire term from database"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    result = collection.delete_one({'searchTerm': term})
    
    return result.deleted_count > 0


def promote_to_main_algo(term):
    """Promote term to main algo (lock it)"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    # Update status to locked
    result = collection.update_one(
        {'searchTerm': term},
        {
            '$set': {
                'status': 'locked',
                'updatedDate': datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        # Log the promotion
        log_edit_history(term, 'promoted_to_main', 
                        'Manually promoted to main algorithm (control migrated)')
        return True
    
    return False


def fetch_catalog_categories_for_live_entry(search_term):
    """Fetch catalog categories from Blibli API"""
    from scrapper.fetchTermToCategoryMapping import HEADERS, COOKIES, SEARCH_API_URL, extract_c3_categories
    
    try:
        params = {
            'searchTerm': search_term,
            'facetOnly': 'true',
            'page': 1,
            'start': 0,
            'merchantSearch': 'true',
            'multiCategory': 'true',
            'intent': 'true',
            'channelId': 'android',
            'firstLoad': 'true'
        }
        
        response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, cookies=COOKIES, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Navigate to filters and find Kategori
        if 'data' in data and 'filters' in data['data']:
            filters = data['data']['filters']
            
            for filter_item in filters:
                if filter_item.get('name') == 'Kategori':
                    # Extract C3 categories from the Kategori filter
                    c3_categories = extract_c3_categories(filter_item, top_n=5)
                    
                    # Convert to the format needed
                    catalog_categories = []
                    for c3 in c3_categories:
                        catalog_categories.append({
                            'code': c3['code'],
                            'name': c3['label']
                        })
                    
                    return catalog_categories, None
        
        # No categories found
        return [], None
        
    except Exception as e:
        return [], str(e)


def fetch_model_predictions(search_term):
    """Call the model API to get predictions"""
    try:
        response = requests.post(
            'http://localhost:8090/search',
            json={'search_term': search_term},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        
        if 'result' in data and 'predictions' in data['result']:
            predictions = data['result']['predictions']
            if predictions and len(predictions) > 0:
                term_predictions = predictions[0].get('predictions', [])
                
                # Convert to format needed for MongoDB
                model_categories = []
                for pred in term_predictions:
                    model_categories.append({
                        'code': pred['code'],
                        'name': pred['name'],
                        'score': pred['score'],
                        'boostValue': 100  # Default boost
                    })
                
                token_details = data.get('token_details', {})
                return model_categories, token_details, None
        
        return [], {}, "No predictions in response"
        
    except requests.exceptions.ConnectionError:
        return [], {}, "Model API not running at localhost:8090"
    except Exception as e:
        return [], {}, str(e)


def save_live_entry(search_term, catalog_categories, model_categories):
    """Save the live generated entry to MongoDB"""
    connector = get_db()
    if not connector:
        return False, "Database connection failed"
    
    collection = connector.get_collection('search_term_categories')
    
    # Check if term already exists
    existing = collection.find_one({'searchTerm': search_term})
    
    if existing:
        return False, f"Term '{search_term}' already exists in database"
    
    # Create new entry
    entry_data = {
        'searchTerm': search_term,
        'catalogCategories': catalog_categories,
        'modelIdentifiedCategories': model_categories,
        'status': 'in_progress',
        'createdDate': datetime.utcnow(),
        'updatedDate': datetime.utcnow(),
        'editHistory': [
            {
                'timestamp': datetime.utcnow(),
                'action': 'created',
                'details': 'Live entry generated from UI'
            }
        ]
    }
    
    try:
        collection.insert_one(entry_data)
        return True, "Entry saved successfully"
    except Exception as e:
        return False, str(e)


def calculate_trend_status(term):
    """Get trend status from stored trends data"""
    connector = get_db()
    if not connector:
        return "Neutral", 0
    
    trends_collection = connector.get_collection('search_term_trends')
    trends_data = trends_collection.find_one({'searchTerm': term})
    
    if not trends_data:
        return "Neutral", 0
    
    # Get stored trend type
    trend_type = trends_data.get('trendType', 'neutral')
    
    # Calculate actual percentage change from CTR data
    ctr = trends_data.get('ctr', [])
    if len(ctr) >= 5:
        recent_ctrs = ctr[-5:]  # Last 5 days
        first_ctr = recent_ctrs[0]
        last_ctr = recent_ctrs[-1]
        
        if first_ctr > 0:
            pct_change = ((last_ctr - first_ctr) / first_ctr) * 100
        else:
            pct_change = 0
    else:
        pct_change = 0
    
    # Map trend_type to display format
    if trend_type == "improvement":
        return "Improvement", pct_change
    elif trend_type == "underperforming":
        return "Underperforming", pct_change
    else:
        return "Neutral", pct_change


def check_upward_trend_days(term):
    """Check how many consecutive days of upward trend"""
    trends_data = get_trends_data(term)
    
    if not trends_data or 'trends' not in trends_data:
        return 0
    
    trends = trends_data['trends']
    if len(trends) < 2:
        return 0
    
    # Count consecutive days with increasing CTR
    consecutive_days = 0
    for i in range(len(trends) - 1, 0, -1):
        if trends[i]['ctr'] > trends[i-1]['ctr']:
            consecutive_days += 1
        else:
            break
    
    return consecutive_days


def check_and_auto_lock(term):
    """Check if term should be auto-locked based on 5-day upward trend"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    # Check if already locked
    term_data = collection.find_one({'searchTerm': term})
    if term_data and term_data.get('status') == 'locked':
        return False
    
    # Check for 5-day upward trend
    upward_days = check_upward_trend_days(term)
    
    if upward_days >= 5:
        # Auto-lock the term
        result = collection.update_one(
            {'searchTerm': term},
            {
                '$set': {
                    'status': 'locked',
                    'updatedDate': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            # Log the auto-lock
            log_edit_history(term, 'auto_locked', 
                           f"Auto-locked after {upward_days} days of upward trend")
            return True
    
    return False


def get_trends_data(term):
    """Get CTR/CVR trends data for a term"""
    connector = get_db()
    if not connector:
        return None
    
    collection = connector.get_collection('search_term_trends')
    return collection.find_one({'searchTerm': term})


@st.dialog("🚀 Generate Live Entry", width="large")
def show_live_entry_generator():
    """Dialog for generating live predictions and saving to database"""
    st.subheader("Generate New Entry with AI Predictions")
    
    st.markdown("""
    This tool will:
    1. 📚 Fetch catalog categories from Blibli API
    2. 🤖 Get AI predictions from the model
    3. 💾 Save the entry to MongoDB
    """)
    
    # Input for search term
    search_term = st.text_input(
        "Enter Search Term",
        placeholder="e.g., apple iphone, nike shoes, samsung tv",
        key="live_entry_search_term"
    )
    
    if st.button("🔍 Generate Predictions", type="primary", use_container_width=True):
        if not search_term or len(search_term.strip()) == 0:
            st.error("Please enter a search term")
            return
        
        search_term = search_term.strip()
        
        # Step 1: Fetch catalog categories
        st.markdown("### Step 1: Fetching Catalog Categories...")
        with st.spinner("Calling Blibli API..."):
            catalog_categories, catalog_error = fetch_catalog_categories_for_live_entry(search_term)
        
        if catalog_error:
            st.error(f"❌ Catalog API Error: {catalog_error}")
        elif catalog_categories:
            st.success(f"✅ Found {len(catalog_categories)} catalog categories")
            with st.expander("📚 Catalog Categories", expanded=True):
                for cat in catalog_categories:
                    st.markdown(f"• **{cat['name']}** `{cat['code']}`")
        else:
            st.warning("⚠️ No catalog categories found")
        
        # Step 2: Fetch model predictions
        st.markdown("### Step 2: Getting AI Model Predictions...")
        with st.spinner("Calling Model API at localhost:8090..."):
            model_categories, token_details, model_error = fetch_model_predictions(search_term)
        
        if model_error:
            st.error(f"❌ Model API Error: {model_error}")
            st.info("💡 Make sure the model API is running: `python model/fetchDetailsFromModel.py`")
        elif model_categories:
            st.success(f"✅ Model predicted {len(model_categories)} categories")
            
            # Show model predictions
            with st.expander("🤖 AI Model Predictions", expanded=True):
                for cat in model_categories:
                    score = cat['score']
                    # Color coding
                    if score >= 80:
                        color = "#28a745"
                    elif score >= 50:
                        color = "#ffc107"
                    else:
                        color = "#fd7e14"
                    
                    st.markdown(
                        f"• **{cat['name']}** `{cat['code']}` - "
                        f"<span style='background-color: {color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.85em;'>Score: {score}</span>",
                        unsafe_allow_html=True
                    )
        else:
            st.warning("⚠️ No model predictions received")
        
        # Step 3: Save to MongoDB
        if catalog_categories or model_categories:
            st.markdown("### Step 3: Save to Database")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"**Search Term:** {search_term}")
                st.write(f"📚 Catalog Categories: {len(catalog_categories)}")
                st.write(f"🤖 Model Categories: {len(model_categories)}")
            
            with col2:
                if st.button("💾 Save Entry", type="primary", use_container_width=True):
                    success, message = save_live_entry(search_term, catalog_categories, model_categories)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.info("Entry saved! Refresh the main page to see it.")
                    else:
                        st.error(f"❌ {message}")


@st.dialog("Product Comparison", width="large")
def show_product_comparison_dialog(term):
    """Dialog for showing side-by-side product comparison"""
    st.subheader(f"🛍️ Product Comparison: **{term}**")
    
    # Get term data from database
    connector = get_db()
    if not connector:
        st.error("❌ Database connection failed")
        return
    
    collection = connector.get_collection('search_term_categories')
    term_data = collection.find_one({'searchTerm': term})
    
    if not term_data:
        st.error(f"Term '{term}' not found in database")
        return
    
    # Extract model category codes
    model_categories = term_data.get('modelIdentifiedCategories', [])
    
    # Apply boost value filtering (only categories with boost > 0)
    active_categories = [cat for cat in model_categories if cat.get('boostValue', 100) > 0]
    category_codes = [cat['code'] for cat in active_categories]
    
    # Show active AI categories (always expanded)
    if active_categories:
        st.markdown("**📋 AI Categories Applied:**")
        for cat in active_categories:
            score = cat.get('score', 0)
            boost = cat.get('boostValue', 100)
            st.markdown(f"• **{cat['name']}** `{cat['code']}` - Score: {score} | Boost: {boost}")
        st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
    
    # Fetch products for both scenarios
    with st.spinner("🔄 Fetching products..."):
        # Control: With searchTerm, no category filter
        control_products, control_error = fetch_products(term, category_codes=None, limit=40, include_search_term=True)
        
        # AI Categories: Without searchTerm, only category filters
        ai_products, ai_error = fetch_products(term, category_codes=category_codes, limit=40, include_search_term=False)
    
    # Display any errors
    if control_error:
        st.error(control_error['message'])
        with st.expander("🔍 Error Details"):
            st.code(control_error['details'])
    
    if ai_error:
        st.error(ai_error['message'])
        with st.expander("🔍 Error Details"):
            st.code(ai_error['details'])
    
    # Add CSS for product grid
    st.markdown("""
    <style>
    .product-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
    }
    .product-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .product-image {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 5px;
        margin-bottom: 8px;
    }
    .product-name {
        font-size: 0.85em;
        font-weight: 500;
        color: #212529;
        margin-bottom: 5px;
        height: 40px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .product-price {
        font-size: 0.95em;
        font-weight: 600;
        color: #1971c2;
        margin-bottom: 5px;
    }
    .product-rating {
        font-size: 0.8em;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display comparison in two columns with separator
    col_control, col_separator, col_ai = st.columns([10, 0.5, 10])
    
    with col_control:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 2px solid #868e96;">
            <h3 style="margin: 0; color: #495057;">📦 Control Response</h3>
            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #6c757d;">No category filters</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"<p style='text-align: center; color: #868e96; margin: 10px 0;'><strong>{len(control_products)}</strong> products</p>", unsafe_allow_html=True)
        
        if control_products:
            # Display all products in 3-column grid within this column
            for i in range(0, len(control_products), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(control_products):
                        product = control_products[i + j]
                        with cols[j]:
                            if product['image']:
                                st.markdown(f'<img src="{product["image"]}" class="product-image" />', unsafe_allow_html=True)
                            else:
                                st.markdown('<div style="width: 100%; height: 150px; background-color: #e9ecef; display: flex; align-items: center; justify-content: center; border-radius: 5px; margin-bottom: 8px;">📦</div>', unsafe_allow_html=True)
                            
                            st.markdown(f'<div class="product-name" title="{product["name"]}">{product["name"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="product-price">💰 Rp {product["price"]:,.0f}</div>', unsafe_allow_html=True)
                            
                            rating = product['rating']
                            full_stars = int(rating)
                            empty_stars = 5 - full_stars
                            stars = "⭐" * full_stars + "☆" * empty_stars
                            st.markdown(f'<div class="product-rating">{stars} {rating:.1f}/5.0</div>', unsafe_allow_html=True)
        else:
            st.info("No products found")
    
    with col_separator:
        # Add vertical separator line
        st.markdown("""
        <div style="height: 100%; border-left: 3px solid #e0e0e0; margin: 0 auto;"></div>
        """, unsafe_allow_html=True)
    
    with col_ai:
        st.markdown("""
        <div style="background-color: #e7f5ff; padding: 15px; border-radius: 10px; border: 2px solid #1971c2;">
            <h3 style="margin: 0; color: #1971c2;">🤖 AI Category Response</h3>
            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #1864ab;">With AI filters</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"<p style='text-align: center; color: #1971c2; margin: 10px 0;'><strong>{len(ai_products)}</strong> products</p>", unsafe_allow_html=True)
        
        if ai_products:
            # Display all products in 3-column grid within this column
            for i in range(0, len(ai_products), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(ai_products):
                        product = ai_products[i + j]
                        with cols[j]:
                            if product['image']:
                                st.markdown(f'<img src="{product["image"]}" class="product-image" />', unsafe_allow_html=True)
                            else:
                                st.markdown('<div style="width: 100%; height: 150px; background-color: #e9ecef; display: flex; align-items: center; justify-content: center; border-radius: 5px; margin-bottom: 8px;">📦</div>', unsafe_allow_html=True)
                            
                            st.markdown(f'<div class="product-name" title="{product["name"]}">{product["name"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="product-price">💰 Rp {product["price"]:,.0f}</div>', unsafe_allow_html=True)
                            
                            rating = product['rating']
                            full_stars = int(rating)
                            empty_stars = 5 - full_stars
                            stars = "⭐" * full_stars + "☆" * empty_stars
                            st.markdown(f'<div class="product-rating">{stars} {rating:.1f}/5.0</div>', unsafe_allow_html=True)
        else:
            st.info("No products found")


@st.dialog("CTR/CVR Trends", width="large")
def show_trends_dialog(term):
    """Dialog for showing CTR/CVR trends"""
    st.subheader(f"📈 Performance Trends: **{term}**")
    
    # Get trends data
    trends_data = get_trends_data(term)
    
    if not trends_data:
        st.warning("No trends data available for this term")
        return
    
    ctr = trends_data.get('ctr', [])
    cvr = trends_data.get('cvr', [])
    timestamps = trends_data.get('timestamps', [])
    
    if not ctr or not cvr or not timestamps:
        st.warning("Incomplete trends data")
        return
    
    # Get edit history for markers
    term_data = get_term_data(term)
    edit_history = term_data.get('editHistory', []) if term_data else []
    
    # Create dual-axis chart
    fig = go.Figure()
    
    # Add CTR line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=ctr,
        name='CTR (Click-Through Rate)',
        mode='lines+markers',
        line=dict(color='#1971c2', width=3),
        marker=dict(size=8),
        yaxis='y'
    ))
    
    # Add CVR line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=cvr,
        name='CVR (Conversion Rate)',
        mode='lines+markers',
        line=dict(color='#28a745', width=3),
        marker=dict(size=8),
        yaxis='y'
    ))
    
    # Add edit history markers and annotations
    edit_markers_x = []
    edit_markers_y = []
    edit_labels = []
    
    for edit in edit_history:
        edit_time = edit.get('timestamp')
        if edit_time:
            # Convert timestamp to string format for matching
            if isinstance(edit_time, datetime):
                edit_time_str = edit_time.strftime('%Y-%m-%d')
            else:
                edit_time_str = str(edit_time)
            
            # Check if this timestamp exists in our trends data
            if edit_time_str in timestamps:
                idx = timestamps.index(edit_time_str)
                
                # Add vertical line for each edit
                fig.add_vline(
                    x=edit_time_str,
                    line_dash="dash",
                    line_color="#ff6b35",
                    line_width=2,
                    opacity=0.7
                )
                
                # Prepare annotation
                action = edit.get('action', 'Edit')
                action_icon = {
                    'boost_update': '⚡',
                    'category_added': '➕',
                    'category_removed': '➖',
                    'auto_locked': '🔒',
                    'created': '🆕'
                }.get(action, '✏️')
                
                # Add scatter point for the edit
                edit_markers_x.append(edit_time_str)
                edit_markers_y.append(ctr[idx])
                edit_labels.append(f"{action_icon} {action}")
    
    # Add edit markers as scatter points
    if edit_markers_x:
        fig.add_trace(go.Scatter(
            x=edit_markers_x,
            y=edit_markers_y,
            mode='markers+text',
            name='Edits',
            marker=dict(
                size=12,
                color='#ff6b35',
                symbol='diamond',
                line=dict(width=2, color='white')
            ),
            text=edit_labels,
            textposition='top center',
            textfont=dict(size=10, color='#ff6b35', family='Arial Black'),
            hovertemplate='<b>%{text}</b><br>Date: %{x}<extra></extra>',
            showlegend=True
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'Performance Trends for "{term}"',
            font=dict(size=20, color='#212529')
        ),
        xaxis=dict(
            title='Date',
            showgrid=True,
            gridcolor='#e0e0e0'
        ),
        yaxis=dict(
            title='Rate (0-1)',
            showgrid=True,
            gridcolor='#e0e0e0',
            range=[0, 1]
        ),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        template='plotly_white'
    )
    
    # Display chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Show edit history below the chart
    if edit_history:
        st.subheader("📝 Edit History")
        for edit in reversed(edit_history):  # Most recent first
            timestamp = edit.get('timestamp', 'Unknown')
            action = edit.get('action', 'Unknown')
            details = edit.get('details', 'No details')
            
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
            else:
                timestamp_str = str(timestamp)
            
            st.markdown(f"**{timestamp_str}** - *{action}*: {details}")
    
    # Show statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg CTR", f"{sum(ctr)/len(ctr):.3f}")
    
    with col2:
        st.metric("Avg CVR", f"{sum(cvr)/len(cvr):.3f}")
    
    with col3:
        latest_ctr = ctr[-1] if ctr else 0
        prev_ctr = ctr[-2] if len(ctr) > 1 else latest_ctr
        ctr_change = ((latest_ctr - prev_ctr) / prev_ctr * 100) if prev_ctr > 0 else 0
        st.metric("Latest CTR", f"{latest_ctr:.3f}", f"{ctr_change:+.1f}%")
    
    with col4:
        latest_cvr = cvr[-1] if cvr else 0
        prev_cvr = cvr[-2] if len(cvr) > 1 else latest_cvr
        cvr_change = ((latest_cvr - prev_cvr) / prev_cvr * 100) if prev_cvr > 0 else 0
        st.metric("Latest CVR", f"{latest_cvr:.3f}", f"{cvr_change:+.1f}%")


@st.dialog("Manage AI Categories", width="large")
def edit_term_dialog(term):
    """Dialog for editing term categories"""
    st.subheader(f"🧠 AI Category Management: **{term}**")
    
    # Get fresh data
    term_data = get_term_data(term)
    
    if not term_data:
        st.error("Term data not found")
        return
    
    # Load C3 categories
    if st.session_state.c3_categories is None:
        st.session_state.c3_categories = load_c3_categories()
    c3_categories = st.session_state.c3_categories
    
    # Create tabs
    tab1, tab2 = st.tabs(["⚡ Optimize Boost Weights", "➕ Manage AI Categories"])
    
    # TAB 1: Edit Boost Values
    with tab1:
        st.markdown("### 🤖 AI Identified Categories")
        
        model = term_data.get('modelIdentifiedCategories', [])
        if model:
            for idx, cat in enumerate(model):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    # Add MANUAL indicator for manually added categories
                    if cat['score'] == 0:
                        st.markdown(f"**{cat['name']}** ✋")
                        st.caption(f"Code: {cat['code']} | 🏷️ Manually Added")
                    else:
                        st.markdown(f"**{cat['name']}**")
                        st.caption(f"Code: {cat['code']}")
                
                with col2:
                    score_label = f"{cat['score']} (Manual)" if cat['score'] == 0 else str(cat['score'])
                    st.metric("Score", score_label)
                
                with col3:
                    new_boost = st.number_input(
                        "Boost",
                        min_value=0,
                        value=cat['boostValue'],
                        step=10,
                        key=f"boost_{term}_{cat['code']}_{idx}",
                        label_visibility="visible"
                    )
                
                with col4:
                    if new_boost != cat['boostValue']:
                        if st.button("💾 Save", key=f"save_{term}_{cat['code']}_{idx}", help="Save changes", use_container_width=True):
                            if update_boost_value(term, cat['code'], new_boost):
                                st.success(f"✓ Boost value updated to {new_boost}")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("✗ Failed to update")
                    else:
                        st.markdown("<div style='height: 38px;'></div>", unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("No model categories available")
    
    # TAB 2: Add/Remove Categories
    with tab2:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### ➕ Add Category")
            
            # Category selection
            category_options = [f"{code} - {name}" for code, name in sorted(c3_categories.items(), key=lambda x: x[1])]
            selected_category = st.selectbox(
                "Select Category",
                options=category_options,
                key=f"add_cat_{term}"
            )
            
            if selected_category:
                selected_code = selected_category.split(" - ")[0]
                selected_name = c3_categories[selected_code]
                
                # Check if already exists
                existing_codes = [cat['code'] for cat in term_data.get('modelIdentifiedCategories', [])]
                
                if selected_code in existing_codes:
                    st.warning("⚠️ Category already exists")
                else:
                    boost = st.number_input("Boost Value", min_value=0, value=100, step=10, key=f"boost_add_{term}")
                    st.caption("💡 Enter any integer value (e.g., 50, 100, 200, 500, etc.)")
                    
                    if st.button("➕ Add Category", type="primary", use_container_width=True, key=f"add_btn_{term}"):
                        if add_model_category(term, selected_code, selected_name, boost):
                            st.success(f"✓ Successfully added '{selected_name}' with boost value {boost}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("✗ Failed to add category")
        
        with col2:
            st.markdown("### 🗑️ Remove Category")
            
            model = term_data.get('modelIdentifiedCategories', [])
            if model:
                for cat in model:
                    col_info, col_btn = st.columns([3, 1])
                    
                    with col_info:
                        # Add MANUAL indicator
                        if cat['score'] == 0:
                            st.markdown(f"**{cat['name']}** ✋")
                            st.caption(f"{cat['code']} | Score: {cat['score']} (Manual) | Boost: {cat['boostValue']}")
                        else:
                            st.markdown(f"**{cat['name']}**")
                            st.caption(f"{cat['code']} | Score: {cat['score']} | Boost: {cat['boostValue']}")
                    
                    with col_btn:
                        if st.button("🗑️ Remove", key=f"remove_{term}_{cat['code']}", help="Remove category", use_container_width=True, type="secondary"):
                            if remove_model_category(term, cat['code']):
                                st.success(f"✓ Removed '{cat['name']}' from AI categories")
                                st.rerun()
                            else:
                                st.error("✗ Failed to remove")
                    
                    st.divider()
            else:
                st.info("No categories to remove")
    
    # Show catalog categories at bottom
    with st.expander("📚 View Catalog Categories", expanded=False):
        catalog = term_data.get('catalogCategories', [])
        if catalog:
            df_catalog = pd.DataFrame(catalog)
            st.dataframe(df_catalog, use_container_width=True)
        else:
            st.info("No catalog categories")
    
    # Delete term option at bottom
    st.markdown("---")
    st.markdown("### ⚠️ Danger Zone")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Delete this search term permanently**")
        st.caption("This action cannot be undone. All catalog and AI categories will be removed.")
    
    with col2:
        if st.button("🗑️ Delete Term", type="secondary", use_container_width=True, key=f"delete_term_{term}"):
            if delete_term(term):
                st.success(f"✓ Successfully deleted term '{term}' and all its categories")
                st.rerun()
            else:
                st.error("✗ Failed to delete term")


# Main UI - Display Logo and Title
st.markdown("""
<style>
.logo-header {
    display: flex;
    align-items: center;
    margin-bottom: 1rem;
}
.logo-header img {
    margin-right: 20px;
}
</style>
""", unsafe_allow_html=True)

col_logo, col_title = st.columns([1, 6])

with col_logo:
    # Try to display logo if available
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "semantic_sensei_logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=120)
    else:
        st.markdown('<div style="font-size: 80px; text-align: center;">🧠</div>', unsafe_allow_html=True)

with col_title:
    st.markdown('<h1 style="margin-bottom: 0;">Semantic Sensei</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="margin-top: 0; color: #1971c2;">AI Category Intelligence</h3>', unsafe_allow_html=True)
    st.caption("AI-powered search term category identification and optimization")

# Add CSS for animations and search box styling
st.markdown("""
<style>
/* Search box styling */
.stTextInput > div > div > input {
    border-radius: 25px !important;
    padding: 12px 20px !important;
    border: 2px solid #1971c2 !important;
    font-size: 1.1em !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 4px rgba(25, 113, 194, 0.1) !important;
}

.stTextInput > div > div > input:focus {
    border-color: #1864ab !important;
    box-shadow: 0 4px 8px rgba(25, 113, 194, 0.2) !important;
    transform: translateY(-1px);
}

/* Refresh button styling */
.stButton > button {
    border-radius: 20px !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* Fade-in animation for rows */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeIn 0.5s ease-out;
}

/* Page transition animation */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Loading animation */
@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.5;
    }
}

.loading {
    animation: pulse 1.5s ease-in-out infinite;
}

/* Smooth scroll */
html {
    scroll-behavior: smooth;
}

/* Scroll to top button */
.scroll-to-top {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background-color: #1971c2;
    color: white;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(25, 113, 194, 0.4);
    z-index: 1000;
    transition: all 0.3s ease;
    opacity: 0;
    visibility: hidden;
}

.scroll-to-top.visible {
    opacity: 1;
    visibility: visible;
}

.scroll-to-top:hover {
    background-color: #1864ab;
    transform: translateY(-5px);
    box-shadow: 0 6px 16px rgba(25, 113, 194, 0.5);
}

/* Enhanced hover effects for cards */
div[style*="border-left"] {
    transition: all 0.2s ease;
}

div[style*="border-left"]:hover {
    transform: translateX(3px);
}
</style>

<script>
// Scroll to top functionality
window.onscroll = function() {
    const scrollBtn = document.querySelector('.scroll-to-top');
    if (scrollBtn) {
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            scrollBtn.classList.add('visible');
        } else {
            scrollBtn.classList.remove('visible');
        }
    }
};

function scrollToTop() {
    window.scrollTo({top: 0, behavior: 'smooth'});
}
</script>

<!-- Floating Scroll to Top Button -->
<div class="scroll-to-top" onclick="scrollToTop()">
    <span style="font-size: 24px;">↑</span>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN PAGE - CATEGORY MANAGER
# ============================================================================

if True:  # Keep existing logic structure
    # Original Category Manager Page
    # Top action bar with live entry generator
    col_action1, col_action2 = st.columns([6, 2])
    
    with col_action1:
        st.markdown("""
        <div style="padding: 8px 0;">
            <h3 style="margin: 0; color: #1971c2;">📊 Semantic Sensei - Category Manager</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col_action2:
        if st.button("🚀 Generate New Entry", use_container_width=True, type="primary"):
            show_live_entry_generator()
    
    st.divider()
    
    # Search bar and filters at top with improved design
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([2.5, 1.75, 1.75, 1])

    with col1:
        search_input = st.text_input(
            "🔎 Search for a term", 
            value=st.session_state.search_query, 
            key="search_input", 
            label_visibility="collapsed", 
            placeholder="🔍 Search by term name..."
        )

    with col2:
        # Status filter
        status_filter = st.selectbox(
            "Filter by Status",
            options=["in_progress", "locked", "all"],
            format_func=lambda x: "🔄 In Progress" if x == "in_progress" else "🔒 Locked (Migrated)" if x == "locked" else "📋 All Terms",
            index=0,
            key="status_filter",
            label_visibility="collapsed"
        )

    with col3:
        # Trend filter
        trend_filter = st.selectbox(
            "Filter by Trend",
            options=["all", "improvement", "underperforming", "neutral"],
            format_func=lambda x: "📊 All Trends" if x == "all" else "📈 Improvement" if x == "improvement" else "📉 Underperforming" if x == "underperforming" else "➡️ Neutral",
            index=0,
            key="trend_filter",
            label_visibility="collapsed"
        )

    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    if search_input != st.session_state.search_query:
        st.session_state.search_query = search_input
        st.session_state.current_page = 0
        st.rerun()

    st.divider()

    # Main content area
    page_size = 10
    skip = st.session_state.current_page * page_size

    # Get data with status and trend filters
    filter_status = None if status_filter == "all" else status_filter
    terms, total = get_terms(skip=skip, limit=page_size, query=st.session_state.search_query, status_filter=filter_status, trend_filter=trend_filter)

    if terms:
        # Add CSS for sticky header and compact display
        st.markdown("""
        <style>
        .sticky-table-header {
            position: sticky;
            top: 70px;
            background-color: white;
            z-index: 100;
            padding: 10px 0 8px 0;
            margin: -5px -5% 0 -5%;
            padding-left: 5%;
            padding-right: 5%;
            border-bottom: 2px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Compact row spacing */
        .stButton button {
            padding: 4px 8px;
            font-size: 0.9em;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create HTML table header
        st.markdown("""
        <div class="sticky-table-header">
            <div style="display: flex; align-items: flex-start;">
                <div style="flex: 1.5; padding-right: 10px;">
                    <strong>Search Term</strong>
                </div>
                <div style="flex: 2.5; padding-right: 10px;">
                    <strong>📚 Catalog Categories</strong>
                </div>
                <div style="flex: 2.5; padding-right: 10px;">
                    <strong>🤖 AI Identified Categories</strong>
                    <div style="font-size: 0.8em; color: #666; margin-top: 2px;">Score = AI Confidence | Boost = Weight</div>
                </div>
                <div style="flex: 1; padding-right: 10px; text-align: center;">
                    <strong>📊 Trend Status</strong>
                </div>
                <div style="flex: 0.8; padding-right: 10px; text-align: center;">
                    <strong>Last Updated</strong>
                </div>
                <div style="flex: 1.2; padding-right: 5px; text-align: center;">
                    <strong>Actions</strong>
                </div>
                <div style="flex: 0.7; padding-right: 5px; text-align: center;">
                    <strong>Promote</strong>
                </div>
                <div style="flex: 0.6; padding-right: 5px; text-align: center;">
                    <strong>Edit</strong>
                </div>
                <div style="flex: 0.6; text-align: center;">
                    <strong>Delete</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display table with categories (with animation)
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        
        for idx, term_doc in enumerate(terms):
            term = term_doc['searchTerm']
            catalog_cats = term_doc.get('catalogCategories', [])
            model_cats = term_doc.get('modelIdentifiedCategories', [])
        
            # Format catalog categories (styled) - show up to 5
            catalog_parts = []
            for cat in catalog_cats[:5]:
                cat_html = f'<div style="display: inline-block; margin: 1px 0; padding: 3px 6px; background-color: #e7f5ff; border-radius: 3px; border-left: 2px solid #1971c2;"><span style="font-weight: 500; color: #212529; font-size: 0.9em;">{cat["name"]}</span></div>'
                catalog_parts.append(cat_html)
        
            if catalog_parts:
                catalog_display = "<br>".join(catalog_parts)
            else:
                catalog_display = "—"
        
            # Format model categories with score and boost (styled) - show up to 5
            model_parts = []
            for cat in model_cats[:5]:
                score = cat.get('score', 0)
                boost = cat.get('boostValue', 100)
            
                # Color coding based on score
                if score >= 80:
                    score_color = "#28a745"  # Green
                elif score >= 50:
                    score_color = "#ffc107"  # Yellow
                elif score > 0:
                    score_color = "#fd7e14"  # Orange
                else:
                    score_color = "#6c757d"  # Gray for manual (0)
            
                # Boost badge color
                if boost > 100:
                    boost_color = "#007bff"  # Blue for boosted
                else:
                    boost_color = "#6c757d"  # Gray for default
            
                # Add MANUAL badge for manually added categories (score = 0)
                manual_badge = ""
                if score == 0:
                    manual_badge = '<span title="Manually Added Category" style="background-color: #6c757d; color: white; padding: 1px 4px; border-radius: 2px; font-size: 0.75em; font-weight: 600; margin-left: 3px;">✋ MANUAL</span>'
            
                cat_html = f'<div style="display: inline-block; margin: 1px 0; padding: 3px 6px; background-color: #f8f9fa; border-radius: 3px; border-left: 2px solid {score_color};"><span style="font-weight: 500; color: #212529; font-size: 0.9em;">{cat["name"]}</span><span style="margin-left: 6px;"><span title="AI Confidence Score" style="background-color: {score_color}; color: white; padding: 1px 4px; border-radius: 2px; font-size: 0.75em; font-weight: 600;">Score: {score}</span><span title="Boost Weight Value" style="background-color: {boost_color}; color: white; padding: 1px 4px; border-radius: 2px; font-size: 0.75em; margin-left: 3px; font-weight: 600;">Boost: {boost}</span>{manual_badge}</span></div>'
            
                model_parts.append(cat_html)
        
            if model_parts:
                model_display = "<br>".join(model_parts)
            else:
                model_display = "—"
            
            # Calculate trend status
            trend_status, pct_change = calculate_trend_status(term)
            
            # Format trend status with color (single line, compact)
            if trend_status == "Underperforming":
                trend_badge = f'<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 4px; font-size: 0.85em; font-weight: 600; white-space: nowrap; display: inline-block;">📉 {pct_change:.1f}%</span>'
            elif trend_status == "Improvement":
                trend_badge = f'<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 4px; font-size: 0.85em; font-weight: 600; white-space: nowrap; display: inline-block;">📈 +{pct_change:.1f}%</span>'
            else:
                trend_badge = f'<span style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 4px; font-size: 0.85em; font-weight: 600; white-space: nowrap; display: inline-block;">➡️ Neutral</span>'
        
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 2.5, 2.5, 1, 0.8, 1.2, 0.7, 0.6, 0.6])
        
            with col1:
                # Show lock icon if locked
                status = term_doc.get('status', 'in_progress')
                lock_icon = "🔒 " if status == "locked" else ""
                st.markdown(f"{lock_icon}{term}")
        
            with col2:
                st.markdown(f"{catalog_display}", unsafe_allow_html=True)
        
            with col3:
                st.markdown(f"{model_display}", unsafe_allow_html=True)
        
            with col4:
                # Trend status badge
                st.markdown(f"<div style='text-align: center;'>{trend_badge}</div>", unsafe_allow_html=True)
        
            with col5:
                # Format updatedDate
                updated_date = term_doc.get('updatedDate')
                if updated_date:
                    formatted_date = updated_date.strftime('%Y-%m-%d %H:%M')
                    st.markdown(f"<div style='text-align: center; font-size: 0.85em; color: #666;'>{formatted_date}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align: center; font-size: 0.85em; color: #999;'>—</div>", unsafe_allow_html=True)
        
            with col6:
                # Create action buttons side by side
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("📈", key=f"trends_{term}_{idx}", use_container_width=True, help="Show trends"):
                        show_trends_dialog(term)
                with btn_col2:
                    if st.button("🛍️", key=f"visualize_{term}_{idx}", use_container_width=True, help="Visualize diff"):
                        show_product_comparison_dialog(term)
        
            with col7:
                # Promote button - only for in_progress terms
                status = term_doc.get('status', 'in_progress')
                if status == "in_progress":
                    if st.button("🚀", key=f"promote_{term}_{idx}", use_container_width=True, help="Promote to Main Algo", type="primary"):
                        if promote_to_main_algo(term):
                            st.success("✓ Promoted!")
                            st.rerun()
                        else:
                            st.error("✗ Failed")
                else:
                    st.button("✓", key=f"promote_{term}_{idx}", use_container_width=True, disabled=True, help="Already in Main Algo")
        
            with col8:
                # Disable edit for locked terms
                status = term_doc.get('status', 'in_progress')
                if status == "locked":
                    st.button("🔒", key=f"edit_{term}_{idx}", use_container_width=True, disabled=True, help="Locked - Control Migrated")
                else:
                    if st.button("✏️", key=f"edit_{term}_{idx}", use_container_width=True, help="Edit categories"):
                        edit_term_dialog(term)
        
            with col9:
                if st.button("🗑️", key=f"delete_{term}_{idx}", use_container_width=True, help="Delete term", type="secondary"):
                    if delete_term(term):
                        st.success("✓ Deleted")
                        st.rerun()
                    else:
                        st.error("✗ Failed")
        
            st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid #e0e0e0;">', unsafe_allow_html=True)
    
        st.markdown('</div>', unsafe_allow_html=True)
    
        # Pagination with scroll to top
        st.markdown("---")
    
        # Add scroll to top marker
        st.markdown('<div id="top-marker"></div>', unsafe_allow_html=True)
    
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
        total_pages = (total + page_size - 1) // page_size
    
        with col1:
            if st.session_state.current_page > 0:
                if st.button("⬅️ Previous", use_container_width=True, key="prev_page"):
                    st.session_state.current_page -= 1
                    # Scroll to top after page change
                    st.markdown("""
                    <script>
                    window.scrollTo({top: 0, behavior: 'smooth'});
                    </script>
                    """, unsafe_allow_html=True)
                    st.rerun()
    
        with col3:
            st.markdown(f"""
            <center style="padding: 8px; background-color: #f8f9fa; border-radius: 8px; font-weight: 500;">
                Page {st.session_state.current_page + 1} of {total_pages}
            </center>
            """, unsafe_allow_html=True)
    
        with col5:
            if st.session_state.current_page < total_pages - 1:
                if st.button("Next ➡️", use_container_width=True, key="next_page"):
                    st.session_state.current_page += 1
                    # Scroll to top after page change
                    st.markdown("""
                    <script>
                    window.scrollTo({top: 0, behavior: 'smooth'});
                    </script>
                    """, unsafe_allow_html=True)
                    st.rerun()

    else:
        if st.session_state.search_query:
            st.warning(f"No results found for '{st.session_state.search_query}'")
        else:
            st.error("No data available in the database")

# ============================================================================
# PRODUCT COMPARISON PAGE
# ============================================================================

# Product Comparison is now integrated as a dialog accessible from each row
