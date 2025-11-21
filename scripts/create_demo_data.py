"""
Create realistic demo data for selected terms
- Clean up all existing edits
- Select 10-15 terms for demo
- Create realistic edit history with specific dates
- Generate CTR trends showing improvement/underperforming/neutral
"""

from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import MONGODB_CONFIG


def clean_all_edits():
    """Remove edit history from all terms"""
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_categories']
    
    result = collection.update_many(
        {},
        {'$set': {'editHistory': []}}
    )
    
    print(f"✅ Cleaned edit history from {result.modified_count} terms")
    client.close()


def select_demo_terms():
    """Select 12 diverse terms for demo (4 improvement, 4 underperforming, 4 neutral)"""
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_categories']
    
    # Get all terms with model categories
    all_terms = list(collection.find(
        {
            'modelIdentifiedCategories': {'$exists': True, '$ne': []},
            'catalogCategories': {'$exists': True, '$ne': []}
        },
        {'searchTerm': 1, 'modelIdentifiedCategories': 1}
    ).limit(50))
    
    # Select 12 diverse terms
    selected = random.sample(all_terms, min(12, len(all_terms)))
    client.close()
    
    return [term['searchTerm'] for term in selected]


def generate_ctr_trend(days, trend_type):
    """
    Generate CTR trend data based on trend type
    
    Args:
        days: Number of days to generate
        trend_type: 'improvement', 'underperforming', or 'neutral'
    
    Returns:
        List of CTR values
    """
    base_ctr = round(random.uniform(0.20, 0.30), 3)
    ctr_values = []
    
    for i in range(days):
        if trend_type == 'improvement':
            # Gradual upward trend
            progress = i / days
            trend_component = progress * 0.20  # Up to 20% increase
            noise = random.uniform(-0.02, 0.03)
            ctr = round(min(0.60, base_ctr + trend_component + noise), 3)
        
        elif trend_type == 'underperforming':
            # Gradual downward trend
            progress = i / days
            trend_component = progress * -0.15  # Up to 15% decrease
            noise = random.uniform(-0.03, 0.02)
            ctr = round(max(0.05, base_ctr + trend_component + noise), 3)
        
        else:  # neutral
            # Random fluctuation around base
            noise = random.uniform(-0.05, 0.05)
            ctr = round(max(0.05, min(0.50, base_ctr + noise)), 3)
        
        ctr_values.append(ctr)
    
    return ctr_values


def create_demo_data(demo_terms):
    """
    Create realistic demo data for selected terms
    
    Timeline:
    - D-5: Entry created
    - D-3: Added category with boost N
    - D-1: Boost changed for any category
    """
    client = MongoClient(MONGODB_CONFIG['uri'])
    db = client[MONGODB_CONFIG['database']]
    collection = db['search_term_categories']
    trends_collection = db['search_term_trends']
    
    today = datetime.now(timezone.utc).replace(tzinfo=None, hour=12, minute=0, second=0, microsecond=0)
    
    # Divide terms into three groups
    num_terms = len(demo_terms)
    improvement_terms = demo_terms[:num_terms//3]
    underperforming_terms = demo_terms[num_terms//3:2*num_terms//3]
    neutral_terms = demo_terms[2*num_terms//3:]
    
    print("\n" + "=" * 70)
    print("DEMO TERMS CLASSIFICATION")
    print("=" * 70)
    print(f"\n📈 IMPROVEMENT ({len(improvement_terms)} terms):")
    for term in improvement_terms:
        print(f"  • {term}")
    
    print(f"\n📉 UNDERPERFORMING ({len(underperforming_terms)} terms):")
    for term in underperforming_terms:
        print(f"  • {term}")
    
    print(f"\n➡️ NEUTRAL ({len(neutral_terms)} terms):")
    for term in neutral_terms:
        print(f"  • {term}")
    
    print("\n" + "=" * 70)
    print("CREATING DEMO DATA")
    print("=" * 70)
    
    for term in demo_terms:
        # Determine trend type
        if term in improvement_terms:
            trend_type = 'improvement'
        elif term in underperforming_terms:
            trend_type = 'underperforming'
        else:
            trend_type = 'neutral'
        
        # Get term data
        term_data = collection.find_one({'searchTerm': term})
        if not term_data:
            continue
        
        model_cats = term_data.get('modelIdentifiedCategories', [])
        if not model_cats:
            continue
        
        # Timeline
        d_minus_5 = today - timedelta(days=5)
        d_minus_3 = today - timedelta(days=3)
        d_minus_1 = today - timedelta(days=1)
        
        # Create edit history
        edits = []
        
        # D-5: Entry created
        edits.append({
            'timestamp': d_minus_5,
            'action': 'created',
            'details': 'Initial entry created with AI predictions'
        })
        
        # D-3: Added category with specific boost
        if len(model_cats) > 1:
            new_cat = random.choice(model_cats[1:])
            boost_value = random.choice([120, 150, 180])
            edits.append({
                'timestamp': d_minus_3,
                'action': 'category_added',
                'details': f"Added category '{new_cat['name']}' (boost: {boost_value})"
            })
        
        # D-1: Boost changed
        cat_to_change = random.choice(model_cats)
        old_boost = 100
        new_boost = random.choice([120, 150, 200])
        edits.append({
            'timestamp': d_minus_1,
            'action': 'boost_update',
            'details': f"Updated boost for '{cat_to_change['name']}' from {old_boost} to {new_boost}"
        })
        
        # Update edit history
        collection.update_one(
            {'searchTerm': term},
            {
                '$set': {
                    'editHistory': edits,
                    'createdDate': d_minus_5,
                    'updatedDate': d_minus_1
                }
            }
        )
        
        # Generate CTR/CVR trends from D-5 to today (6 days total)
        num_days = 6
        ctr_values = generate_ctr_trend(num_days, trend_type)
        cvr_values = [round(ctr * random.uniform(0.3, 0.6), 3) for ctr in ctr_values]
        
        # Generate timestamps for each day
        timestamps = [(d_minus_5 + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(num_days)]
        
        # Use the intended trend type (don't recalculate)
        calculated_trend = trend_type
        
        # Update trends
        trends_collection.update_one(
            {'searchTerm': term},
            {
                '$set': {
                    'searchTerm': term,
                    'ctr': ctr_values,
                    'cvr': cvr_values,
                    'timestamps': timestamps,
                    'trendType': calculated_trend,
                    'lastUpdated': today
                }
            },
            upsert=True
        )
        
        print(f"✅ {term} ({trend_type}) - CTR: {ctr_values[0]:.3f} → {ctr_values[-1]:.3f}")
    
    print("\n" + "=" * 70)
    print("✅ DEMO DATA CREATED SUCCESSFULLY")
    print("=" * 70)
    
    client.close()
    
    return {
        'improvement': improvement_terms,
        'underperforming': underperforming_terms,
        'neutral': neutral_terms
    }


def main():
    print("=" * 70)
    print("DEMO DATA SETUP")
    print("=" * 70)
    
    # Step 1: Clean all existing edits
    print("\nStep 1: Cleaning all existing edits...")
    clean_all_edits()
    
    # Step 2: Select demo terms
    print("\nStep 2: Selecting demo terms...")
    demo_terms = select_demo_terms()
    print(f"Selected {len(demo_terms)} terms for demo")
    
    # Step 3: Create demo data
    print("\nStep 3: Creating demo data...")
    categorized_terms = create_demo_data(demo_terms)
    
    # Print summary
    print("\n" + "=" * 70)
    print("DEMO TERMS FOR PRESENTATION")
    print("=" * 70)
    
    print("\n📈 USE THESE TERMS TO SHOW IMPROVEMENT:")
    for term in categorized_terms['improvement']:
        print(f"  • {term}")
    
    print("\n📉 USE THESE TERMS TO SHOW UNDERPERFORMING:")
    for term in categorized_terms['underperforming']:
        print(f"  • {term}")
    
    print("\n➡️ USE THESE TERMS TO SHOW NEUTRAL:")
    for term in categorized_terms['neutral']:
        print(f"  • {term}")
    
    print("\n" + "=" * 70)
    print("Timeline for each term:")
    print("  D-5: Entry created")
    print("  D-3: Category added with boost value")
    print("  D-1: Boost value changed")
    print("  D-0: Today (6 data points total)")
    print("=" * 70)


if __name__ == "__main__":
    main()

