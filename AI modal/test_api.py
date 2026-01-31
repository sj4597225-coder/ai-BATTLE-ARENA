"""
Quick test script for the AI PDF QA API
"""
import requests
import json

API_URL = "http://localhost:8000/aibattle"

# Test data
test_data = {
    "pdf_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "questions": [
        "What is this document about?",
        "What is the purpose of this PDF?"
    ]
}

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get("http://localhost:8000/api/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_answer():
    """Test answer endpoint"""
    print("Testing answer endpoint...")
    print(f"Request: {json.dumps(test_data, indent=2)}")
    print()
    
    response = requests.post(API_URL, json=test_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("=" * 60)
    print("AI PDF Question Answering System - Test Script")
    print("=" * 60)
    print()
    
    try:
        test_health()
        test_answer()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server.")
        print("Make sure the server is running: uvicorn app:app --reload")
    except Exception as e:
        print(f"ERROR: {e}")
