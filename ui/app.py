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


def get_terms(skip=0, limit=10, query=""):
    """Get terms from database with pagination"""
    connector = get_db()
    if not connector:
        return [], 0
    
    collection = connector.get_collection('search_term_categories')
    
    if query:
        # Case-insensitive search
        filter_query = {'searchTerm': {'$regex': query, '$options': 'i'}}
    else:
        filter_query = {}
    
    total = collection.count_documents(filter_query)
    results = collection.find(filter_query).sort('searchTerm', 1).skip(skip).limit(limit)
    
    return list(results), total


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


@st.dialog("Edit Categories", width="large")
def edit_term_dialog(term):
    """Dialog for editing term categories"""
    st.subheader(f"📝 Editing: **{term}**")
    
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
    tab1, tab2 = st.tabs(["⚡ Edit Boost Values", "➕ Add/Remove Categories"])
    
    # TAB 1: Edit Boost Values
    with tab1:
        st.markdown("### 🤖 Model Identified Categories")
        
        model = term_data.get('modelIdentifiedCategories', [])
        if model:
            for idx, cat in enumerate(model):
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{cat['name']}**")
                        st.caption(f"Code: {cat['code']}")
                    
                    with col2:
                        st.metric("Score", cat['score'])
                    
                    with col3:
                        new_boost = st.number_input(
                            "Boost",
                            min_value=0,
                            max_value=1000,
                            value=cat['boostValue'],
                            step=10,
                            key=f"boost_{term}_{cat['code']}_{idx}",
                            label_visibility="visible"
                        )
                    
                    with col4:
                        if new_boost != cat['boostValue']:
                            if st.button("💾", key=f"save_{term}_{cat['code']}_{idx}", help="Save changes"):
                                if update_boost_value(term, cat['code'], new_boost):
                                    st.success("✓")
                                    st.rerun()
                                else:
                                    st.error("✗")
                    
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
                    boost = st.number_input("Boost Value", min_value=0, max_value=1000, value=100, step=10, key=f"boost_add_{term}")
                    
                    if st.button("➕ Add Category", type="primary", use_container_width=True, key=f"add_btn_{term}"):
                        if add_model_category(term, selected_code, selected_name, boost):
                            st.success(f"✓ Added {selected_name}")
                            st.rerun()
                        else:
                            st.error("✗ Failed to add")
        
        with col2:
            st.markdown("### 🗑️ Remove Category")
            
            model = term_data.get('modelIdentifiedCategories', [])
            if model:
                for cat in model:
                    with st.container():
                        col_info, col_btn = st.columns([3, 1])
                        
                        with col_info:
                            st.markdown(f"**{cat['name']}**")
                            st.caption(f"{cat['code']} | Score: {cat['score']} | Boost: {cat['boostValue']}")
                        
                        with col_btn:
                            if st.button("🗑️", key=f"remove_{term}_{cat['code']}", help="Remove", use_container_width=True):
                                if remove_model_category(term, cat['code']):
                                    st.success("✓")
                                    st.rerun()
                                else:
                                    st.error("✗")
                        
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


# Main UI
st.title("🔍 Search Term Category Manager")

# Search bar at top
col1, col2 = st.columns([4, 1])

with col1:
    search_input = st.text_input("🔎 Search for a term", value=st.session_state.search_query, key="search_input", label_visibility="collapsed", placeholder="Search for a term...")

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if search_input != st.session_state.search_query:
    st.session_state.search_query = search_input
    st.session_state.current_page = 0
    st.rerun()

st.divider()

# Main content area
page_size = 10
skip = st.session_state.current_page * page_size

# Get data
terms, total = get_terms(skip=skip, limit=page_size, query=st.session_state.search_query)

if terms:
    # Display table header
    col1, col2, col3, col4 = st.columns([2, 3, 3, 1])
    
    with col1:
        st.markdown("**Search Term**")
    
    with col2:
        st.markdown("**📚 Catalog Categories**")
    
    with col3:
        st.markdown("**🤖 Model Categories (Score/Boost)**")
    
    with col4:
        st.markdown("**Action**")
    
    st.markdown("---")
    
    # Display table with categories
    for idx, term_doc in enumerate(terms):
        term = term_doc['searchTerm']
        catalog_cats = term_doc.get('catalogCategories', [])
        model_cats = term_doc.get('modelIdentifiedCategories', [])
        
        # Format catalog categories (styled)
        catalog_parts = []
        for cat in catalog_cats[:3]:
            cat_html = f"""
            <div style="display: inline-block; margin: 2px 0; padding: 4px 8px; background-color: #e7f5ff; border-radius: 4px; border-left: 3px solid #1971c2;">
                <span style="font-weight: 500;">{cat['name']}</span>
            </div>
            """
            catalog_parts.append(cat_html)
        
        if len(catalog_cats) > 3:
            catalog_parts.append(f'<div style="display: inline-block; margin: 2px 0; padding: 4px 8px; color: #6c757d; font-style: italic;">+{len(catalog_cats) - 3} more</div>')
        
        if catalog_parts:
            catalog_display = "<br>".join(catalog_parts)
        else:
            catalog_display = "—"
        
        # Format model categories with score and boost (styled)
        model_parts = []
        for cat in model_cats[:3]:
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
            
            cat_html = f"""
            <div style="display: inline-block; margin: 2px 0; padding: 4px 8px; background-color: #f8f9fa; border-radius: 4px; border-left: 3px solid {score_color};">
                <span style="font-weight: 500;">{cat['name']}</span>
                <span style="margin-left: 8px;">
                    <span style="background-color: {score_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.85em;">S:{score}</span>
                    <span style="background-color: {boost_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.85em; margin-left: 4px;">B:{boost}</span>
                </span>
            </div>
            """
            model_parts.append(cat_html)
        
        if len(model_cats) > 3:
            model_parts.append(f'<div style="display: inline-block; margin: 2px 0; padding: 4px 8px; color: #6c757d; font-style: italic;">+{len(model_cats) - 3} more</div>')
        
        if model_parts:
            model_display = "<br>".join(model_parts)
        else:
            model_display = "—"
        
        col1, col2, col3, col4 = st.columns([2, 3, 3, 1])
        
        with col1:
            st.markdown(f"{term}")
        
        with col2:
            st.markdown(f"{catalog_display}", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"{model_display}", unsafe_allow_html=True)
        
        with col4:
            if st.button("✏️ Edit", key=f"edit_{term}_{idx}", use_container_width=True):
                edit_term_dialog(term)
        
        st.divider()
    
    # Pagination
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    total_pages = (total + page_size - 1) // page_size
    
    with col1:
        if st.session_state.current_page > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.current_page -= 1
                st.rerun()
    
    with col3:
        st.markdown(f"<center>Page {st.session_state.current_page + 1} of {total_pages}</center>", unsafe_allow_html=True)
    
    with col5:
        if st.session_state.current_page < total_pages - 1:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.current_page += 1
                st.rerun()

else:
    if st.session_state.search_query:
        st.warning(f"No results found for '{st.session_state.search_query}'")
    else:
        st.error("No data available in the database")
