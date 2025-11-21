"""
Utility for fetching products from Blibli API
"""

import requests
import urllib.parse
import traceback

# Blibli API Configuration - UPDATE COOKIES WHEN THEY EXPIRE
BLIBLI_HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'id',
    'cache-control': 'no-cache',
    'channelid': 'web',
    'content-type': 'application/json;charset=UTF-8',
    'isjual': 'false',
    'params': '[object Object]',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}

BLIBLI_COOKIES = {
    '__cf_bm': '8aho6ZcdQ1ExvNow4g4vnl.eLXna1BGF8sH1XGsi8IY-1763631164-1.0.1.1-PpzMsVQpfMBnUWFXkBi0B_EMlWDjPkRCy6cD9wiNStqxmOpfUdauC.FnP90jFRIuyMg4phvWwfE8xZHvAPvGYMls6lv5hNC1CqFOFFUaMvs',
    '_cfuvid': 'RXDStfrdP1O1hC5mulNoFKLPpU3l.yE1yxppjDTIE6U-1763631164097-0.0.1.1-604800000',
    'cf_clearance': 'oFmmc6ABnqOnGoVDmBISjZ2zDtFzn1uSej3GtlUtUKw-1763631164-1.2.1.1-NJNROWv6EDWc3z1widhs.50djT2i030sL7Pj18AVgVVipfYCm0NGL89p64hOUAMMTL1.b0Ga0OIsUWRw9PapS8rY1O5St43IvuL2vKYw37Hxj6Ifc_9TiQlzARQ6P6SraE81BL5IK_4UwJP9RrWrvryF6KT0gZbSH9SiYlu.WcM.xzZGepQmeZa1J6Zex6pHC7hYL7g26nOK61Iqh49lUxxB480n3oEFUSVuC5HdlTo',
    'Blibli-Additional-Parameter-Signature': '',
    'Blibli-Is-Member': 'false',
    'Blibli-Is-Remember': 'false',
    'Blibli-Device-Id': 'U.d6defa5d-064a-432f-810e-fc261b9031bb',
    'Blibli-Device-Id-Signature': 'e6af3d9d81f758e2e4c10627d12be640ab100ec1',
    'Blibli-Session-Id': '6813c2d4-025c-44f8-a5bf-005080178380',
    'Blibli-Signature': 'fad9b0ad74b5485130390c55e99d4ae48a3f4f0c',
    'Blibli-User-Id': '6813c2d4-025c-44f8-a5bf-005080178380',
    'Blibli-Unm-Signature': '9e950b91c77790f5ed1bef5865a5d83b250ac113',
    'Blibli-Unm-Id': '6813c2d4-025c-44f8-a5bf-005080178380',
    'g_state': '{"i_l":0,"i_ll":1763631168030,"i_b":"AfU1mCwMbLwA7gOLlGslndgIGayca06Ke6xCntv/nLI"}',
    'Blibli-dv-token': 'JT_wco7WAUta_-x0g4ENGRJb0ZO_GTyeEz8HjbTqsP01et',
    'forterToken': '9ccc61559b9740d2bbab630e7f6de307_1763631167976_76_UDAD43b-mnts-a9-r8-n4_25ck_',
}


def fetch_products(search_term, category_codes=None, page=1, limit=20, include_search_term=True, environment="production", boost_param=None):
    """
    Fetch products from Blibli API or Lower Env API
    
    Args:
        search_term: The search query
        category_codes: Optional list of category codes to filter by
        page: Page number (default 1)
        limit: Number of results per page (default 20)
        include_search_term: Whether to include searchTerm in request (default True)
        environment: "production" or "lowerEnv" (default "production")
        boost_param: Boost parameter string for lowerEnv (e.g., "c1:100,c2:101")
    
    Returns:
        Tuple of (products_list, error_message)
        - products_list: List of product dictionaries with name, image, price, rating
        - error_message: None if successful, error string if failed
    """
    try:
        # Choose base URL based on environment
        if environment == "lowerEnv":
            # Lower Env API endpoint
            url = f"http://localhost:9090/backend/search/products?page={page}&start=0&merchantSearch=true&multiCategory=true&channelId=web&showFacet=false&isMobileBCA=false&isJual=false&firstLoad=true"
        else:
            # Production Blibli API
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
        
        # Add boost parameter for lowerEnv
        if environment == "lowerEnv" and boost_param:
            encoded_boost = urllib.parse.quote(boost_param)
            url += f"&boostParam={encoded_boost}"
        
        # Add dynamic referer header based on search term
        headers = BLIBLI_HEADERS.copy()
        if include_search_term:
            encoded_term = urllib.parse.quote(search_term)
            if environment == "lowerEnv":
                headers['referer'] = f'http://localhost:9090/backend/cari/{encoded_term}'
            else:
                headers['referer'] = f'https://www.blibli.com/cari/{encoded_term}'
        else:
            if environment == "lowerEnv":
                headers['referer'] = 'http://localhost:9090/backend/'
            else:
                headers['referer'] = 'https://www.blibli.com/'
        
        # Make the request (no cookies for lowerEnv)
        if environment == "lowerEnv":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.get(url, headers=headers, cookies=BLIBLI_COOKIES, timeout=10)
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

