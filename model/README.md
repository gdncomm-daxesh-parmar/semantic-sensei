# Model API - Gemini Category Prediction

This Flask API uses Google Gemini AI to predict categories for search terms.

## Prerequisites

```bash
pip install flask google-generativeai
```

## Running the API

```bash
cd /Users/daxeshparmar/PycharmProjects/semantic-sensei
python model/model_predict.py
```

The API will start on `http://localhost:8090`

## Testing the API

```bash
curl -X POST http://localhost:8090/search \
  -H "Content-Type: application/json" \
  -d '{"search_term": "apple iphone"}'
```

## API Response Format

```json
{
  "result": {
    "predictions": [
      {
        "term": "apple iphone",
        "predictions": [
          {
            "code": "IP-1000001",
            "name": "iPhone",
            "score": 95
          }
        ]
      }
    ]
  },
  "token_details": {
    "prompt_tokens": 16981,
    "candidates_tokens": 194,
    "total_tokens": 17175
  }
}
```

## Integration with UI

The model API is integrated into the UI's "🚀 Generate New Entry" feature:

1. Click "🚀 Generate New Entry" button in the UI
2. Enter a search term
3. Click "🔍 Generate Predictions"
4. The UI will:
   - Fetch catalog categories from Blibli API
   - Call this model API for AI predictions
   - Display both results
   - Allow saving to MongoDB

## Notes

- Make sure the API is running before using the "Generate New Entry" feature in the UI
- The API uses the `c3_categories.csv` file from the `data/` directory
- Gemini API key is embedded in the code (consider moving to environment variable for production)

