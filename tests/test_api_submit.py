#!/usr/bin/env python3
"""
Test script for Transport Request API
Tests the /api/submit endpoint with various test data scenarios
"""

import requests
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

# API Configuration
API_BASE_URL = "https://your-production-server.yourdomain.com:5443"
SUBMIT_ENDPOINT = f"{API_BASE_URL}/api/submit"

# Test data templates
TEST_COUNTRIES = ["Austria", "Germany", "Hungary", "Bulgaria", "Serbia", "Poland"]
TEST_BORDER_CROSSINGS = [
    "Nădlac II", "Borș II", "Petea", "Urziceni", "Cenad", "Moravița",
    "Stamora Moravița", "Jimbolia", "Naidăș", "Turnu"
]

def generate_test_data():
    """Generate random test data for transport request"""
    today = datetime.now()
    crossing_date = today + timedelta(days=random.randint(1, 30))
    
    return {
        "deliveryNoteNumber": f"DN{random.randint(100000, 999999)}",
        "truckLicensePlates": f"TR-{random.randint(100, 999)}-AB",
        "trailerLicensePlates": f"TL-{random.randint(100, 999)}-CD",
        "carrierCountry": random.choice(TEST_COUNTRIES),
        "carrierTaxCode": f"TAX{random.randint(10000000, 99999999)}",
        "carrierFullName": f"Transport Company {random.randint(1, 100)} SRL",
        "borderCrossing": random.choice(TEST_BORDER_CROSSINGS),
        "borderCrossingDate": crossing_date.strftime("%Y-%m-%d"),
        "email": f"test{random.randint(1, 1000)}@example.com",
        "phoneNumber": f"+40 {random.randint(700, 799)} {random.randint(100, 999)} {random.randint(100, 999)}"
    }

def create_test_file():
    """Create a temporary test file for attachment"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(f"""Test attachment file
Created: {datetime.now().isoformat()}
Purpose: API testing
Content: Random test data for transport request
""")
    temp_file.close()
    return temp_file.name

def test_submit_without_attachment():
    """Test submit endpoint without attachment"""
    print("🧪 Testing submit WITHOUT attachment...")
    
    test_data = generate_test_data()
    print(f"📄 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Prepare form data
        form_data = {
            'data': json.dumps(test_data)
        }
        
        response = requests.post(SUBMIT_ENDPOINT, data=form_data, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"✅ SUCCESS: {json.dumps(response_json, indent=2)}")
            return True, response_json
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False, None

def test_submit_with_attachment():
    """Test submit endpoint with attachment"""
    print("\n🧪 Testing submit WITH attachment...")
    
    test_data = generate_test_data()
    test_file_path = create_test_file()
    
    print(f"📄 Test data: {json.dumps(test_data, indent=2)}")
    print(f"📎 Test file: {test_file_path}")
    
    try:
        # Prepare form data with file
        form_data = {
            'data': json.dumps(test_data)
        }
        
        with open(test_file_path, 'rb') as f:
            files = {'attachments': ('test_document.txt', f, 'text/plain')}
            
            response = requests.post(SUBMIT_ENDPOINT, data=form_data, files=files, timeout=30)
        
        # Cleanup temp file
        os.unlink(test_file_path)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"✅ SUCCESS: {json.dumps(response_json, indent=2)}")
            return True, response_json
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        # Cleanup temp file on error
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
        return False, None

def test_api_health():
    """Test API health endpoint"""
    print("🧪 Testing API health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=10)
        print(f"📊 Health Status: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health OK: {health_data}")
            return True
        else:
            print(f"❌ Health FAIL: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Health EXCEPTION: {e}")
        return False

def test_invalid_data():
    """Test submit with invalid data"""
    print("\n🧪 Testing submit with INVALID data...")
    
    # Missing required fields
    invalid_data = {
        "deliveryNoteNumber": "",  # Empty required field
        "truckLicensePlates": "TR-123-AB",
        "email": ""  # Empty required email field
        # Missing other required fields
    }
    
    print(f"📄 Invalid data: {json.dumps(invalid_data, indent=2)}")
    
    try:
        form_data = {
            'data': json.dumps(invalid_data)
        }
        
        response = requests.post(SUBMIT_ENDPOINT, data=form_data, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 400:
            print(f"✅ EXPECTED ERROR: {response.text}")
            return True
        else:
            print(f"❌ UNEXPECTED: Expected 400, got {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Transport Request API Tests")
    print(f"🎯 API Base URL: {API_BASE_URL}")
    print("=" * 60)
    
    results = []
    
    # Test 1: API Health
    results.append(("API Health", test_api_health()))
    
    # Test 2: Submit without attachment
    success, response = test_submit_without_attachment()
    results.append(("Submit without attachment", success))
    
    # Test 3: Submit with attachment
    success, response = test_submit_with_attachment()
    results.append(("Submit with attachment", success))
    
    # Test 4: Invalid data
    results.append(("Invalid data handling", test_invalid_data()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY:")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()