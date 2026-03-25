#!/bin/bash

echo "🚀 Starting Kostructure..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "📦 Building services..."
docker-compose build

echo "🔧 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ API Gateway: healthy" || echo "❌ API Gateway: unhealthy"
curl -s http://localhost:8001/health | grep -q "healthy" && echo "✅ Parser Service: healthy" || echo "❌ Parser Service: unhealthy"
curl -s http://localhost:8002/health | grep -q "healthy" && echo "✅ Cost Service: healthy" || echo "❌ Cost Service: unhealthy"

echo ""
echo "✨ Kostructure is ready!"
echo ""
echo "📍 Access points:"
echo "   Web UI:        http://localhost:3000"
echo "   API Gateway:   http://localhost:8000"
echo "   Parser:        http://localhost:8001"
echo "   Cost Service:  http://localhost:8002"
echo ""
echo "📝 View logs: docker-compose logs -f"
echo "🛑 Stop:      docker-compose down"
