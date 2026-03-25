#!/bin/bash
# Quick test script for Kostructure

echo "🧪 Kostructure Test Suite"
echo "========================="
echo ""

# Check if services are running
echo "1️⃣ Checking services..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ API Gateway: Running"
else
    echo "   ❌ API Gateway: Not running"
    echo "   Run: docker-compose up -d"
    exit 1
fi

if curl -s http://localhost:8001/health > /dev/null; then
    echo "   ✅ Parser Service: Running"
else
    echo "   ❌ Parser Service: Not running"
fi

if curl -s http://localhost:8002/health > /dev/null; then
    echo "   ✅ Cost Service: Running"
else
    echo "   ❌ Cost Service: Not running"
fi

echo ""
echo "2️⃣ Testing CLI..."
if [ -f "./cli/kostructure" ]; then
    echo "   ✅ CLI binary exists"
    ./cli/kostructure estimate --path examples/basic-ec2.tf > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ CLI working"
    else
        echo "   ❌ CLI failed"
    fi
else
    echo "   ❌ CLI not built. Run: ./build-cli.sh"
fi

echo ""
echo "3️⃣ Testing API..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "files": [{
      "name": "test.tf",
      "content": "resource \"aws_instance\" \"test\" { instance_type = \"t3.micro\" }"
    }],
    "region": "us-east-1"
  }')

if echo "$RESPONSE" | grep -q "total_monthly_cost"; then
    COST=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_monthly_cost'])")
    echo "   ✅ API working (Cost: \$$COST/month)"
else
    echo "   ❌ API failed"
fi

echo ""
echo "4️⃣ Sample files available:"
ls -1 examples/*.tf | wc -l | xargs echo "   📄" "files in examples/"

echo ""
echo "✨ Test complete!"
echo ""
echo "Try:"
echo "  ./cli/kostructure estimate --path examples/production.tf"
echo "  Open http://localhost:3000 for Web UI"
