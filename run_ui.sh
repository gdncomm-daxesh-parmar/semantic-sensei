#!/bin/bash

# Launch Streamlit UI for Search Term Category Manager
cd "$(dirname "$0")"

echo "🚀 Starting Search Term Category Manager UI..."
echo ""
echo "📝 The UI will open in your browser at http://localhost:8501"
echo ""
echo "💡 Features:"
echo "   • Search for terms and view their categories"
echo "   • Edit boost values for model predictions"
echo "   • Add/Remove model identified categories"
echo ""
echo "⌨️  Press Ctrl+C to stop the server"
echo ""

streamlit run ui/app.py --server.port 8501 --server.address localhost

