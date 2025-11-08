#!/bin/bash

echo "========================================"
echo "  CodeMind - Starting Application"
echo "========================================"
echo ""

cd backend

if [ ! -f .env ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please create backend/.env with:"
    echo "GEMINI_API_KEY=your_api_key_here"
    echo ""
    echo "Get your FREE API key at: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press enter to continue anyway..."
fi

echo ""
echo "Starting Flask server..."
echo ""
echo "Open your browser to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py

