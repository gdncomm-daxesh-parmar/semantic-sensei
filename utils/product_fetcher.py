"""
Utility for fetching products from Blibli API
"""

import requests
import urllib.parse
import traceback


# Blibli API Configuration
BLIBLI_HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'id',
    'cache-control': 'no-cache',
    'channelid': 'web',
    'content-type': 'application/json;charset=UTF-8',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

BLIBLI_COOKIES = {
    'Blibli-User-Id': 'e554ebe6-ae81-487c-bc8b-04ce88f6ba8d',
    'Blibli-Is-Member': 'false',
    'Blibli-Is-Remember': 'false',
    'Blibli-Session-Id': '03d8b16c-88e8-4984-a626-4a6b1f68aeb1',
    'Blibli-Signature': 'c257e91c7602228370423d98b4cb38dac227ab6c',
    'Blibli-Device-Id': 'U.10f1f12e-8944-403d-ba87-72c8556f532b',
    'Blibli-Device-Id-Signature': 'bb2e8ea51e803d0f30cd5e29e6ef50609d3d715d',
}


def fetch_products(search_term, category_codes=None, page=1, limit=20, include_search_term=True):
    """
    Fetch products from Blibli API
    
    Args:
        search_term: The search query
        category_codes: Optional list of category codes to filter by
        page: Page number (default 1)
        limit: Number of results per page (default 20)
        include_search_term: Whether to include searchTerm in request (default True)
    
    Returns:
        Tuple of (products_list, error_message)
        - products_list: List of product dictionaries with name, image, price, rating
        - error_message: None if successful, error string if failed
    """
    try:
        # Build the base URL without intent parameter
        url = f"https://www.blibli.com/backend/search/products?page={page}&start=0&merchantSearch=true&multiCategory=true&channelId=web&showFacet=false&isMobileBCA=false&isJual=false&firstLoad=true"
        
        # Add searchTerm only if requested (Control request includes it, Model request excludes it)
        if include_search_term:
            encoded_term = urllib.parse.quote(search_term)
            url += f"&searchTerm={encoded_term}"
        
        # If category codes provided, add them to the URL
        # Multiple categories should be passed as: category=code1&category=code2&category=code3
        if category_codes:
            for code in category_codes:
                url += f"&category={urllib.parse.quote(code)}"
        
        # Make the request
        response = requests.get(url, headers=BLIBLI_HEADERS, cookies=BLIBLI_COOKIES, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract products from response
        products = []
        if 'data' in data and 'products' in data['data']:
            for product in data['data']['products'][:limit]:
                # Skip if product is not a dict
                if not isinstance(product, dict):
                    continue
                
                # Safely extract product name
                name = product.get('name', 'N/A')
                
                # Safely extract image
                image = ''
                images = product.get('images', [])
                if isinstance(images, list) and len(images) > 0:
                    if isinstance(images[0], dict):
                        image = images[0].get('full', '')
                    elif isinstance(images[0], str):
                        image = images[0]
                
                # Safely extract price - use actual Blibli API field names
                price = 0
                price_data = product.get('price', {})
                if isinstance(price_data, dict):
                    # Blibli API uses: salePrice, minPrice, listPrice
                    price = (price_data.get('salePrice') or 
                            price_data.get('minPrice') or 
                            price_data.get('listPrice') or 
                            price_data.get('offered') or 0)
                elif isinstance(price_data, (int, float)):
                    price = price_data
                
                # Safely extract rating
                rating = 0
                review_data = product.get('review', {})
                if isinstance(review_data, dict):
                    rating = review_data.get('rating', 0)
                elif isinstance(review_data, (int, float)):
                    rating = review_data
                
                products.append({
                    'name': name,
                    'image': image,
                    'price': price,
                    'rating': rating,
                    'id': product.get('id', ''),
                    'url': f"https://www.blibli.com{product.get('url', '')}"
                })
        
        return products, None
        
    except Exception as e:
        error_msg = f"Error fetching products: {str(e)}"
        error_details = traceback.format_exc()
        return [], {'message': error_msg, 'details': error_details}

