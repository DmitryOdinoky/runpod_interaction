#!/usr/bin/env python3
"""Test RunPod API connection and endpoint"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

print(f"Testing RunPod endpoint: {RUNPOD_ENDPOINT_ID}")
print(f"API Key: {RUNPOD_API_KEY[:10]}..." if RUNPOD_API_KEY else "No API key found")

# Test 1: Check endpoint health
health_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/health"
print(f"\n1. Testing health endpoint: {health_url}")

try:
    response = requests.get(health_url, headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"})
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Try /runsync endpoint
runsync_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"
print(f"\n2. Testing /runsync endpoint: {runsync_url}")

minimal_workflow = {
    "input": {
        "workflow": {
            "30": {
                "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"},
                "class_type": "CheckpointLoaderSimple"
            }
        }
    }
}

try:
    response = requests.post(
        runsync_url,
        json=minimal_workflow,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RUNPOD_API_KEY}"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Try /run endpoint (async)
run_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"
print(f"\n3. Testing /run endpoint (async): {run_url}")

try:
    response = requests.post(
        run_url,
        json=minimal_workflow,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RUNPOD_API_KEY}"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*60)
print("Diagnosis:")
print("="*60)
print("- If health returns 200: Endpoint is running")
print("- If /runsync works: Bot should work fine")
print("- If only /run works: Need to update bot to use async API")
print("- If all fail: Check RunPod dashboard for endpoint status")
