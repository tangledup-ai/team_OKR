#!/usr/bin/env python
"""
Quick verification script to test the User Authentication API
Run this after starting the Django server: python manage.py runserver
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/users"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")

def main():
    print("🚀 Testing User Authentication API")
    print("="*60)
    
    # Test 1: Login as admin
    print("\n1️⃣ Testing Admin Login...")
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    print_response("Admin Login", response)
    
    if response.status_code == 200:
        admin_token = response.json()['access']
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test 2: List users
        print("\n2️⃣ Testing User List...")
        response = requests.get(f"{BASE_URL}/", headers=headers)
        print_response("User List", response)
        
        # Test 3: Register new user
        print("\n3️⃣ Testing User Registration (Admin)...")
        new_user_data = {
            "email": "testuser@example.com",
            "name": "测试用户",
            "department": "software",
            "role": "member",
            "password": "testpass123",
            "password_confirm": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/auth/register/", json=new_user_data, headers=headers)
        print_response("User Registration", response)
        
        if response.status_code == 201:
            new_user_id = response.json()['id']
            
            # Test 4: Login as new user
            print("\n4️⃣ Testing New User Login...")
            login_data = {
                "email": "testuser@example.com",
                "password": "testpass123"
            }
            response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
            print_response("New User Login", response)
            
            # Test 5: Get user detail
            print("\n5️⃣ Testing User Detail...")
            response = requests.get(f"{BASE_URL}/{new_user_id}/", headers=headers)
            print_response("User Detail", response)
            
            # Test 6: Update user
            print("\n6️⃣ Testing User Update (Admin)...")
            update_data = {
                "name": "更新后的名字",
                "department": "hardware"
            }
            response = requests.patch(f"{BASE_URL}/{new_user_id}/", json=update_data, headers=headers)
            print_response("User Update", response)
            
            # Test 7: Delete user (cleanup)
            print("\n7️⃣ Testing User Delete (Cleanup)...")
            response = requests.delete(f"{BASE_URL}/{new_user_id}/", headers=headers)
            print_response("User Delete", response)
    
    print("\n" + "="*60)
    print("✅ API Verification Complete!")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Please make sure the Django server is running:")
        print("  python manage.py runserver")
    except Exception as e:
        print(f"\n❌ Error: {e}")
