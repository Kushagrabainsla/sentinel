#!/usr/bin/env python3

"""
Test script for API Gateway authentication system
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "https://api.thesentinel.site/v1"
# API_BASE_URL = "https://xxxxxx.execute-api.us-east-1.amazonaws.com"  # Use if custom domain not set up

def test_registration():
    """Test user registration"""
    print("🔐 Testing user registration...")
    
    user_data = {
        "email": f"test-{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    }
    
    response = requests.post(f"{API_BASE_URL}/auth/register", json=user_data)
    
    if response.status_code == 201:
        result = response.json()
        print(result)
        api_key = result.get('user', {}).get('api_key')
        print(f"✅ Registration successful! API Key: {api_key if api_key else 'Not provided'}")
        return api_key
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None

def test_authentication(api_key):
    """Test authentication with API key"""
    print(f"\n🔑 Testing authentication with API key...")
    
    headers = {"X-API-Key": api_key}
    
    # Test authenticated endpoint - get user info
    response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        user_info = response.json()
        print(f"✅ Authentication successful! User: {user_info.get('user', {}).get('email')}")
        return True
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        return False

def test_segments_api(api_key):
    """Test segments API with authentication"""
    print(f"\n📊 Testing segments API with authentication...")
    
    headers = {"X-API-Key": api_key}
    
    # Test creating a segment
    segment_data = {
        "name": "API Gateway Test Segment",
        "description": "Testing API Gateway authentication",
        "emails": ["test1@example.com", "test2@example.com"]
    }
    
    print("Creating segment...")
    response = requests.post(f"{API_BASE_URL}/segments", json=segment_data, headers=headers)
    
    if response.status_code == 201:
        segment = response.json().get('segment', {})
        segment_id = segment.get('id')
        print(f"✅ Segment created successfully! ID: {segment_id}")
        
        # Test listing segments
        print("Listing segments...")
        response = requests.get(f"{API_BASE_URL}/segments", headers=headers)
        
        if response.status_code == 200:
            segments = response.json().get('segments', [])
            print(f"✅ Listed {len(segments)} segments")
            
            # Test getting specific segment
            if segment_id:
                print(f"Getting segment {segment_id}...")
                response = requests.get(f"{API_BASE_URL}/segments/{segment_id}", headers=headers)
                
                if response.status_code == 200:
                    print("✅ Got segment successfully!")
                    return segment_id
                else:
                    print(f"❌ Failed to get segment: {response.status_code} - {response.text}")
        else:
            print(f"❌ Failed to list segments: {response.status_code} - {response.text}")
    else:
        print(f"❌ Failed to create segment: {response.status_code} - {response.text}")
    
    return None

def test_unauthorized_access():
    """Test that endpoints are protected without authentication"""
    print(f"\n🚫 Testing unauthorized access...")
    
    # Try to access protected endpoint without API key
    response = requests.get(f"{API_BASE_URL}/segments")
    
    if response.status_code == 401:
        print("✅ Correctly rejected unauthorized request!")
        return True
    else:
        print(f"❌ Should have rejected unauthorized request! Got: {response.status_code}")
        return False

def test_invalid_api_key():
    """Test with invalid API key"""
    print(f"\n🔐 Testing invalid API key...")
    
    headers = {"X-API-Key": "invalid-key-12345"}
    
    response = requests.get(f"{API_BASE_URL}/segments", headers=headers)
    
    if response.status_code == 401:
        print("✅ Correctly rejected invalid API key!")
        return True
    else:
        print(f"❌ Should have rejected invalid API key! Got: {response.status_code}")
        return False

def main():
    """Run all authentication tests"""
    print("🚀 Starting API Gateway Authentication Tests")
    print("=" * 50)
    
    try:
        # Test 1: Registration
        api_key = test_registration()
        if not api_key:
            print("❌ Cannot continue without valid API key")
            return
        
        # Test 2: Authentication
        if not test_authentication(api_key):
            print("❌ Cannot continue with failed authentication")
            return
        
        # Test 3: Segments API with auth
        segment_id = test_segments_api(api_key)
        
        # Test 4: Unauthorized access
        test_unauthorized_access()
        
        # Test 5: Invalid API key
        test_invalid_api_key()
        
        print("\n" + "=" * 50)
        print("🎉 API Gateway authentication tests completed!")
        
        if segment_id:
            print(f"\n💡 You can clean up the test segment with:")
            print(f"   curl -X DELETE {API_BASE_URL}/segments/{segment_id} -H 'X-API-Key: {api_key}'")
        
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")

if __name__ == "__main__":
    main()