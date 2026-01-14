"""
Token Manager - Automatyczne pobieranie i odświeżanie Access Token z REST API
"""

import requests
import warnings
import ssl
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

# Wyłącz ostrzeżenia SSL dla wewnętrznych API bez certyfikatu
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Zarządza pobieraniem i cache'owaniem Access Token z wewnętrznego API
    
    Token jest:
    - Pobierany z REST API gdy jest potrzebny
    - Cache'owany w pamięci z datą wygaśnięcia
    - Automatycznie odświeżany gdy wygaśnie
    """
    
    def __init__(self, 
                 token_api_url: str = "https://your-token-api.yourdomain.com/getaccesstoken",
                 email: str = "transport-app@yourdomain.com",
                 password: str = None,
                 application_name: str = "your-app-name",
                 token_lifetime_hours: int = 1):
        """
        Inicjalizacja Token Manager
        
        Args:
            token_api_url: URL API do pobierania tokena
            email: Email użytkownika RPA
            password: Hasło (z env lub keyring)
            application_name: Nazwa aplikacji RPA
            token_lifetime_hours: Ile godzin token jest ważny (default: 1h)
        """
        self.token_api_url = token_api_url
        self.email = email
        self.application_name = application_name
        self.token_lifetime_hours = token_lifetime_hours
        
        # Token cache
        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Pobierz hasło z env (fallback: ze zmiennej środowiskowej)
        self.password = password or os.getenv('RPA_BOT_PASSWORD')
        
        if not self.password:
            logger.warning("\033[93m⚠ RPA_BOT_PASSWORD not set - token fetching will fail\033[0m")
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        Pobierz Access Token (z cache lub z API)
        
        Args:
            force_refresh: Czy wymusić pobranie nowego tokena (ignoruj cache)
            
        Returns:
            str: Access Token gotowy do użycia
            
        Raises:
            Exception: Jeśli nie udało się pobrać tokena
        """
        # Sprawdź czy mamy ważny token w cache
        if not force_refresh and self._is_token_valid():
            logger.debug("\033[92m✓ Using cached token (valid)\033[0m")
            return self._cached_token
        
        # Pobierz nowy token z API
        logger.info("\033[94mℹ Fetching new access token from API...\033[0m")
        try:
            token = self._fetch_token_from_api()
            self._cached_token = token
            self._token_expires_at = datetime.now() + timedelta(hours=self.token_lifetime_hours)
            logger.info(f"\033[92m✓ New token fetched (expires: {self._token_expires_at.strftime('%Y-%m-%d %H:%M:%S')})\033[0m")
            return token
        except Exception as e:
            logger.error(f"\033[91m✗ Failed to fetch token: {e}\033[0m")
            # Fallback: spróbuj użyć tokena z .env jeśli jest
            env_token = os.getenv('SHAREPOINT_ACCESS_TOKEN')
            if env_token:
                logger.warning("\033[93m⚠ Using fallback token from SHAREPOINT_ACCESS_TOKEN env variable\033[0m")
                return env_token
            raise
    
    def _is_token_valid(self) -> bool:
        """Sprawdź czy cached token jest jeszcze ważny"""
        if not self._cached_token or not self._token_expires_at:
            return False
        
        # Token jest ważny jeśli nie wygasł (z 5min buforem bezpieczeństwa)
        buffer = timedelta(minutes=5)
        return datetime.now() < (self._token_expires_at - buffer)
    
    def _fetch_token_from_api(self) -> str:
        """
        Pobierz token z REST API (wewnętrzne API)
        
        Returns:
            str: Access Token
            
        Raises:
            Exception: Jeśli API zwróci błąd
        """
        if not self.password:
            raise ValueError("RPA_BOT_PASSWORD not configured - cannot fetch token")
        
        try:
            # Przygotuj request do Token Manager API
            body = {
                "email": self.email,
                "password": self.password,
                "application_name": self.application_name
            }
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            logger.info(f"\033[94mℹ Fetching token from API: {self.token_api_url}\033[0m")
            
            # Wyślij zapytanie do API
            response = requests.post(
                self.token_api_url,
                json=body,
                headers=headers,
                verify=False,  # Wewnętrzne API bez weryfikacji SSL
                timeout=30
            )
            
            logger.info(f"\033[92m✓ Token API response: {response.status_code}\033[0m")
            
        except Exception as e:
            logger.error(f"\033[91m✗ Token API connection error: {type(e).__name__}: {str(e)}\033[0m")
            raise
        
        # Sprawdź status
        if response.status_code != 200:
            error_msg = f"Token API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Pobierz token z odpowiedzi
        try:
            response_json = response.json()
            token = response_json.get('access_token')
            
            if not token:
                raise ValueError("Response does not contain 'access_token' field")
            
            logger.debug(f"Token received: {token[:50]}... (length: {len(token)})")
            return token
            
        except (ValueError, KeyError) as e:
            error_msg = f"Invalid API response: {e} - Response: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def clear_cache(self):
        """Wyczyść cached token (wymusi pobranie nowego przy następnym użyciu)"""
        self._cached_token = None
        self._token_expires_at = None
        logger.info("\033[94mℹ Token cache cleared\033[0m")
    
    def get_token_info(self) -> dict:
        """
        Pobierz informacje o stanie tokena (do diagnostyki)
        
        Returns:
            dict: Informacje o tokenie
        """
        return {
            "has_cached_token": bool(self._cached_token),
            "token_preview": self._cached_token[:50] + "..." if self._cached_token else None,
            "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
            "is_valid": self._is_token_valid(),
            "minutes_until_expiry": int((self._token_expires_at - datetime.now()).total_seconds() / 60) 
                                    if self._token_expires_at and self._is_token_valid() else None,
            "config": {
                "email": self.email,
                "application_name": self.application_name,
                "token_api_url": self.token_api_url,
                "token_lifetime_hours": self.token_lifetime_hours,
                "has_password": bool(self.password)
            }
        }


# Global singleton instance
_token_manager: Optional[TokenManager] = None


def get_token_manager(config: dict = None) -> TokenManager:
    """
    Pobierz singleton instance TokenManager
    
    Args:
        config: Opcjonalna konfiguracja (jeśli None, użyje domyślnych wartości)
        
    Returns:
        TokenManager: Instance token managera
    """
    global _token_manager
    
    if _token_manager is None:
        # Inicjalizuj z konfiguracją
        if config:
            token_config = config.get('token_manager', {})
            _token_manager = TokenManager(
                token_api_url=token_config.get('api_url', 
                    'https://your-token-api.yourdomain.com/getaccesstoken'),
                email=token_config.get('email', 'transport-app@yourdomain.com'),
                password=token_config.get('password') or os.getenv('RPA_BOT_PASSWORD'),
                application_name=token_config.get('application_name', 'your-app-name'),
                token_lifetime_hours=token_config.get('token_lifetime_hours', 1)
            )
        else:
            # Domyślna konfiguracja
            _token_manager = TokenManager()
        
        logger.info("\033[94mℹ TokenManager initialized\033[0m")
    
    return _token_manager


def get_access_token(force_refresh: bool = False) -> str:
    """
    Convenience function: Pobierz Access Token
    
    Args:
        force_refresh: Czy wymusić pobranie nowego tokena
        
    Returns:
        str: Access Token
    """
    manager = get_token_manager()
    return manager.get_token(force_refresh=force_refresh)
