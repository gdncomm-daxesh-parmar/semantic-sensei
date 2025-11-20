"""
Initialize status and editHistory fields for existing MongoDB documents
"""

from pymongo import MongoClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import MONGODB_CONFIG

def initialize_fields():
    """Initialize status and editHistory fields for all documents"""
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_categories']
    
    print("Initializing status and editHistory fields...")
    print("=" * 60)
    
    # Count documents without status field
    docs_without_status = collection.count_documents({'status': {'$exists': False}})
    print(f"Documents without status field: {docs_without_status}")
    
    if docs_without_status > 0:
        # Update all documents without status to 'in_progress'
        result = collection.update_many(
            {'status': {'$exists': False}},
            {'$set': {'status': 'in_progress'}}
        )
        print(f"✅ Updated {result.modified_count} documents with status='in_progress'")
    
    # Count documents without editHistory field
    docs_without_history = collection.count_documents({'editHistory': {'$exists': False}})
    print(f"Documents without editHistory field: {docs_without_history}")
    
    if docs_without_history > 0:
        # Initialize editHistory as empty array with creation entry
        for doc in collection.find({'editHistory': {'$exists': False}}):
            created_date = doc.get('createdDate', datetime.utcnow())
            initial_history = [{
                'timestamp': created_date,
                'action': 'created',
                'details': 'Initial entry created'
            }]
            
            collection.update_one(
                {'_id': doc['_id']},
                {'$set': {'editHistory': initial_history}}
            )
        
        print(f"✅ Initialized editHistory for {docs_without_history} documents")
    
    print("=" * 60)
    print("Done!")
    
    # Show summary
    total_docs = collection.count_documents({})
    in_progress = collection.count_documents({'status': 'in_progress'})
    locked = collection.count_documents({'status': 'locked'})
    
    print(f"\nSummary:")
    print(f"  Total documents: {total_docs}")
    print(f"  In Progress: {in_progress}")
    print(f"  Locked: {locked}")
    
    client.close()

if __name__ == "__main__":
    initialize_fields()

