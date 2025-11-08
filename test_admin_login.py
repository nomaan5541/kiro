#!/usr/bin/env python3
"""Test script to simulate admin login"""

import requests

def test_admin_login():
    base_url = "http://127.0.0.1:5000"
    
    # First, get the login page to establish a session
    session = requests.Session()
    
    print("1. Getting login page...")
    response = session.get(f"{base_url}/auth/login")
    print(f"   Status: {response.status_code}")
    
    # Now try to login
    print("2. Attempting admin login...")
    login_data = {
        'role': 'admin',
        'email': 'demo@school.com',
        'password': 'school123'
    }
    
    response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    
    if response.status_code == 302:
        print(f"   Redirect to: {response.headers.get('Location')}")
        print("   ✅ Login successful!")
    else:
        print(f"   Response text: {response.text[:500]}...")
        print("   ❌ Login failed!")

if __name__ == '__main__':
    test_admin_login()