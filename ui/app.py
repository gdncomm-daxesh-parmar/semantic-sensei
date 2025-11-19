"""
Streamlit UI for Search Term Category Management
"""

import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_connector import get_db_connection


# Set page config
st.set_page_config(
    page_title="Search Term Category Manager",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'selected_term' not in st.session_state:
    st.session_state.selected_term = None
if 'db_connector' not in st.session_state:
    st.session_state.db_connector = None
if 'c3_categories' not in st.session_state:
    st.session_state.c3_categories = None


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


def search_terms(query, limit=50):
    """Search for terms in database"""
    connector = get_db()
    if not connector:
        return []
    
    collection = connector.get_collection('search_term_categories')
    
    if query:
        # Case-insensitive search
        results = collection.find(
            {'searchTerm': {'$regex': query, '$options': 'i'}},
            limit=limit
        ).sort('searchTerm', 1)
    else:
        # No query - return first N results
        results = collection.find(
            {},
            limit=limit
        ).sort('searchTerm', 1)
    
    return list(results)


def get_term_data(term):
    """Get full data for a specific term"""
    connector = get_db()
    if not connector:
        return None
    
    collection = connector.get_collection('search_term_categories')
    return collection.find_one({'searchTerm': term})


def update_boost_value(term, category_code, new_boost):
    """Update boost value for a model category"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    result = collection.update_one(
        {
            'searchTerm': term,
            'modelIdentifiedCategories.code': category_code
        },
        {
            '$set': {'modelIdentifiedCategories.$.boostValue': new_boost}
        }
    )
    
    return result.modified_count > 0


def add_model_category(term, category_code, category_name, score, boost_value):
    """Add a new model category to a term"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    new_category = {
        'code': category_code,
        'name': category_name,
        'score': score,
        'boostValue': boost_value
    }
    
    result = collection.update_one(
        {'searchTerm': term},
        {'$push': {'modelIdentifiedCategories': new_category}}
    )
    
    return result.modified_count > 0


def remove_model_category(term, category_code):
    """Remove a model category from a term"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    result = collection.update_one(
        {'searchTerm': term},
        {'$pull': {'modelIdentifiedCategories': {'code': category_code}}}
    )
    
    return result.modified_count > 0


# Main UI
st.title("🔍 Search Term Category Manager")

# Load C3 categories
if st.session_state.c3_categories is None:
    with st.spinner("Loading C3 categories..."):
        st.session_state.c3_categories = load_c3_categories()

c3_categories = st.session_state.c3_categories

# Sidebar for search
with st.sidebar:
    st.header("Search Terms")
    search_query = st.text_input("🔎 Search for a term", "")
    
    with st.spinner("Loading..."):
        if search_query:
            results = search_terms(search_query, limit=50)
            result_label = f"Found {len(results)} results"
        else:
            results = search_terms("", limit=10)
            result_label = f"Showing first {len(results)} terms"
    
    if results:
        if search_query:
            st.success(result_label)
        else:
            st.info(result_label)
        
        # Display results as buttons
        for result in results:
            if st.button(result['searchTerm'], key=f"btn_{result['searchTerm']}", use_container_width=True):
                st.session_state.selected_term = result['searchTerm']
                st.rerun()
    else:
        st.warning("No results found")

# Main content area
if st.session_state.selected_term:
    term = st.session_state.selected_term
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.header(f"📝 Term: **{term}**")
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Get fresh data
    term_data = get_term_data(term)
    
    if term_data:
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["📊 View Categories", "⚡ Edit Boost Values", "➕ Add/Remove Categories"])
        
        # TAB 1: View Categories
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📚 Catalog Categories")
                catalog = term_data.get('catalogCategories', [])
                if catalog:
                    df_catalog = pd.DataFrame(catalog)
                    df_catalog.index = range(1, len(df_catalog) + 1)
                    st.dataframe(df_catalog, use_container_width=True, height=400)
                    st.info(f"Total: {len(catalog)} categories")
                else:
                    st.warning("No catalog categories")
            
            with col2:
                st.subheader("🤖 Model Identified Categories")
                model = term_data.get('modelIdentifiedCategories', [])
                if model:
                    df_model = pd.DataFrame(model)
                    df_model.index = range(1, len(df_model) + 1)
                    st.dataframe(df_model, use_container_width=True, height=400)
                    st.info(f"Total: {len(model)} categories")
                else:
                    st.warning("No model identified categories")
        
        # TAB 2: Edit Boost Values
        with tab2:
            st.subheader("⚡ Edit Boost Values for Model Categories")
            
            model = term_data.get('modelIdentifiedCategories', [])
            if model:
                for idx, cat in enumerate(model):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        
                        with col1:
                            st.text(f"{cat['name']}")
                            st.caption(f"Code: {cat['code']}")
                        
                        with col2:
                            st.metric("Score", cat['score'])
                        
                        with col3:
                            new_boost = st.number_input(
                                "Boost Value",
                                min_value=0,
                                max_value=1000,
                                value=cat['boostValue'],
                                step=10,
                                key=f"boost_{cat['code']}",
                                label_visibility="collapsed"
                            )
                        
                        with col4:
                            if new_boost != cat['boostValue']:
                                if st.button("💾 Save", key=f"save_{cat['code']}", use_container_width=True):
                                    if update_boost_value(term, cat['code'], new_boost):
                                        st.success("✓ Updated")
                                        st.rerun()
                                    else:
                                        st.error("✗ Failed")
                        
                        st.divider()
            else:
                st.info("No model categories to edit")
        
        # TAB 3: Add/Remove Categories
        with tab3:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("➕ Add Model Category")
                
                # Category selection
                category_options = [f"{code} - {name}" for code, name in sorted(c3_categories.items(), key=lambda x: x[1])]
                selected_category = st.selectbox(
                    "Select Category",
                    options=category_options,
                    key="add_category_select"
                )
                
                if selected_category:
                    selected_code = selected_category.split(" - ")[0]
                    selected_name = c3_categories[selected_code]
                    
                    # Check if already exists
                    existing_codes = [cat['code'] for cat in term_data.get('modelIdentifiedCategories', [])]
                    
                    if selected_code in existing_codes:
                        st.warning("⚠️ This category already exists for this term")
                    else:
                        col_score, col_boost = st.columns(2)
                        
                        with col_score:
                            score = st.number_input("Score", min_value=0, max_value=100, value=50, step=5)
                        
                        with col_boost:
                            boost = st.number_input("Boost Value", min_value=0, max_value=1000, value=100, step=10)
                        
                        if st.button("➕ Add Category", type="primary", use_container_width=True):
                            if add_model_category(term, selected_code, selected_name, score, boost):
                                st.success(f"✓ Added {selected_name}")
                                st.rerun()
                            else:
                                st.error("✗ Failed to add category")
            
            with col2:
                st.subheader("🗑️ Remove Model Category")
                
                model = term_data.get('modelIdentifiedCategories', [])
                if model:
                    for cat in model:
                        with st.container():
                            col_info, col_btn = st.columns([3, 1])
                            
                            with col_info:
                                st.text(f"**{cat['name']}**")
                                st.caption(f"Code: {cat['code']} | Score: {cat['score']} | Boost: {cat['boostValue']}")
                            
                            with col_btn:
                                if st.button("🗑️ Remove", key=f"remove_{cat['code']}", type="secondary", use_container_width=True):
                                    if remove_model_category(term, cat['code']):
                                        st.success("✓ Removed")
                                        st.rerun()
                                    else:
                                        st.error("✗ Failed")
                            
                            st.divider()
                else:
                    st.info("No model categories to remove")
    else:
        st.error("Term data not found")
else:
    # Welcome screen
    st.markdown("""
    ## 👋 Welcome to Search Term Category Manager
    
    **Get Started:**
    - 👈 Click any term in the sidebar to view details
    - 🔎 Use the search box to find specific terms
    - The first 10 terms are already loaded for you
    
    ---
    """)
    
    # Show some stats
    connector = get_db()
    if connector:
        collection = connector.get_collection('search_term_categories')
        
        st.subheader("📊 Database Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total = collection.count_documents({})
            st.metric("📊 Total Terms", f"{total:,}")
        
        with col2:
            with_model = collection.count_documents({'modelIdentifiedCategories': {'$ne': []}})
            st.metric("🤖 With Model Data", f"{with_model:,}")
        
        with col3:
            with_catalog = collection.count_documents({'catalogCategories': {'$ne': []}})
            st.metric("📚 With Catalog Data", f"{with_catalog:,}")
        
        st.markdown("---")
        
        st.subheader("✨ Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📊 View Categories**
            - Compare catalog vs model categories
            - See all category details
            """)
        
        with col2:
            st.markdown("""
            **⚡ Edit Boost Values**
            - Adjust category weights
            - Real-time updates
            """)
        
        with col3:
            st.markdown("""
            **➕ Add/Remove**
            - 2,023 C3 categories
            - One-click management
            """)

