import requests
import csv
import time
import json
import os
from typing import List, Dict, Optional

# API endpoint
SEARCH_API_URL = "https://www.blibli.com/backend/search/products"

# Headers for the API request
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'id',
    'cache-control': 'no-cache',
    'channelid': 'android',
    'content-type': 'application/json;charset=UTF-8',
    'priority': 'u=1, i',
    'referer': 'https://www.blibli.com/cari/Samsung',
    'sec-ch-ua': '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-arch': '"arm"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version-list': '"Chromium";v="142.0.0.0", "Brave";v="142.0.0.0", "Not_A Brand";v="99.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"macOS"',
    'sec-ch-ua-platform-version': '"15.5.0"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'build-no': '1111'
}

# Cookies
COOKIES = {
    'Blibli-User-Id': 'e554ebe6-ae81-487c-bc8b-04ce88f6ba8d',
    'Blibli-Is-Member': 'false',
    'Blibli-Is-Remember': 'false',
    'Blibli-Session-Id': '03d8b16c-88e8-4984-a626-4a6b1f68aeb1',
    'Blibli-Signature': 'c257e91c7602228370423d98b4cb38dac227ab6c',
    '_cfuvid': 'USXxJ70siGTCcQvvZWvqGG5rxU0X5.kvrGR_oUz_XGE-1763530900491-0.0.1.1-604800000',
    'Blibli-Device-Id': 'U.10f1f12e-8944-403d-ba87-72c8556f532b',
    'Blibli-Device-Id-Signature': 'bb2e8ea51e803d0f30cd5e29e6ef50609d3d715d',
    '__cf_bm': 'hyb9D9kbhqWJPbFdgRwpnqzgZHEM4eSdVARyvO9C7g0-1763541864-1.0.1.1-cTP67xlZxl.TFXmR6m6cuYpsoDD5cRFp37I0R2eGGGgbQrmx.w1Yy3SmqxUFIof3xI5qyomoa8NIBr1NYAGcWN3ysN2SS.s5vnEy99eVfSc',
    'cf_clearance': 'iNLDKHCp3vDOZ0RnYPFZMQiJl4zYnflahK8kH2MQvdE-1763541865-1.2.1.1-dzpLsfRF1UI8Vva7WMASLnyu33RSsYtFXixYSpnbaRCGDiL_HBdyIMX1GRJvmu3AeuCN08TXa5ghnpFSyS8BU1qoZYcR_LzHydCZgDTWO_eyMYtjnVoiidXpjXKqK4QyYYwk7uadCtl5Grsidi1BfVbdDxfs1XtADnI73fJODbYHUrkyoka7CzHCZAsed0Z_Kn4hplAdhFTRS..PwPkN.omliIR7su10h7eno8ka4klLq.IdZnb1MuMK0xNpYnIc',
    'g_state': '{"i_l":0,"i_ll":1763542006197,"i_b":"bmKnsPczYkWAgPAImBrdvu40FxT6E/IryRQnSyhP4nk"}',
    'Blibli-dv-token': 'JT__CTa1mCKccTsMfT9YQRno2-lgRRq0-2WsZy8N0lac3Y',
    'forterToken': 'f325fa4658344ef58e3c361eb823a0df_1763542006103_146_UAS9b_25ck'
}

def extract_c3_categories(kategori_filter: Dict, top_n: int = 5) -> List[Dict]:
    """
    Extract top N C3 categories by count from the nested category structure.
    
    Args:
        kategori_filter: The Kategori filter object from the API response
        top_n: Number of top categories to return (default 5)
        
    Returns:
        List of dictionaries containing top N C3 category code and count
    """
    c3_categories = []
    
    # Navigate through the nested structure: C1 -> C2 -> C3
    data = kategori_filter.get('data', [])
    
    for c1 in data:
        # C1 level
        c1_subcategories = c1.get('subCategory', [])
        
        for c2 in c1_subcategories:
            # C2 level
            c2_subcategories = c2.get('subCategory', [])
            
            for c3 in c2_subcategories:
                # C3 level
                if c3.get('level') == 3:
                    c3_categories.append({
                        'code': c3.get('value'),
                        'label': c3.get('label'),
                        'count': c3.get('count', 0)
                    })
    
    # Sort by count (descending) and return top N
    c3_categories.sort(key=lambda x: x['count'], reverse=True)
    return c3_categories[:top_n]

def search_term_and_get_categories(search_term: str) -> Dict:
    """
    Search for a term and extract top 5 C3 categories with their counts.
    
    Args:
        search_term: The search keyword to query
        
    Returns:
        Dictionary containing search term and top 5 C3 categories (empty list if none found)
    """
    params = {
        'searchTerm': search_term,
        'facetOnly': 'true',
        'page': '1',
        'start': '0',
        'merchantSearch': 'true',
        'multiCategory': 'true',
        'intent': 'true',
        'channelId': 'android',
        'firstLoad': 'true'
    }
    
    try:
        response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, cookies=COOKIES)
        response.raise_for_status()
        
        data = response.json()
        
        # Navigate to filters
        if 'data' in data and 'filters' in data['data']:
            filters = data['data']['filters']
            
            # Find the Kategori filter
            for filter_item in filters:
                if filter_item.get('name') == 'Kategori':
                    # Extract top 5 C3 categories
                    c3_categories = extract_c3_categories(filter_item, top_n=5)
                    print(f"  Found {len(c3_categories)} top C3 categories")
                    
                    return {
                        'search_term': search_term,
                        'c3_categories': c3_categories
                    }
        
        # No Kategori filter found - return empty categories
        print(f"  No categories found")
        return {
            'search_term': search_term,
            'c3_categories': []
        }
        
    except Exception as e:
        print(f"  Error: {e}")
        # Return empty categories on error
        return {
            'search_term': search_term,
            'c3_categories': []
        }

def read_search_terms(csv_file: str, limit: int = None) -> List[str]:
    """
    Read search terms from the CSV file.
    
    Args:
        csv_file: Path to the CSV file
        limit: Maximum number of terms to read (None for all)
        
    Returns:
        List of search keywords
    """
    search_terms = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                search_term = row.get('Search Keyword', '').strip()
                if search_term:
                    search_terms.append(search_term)
        
        print(f"Read {len(search_terms)} search terms from {csv_file}")
        return search_terms
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def load_checkpoint(checkpoint_file: str = "progress_checkpoint.json") -> Dict:
    """Load progress checkpoint if it exists."""
    try:
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            print(f"✓ Loaded checkpoint: {checkpoint['processed']}/{checkpoint['total']} terms processed")
            return checkpoint
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
    return {'processed': 0, 'total': 0, 'results': []}

def save_checkpoint(checkpoint: Dict, checkpoint_file: str = "progress_checkpoint.json"):
    """Save progress checkpoint."""
    try:
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving checkpoint: {e}")


def save_term_category_mappings(results: List[Dict], filename: str = "term_to_category_mapping.txt"):
    """
    Save search term to C3 category mappings in the format:
    searchTerm -> c3_code(c3_name):count,c3_code2(c3_name2):count2,...
    Empty categories shown as: searchTerm -> 
    
    Args:
        results: List of result dictionaries containing search terms and C3 categories
        filename: Output filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for result in results:
                search_term = result['search_term']
                c3_categories = result['c3_categories']
                
                if c3_categories:
                    # Format: c3_code(c3_label):count,c3_code2(c3_label2):count2,...
                    category_mappings = []
                    for cat in c3_categories:
                        category_mappings.append(f"{cat['code']}({cat['label']}):{cat['count']}")
                    
                    # Join with commas
                    mapping_str = ','.join(category_mappings)
                else:
                    # Empty categories
                    mapping_str = ""
                
                # Write in format: searchTerm -> mapping (or empty if no categories)
                f.write(f"{search_term} -> {mapping_str}\n")
        
        print(f"  ✓ Term-to-category mappings saved")
        
    except Exception as e:
        print(f"Error saving mappings: {e}")

def save_detailed_mappings(results: List[Dict], filename: str = "term_to_category_detailed.csv"):
    """
    Save detailed search term to C3 category mappings as CSV.
    Terms without categories are also included with empty fields.
    
    Args:
        results: List of result dictionaries containing search terms and C3 categories
        filename: Output filename
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['SearchTerm', 'C3Code', 'C3Label', 'Count'])
            
            for result in results:
                search_term = result['search_term']
                c3_categories = result['c3_categories']
                
                if c3_categories:
                    # Write each category
                    for cat in c3_categories:
                        writer.writerow([
                            search_term,
                            cat['code'],
                            cat['label'],
                            cat['count']
                        ])
                else:
                    # Write term with empty categories
                    writer.writerow([
                        search_term,
                        '',
                        '',
                        ''
                    ])
        
        print(f"  ✓ Detailed CSV saved")
        
    except Exception as e:
        print(f"Error saving detailed mappings: {e}")

def main():
    """Main function to process all search terms."""
    print("=" * 60)
    print("Fetching Top 5 C3 Categories for ALL Search Terms")
    print("=" * 60)
    
    # Read all search terms
    csv_file = "/Users/daxeshparmar/PycharmProjects/semantic-sensei/data/non_performing_terms.csv"
    search_terms = read_search_terms(csv_file, limit=None)  # None = process all
    
    if not search_terms:
        print("No search terms found. Exiting.")
        return
    
    # Load checkpoint if exists
    checkpoint = load_checkpoint()
    start_index = checkpoint['processed']
    results = checkpoint['results']
    
    if start_index > 0:
        print(f"Resuming from term {start_index + 1}\n")
    
    # Process each search term starting from checkpoint
    try:
        for i in range(start_index, len(search_terms)):
            term = search_terms[i]
            print(f"[{i + 1}/{len(search_terms)}] {term}", end=" ")
            
            # Always get a result (empty or with categories)
            result = search_term_and_get_categories(term)
            results.append(result)
            
            # Save checkpoint every 50 terms
            if (i + 1) % 50 == 0:
                checkpoint = {
                    'processed': i + 1,
                    'total': len(search_terms),
                    'results': results
                }
                save_checkpoint(checkpoint)
                print(f"\n  💾 Checkpoint saved: {i + 1}/{len(search_terms)} terms")
            
            # Progress indicator every 100 terms
            if (i + 1) % 100 == 0:
                print(f"\n  ✓ Progress: {i + 1}/{len(search_terms)} terms processed")
            
            # Rate limiting: 1 second sleep after every 25 requests
            if (i + 1) % 25 == 0:
                print(f"\n  ⏸ Rate limit pause (1s)...")
                time.sleep(1.0)
            else:
                # Normal delay between requests
                time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving checkpoint...")
        checkpoint = {
            'processed': i + 1,
            'total': len(search_terms),
            'results': results
        }
        save_checkpoint(checkpoint)
        print("Checkpoint saved. Run again to resume.")
        return
    
    # Count terms with and without categories
    terms_with_categories = sum(1 for r in results if r['c3_categories'])
    terms_without_categories = len(results) - terms_with_categories
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"Processing Complete!")
    print(f"{'=' * 60}")
    print(f"Total terms processed: {len(results)}")
    print(f"Terms with categories: {terms_with_categories}")
    print(f"Terms without categories: {terms_without_categories}")
    print(f"{'=' * 60}")
    
    # Save all results (including empty ones)
    if results:
        # Save in the requested format: searchTerm -> c3_code(c3_name):count
        save_term_category_mappings(results, "../data/term_to_category_mapping.txt")
        
        # Also save detailed CSV for analysis
        save_detailed_mappings(results, "../data/term_to_category_detailed.csv")
        
        print(f"\n✓ Results saved:")
        print(f"  - term_to_category_mapping.txt ({len(results)} terms)")
        print(f"  - term_to_category_detailed.csv")
        
        # Clean up checkpoint file after successful completion
        if os.path.exists("progress_checkpoint.json"):
            os.remove("progress_checkpoint.json")
            print(f"\n✓ Checkpoint file removed (processing complete).")
    else:
        print("\nNo results to save.")

if __name__ == "__main__":
    main()

