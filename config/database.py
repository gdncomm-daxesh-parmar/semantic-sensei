"""
Database configuration for MongoDB connection
"""

# MongoDB Configuration
MONGODB_CONFIG = {
    'uri': 'mongodb://xsearch_user:FE37k4MUjkvJ@central-mongo-v60-01.qa2-sg.cld:27017,central-mongo-v60-02.qa2-sg.cld:27017/xsearch?connectTimeoutMS=30000&socketTimeoutMS=30000&readPreference=secondaryPreferred',
    'database': 'xsearch',
    'connect_timeout_ms': 30000,
    'socket_timeout_ms': 30000,
    'read_preference': 'secondaryPreferred'
}

# MongoDB Connection Settings
MONGODB_HOSTS = [
    'central-mongo-v60-01.qa2-sg.cld:27017',
    'central-mongo-v60-02.qa2-sg.cld:27017'
]

MONGODB_CREDENTIALS = {
    'username': 'xsearch_user',
    'password': 'FE37k4MUjkvJ'
}

# Collection Names (add your collection names here)
COLLECTIONS = {
    'search_terms': 'search_terms',
    'categories': 'categories',
    'mappings': 'term_category_mappings'
}

