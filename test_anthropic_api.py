#!/usr/bin/env python3
"""Direct test of Anthropic API to diagnose 404 errors."""

import os
import sys
import httpx
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# Get API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ANTHROPIC_API_KEY not found in environment")
    sys.exit(1)

print(f"🔑 API Key found: {api_key[:10]}...{api_key[-10:]}")

# Test API call
url = "https://api.anthropic.com/v1/messages"
headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

payload = {
    "model": "claude-sonnet-4-5",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Say 'Hello from Anthropic API test!'"}],
}

print(f"📡 Making request to: {url}")
print(f"🤖 Using model: claude-sonnet-4-5")
print(f"📦 Payload: {payload}")

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=payload)

        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response: {data}")
            content = data.get("content", [{}])[0].get("text", "")
            print(f"📝 Model response: {content}")
        else:
            print(f"❌ Error Response: {response.text}")
            print(f"🔍 Full response: {response}")

except httpx.TimeoutException:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
