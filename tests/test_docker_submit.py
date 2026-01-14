#!/usr/bin/env python3
"""
Test Docker API submit with SharePoint integration
"""

import requests
import json
import base64
from datetime import datetime

# Docker API
API_BASE_URL = "http://localhost:8010"

def test_submit_docker():
    """Test form submission via Docker container"""
    print("🐳 Testing Docker submit with SharePoint integration...")
    print(f"🎯 API: {API_BASE_URL}")
    
    # Test data
    test_data = {
        "deliveryNoteNumber": f"DOCKER-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "truckLicensePlates": "DOCKER-999-AA",
        "trailerLicensePlates": "DOCKER-888-BB",
        "carrierCountry": "Germany",
        "carrierTaxCode": "DE1234567890",
        "carrierFullName": "Docker Test Transport GmbH",
        "borderCrossing": "Nădlac II",
        "borderCrossingDate": datetime.now().strftime("%Y-%m-%d"),
        "email": "docker-test@example.com",
        "phoneNumber": "+49 123 456 789"
    }
    
    print(f"📄 Test data:")
    print(json.dumps(test_data, indent=2))
    
    try:
        # Encode data as Base64
        json_string = json.dumps(test_data)
        encoded_data = base64.b64encode(json_string.encode()).decode()
        
        form_data = {'data': encoded_data}
        
        headers = {
            'X-Content-Type': 'application/transport-form',
            'X-Request-Source': 'transport-frontend',
            'X-Bypass-SQLI': 'legitimate-form-data',
            'X-Data-Encoding': 'base64'
        }
        
        print(f"\n📤 Sending POST to {API_BASE_URL}/api/submit...")
        response = requests.post(
            f"{API_BASE_URL}/api/submit",
            data=form_data,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"✅ SUCCESS!")
            print(json.dumps(response_json, indent=2))
            
            request_id = response_json.get('request_id')
            excel_saved = response_json.get('excel_saved')
            
            print(f"\n🎯 Request ID: {request_id}")
            print(f"📊 Excel Saved: {excel_saved}")
            
            if excel_saved:
                print(f"\n✅ SharePoint integration works in Docker!")
                print(f"📋 Check SharePoint Excel for new row with Request ID: {request_id}")
            else:
                print(f"\n⚠️  Excel not saved - check backend logs")
            
            return True, response_json
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    print("🚀 Starting Docker API + SharePoint Test")
    print("=" * 70)
    
    success, response = test_submit_docker()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 DOCKER TEST PASSED!")
    else:
        print("⚠️  DOCKER TEST FAILED.")
