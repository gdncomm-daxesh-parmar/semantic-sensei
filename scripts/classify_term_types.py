"""
Classify search terms into boostingConfiguration or filterConfiguration
Based on intersection between catalog categories and model-identified categories
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_connector import get_db_connection


def classify_term_type(term_doc):
    """
    Classify a term based on catalog vs model category intersection
    
    Rules:
    1. If there's any intersection between catalog and model categories → boostingConfiguration
    2. If no intersection → filterConfiguration
    
    Args:
        term_doc: MongoDB document with catalogCategories and modelIdentifiedCategories
        
    Returns:
        str: 'boostingConfiguration' or 'filterConfiguration'
    """
    catalog_categories = term_doc.get('catalogCategories', [])
    model_categories = term_doc.get('modelIdentifiedCategories', [])
    
    # Extract category codes
    catalog_codes = set(cat['code'] for cat in catalog_categories if 'code' in cat)
    model_codes = set(cat['code'] for cat in model_categories if 'code' in cat)
    
    # Check for intersection
    intersection = catalog_codes & model_codes
    
    if intersection:
        return 'boostingConfiguration'
    else:
        return 'filterConfiguration'


def classify_all_terms():
    """
    Process all terms in the database and classify them
    Adds 'termType' field to each document
    """
    connector = get_db_connection()
    if not connector:
        print("✗ Failed to connect to MongoDB")
        return False
    
    try:
        collection = connector.get_collection('search_term_categories')
        
        print("=" * 70)
        print("Classifying Search Terms: Boosting vs Filter Configuration")
        print("=" * 70)
        
        # Get all terms
        all_terms = list(collection.find({}))
        total_terms = len(all_terms)
        
        print(f"\nProcessing {total_terms} terms...")
        
        boosting_count = 0
        filter_count = 0
        updated_count = 0
        
        for idx, term_doc in enumerate(all_terms, 1):
            term = term_doc['searchTerm']
            
            # Classify the term
            term_type = classify_term_type(term_doc)
            
            # Count
            if term_type == 'boostingConfiguration':
                boosting_count += 1
            else:
                filter_count += 1
            
            # Update the document
            result = collection.update_one(
                {'_id': term_doc['_id']},
                {
                    '$set': {
                        'termType': term_type,
                        'termTypeClassifiedDate': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
            
            # Progress indicator
            if idx % 100 == 0 or idx == total_terms:
                print(f"  Progress: {idx}/{total_terms} terms processed...")
        
        print("\n" + "=" * 70)
        print("Classification Complete!")
        print("=" * 70)
        print(f"\n📊 Results:")
        print(f"  Total terms processed: {total_terms}")
        print(f"  Updated terms: {updated_count}")
        print(f"  🎯 Boosting Configuration: {boosting_count} ({boosting_count/total_terms*100:.1f}%)")
        print(f"  🔍 Filter Configuration: {filter_count} ({filter_count/total_terms*100:.1f}%)")
        
        # Show some examples
        print(f"\n📋 Sample Classifications:")
        boosting_samples = list(collection.find({'termType': 'boostingConfiguration'}).limit(3))
        filter_samples = list(collection.find({'termType': 'filterConfiguration'}).limit(3))
        
        print(f"\n  Boosting Configuration Examples:")
        for sample in boosting_samples:
            catalog_codes = [cat['code'] for cat in sample.get('catalogCategories', [])]
            model_codes = [cat['code'] for cat in sample.get('modelIdentifiedCategories', [])]
            intersection = set(catalog_codes) & set(model_codes)
            print(f"    • '{sample['searchTerm']}' - Intersection: {len(intersection)} categories")
        
        print(f"\n  Filter Configuration Examples:")
        for sample in filter_samples:
            catalog_count = len(sample.get('catalogCategories', []))
            model_count = len(sample.get('modelIdentifiedCategories', []))
            print(f"    • '{sample['searchTerm']}' - Catalog: {catalog_count}, Model: {model_count}, No overlap")
        
        print("\n" + "=" * 70)
        
        return True
        
    except Exception as e:
        print(f"✗ Error during classification: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        connector.disconnect()


def show_term_classification(search_term):
    """
    Show the classification details for a specific term
    """
    connector = get_db_connection()
    if not connector:
        print("✗ Failed to connect to MongoDB")
        return
    
    try:
        collection = connector.get_collection('search_term_categories')
        term_doc = collection.find_one({'searchTerm': search_term})
        
        if not term_doc:
            print(f"✗ Term '{search_term}' not found")
            return
        
        term_type = classify_term_type(term_doc)
        
        catalog_categories = term_doc.get('catalogCategories', [])
        model_categories = term_doc.get('modelIdentifiedCategories', [])
        
        catalog_codes = set(cat['code'] for cat in catalog_categories)
        model_codes = set(cat['code'] for cat in model_categories)
        intersection = catalog_codes & model_codes
        
        print("=" * 70)
        print(f"Classification Details: '{search_term}'")
        print("=" * 70)
        print(f"\n🏷️  Term Type: {term_type}")
        print(f"\n📚 Catalog Categories ({len(catalog_categories)}):")
        for cat in catalog_categories[:5]:
            print(f"    • {cat['code']} - {cat['name']}")
        if len(catalog_categories) > 5:
            print(f"    ... and {len(catalog_categories) - 5} more")
        
        print(f"\n🤖 Model Identified Categories ({len(model_categories)}):")
        for cat in model_categories[:5]:
            print(f"    • {cat['code']} - {cat['name']}")
        if len(model_categories) > 5:
            print(f"    ... and {len(model_categories) - 5} more")
        
        print(f"\n🔗 Intersection ({len(intersection)}):")
        if intersection:
            for code in list(intersection)[:5]:
                # Find the category name
                cat_name = next((cat['name'] for cat in catalog_categories if cat['code'] == code), 'Unknown')
                print(f"    • {code} - {cat_name}")
        else:
            print("    (No common categories)")
        
        print("\n" + "=" * 70)
        
    finally:
        connector.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Classify search terms')
    parser.add_argument('--term', type=str, help='Show classification for a specific term')
    parser.add_argument('--classify-all', action='store_true', help='Classify all terms in database')
    
    args = parser.parse_args()
    
    if args.term:
        show_term_classification(args.term)
    elif args.classify_all:
        classify_all_terms()
    else:
        # Default: classify all
        classify_all_terms()

