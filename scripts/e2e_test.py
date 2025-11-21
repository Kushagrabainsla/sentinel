import requests
import json
import os
import time

# Configuration
API_BASE_URL = "https://api.thesentinel.site" # Update if different
API_KEY = os.environ.get("SENTINEL_API_KEY") # If needed for protected routes
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # Used for local verification if needed

def test_subject_line_generator():
    print("\n--- Testing Subject Line Generator ---")
    url = f"{API_BASE_URL}/api/generate-subject-lines"
    payload = {
        "content": "Black Friday sale. 70% off everything.",
        "audience": "Bargain hunters",
        "goal": "Maximize revenue"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("SUCCESS: Generated subject lines:")
            print(json.dumps(response.json(), indent=2))
            return response.json()
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

def test_optimization_agent():
    print("\n--- Testing Campaign Optimization Agent ---")
    url = f"{API_BASE_URL}/api/analyze-optimization"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("SUCCESS: Optimization analysis received:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

def main():
    print("Starting End-to-End Test for AI Features...")
    
    # 1. Generate Subject Lines
    suggestions = test_subject_line_generator()
    
    # 2. (Optional) Create Campaign & Send - omitted as per user request to focus on AI features first
    # But user said "we will send actual mail... and when we get analytics... call these analytics"
    # For this script, we will just test the AI endpoints. 
    # The optimization agent relies on existing data. If the DB is empty, it will return a message.
    
    # 3. Analyze Optimization
    test_optimization_agent()

if __name__ == "__main__":
    main()
