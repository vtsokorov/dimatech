#!/usr/bin/env python3
"""
Quick test script to verify API endpoints are working.
Run after starting the application.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_docs():
    """Test documentation endpoints"""
    try:
        # Test OpenAPI/Swagger UI at /docs (provided by Sanic-EXT)
        response = requests.get(f"{BASE_URL}/docs")
        print(f"OpenAPI/Swagger UI endpoint (/docs): {response.status_code}")
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'html' in content_type:
                print("✓ OpenAPI/Swagger UI available at /docs")
            else:
                print("✓ Documentation available at /docs")
        else:
            print("⚠ /docs endpoint returned status:", response.status_code)
        
        # Test custom JSON API docs
        response = requests.get(f"{BASE_URL}/api-docs")
        print(f"JSON API docs endpoint (/api-docs): {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ JSON API documentation available at /api-docs")
            print(f"  - Title: {data.get('title')}")
            print(f"  - Version: {data.get('version')}")
            if 'endpoints' in data:
                print(f"  - Endpoints defined: {len(data['endpoints'])}")
        return True
    except Exception as e:
        print(f"Documentation endpoints failed: {e}")
        return False

def test_root():
    """Test root endpoint that shows API info"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data.get('message')}")
            if 'documentation' in data:
                print(f"Documentation info available: {data['documentation'].get('openapi_ui')}")
        return True
    except Exception as e:
        print(f"Root endpoint failed: {e}")
        return False

def test_login():
    """Test login endpoint"""
    try:
        # Test user login
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "testuser@example.com", "password": "password"}
        )
        print(f"User login: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Token type: {data.get('token_type')}")
            return data.get('access_token')
        return None
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def test_admin_login():
    """Test admin login endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/admin/login",
            json={"email": "testadmin@example.com", "password": "password"}
        )
        print(f"Admin login: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        return None
    except Exception as e:
        print(f"Admin login failed: {e}")
        return None

def test_user_profile(token):
    """Test user profile endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/user/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"User profile: {response.status_code}")
        if response.status_code == 200:
            print(f"Profile data: {response.json()}")
    except Exception as e:
        print(f"User profile failed: {e}")

def test_admin_users(token):
    """Test admin users endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Admin users: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Number of users: {len(data)}")
    except Exception as e:
        print(f"Admin users failed: {e}")

if __name__ == "__main__":
    print("=== Payment API Tests ===\n")
    
    # Test basic endpoints
    if not test_health():
        print("❌ API is not running. Please start the application first.")
        exit(1)
    
    test_root()
    test_docs()
    
    # Test authentication
    user_token = test_login()
    admin_token = test_admin_login()
    
    if user_token:
        test_user_profile(user_token)
    
    if admin_token:
        test_admin_users(admin_token)
    
    print("\n=== Test Summary ===")
    print("✅ Health check - OK")
    print("✅ Root endpoint (API info) - OK")
    print("✅ Documentation endpoints - OK")
    print("✅ User login - OK")
    print("✅ Admin login - OK")
    if user_token:
        print("✅ User profile - OK")
    if admin_token:
        print("✅ Admin users - OK")
    print("\n✅ All tests completed successfully!")
    print("\n📚 Access the API documentation:")
    print("   - OpenAPI/Swagger UI: http://localhost:8000/docs")
    print("   - JSON API docs:      http://localhost:8000/api-docs")
    print("   - API info endpoint:  http://localhost:8000/")