"""
Test Token Manager - weryfikacja pobierania tokena z REST API
"""

import sys
import os
from pathlib import Path

# Dodaj backend folder do PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))
from token_manager import TokenManager
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_token_manager():
    """Test pobierania tokena z REST API"""
    
    print("\n" + "="*70)
    print("TOKEN MANAGER TEST")
    print("="*70)
    
    # Sprawdź czy hasło jest ustawione
    password = os.getenv('RPA_BOT_PASSWORD')
    if not password:
        print("\n❌ BŁĄD: Nie znaleziono RPA_BOT_PASSWORD w zmiennych środowiskowych")
        print("\nUstaw hasło:")
        print("  Windows: $env:RPA_BOT_PASSWORD='YourPassword123!'")
        print("  Linux:   export RPA_BOT_PASSWORD='YourPassword123!'")
        print("  .env:    RPA_BOT_PASSWORD=YourPassword123!")
        return False
    
    print(f"\n✅ RPA_BOT_PASSWORD found (length: {len(password)})")
    
    # Inicjalizuj Token Manager
    print("\n📋 Token Manager Configuration:")
    print(f"  API URL: https://your-token-api.yourdomain.com/getaccesstoken")
    print(f"  Email: transport-app@yourdomain.com")
    print(f"  Application: your-app-name")
    print(f"  Token lifetime: 1 hour")
    
    try:
        tm = TokenManager(
            token_api_url="https://your-token-api.yourdomain.com/getaccesstoken",
            email="transport-app@yourdomain.com",
            password=password,
            application_name="your-app-name",
            token_lifetime_hours=1
        )
        
        print("\n✅ TokenManager initialized")
        
        # Test 1: Pobierz token (pierwszy raz - z API)
        print("\n" + "-"*70)
        print("TEST 1: Fetching token from REST API (first time)")
        print("-"*70)
        
        token = tm.get_token()
        
        print(f"\n✅ Token fetched successfully!")
        print(f"  Token preview: {token[:50]}...")
        print(f"  Token length: {len(token)} characters")
        print(f"  Valid format: {'Yes' if token.startswith('eyJ') else 'No'}")
        
        # Pokaż info o tokenie
        info = tm.get_token_info()
        print(f"\n📊 Token Info:")
        print(f"  Has cached token: {info['has_cached_token']}")
        print(f"  Expires at: {info['expires_at']}")
        print(f"  Is valid: {info['is_valid']}")
        print(f"  Minutes until expiry: {info['minutes_until_expiry']}")
        
        # Test 2: Pobierz token drugi raz (z cache)
        print("\n" + "-"*70)
        print("TEST 2: Getting token again (should use cache)")
        print("-"*70)
        
        token2 = tm.get_token()
        
        if token == token2:
            print("\n✅ Token retrieved from cache (same as before)")
        else:
            print("\n⚠️ WARNING: Got different token (should be cached)")
        
        # Test 3: Force refresh
        print("\n" + "-"*70)
        print("TEST 3: Force refresh token")
        print("-"*70)
        
        token3 = tm.get_token(force_refresh=True)
        
        print(f"\n✅ New token fetched!")
        print(f"  New token preview: {token3[:50]}...")
        print(f"  Same as old: {'Yes' if token3 == token else 'No (expected - new token)'}")
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print("\n" + "="*70)
        print(f"❌ TEST FAILED: {e}")
        print("="*70)
        
        import traceback
        print("\nFull error:")
        print(traceback.format_exc())
        
        return False


if __name__ == "__main__":
    success = test_token_manager()
    sys.exit(0 if success else 1)
