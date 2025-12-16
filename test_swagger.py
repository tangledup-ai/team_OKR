#!/usr/bin/env python
"""
Test script to verify Swagger API documentation is working correctly
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    # Import after Django setup
    from django.urls import reverse
    from django.test import Client
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    client = Client()
    
    print("Testing Swagger API Documentation...")
    
    # Test Swagger UI endpoint
    try:
        response = client.get('/swagger/')
        if response.status_code == 200:
            print("✅ Swagger UI is accessible at /swagger/")
        else:
            print(f"❌ Swagger UI failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Swagger UI error: {e}")
    
    # Test ReDoc endpoint
    try:
        response = client.get('/redoc/')
        if response.status_code == 200:
            print("✅ ReDoc is accessible at /redoc/")
        else:
            print(f"❌ ReDoc failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ ReDoc error: {e}")
    
    # Test Swagger JSON schema
    try:
        response = client.get('/swagger.json')
        if response.status_code == 200:
            print("✅ Swagger JSON schema is accessible at /swagger.json")
            
            # Check if the response contains expected API endpoints
            content = response.content.decode('utf-8')
            if '/api/users/' in content:
                print("✅ Users API endpoints found in schema")
            if '/api/tasks/' in content:
                print("✅ Tasks API endpoints found in schema")
            if '/api/reviews/' in content:
                print("✅ Reviews API endpoints found in schema")
            if '/api/reports/' in content:
                print("✅ Reports API endpoints found in schema")
                
        else:
            print(f"❌ Swagger JSON failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Swagger JSON error: {e}")
    
    print("\nSwagger API Documentation test completed!")
    print("\nTo view the documentation:")
    print("1. Start the Django server: python manage.py runserver")
    print("2. Open your browser and go to:")
    print("   - Swagger UI: http://localhost:8000/swagger/")
    print("   - ReDoc: http://localhost:8000/redoc/")
    print("   - JSON Schema: http://localhost:8000/swagger.json")