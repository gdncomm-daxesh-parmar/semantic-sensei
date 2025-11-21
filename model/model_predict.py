from flask import Flask, request, jsonify
import requests
import json
import pandas as pd
import os

app = Flask(__name__)

# --- Configuration ---
GEMINI_API_KEY = "AIzaSyC1r51DFK3X2glPw2w6lvk43FNdRsWm8jo"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# Get the absolute path to c3_categories.csv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_FILE = os.path.join(BASE_DIR, '..', 'data', 'c3_categories.csv')

# --- Category Loading Function ---
def load_categories(file_path):
    """Loads the category list from CSV and returns both formatted string and mapping."""
    try:
        df = pd.read_csv(file_path)
        # Combine all category names into a single, comma-separated string
        category_names = df['C3Name'].dropna().tolist()
        categories_string = ", ".join(category_names)
        
        # Create a mapping of name -> code for lookup
        category_mapping = {}
        for _, row in df.iterrows():
            if pd.notna(row['C3Name']) and pd.notna(row['C3Code']):
                category_mapping[row['C3Name']] = row['C3Code']
        
        return categories_string, category_mapping
    except Exception as e:
        print(f"Warning: Could not read {file_path}. Using fallback. Error: {e}")
        return "Parfum Wanita, Pakaian Olahraga Wanita, Mainan, Perlengkapan Anak, Aksesoris", {}

# Load the full, formatted list of categories and mapping
CATEGORIES_LIST_FULL, CATEGORY_NAME_TO_CODE = load_categories(CATEGORIES_FILE)

# --- System Prompt ---
SYSTEM_PROMPT = f"""
You are an expert product-category classifier for an Indonesian e-commerce search engine.

# CLASSIFICATION MODEL AND CONTEXT
The classification must be performed based on the current search trends and deep e-commerce context of Indonesia.

Your predictions must be based on a comprehensive "research and thinking model" that considers the following query contexts:

1. **Commercial Intent (Primary):** Is the term a direct product name, a brand name, or a category keyword? (e.g., 'eser' is a known local perfume brand, 'cuculemon' is a known aesthetic tumbler brand).
1. **Grounded Research (Product Derivation):** First, autonomously determine the dominant consumer product or brand associated with the search term by referencing current Indonesian e-commerce data (Shopee, Tokopedia, local trends).
2. **Context Determination:** Explicitly identify the derived product context (e.g., 'NOX' is a well-known Padel racket brand, 'eser' is a local perfume brand).
1. **Grounded Research (Product Derivation):** First, autonomously determine the dominant consumer product or brand associated with the search term by referencing current Indonesian e-commerce data (Shopee, Tokopedia, local trends).
2. **Context Determination:** Explicitly identify the derived product context (e.g., 'NOX' is a well-known Padel racket brand, 'eser' is a local perfume brand).

2. **Linguistic Context (Local Slang/Typo):** Is it an abbreviation, misspelling, or a term unique to Indonesian slang (e.g., 'kaos' for T-shirt, or common typos)?

3. **Trending & Viral Products:** Does the term correlate with currently viral or "aesthetic" goods frequently sold on TikTok Shop, Shopee, or Tokopedia (e.g., viral tumblers, local cosmetic lines)?

4. **Functional/Usage Context:** If the term is generic, what is the most common use case? (e.g., 'dance ladies' refers to dancewear, which maps to athletic apparel).

5. **Ambiguity Assessment:** If the term has zero commercial signal in Indonesia (e.g., a foreign forum handle or nonsensical), classify as uncertain.

6. **Multi-Context Resolution (NEW):** If the term (e.g., 'nox') is a known brand in a high-traffic consumer category (e.g., Padel/Sports) AND also a match for a low-traffic industrial/B2B product (e.g., automotive sensor), **PRIORITIZE the high-traffic consumer category** (Sports) for the top predictions.

OUTPUT RULES:
- Always return JSON only. No extra commentary.
- Provide up to top 5 predictions, ordered by descending confidence score.
- Use only categories from the provided list.
- Score must be integer 1..100 (higher = more confident). Scores DO NOT need to sum to 100.
- If the term is ambiguous set uncertain: true; else uncertain: false.
- Preserve the original search term text exactly.
- Only include predictions with score > 30.

JSON structure to return:
{{
    "predictions": [
        {{
            "term": "<search_term>",
            "uncertain": <true|false>,
            "predictions": [
                {{"category": "<category_name>", "score": <int>}},
                {{"category": "<category_name>", "score": <int>}}
            ]
        }}
    ]
}}
"""

# --- API Call Function ---
def call_gemini_api(search_term):
    """Calls the Gemini API with the search term."""
    
    user_prompt = f"""
Categories (use these exactly): {CATEGORIES_LIST_FULL}

Now classify the following search term (produce only JSON):
{search_term}
"""
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # Constructing the request payload
    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT.strip()}]},
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 10000,
            "responseMimeType": "application/json"
        },
        "tools": [{"google_search": {}}]
    }
    
    # Adding the API key to the URL as a query parameter
    full_url = f"{API_URL}?key={GEMINI_API_KEY}"
    
    try:
        response = requests.post(full_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the generated text from the response
        generated_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No text generated.')
        
        # Parse the JSON response
        parsed_result = json.loads(generated_text)
        
        # Convert the format to match UI expectations
        # The API returns: {"predictions": [{"term": "...", "uncertain": ..., "predictions": [{"category": "...", "score": ...}]}]}
        # We need to convert to: {"predictions": [{"term": "...", "uncertain": ..., "predictions": [{"code": "...", "name": "...", "score": ...}]}]}
        
        if 'predictions' in parsed_result:
            for term_pred in parsed_result['predictions']:
                if 'predictions' in term_pred:
                    converted_predictions = []
                    for pred in term_pred['predictions']:
                        category_name = pred.get('category', '')
                        score = pred.get('score', 0)
                        
                        # Look up the category code
                        category_code = CATEGORY_NAME_TO_CODE.get(category_name, 'UNKNOWN')
                        
                        converted_predictions.append({
                            'code': category_code,
                            'name': category_name,
                            'score': score
                        })
                    
                    term_pred['predictions'] = converted_predictions
        
        # Extract token usage if available
        token_details = {}
        usage_metadata = result.get('usageMetadata', {})
        if usage_metadata:
            token_details = {
                "prompt_tokens": usage_metadata.get('promptTokenCount', 0),
                "candidates_tokens": usage_metadata.get('candidatesTokenCount', 0),
                "total_tokens": usage_metadata.get('totalTokenCount', 0)
            }
        
        return parsed_result, token_details
        
    except requests.exceptions.RequestException as err:
        raise Exception(f"API Request Error: {err}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing JSON response: {e}")
    except Exception as e:
        raise Exception(f"Error processing response: {e}")


@app.route('/search', methods=['POST'])
def search():
    """Flask endpoint for category prediction."""
    try:
        # Get the search term from request
        data = request.get_json()

        if not data or 'search_term' not in data:
            return jsonify({
                'error': 'Missing search_term in request body'
            }), 400

        search_term = data['search_term']
        
        # Call the Gemini API
        result, token_details = call_gemini_api(search_term)

        return jsonify({
            'result': result,
            'token_details': token_details
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500


if __name__ == '__main__':
    print(f"Starting Flask API server on port 8090...")
    print(f"Categories loaded: {len(CATEGORIES_LIST_FULL.split(','))} categories")
    app.run(debug=False, host='0.0.0.0', port=8090)
