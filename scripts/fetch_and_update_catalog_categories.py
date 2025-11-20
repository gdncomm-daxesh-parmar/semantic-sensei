"""
Fetch catalog categories for all terms and update MongoDB
"""

import sys
import os
import time
import requests
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import MONGODB_CONFIG
from pymongo import MongoClient

# Import headers and cookies from scrapper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scrapper')))
from fetchTermToCategoryMapping import HEADERS, COOKIES, SEARCH_API_URL, extract_c3_categories

def fetch_catalog_categories_for_term(search_term):
    """Fetch catalog categories for a single term"""
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
                    
                    # Convert to the format needed for MongoDB
                    catalog_categories = []
                    for c3 in c3_categories:
                        catalog_categories.append({
                            'code': c3['code'],
                            'name': c3['label']  # Use 'label' from extract_c3_categories
                        })
                    
                    return catalog_categories, None
        
        # No categories found
        return [], None
        
    except Exception as e:
        return [], str(e)


def update_all_catalog_categories():
    """Fetch and update catalog categories for all terms"""
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_categories']
    
    # Get all terms that don't have catalog categories or have empty ones
    terms = list(collection.find({
        '$or': [
            {'catalogCategories': {'$exists': False}},
            {'catalogCategories': {'$size': 0}}
        ]
    }, {'searchTerm': 1}))
    
    print("=" * 70)
    print("FETCHING CATALOG CATEGORIES FOR ALL TERMS")
    print("=" * 70)
    print(f"\nFound {len(terms)} terms without catalog categories")
    print("This will take some time due to rate limiting (1 sec delay per request)")
    print()
    
    success_count = 0
    error_count = 0
    
    for idx, term_doc in enumerate(terms, 1):
        term = term_doc['searchTerm']
        
        print(f"[{idx}/{len(terms)}] Fetching categories for '{term}'...", end=' ')
        
        # Fetch categories
        catalog_categories, error = fetch_catalog_categories_for_term(term)
        
        if error:
            print(f"❌ Error: {error}")
            error_count += 1
        else:
            # Update MongoDB
            result = collection.update_one(
                {'searchTerm': term},
                {
                    '$set': {
                        'catalogCategories': catalog_categories,
                        'updatedDate': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Added {len(catalog_categories)} categories")
                success_count += 1
            else:
                print("⚠️  No update needed")
        
        # Rate limiting - wait 1 second between requests
        if idx < len(terms):
            time.sleep(1)
    
    print()
    print("=" * 70)
    print(f"✅ Successfully updated: {success_count}")
    print(f"❌ Errors: {error_count}")
    print("=" * 70)
    
    client.close()


if __name__ == "__main__":
    update_all_catalog_categories()

