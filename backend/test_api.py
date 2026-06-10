import requests
import json

# Test REST API
print("Testing REST API...")

# Test root endpoint
response = requests.get("http://localhost:8000/")
print(f"Root endpoint: {response.status_code}")
print(response.json())

# Test health endpoint
response = requests.get("http://localhost:8000/health")
print(f"\nHealth check: {response.status_code}")
print(response.json())

# Test chat history endpoint
response = requests.get("http://localhost:8000/api/chat/history/teacher1?current_user_id=student1")
print(f"\nChat history: {response.status_code}")
if response.status_code == 200:
    print(f"Found {len(response.json().get('messages', []))} messages")