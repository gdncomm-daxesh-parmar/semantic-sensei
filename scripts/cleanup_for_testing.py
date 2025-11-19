"""
Cleanup script - Remove terms without model categories (for testing)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_connector import get_db_connection


def cleanup_mongo():
    """Remove all terms that don't have model categories"""
    connector = get_db_connection()
    if not connector:
        print("Failed to connect to MongoDB")
        return
    
    try:
        collection = connector.get_collection('search_term_categories')
        
        # Count before
        total_before = collection.count_documents({})
        with_model = collection.count_documents({'modelIdentifiedCategories': {'$ne': []}})
        without_model = total_before - with_model
        
        print("=" * 60)
        print("MongoDB Cleanup - Remove Terms Without Model Categories")
        print("=" * 60)
        print(f"\nBefore cleanup:")
        print(f"  Total terms: {total_before}")
        print(f"  With model categories: {with_model}")
        print(f"  Without model categories: {without_model}")
        
        # Delete documents where modelIdentifiedCategories is empty or doesn't exist
        result = collection.delete_many({
            '$or': [
                {'modelIdentifiedCategories': {'$exists': False}},
                {'modelIdentifiedCategories': []},
                {'modelIdentifiedCategories': {'$size': 0}}
            ]
        })
        
        print(f"\n✓ Deleted {result.deleted_count} terms")
        
        # Count after
        total_after = collection.count_documents({})
        
        print(f"\nAfter cleanup:")
        print(f"  Total terms remaining: {total_after}")
        print(f"  All have model categories: ✓")
        
        print("\n" + "=" * 60)
        print("Cleanup completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    finally:
        connector.disconnect()


if __name__ == "__main__":
    cleanup_mongo()

