#!/bin/bash
# =============================================================================
# TEST ENVIRONMENT ONLY
# =============================================================================
# This script is for local testing/development purposes only.
# Do NOT use in production. The frontend served here is a testing interface.
# =============================================================================

set -e

echo "🧪 Starting test environment..."

# Start PostgreSQL if not running
if ! docker ps --format '{{.Names}}' | grep -q "ins-sup-agent-db"; then
    echo "📦 Starting PostgreSQL on port 5433..."
    docker-compose up -d db
    
    echo "⏳ Waiting for database to be ready..."
    until docker exec ins-sup-agent-db pg_isready -U postgres 2>/dev/null; do
        sleep 1
    done
    echo "✅ Database ready!"
fi

echo ""
echo "============================================"
echo "  TEST ENVIRONMENT"
echo "  API Docs: http://localhost:8000/v1/docs"
echo "  Frontend: http://localhost:8000"
echo "============================================"
echo ""
echo "🚀 Starting API server..."

uv run python main.py
