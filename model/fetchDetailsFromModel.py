from flask import Flask, request, jsonify
from google import genai
import json
import os

app = Flask(__name__)

GEMINI_API_KEY = "AIzaSyC1r51DFK3X2glPw2w6lvk43FNdRsWm8jo"
MODEL_NAME = "gemini-2.0-flash"

client = genai.Client(api_key=GEMINI_API_KEY)

# Get the absolute path to c3_categories.csv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_FILE = os.path.join(BASE_DIR, '..', 'data', 'c3_categories.csv')


@app.route('/search', methods=['POST'])
def search():
    try:
        # Get the search term from request
        data = request.get_json()

        if not data or 'search_term' not in data:
            return jsonify({
                'error': 'Missing search_term in request body'
            }), 400

        search_term = data['search_term']

        prompt_text = f"""You are an expert product-category classifier for an Indonesian e-commerce search engine.

OUTPUT RULES:
- Always return JSON only. No extra commentary.
- Use the exact JSON structure specified in the schema.
- Provide up to top 5 predictions, ordered by descending confidence score.
- Use only categories from the provided c3_categories.csv file.
- Score must be integer 1..100 (higher = more confident). Scores DO NOT need to sum to 100.
- If the term is ambiguous set uncertain: true; else uncertain: false.
- Preserve the original search term text exactly.
- Only include predictions with score > 30.

Categories: Use categories from the provided c3_categories.csv file (match code and name exactly).

For each search term I provide, output JSON as specified in the schema. The input may include typos, abbreviations, or slang. Use your best judgment and place higher probability where you are confident. If the term is very likely to be out-of-scope (no category match), return the top categories with small probabilities and set "uncertain": true.

IMPORTANT CONTEXT:
- "eser" is a popular Indonesian perfume brand → should return Parfum categories (Parfum Wanita, Parfum Pria, etc.)
- "nike" → Sports shoes, sportswear
- "samsung" → Electronics, phones, smartphones

Now classify the following search term:

{search_term}
"""
        
        # Upload the categories file
        category_file = client.files.upload(file=CATEGORIES_FILE)
        config = genai.types.GenerateContentConfig(
            temperature=0.25,
            max_output_tokens=10000,
            response_mime_type="application/json",
            response_json_schema={
                "type": "object",
                "properties": {
                    "predictions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "term": {
                                    "type": "string"
                                },
                                "uncertain": {
                                    "type": "boolean"
                                },
                                "predictions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "code": {
                                                "type": "string"
                                            },
                                            "name": {
                                                "type": "string"
                                            },
                                            "score": {
                                                "type": "integer"
                                            }
                                        },
                                        "propertyOrdering": [
                                            "code",
                                            "name",
                                            "score"
                                        ],
                                        "required": [
                                            "code",
                                            "name",
                                            "score"
                                        ]
                                    }
                                }
                            },
                            "propertyOrdering": [
                                "term",
                                "uncertain",
                                "predictions"
                            ],
                            "required": [
                                "term",
                                "uncertain",
                                "predictions"
                            ]
                        }
                    }
                },
                "propertyOrdering": [
                    "predictions"
                ],
                "required": [
                    "predictions"
                ]
            }
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt_text, category_file],
            config=config
        )
        token_details = {
            "prompt_tokens": response.usage_metadata.prompt_token_count,
            "candidates_tokens": response.usage_metadata.candidates_token_count,
            "cached_tokens": response.usage_metadata.cached_content_token_count,
            "total_tokens": response.usage_metadata.total_token_count
        }

        return jsonify({
            'result': json.loads(response.text),
            'token_details': token_details
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8090)
