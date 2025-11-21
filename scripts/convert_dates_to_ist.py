"""
Convert all UTC dates to IST in the database
- search_term_categories: createdDate, updatedDate, editHistory timestamps
- search_term_trends: timestamps (date strings)
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import MONGODB_CONFIG

IST_OFFSET = timedelta(hours=5, minutes=30)

def utc_to_ist(utc_dt):
    """Convert UTC datetime to IST"""
    if utc_dt is None:
        return None
    return utc_dt + IST_OFFSET

def convert_categories_to_ist():
    """Convert dates in search_term_categories to IST"""
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_categories']
    
    print("Converting search_term_categories to IST...")
    
    count = 0
    for doc in collection.find({}):
        updates = {}
        
        # Convert createdDate
        if 'createdDate' in doc and doc['createdDate']:
            updates['createdDate'] = utc_to_ist(doc['createdDate'])
        
        # Convert updatedDate
        if 'updatedDate' in doc and doc['updatedDate']:
            updates['updatedDate'] = utc_to_ist(doc['updatedDate'])
        
        # Convert editHistory timestamps
        if 'editHistory' in doc and doc['editHistory']:
            new_history = []
            for edit in doc['editHistory']:
                if 'timestamp' in edit and edit['timestamp']:
                    edit['timestamp'] = utc_to_ist(edit['timestamp'])
                new_history.append(edit)
            updates['editHistory'] = new_history
        
        # Convert termTypeClassifiedDate
        if 'termTypeClassifiedDate' in doc and doc['termTypeClassifiedDate']:
            updates['termTypeClassifiedDate'] = utc_to_ist(doc['termTypeClassifiedDate'])
        
        if updates:
            collection.update_one({'_id': doc['_id']}, {'$set': updates})
            count += 1
    
    print(f"✅ Updated {count} documents in search_term_categories")
    client.close()

def convert_trends_to_ist():
    """Convert date strings in search_term_trends to IST"""
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_trends']
    
    print("Converting search_term_trends timestamps to IST...")
    
    count = 0
    for doc in collection.find({}):
        updates = {}
        
        # Convert timestamp strings (YYYY-MM-DD format remains same in IST)
        # Since timestamps are date strings only, we keep them as is
        # Only convert lastUpdated datetime
        if 'lastUpdated' in doc and doc['lastUpdated']:
            updates['lastUpdated'] = utc_to_ist(doc['lastUpdated'])
        
        if updates:
            collection.update_one({'_id': doc['_id']}, {'$set': updates})
            count += 1
    
    print(f"✅ Updated {count} documents in search_term_trends")
    client.close()

def main():
    print("=" * 70)
    print("Converting All Dates from UTC to IST")
    print("=" * 70)
    print()
    
    convert_categories_to_ist()
    print()
    convert_trends_to_ist()
    
    print()
    print("=" * 70)
    print("✅ All dates converted to IST successfully!")
    print("=" * 70)

if __name__ == "__main__":
    main()

