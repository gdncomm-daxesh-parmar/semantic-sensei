"""
Load combined search term data into MongoDB
Combines catalog categories and model predictions
"""

import csv
import sys
import os
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_connector import get_db_connection


def read_catalog_categories(csv_file):
    """
    Read catalog categories from term_to_category_detailed.csv
    Returns: dict with term as key and list of categories
    """
    catalog_data = defaultdict(list)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row['SearchTerm'].strip()
            code = row['C3Code'].strip()
            name = row['C3Label'].strip()
            count = int(row['Count']) if row['Count'] else 0
            
            # Skip empty entries
            if not code or not name:
                continue
            
            catalog_data[term].append({
                'code': code,
                'name': name
            })
    
    print(f"✓ Loaded catalog categories for {len(catalog_data)} terms")
    return catalog_data


def read_model_predictions(csv_file):
    """
    Read model predictions from model_predictions.csv
    Returns: dict with term as key and list of predictions
    """
    model_data = defaultdict(list)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row['Term'].strip()
            code = row['CategoryCode'].strip()
            name = row['CategoryName'].strip()
            score = int(row['Score']) if row['Score'] else 0
            
            model_data[term].append({
                'code': code,
                'name': name,
                'score': score,
                'boostValue': 100  # Default boost value
            })
    
    print(f"✓ Loaded model predictions for {len(model_data)} terms")
    return model_data


def create_combined_documents(catalog_data, model_data):
    """
    Combine catalog and model data into MongoDB documents
    """
    documents = []
    
    # Get all unique terms
    all_terms = set(catalog_data.keys()) | set(model_data.keys())
    
    for term in all_terms:
        doc = {
            'searchTerm': term,
            'catalogCategories': catalog_data.get(term, []),
            'modelIdentifiedCategories': model_data.get(term, [])
        }
        documents.append(doc)
    
    print(f"✓ Created {len(documents)} combined documents")
    return documents


def insert_to_mongo(documents, collection_name='search_term_categories'):
    """
    Insert documents into MongoDB
    """
    connector = get_db_connection()
    if not connector:
        print("✗ Failed to connect to MongoDB")
        return False
    
    try:
        collection = connector.get_collection(collection_name)
        
        # Clear existing data (optional - comment out if you want to keep old data)
        print(f"\nClearing existing data in collection '{collection_name}'...")
        result = collection.delete_many({})
        print(f"  Deleted {result.deleted_count} existing documents")
        
        # Insert new documents
        print(f"\nInserting {len(documents)} documents...")
        result = collection.insert_many(documents)
        print(f"✓ Successfully inserted {len(result.inserted_ids)} documents")
        
        # Show sample document
        sample = collection.find_one()
        if sample:
            print(f"\nSample document:")
            print(f"  searchTerm: {sample['searchTerm']}")
            print(f"  catalogCategories: {len(sample.get('catalogCategories', []))} entries")
            print(f"  modelIdentifiedCategories: {len(sample.get('modelIdentifiedCategories', []))} entries")
            
            if sample.get('catalogCategories'):
                print(f"\n  First catalog category:")
                print(f"    {sample['catalogCategories'][0]}")
            
            if sample.get('modelIdentifiedCategories'):
                print(f"\n  First model prediction:")
                print(f"    {sample['modelIdentifiedCategories'][0]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error inserting documents: {e}")
        return False
    
    finally:
        connector.disconnect()


def main():
    """Main function"""
    print("=" * 70)
    print("Loading Search Term Data to MongoDB")
    print("=" * 70)
    
    # File paths
    base_dir = "/Users/daxeshparmar/PycharmProjects/semantic-sensei/data"
    catalog_file = f"{base_dir}/term_to_category_detailed.csv"
    model_file = f"{base_dir}/model_predictions.csv"
    
    # Read data
    print("\n1. Reading data files...")
    catalog_data = read_catalog_categories(catalog_file)
    model_data = read_model_predictions(model_file)
    
    # Combine data
    print("\n2. Combining data...")
    documents = create_combined_documents(catalog_data, model_data)
    
    # Show statistics
    print("\n3. Data Statistics:")
    terms_with_both = sum(1 for doc in documents if doc['catalogCategories'] and doc['modelIdentifiedCategories'])
    terms_catalog_only = sum(1 for doc in documents if doc['catalogCategories'] and not doc['modelIdentifiedCategories'])
    terms_model_only = sum(1 for doc in documents if not doc['catalogCategories'] and doc['modelIdentifiedCategories'])
    
    print(f"  Total terms: {len(documents)}")
    print(f"  Terms with catalog & model data: {terms_with_both}")
    print(f"  Terms with catalog only: {terms_catalog_only}")
    print(f"  Terms with model predictions only: {terms_model_only}")
    
    # Insert to MongoDB
    print("\n4. Inserting to MongoDB...")
    collection_name = 'search_term_categories'
    success = insert_to_mongo(documents, collection_name)
    
    if success:
        print(f"\n{'=' * 70}")
        print(f"✓ Data successfully loaded to MongoDB collection: '{collection_name}'")
        print(f"{'=' * 70}")
    else:
        print(f"\n{'=' * 70}")
        print(f"✗ Failed to load data to MongoDB")
        print(f"{'=' * 70}")


if __name__ == "__main__":
    main()

