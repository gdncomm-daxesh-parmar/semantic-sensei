"""
Add sample edit history to terms with specific past dates
Creates 2-3 edits with dates like N-10, N-4 days ago
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import MONGODB_CONFIG

def add_dated_edits():
    """Add sample edit history with specific past dates"""
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_categories']
    
    print("=" * 70)
    print("Adding Sample Edit History with Past Dates")
    print("=" * 70)
    
    # Get all terms with model categories
    all_terms = list(collection.find(
        {'modelIdentifiedCategories': {'$exists': True, '$ne': []}},
        {'searchTerm': 1, 'createdDate': 1, 'modelIdentifiedCategories': 1}
    ))
    
    if not all_terms:
        print("No terms found with model categories")
        client.close()
        return
    
    # Select random 5 terms to add edit history
    terms_to_edit = random.sample(all_terms, min(5, len(all_terms)))
    
    from datetime import timezone
    today = datetime.now(timezone.utc).replace(tzinfo=None)  # UTC without timezone info
    
    edit_templates = [
        ('boost_update', 'Updated boost for "{}" from {} to {}'),
        ('category_added', 'Added category "{}" (boost: {})'),
        ('category_removed', 'Removed category "{}"'),
    ]
    
    for term_doc in terms_to_edit:
        term = term_doc['searchTerm']
        created_date = term_doc.get('createdDate', today - timedelta(days=20))
        model_cats = term_doc.get('modelIdentifiedCategories', [])
        
        if not model_cats:
            continue
        
        # Determine number of edits (2 or 3)
        num_edits = random.choice([2, 3])
        
        # Create edit history with specific past dates
        edits = []
        
        # Initial creation edit
        edits.append({
            'timestamp': created_date,
            'action': 'created',
            'details': 'Initial entry created'
        })
        
        # Generate edits with specific past dates
        # Example: If today is N, create edits at N-10, N-4, etc.
        past_days = [10, 7, 4, 2]  # Days ago
        selected_days = random.sample(past_days, num_edits)
        selected_days.sort(reverse=True)  # Oldest first, most recent last
        
        for days_ago in selected_days:
            # Subtract days to go into the past
            edit_date = today - timedelta(days=days_ago)
            
            # Ensure edit date is after creation date
            if edit_date < created_date:
                edit_date = created_date + timedelta(days=1)
            
            # Random action
            action_type, detail_template = random.choice(edit_templates)
            
            # Get a random category name
            cat_name = random.choice(model_cats)['name']
            
            # Create details based on action type
            if action_type == 'boost_update':
                old_boost = random.choice([100, 150, 200])
                new_boost = random.choice([120, 150, 180, 200])
                details = detail_template.format(cat_name, old_boost, new_boost)
            elif action_type == 'category_added':
                boost = random.choice([100, 120, 150])
                details = detail_template.format(cat_name, boost)
            else:  # category_removed
                details = detail_template.format(cat_name)
            
            edits.append({
                'timestamp': edit_date,
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
            print(f"✅ Added {len(edits)-1} edits to '{term}'")
            for edit in edits[1:]:  # Skip creation edit
                days_ago = (today - edit['timestamp']).days
                print(f"   {edit['timestamp'].strftime('%Y-%m-%d')} (N-{days_ago}): {edit['action']}")
    
    print("=" * 70)
    print(f"Done! Added edit history to {len(terms_to_edit)} terms")
    print("=" * 70)
    
    client.close()

if __name__ == "__main__":
    add_dated_edits()

