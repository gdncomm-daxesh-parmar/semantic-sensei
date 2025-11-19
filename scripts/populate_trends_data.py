"""
Populate random CTR/CVR trends data for testing
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_connector import get_db_connection


def generate_random_trends(num_points=10):
    """Generate random CTR and CVR trend data"""
    ctr_data = []
    cvr_data = []
    timestamps = []
    
    # Generate data for the last num_points days
    base_date = datetime.now() - timedelta(days=num_points)
    
    for i in range(num_points):
        # Generate random CTR (0.05 to 0.8)
        ctr = round(random.uniform(0.05, 0.8), 3)
        ctr_data.append(ctr)
        
        # Generate random CVR (0.01 to 0.5)
        cvr = round(random.uniform(0.01, 0.5), 3)
        cvr_data.append(cvr)
        
        # Add timestamp
        timestamp = base_date + timedelta(days=i)
        timestamps.append(timestamp.strftime('%Y-%m-%d'))
    
    return {
        'ctr': ctr_data,
        'cvr': cvr_data,
        'timestamps': timestamps
    }


def populate_trends():
    """Populate trends data for all search terms"""
    connector = get_db_connection()
    if not connector:
        print("Failed to connect to MongoDB")
        return
    
    try:
        terms_collection = connector.get_collection('search_term_categories')
        trends_collection = connector.get_collection('search_term_trends')
        
        # Get all search terms
        terms = list(terms_collection.find({}, {'searchTerm': 1}))
        
        print("=" * 60)
        print("Populating CTR/CVR Trends Data")
        print("=" * 60)
        print(f"\nProcessing {len(terms)} terms...")
        
        # Clear existing trends data
        trends_collection.delete_many({})
        
        trends_docs = []
        for term_doc in terms:
            term = term_doc['searchTerm']
            
            # Generate random trends
            trends = generate_random_trends(num_points=15)
            
            trends_doc = {
                'searchTerm': term,
                'ctr': trends['ctr'],
                'cvr': trends['cvr'],
                'timestamps': trends['timestamps'],
                'lastUpdated': datetime.now()
            }
            
            trends_docs.append(trends_doc)
        
        # Insert all trends
        if trends_docs:
            result = trends_collection.insert_many(trends_docs)
            print(f"\n✓ Inserted {len(result.inserted_ids)} trend records")
        
        # Show sample
        sample = trends_collection.find_one()
        if sample:
            print(f"\nSample trend data for '{sample['searchTerm']}':")
            print(f"  CTR: {sample['ctr'][:5]}...")
            print(f"  CVR: {sample['cvr'][:5]}...")
            print(f"  Dates: {sample['timestamps'][:5]}...")
        
        print("\n" + "=" * 60)
        print("✓ Trends data populated successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        connector.disconnect()


if __name__ == "__main__":
    populate_trends()

