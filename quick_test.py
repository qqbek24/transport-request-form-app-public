import requests
import json

# Test z dokładnie takimi samymi danymi jak z przeglądarki
test_data = {
    'deliveryNoteNumber': 'test_1',
    'truckLicensePlates': 'test_1', 
    'trailerLicensePlates': 'test_1',
    'carrierCountry': 'Ukraine',
    'carrierTaxCode': 'test_1',
    'carrierFullName': 'test_1',
    'borderCrossing': 'Vărşand',
    'borderCrossingDate': '2025-10-29'
}

print('🧪 Test z takimi samymi danymi jak w przeglądarce')
print('✅ Poprawny URL z portem 5443')
print('📤 Sending to API...')

response = requests.post(
    'https://your-url-address:5443/api/submit',
    data={'data': json.dumps(test_data)},
    timeout=30
)

print(f'📊 Status: {response.status_code}')

if response.status_code == 200:
    result = response.json()
    print('✅ SUCCESS!')
    print(f'🆔 Request ID: {result.get("request_id")}')
    print('🎯 FRONTEND POWINIEN DZIAŁAĆ gdy Jenkins zdeployuje nową wersję!')
else:
    print(f'❌ ERROR: {response.text}')
    print('Jenkins nadal deployuje starą wersję bez portu 5443')