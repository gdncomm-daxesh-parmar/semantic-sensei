import requests
import csv
import time
import sys
import os
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.blibli_api import BLIBLI_HEADERS as HEADERS, BLIBLI_COOKIES as COOKIES

# API endpoints
BASE_URL = "https://www.blibli.com/backend/content-api/categories"

def fetch_all_c1_categories() -> List[Dict]:
    """Fetch all C1 (level 1) categories from the main API."""
    print("Fetching all C1 categories...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, cookies=COOKIES)
        response.raise_for_status()
        data = response.json()
        
        # Debug: print response structure
        print(f"Response type: {type(data)}")
        if isinstance(data, dict):
            print(f"Response keys: {data.keys()}")
        
        # Handle different response structures
        if isinstance(data, list):
            categories = data
        elif isinstance(data, dict):
            # Try common nested structures
            categories = data.get('data', data.get('categories', data.get('items', [])))
            if not isinstance(categories, list):
                print(f"Warning: Expected list but got {type(categories)}")
                print(f"Response content: {data}")
                return []
        else:
            print(f"Unexpected response type: {type(data)}")
            print(f"Response content: {data}")
            return []
        
        # Filter only level 1 categories
        c1_categories = [cat for cat in categories if isinstance(cat, dict) and cat.get('level') == 1]
        print(f"Found {len(c1_categories)} C1 categories")
        return c1_categories
    except Exception as e:
        print(f"Error fetching C1 categories: {e}")
        import traceback
        traceback.print_exc()
        return []

def fetch_children(category_id: str) -> List[Dict]:
    """Fetch children for a given category ID."""
    url = f"{BASE_URL}/{category_id}/children"
    try:
        response = requests.get(url, headers=HEADERS, cookies=COOKIES)
        response.raise_for_status()
        data = response.json()
        
        # Handle different response structures
        if isinstance(data, list):
            children = data
        elif isinstance(data, dict):
            # Try common nested structures
            children = data.get('data', data.get('children', data.get('items', [])))
        else:
            children = []
        
        return children if isinstance(children, list) else []
    except Exception as e:
        print(f"Error fetching children for category {category_id}: {e}")
        return []

def fetch_all_c3_categories() -> List[Dict]:
    """Fetch all C3 (level 3) categories."""
    all_c3_categories = []
    
    # Step 1: Get all C1 categories
    c1_categories = fetch_all_c1_categories()
    
    # Step 2: For each C1, get its children (C2s)
    for i, c1 in enumerate(c1_categories, 1):
        c1_id = c1.get('id')
        c1_name = c1.get('name')
        c1_code = c1.get('categoryCode')
        
        print(f"\n[{i}/{len(c1_categories)}] Processing C1: {c1_name} ({c1_code})")
        
        # Get C2 categories (children of C1)
        c2_categories = fetch_children(c1_id)
        print(f"  Found {len(c2_categories)} C2 categories")
        
        # Step 3: For each C2, get its children (C3s)
        for j, c2 in enumerate(c2_categories, 1):
            c2_id = c2.get('id')
            c2_name = c2.get('name')
            c2_level = c2.get('level')
            
            # Verify it's a C2 category
            if c2_level == 2:
                c3_categories = fetch_children(c2_id)
                
                # Filter only level 3 categories
                c3_filtered = [cat for cat in c3_categories if cat.get('level') == 3]
                
                if c3_filtered:
                    print(f"    [{j}/{len(c2_categories)}] C2: {c2_name} -> Found {len(c3_filtered)} C3 categories")
                    all_c3_categories.extend(c3_filtered)
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
    
    return all_c3_categories

def save_to_csv(c3_categories: List[Dict], filename: str = "c3_categories.csv"):
    """Save C3 categories to a CSV file."""
    print(f"\nSaving {len(c3_categories)} C3 categories to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['C3Name', 'C3Code'])
        
        # Write data
        for category in c3_categories:
            name = category.get('name', '')
            code = category.get('categoryCode', '')
            writer.writerow([name, code])
    
    print(f"Successfully saved to {filename}")

def main():
    """Main function to orchestrate the fetching and saving process."""
    print("=" * 60)
    print("Fetching C3 Categories from Blibli API")
    print("=" * 60)
    
    # Fetch all C3 categories
    c3_categories = fetch_all_c3_categories()
    
    # Remove duplicates based on categoryCode
    unique_c3 = []
    seen_codes = set()
    for cat in c3_categories:
        code = cat.get('categoryCode')
        if code and code not in seen_codes:
            unique_c3.append(cat)
            seen_codes.add(code)
    
    print(f"\n{'=' * 60}")
    print(f"Total C3 categories found: {len(c3_categories)}")
    print(f"Unique C3 categories: {len(unique_c3)}")
    print(f"{'=' * 60}")
    
    # Save to CSV
    if unique_c3:
        save_to_csv(unique_c3)
    else:
        print("No C3 categories found to save.")

if __name__ == "__main__":
    main()

