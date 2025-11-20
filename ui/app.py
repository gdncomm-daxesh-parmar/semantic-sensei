"""
Streamlit UI for Search Term Category Management
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_connector import get_db_connection
from utils.product_fetcher import fetch_products


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
if 'active_page' not in st.session_state:
    st.session_state.active_page = "Category Manager"


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


def delete_term(term):
    """Delete entire term from database"""
    connector = get_db()
    if not connector:
        return False
    
    collection = connector.get_collection('search_term_categories')
    
    result = collection.delete_one({'searchTerm': term})
    
    return result.deleted_count > 0


def get_trends_data(term):
    """Get CTR/CVR trends data for a term"""
    connector = get_db()
    if not connector:
        return None
    
    collection = connector.get_collection('search_term_trends')
    return collection.find_one({'searchTerm': term})


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
# PAGE NAVIGATION
# ============================================================================

st.markdown("""
<style>
.page-nav {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 10px;
}
.page-nav-btn {
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    background-color: white;
    cursor: pointer;
    transition: all 0.3s ease;
}
.page-nav-btn:hover {
    background-color: #e7f5ff;
}
.page-nav-btn.active {
    background-color: #1971c2;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Page navigation buttons
col1, col2, col3 = st.columns([2, 2, 6])

with col1:
    if st.button("📊 Category Manager", use_container_width=True, 
                 type="primary" if st.session_state.active_page == "Category Manager" else "secondary"):
        st.session_state.active_page = "Category Manager"
        st.rerun()

with col2:
    if st.button("🛍️ Product Comparison", use_container_width=True,
                 type="primary" if st.session_state.active_page == "Product Comparison" else "secondary"):
        st.session_state.active_page = "Product Comparison"
        st.rerun()

st.divider()

# ============================================================================
# RENDER ACTIVE PAGE
# ============================================================================

if st.session_state.active_page == "Category Manager":
    # Original Category Manager Page
    # Search bar at top with improved design
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    col1, col2 = st.columns([5, 1])

    with col1:
        search_input = st.text_input(
            "🔎 Search for a term", 
            value=st.session_state.search_query, 
            key="search_input", 
            label_visibility="collapsed", 
            placeholder="🔍 Search by term name... (e.g., 'adidas', 'nike', 'iphone')"
        )

    with col2:
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

    # Get data
    terms, total = get_terms(skip=skip, limit=page_size, query=st.session_state.search_query)

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
                <div style="flex: 2; padding-right: 10px;">
                    <strong>Search Term</strong>
                </div>
                <div style="flex: 3; padding-right: 10px;">
                    <strong>📚 Catalog Categories</strong>
                </div>
                <div style="flex: 3; padding-right: 10px;">
                    <strong>🤖 AI Identified Categories</strong>
                    <div style="font-size: 0.8em; color: #666; margin-top: 2px;">Score = AI Confidence | Boost = Weight</div>
                </div>
                <div style="flex: 0.7; padding-right: 5px; text-align: center;">
                    <strong>Trends</strong>
                </div>
                <div style="flex: 0.7; padding-right: 5px; text-align: center;">
                    <strong>Edit</strong>
                </div>
                <div style="flex: 0.7; text-align: center;">
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
        
            col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 3, 0.7, 0.7, 0.7])
        
            with col1:
                st.markdown(f"{term}")
        
            with col2:
                st.markdown(f"{catalog_display}", unsafe_allow_html=True)
        
            with col3:
                st.markdown(f"{model_display}", unsafe_allow_html=True)
        
            with col4:
                if st.button("📈", key=f"trends_{term}_{idx}", use_container_width=True, help="Show trends"):
                    show_trends_dialog(term)
        
            with col5:
                if st.button("✏️", key=f"edit_{term}_{idx}", use_container_width=True, help="Edit categories"):
                    edit_term_dialog(term)
        
            with col6:
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

elif st.session_state.active_page == "Product Comparison":
    # Compact header
    st.markdown('<h3 style="color: #1971c2; margin-bottom: 5px;">🛍️ Product Comparison</h3>', unsafe_allow_html=True)
    
    # Get all search terms from database
    connector = get_db()
    if not connector:
        st.error("❌ Database connection failed")
    else:
        collection = connector.get_collection('search_term_categories')
        
        # Get all terms that have model-identified categories
        all_terms = list(collection.find(
            {'modelIdentifiedCategories': {'$exists': True, '$ne': []}},
            {'searchTerm': 1, 'modelIdentifiedCategories': 1}
        ).sort('searchTerm', 1))
        
        if not all_terms:
            st.warning("No terms with AI-identified categories found in the database")
        else:
            # Compact search term selector
            term_options = [term['searchTerm'] for term in all_terms]
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                selected_term = st.selectbox(
                    "Search Term",
                    options=term_options,
                    index=None,
                    placeholder="Select a term...",
                    label_visibility="collapsed"
                )
            
            with col2:
                compare_button = st.button("🔍 Compare", use_container_width=True, type="primary", disabled=(selected_term is None))
            
            # Only fetch and display products if compare button is clicked
            if compare_button and selected_term:
                # Get the term data
                term_data = collection.find_one({'searchTerm': selected_term})
                
                if term_data:
                    # Extract model category codes
                    model_categories = term_data.get('modelIdentifiedCategories', [])
                    
                    # Apply boost value filtering (only categories with boost > 0)
                    active_categories = [cat for cat in model_categories if cat.get('boostValue', 100) > 0]
                    category_codes = [cat['code'] for cat in active_categories]
                    
                    # Compact info bar
                    st.markdown(f"""
                    <div style="background-color: #e7f5ff; padding: 8px 12px; border-radius: 5px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #1971c2; font-weight: 500;">🔍 {selected_term}</span>
                        <span style="color: #495057; font-size: 0.9em;">{len(active_categories)} AI categories</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show active categories in compact expander
                    if active_categories:
                        with st.expander("📋 AI Categories", expanded=False):
                            for cat in active_categories:
                                st.markdown(f"**{cat['name']}** `{cat['code']}` - Score: {cat.get('score', 0)} | Boost: {cat.get('boostValue', 100)}")
                    
                    st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
                    
                    # Fetch products for both scenarios
                    with st.spinner("🔄 Fetching products..."):
                        # Control: With searchTerm, no category filter
                        control_products, control_error = fetch_products(selected_term, category_codes=None, limit=40, include_search_term=True)
                        
                        # AI Categories: Without searchTerm, only category filters
                        ai_products, ai_error = fetch_products(selected_term, category_codes=category_codes, limit=40, include_search_term=False)
                    
                    # Display any errors
                    if control_error:
                        st.error(control_error['message'])
                        with st.expander("🔍 Error Details (for debugging)"):
                            st.code(control_error['details'])
                    
                    if ai_error:
                        st.error(ai_error['message'])
                        with st.expander("🔍 Error Details (for debugging)"):
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
                        display: flex;
                        flex-direction: column;
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
                    
                    # Display comparison in two columns with visible separator
                    col_control, col_separator, col_ai = st.columns([10, 0.3, 10])
                    
                    with col_control:
                        st.markdown("""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #868e96; border: 2px solid #868e96;">
                            <h3 style="margin: 0; color: #495057;">📦 Control Response</h3>
                            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #6c757d;">No category filters applied</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"<p style='text-align: center; color: #868e96; margin-top: 10px; margin-bottom: 15px;'><strong>{len(control_products)}</strong> products found</p>", unsafe_allow_html=True)
                        
                        if control_products:
                            # Display products in 3-column grid
                            for i in range(0, len(control_products), 3):
                                cols = st.columns(3)
                                for j in range(3):
                                    if i + j < len(control_products):
                                        product = control_products[i + j]
                                        with cols[j]:
                                            # Product card
                                            with st.container():
                                                # Image
                                                if product['image']:
                                                    st.markdown(f'<img src="{product["image"]}" class="product-image" />', unsafe_allow_html=True)
                                                else:
                                                    st.markdown('<div style="width: 100%; height: 150px; background-color: #e9ecef; display: flex; align-items: center; justify-content: center; border-radius: 5px; margin-bottom: 8px;">📦</div>', unsafe_allow_html=True)
                                                
                                                # Product info
                                                st.markdown(f'<div class="product-name" title="{product["name"]}">{product["name"]}</div>', unsafe_allow_html=True)
                                                st.markdown(f'<div class="product-price">💰 Rp {product["price"]:,.0f}</div>', unsafe_allow_html=True)
                                                
                                                # Rating
                                                rating = product['rating']
                                                full_stars = int(rating)
                                                empty_stars = 5 - full_stars
                                                stars = "⭐" * full_stars + "☆" * empty_stars
                                                st.markdown(f'<div class="product-rating">{stars} {rating:.1f}/5.0</div>', unsafe_allow_html=True)
                        else:
                            st.info("No products found")
                    
                    # Vertical separator
                    with col_separator:
                        st.markdown("""
                        <div style="width: 3px; background: linear-gradient(to bottom, #868e96, #1971c2); height: 100%; min-height: 800px; margin: 0 auto; border-radius: 2px; box-shadow: 0 0 10px rgba(0,0,0,0.1);"></div>
                        """, unsafe_allow_html=True)
                    
                    with col_ai:
                        st.markdown("""
                        <div style="background-color: #e7f5ff; padding: 15px; border-radius: 10px; border-left: 5px solid #1971c2; border: 2px solid #1971c2;">
                            <h3 style="margin: 0; color: #1971c2;">🤖 AI Category Response</h3>
                            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #1864ab;">With AI-identified category filters</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"<p style='text-align: center; color: #1971c2; margin-top: 10px; margin-bottom: 15px;'><strong>{len(ai_products)}</strong> products found</p>", unsafe_allow_html=True)
                        
                        if ai_products:
                            # Display products in 3-column grid
                            for i in range(0, len(ai_products), 3):
                                cols = st.columns(3)
                                for j in range(3):
                                    if i + j < len(ai_products):
                                        product = ai_products[i + j]
                                        with cols[j]:
                                            # Product card
                                            with st.container():
                                                # Image
                                                if product['image']:
                                                    st.markdown(f'<img src="{product["image"]}" class="product-image" />', unsafe_allow_html=True)
                                                else:
                                                    st.markdown('<div style="width: 100%; height: 150px; background-color: #e9ecef; display: flex; align-items: center; justify-content: center; border-radius: 5px; margin-bottom: 8px;">📦</div>', unsafe_allow_html=True)
                                                
                                                # Product info
                                                st.markdown(f'<div class="product-name" title="{product["name"]}">{product["name"]}</div>', unsafe_allow_html=True)
                                                st.markdown(f'<div class="product-price">💰 Rp {product["price"]:,.0f}</div>', unsafe_allow_html=True)
                                                
                                                # Rating
                                                rating = product['rating']
                                                full_stars = int(rating)
                                                empty_stars = 5 - full_stars
                                                stars = "⭐" * full_stars + "☆" * empty_stars
                                                st.markdown(f'<div class="product-rating">{stars} {rating:.1f}/5.0</div>', unsafe_allow_html=True)
                        else:
                            st.info("No products found with applied category filters")
            
            # Show compact placeholder message if no comparison has been triggered
            elif not compare_button:
                st.info("👆 Select a term and click Compare")
