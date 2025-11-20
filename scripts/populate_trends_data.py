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


def generate_random_trends(start_date=None, num_points=10, trend_type='neutral'):
    """Generate CTR and CVR trend data with specific patterns
    
    Args:
        start_date: Starting date for trends
        num_points: Number of data points
        trend_type: 'upward', 'downward', or 'neutral'
    """
    ctr_data = []
    cvr_data = []
    timestamps = []
    
    # If start_date not provided, use last num_points days from now
    if start_date is None:
        base_date = datetime.now() - timedelta(days=num_points)
    else:
        base_date = start_date
    
    # Starting point for CTR
    base_ctr = random.uniform(0.15, 0.35)
    
    for i in range(num_points):
        # Generate CTR based on trend type
        if trend_type == 'upward':
            # Gradual upward trend with some noise
            trend_component = (i / num_points) * 0.3  # Up to 30% increase
            noise = random.uniform(-0.02, 0.05)  # Slightly positive bias
            ctr = round(min(0.8, base_ctr + trend_component + noise), 3)
        elif trend_type == 'downward':
            # Gradual downward trend with some noise
            trend_component = (i / num_points) * -0.2  # Up to 20% decrease
            noise = random.uniform(-0.05, 0.02)  # Slightly negative bias
            ctr = round(max(0.05, base_ctr + trend_component + noise), 3)
        else:  # neutral
            # Random fluctuation around base
            noise = random.uniform(-0.1, 0.1)
            ctr = round(max(0.05, min(0.8, base_ctr + noise)), 3)
        
        ctr_data.append(ctr)
        
        # CVR follows similar pattern but with smaller values
        cvr = round(ctr * random.uniform(0.3, 0.6), 3)
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
        
        # Get all search terms with their creation dates
        terms = list(terms_collection.find({}, {'searchTerm': 1, 'createdDate': 1}))
        
        print("=" * 60)
        print("Populating CTR/CVR Trends Data")
        print("=" * 60)
        print(f"\nProcessing {len(terms)} terms...")
        
        # Clear existing trends data
        trends_collection.delete_many({})
        
        trends_docs = []
        trend_types = ['upward', 'downward', 'neutral']
        
        for idx, term_doc in enumerate(terms):
            term = term_doc['searchTerm']
            created_date = term_doc.get('createdDate')
            
            # Distribute trend types evenly
            trend_type = trend_types[idx % 3]
            
            # Calculate number of days since creation
            if created_date:
                days_since_creation = (datetime.now() - created_date).days
                # Generate trends from creation date, at least 5 days
                num_points = max(5, min(days_since_creation + 1, 30))
                trends = generate_random_trends(start_date=created_date, num_points=num_points, trend_type=trend_type)
            else:
                # Default to 15 days if no creation date
                trends = generate_random_trends(num_points=15, trend_type=trend_type)
            
            # Calculate the actual trend status from generated data
            if len(trends['ctr']) >= 5:
                recent_ctrs = trends['ctr'][-5:]
                first_ctr = recent_ctrs[0]
                last_ctr = recent_ctrs[-1]
                pct_change = ((last_ctr - first_ctr) / first_ctr * 100) if first_ctr > 0 else 0
                
                # Determine actual status based on data
                if pct_change < -1:
                    calculated_status = 'underperforming'
                elif pct_change > 1:
                    calculated_status = 'improvement'
                else:
                    calculated_status = 'neutral'
            else:
                calculated_status = 'neutral'
            
            trends_doc = {
                'searchTerm': term,
                'ctr': trends['ctr'],
                'cvr': trends['cvr'],
                'timestamps': trends['timestamps'],
                'trendType': calculated_status,  # Store the actual calculated trend
                'lastUpdated': datetime.now()
            }
            
            trends_docs.append(trends_doc)
            
        print(f"  Generated trends: ~{len(terms)//3} upward, ~{len(terms)//3} downward, ~{len(terms)//3} neutral")
        
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

