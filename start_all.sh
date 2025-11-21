#!/bin/bash

cd "$(dirname "$0")"

echo "🚀 Starting Semantic Sensei Services..."
echo ""

# Kill existing processes
echo "Stopping existing processes..."
pkill -f "python.*model_predict.py" 2>/dev/null
pkill -f "streamlit.*app.py" 2>/dev/null
sleep 2

# Start Model API
echo "Starting Model API (port 8090)..."
python model/model_predict.py > model.log 2>&1 &
MODEL_PID=$!
echo "  Model API PID: $MODEL_PID"
sleep 3

# Check if model started
if lsof -ti:8090 > /dev/null 2>&1; then
    echo "  ✅ Model API started successfully"
else
    echo "  ❌ Model API failed to start. Check model.log"
    exit 1
fi

# Start Streamlit UI
echo ""
echo "Starting Streamlit UI (port 8501)..."
streamlit run ui/app.py --server.port 8501 --server.address localhost > streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "  Streamlit PID: $STREAMLIT_PID"
sleep 5

# Check if Streamlit started
if lsof -ti:8501 > /dev/null 2>&1; then
    echo "  ✅ Streamlit UI started successfully"
else
    echo "  ❌ Streamlit failed to start. Check streamlit.log"
    exit 1
fi

echo ""
echo "=" * 60
echo "✅ All services started successfully!"
echo "=" * 60
echo ""
echo "🔗 Access Points:"
echo "   Model API: http://localhost:8090"
echo "   Streamlit UI: http://localhost:8501"
echo ""
echo "📝 Logs:"
echo "   Model: model.log"
echo "   Streamlit: streamlit.log"
echo ""
echo "⏹️  To stop: pkill -f 'model_predict.py|streamlit.*app.py'"
echo ""

