#!/bin/bash
# Build CLI using Docker

docker run --rm \
  -v "$(pwd)/cli:/app" \
  -w /app \
  golang:1.21-alpine \
  sh -c "go mod tidy && go build -o kostructure main.go"

echo "✅ CLI built: cli/kostructure"
