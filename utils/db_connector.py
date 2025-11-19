"""
MongoDB connection utility
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import MONGODB_CONFIG, COLLECTIONS


class MongoDBConnector:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.uri = MONGODB_CONFIG['uri']
        self.database_name = MONGODB_CONFIG['database']
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            print("Connecting to MongoDB...")
            self.client = MongoClient(self.uri)
            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[self.database_name]
            print(f"✓ Successfully connected to MongoDB database: {self.database_name}")
            return True
            
        except ConnectionFailure as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            return False
        except ServerSelectionTimeoutError as e:
            print(f"✗ MongoDB server selection timeout: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error connecting to MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✓ MongoDB connection closed")
    
    def get_collection(self, collection_name):
        """Get a MongoDB collection"""
        if not self.db:
            raise Exception("Database not connected. Call connect() first.")
        return self.db[collection_name]
    
    def test_connection(self):
        """Test MongoDB connection and list collections"""
        if self.connect():
            try:
                # List all collections
                collections = self.db.list_collection_names()
                print(f"\nAvailable collections ({len(collections)}):")
                for col in collections:
                    count = self.db[col].count_documents({})
                    print(f"  - {col}: {count} documents")
                return True
            except Exception as e:
                print(f"Error testing connection: {e}")
                return False
            finally:
                self.disconnect()
        return False


def get_db_connection():
    """Get a MongoDB connection (convenience function)"""
    connector = MongoDBConnector()
    if connector.connect():
        return connector
    return None


if __name__ == "__main__":
    # Test the connection
    print("=" * 60)
    print("Testing MongoDB Connection")
    print("=" * 60)
    
    connector = MongoDBConnector()
    connector.test_connection()

