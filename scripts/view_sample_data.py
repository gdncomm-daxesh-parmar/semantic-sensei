"""
View sample data from MongoDB collection
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_connector import get_db_connection


def view_samples():
    """View sample documents from the collection"""
    connector = get_db_connection()
    if not connector:
        return
    
    try:
        collection = connector.get_collection('search_term_categories')
        
        print("=" * 70)
        print("Sample Documents from 'search_term_categories' Collection")
        print("=" * 70)
        
        # Count total documents
        total = collection.count_documents({})
        print(f"\nTotal documents: {total}")
        
        # Find a term with both catalog and model data
        print("\n" + "=" * 70)
        print("1. Term with BOTH catalog & model predictions:")
        print("=" * 70)
        
        doc_with_both = collection.find_one({
            'catalogCategories': {'$ne': []},
            'modelIdentifiedCategories': {'$ne': []}
        })
        
        if doc_with_both:
            print(f"\nSearch Term: '{doc_with_both['searchTerm']}'")
            print(f"\nCatalog Categories ({len(doc_with_both['catalogCategories'])} total):")
            for i, cat in enumerate(doc_with_both['catalogCategories'][:3], 1):
                print(f"  {i}. {cat['name']} ({cat['code']}) - Count: {cat['count']}")
            
            print(f"\nModel Identified Categories ({len(doc_with_both['modelIdentifiedCategories'])} total):")
            for i, cat in enumerate(doc_with_both['modelIdentifiedCategories'], 1):
                print(f"  {i}. {cat['name']} ({cat['code']}) - Score: {cat['score']}, Boost: {cat['boostValue']}")
        
        # Find a term with only catalog data
        print("\n" + "=" * 70)
        print("2. Term with ONLY catalog categories:")
        print("=" * 70)
        
        doc_catalog_only = collection.find_one({
            'catalogCategories': {'$ne': []},
            'modelIdentifiedCategories': []
        })
        
        if doc_catalog_only:
            print(f"\nSearch Term: '{doc_catalog_only['searchTerm']}'")
            print(f"\nCatalog Categories ({len(doc_catalog_only['catalogCategories'])} total):")
            for i, cat in enumerate(doc_catalog_only['catalogCategories'][:5], 1):
                print(f"  {i}. {cat['name']} ({cat['code']}) - Count: {cat['count']}")
            print(f"\nModel Identified Categories: None")
        
        # Show complete JSON structure of one document
        print("\n" + "=" * 70)
        print("3. Complete JSON structure (sample):")
        print("=" * 70)
        
        sample = collection.find_one({'searchTerm': 'adidas'})
        if sample:
            # Remove MongoDB _id for cleaner display
            sample.pop('_id', None)
            print(json.dumps(sample, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        connector.disconnect()


if __name__ == "__main__":
    view_samples()

