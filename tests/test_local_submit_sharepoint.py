#!/usr/bin/env python3
"""
Test local API submit with SharePoint integration
"""

import requests
import json
import base64
from datetime import datetime

# Local API
API_BASE_URL = "http://127.0.0.1:8010"

def test_submit_with_sharepoint():
    """Test form submission that should save to SharePoint"""
    print("🧪 Testing local submit with SharePoint integration...")
    print(f"🎯 API: {API_BASE_URL}")
    
    # Test data matching form structure
    test_data = {
        "deliveryNoteNumber": f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "truckLicensePlates": "TEST-999-AA",
        "trailerLicensePlates": "TEST-888-BB",
        "carrierCountry": "Poland",
        "carrierTaxCode": "PL9876543210",
        "carrierFullName": "Test Transport Company SRL - GitHub Copilot Test",
        "borderCrossing": "Nădlac II",
        "borderCrossingDate": datetime.now().strftime("%Y-%m-%d"),
        "email": "test@example.com",
        "phoneNumber": "+40 123 456 789"
    }
    
    print(f"📄 Test data:")
    print(json.dumps(test_data, indent=2))
    
    try:
        # Encode data as Base64 (matching frontend behavior)
        json_string = json.dumps(test_data)
        encoded_data = base64.b64encode(json_string.encode()).decode()
        
        print(f"\n🔐 Base64 encoded data: {encoded_data[:50]}...")
        
        # Prepare form data
        form_data = {
            'data': encoded_data
        }
        
        # Send with headers matching frontend
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
            print(f"\n🎯 Request ID: {request_id}")
            print(f"\n📋 Next steps:")
            print(f"1. Check backend logs for SharePoint operations")
            print(f"2. Open SharePoint Excel file:")
            print(f"   https://yourcompany.sharepoint.com/sites/transport-test/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2Ftransport-test%2FShared%20Documents%2FGeneral%2FAll%20Documents%2Ftransport-app&viewid=06c3d9e4%2De76f%2D4dbb%2D82b6%2Da5ca3856dafc")
            print(f"3. Verify new row with Request ID: {request_id}")
            
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
    print("🚀 Starting Local API + SharePoint Test")
    print("=" * 70)
    
    success, response = test_submit_with_sharepoint()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 TEST PASSED! Check SharePoint for new row.")
    else:
        print("⚠️  TEST FAILED. Check logs above.")
