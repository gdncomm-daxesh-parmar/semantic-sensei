"""
Add sample edit history to some terms for testing
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import MONGODB_CONFIG

def add_sample_edits():
    """Add sample edit history to random terms"""
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_categories']
    
    print("Adding sample edit history...")
    print("=" * 60)
    
    # Get all terms
    all_terms = list(collection.find({}, {'searchTerm': 1, 'createdDate': 1, 'modelIdentifiedCategories': 1}))
    
    # Select random 10 terms to add edit history
    selected_terms = random.sample(all_terms, min(10, len(all_terms)))
    
    edit_actions = [
        ('boost_update', 'Updated boost for "{}" from 100 to 150'),
        ('boost_update', 'Updated boost for "{}" from 150 to 200'),
        ('boost_update', 'Updated boost for "{}" from 200 to 120'),
        ('category_added', 'Added category "{}" (boost: 100)'),
        ('category_removed', 'Removed category "{}"'),
    ]
    
    for term_doc in selected_terms:
        term = term_doc['searchTerm']
        created_date = term_doc.get('createdDate', datetime.utcnow())
        model_cats = term_doc.get('modelIdentifiedCategories', [])
        
        if not model_cats:
            continue
        
        # Generate 2-4 random edits
        num_edits = random.randint(2, 4)
        edits = []
        
        # Initial creation edit
        edits.append({
            'timestamp': created_date,
            'action': 'created',
            'details': 'Initial entry created'
        })
        
        # Add random edits between creation date and now
        days_diff = (datetime.utcnow() - created_date).days
        if days_diff < 1:
            days_diff = 5  # Minimum range
        
        for i in range(num_edits):
            # Random timestamp between creation and now
            days_offset = random.randint(1, max(2, days_diff))
            edit_time = created_date + timedelta(days=days_offset)
            
            # Random action
            action_type, detail_template = random.choice(edit_actions)
            
            # Get a random category name from the term
            cat_name = random.choice(model_cats)['name']
            details = detail_template.format(cat_name)
            
            edits.append({
                'timestamp': edit_time,
                'action': action_type,
                'details': details
            })
        
        # Sort by timestamp
        edits.sort(key=lambda x: x['timestamp'])
        
        # Update the document
        result = collection.update_one(
            {'searchTerm': term},
            {'$set': {'editHistory': edits}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Added {len(edits)} edits to '{term}'")
    
    print("=" * 60)
    print(f"Done! Added edit history to {len(selected_terms)} terms")
    
    client.close()

if __name__ == "__main__":
    add_sample_edits()

