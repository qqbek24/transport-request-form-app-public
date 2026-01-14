from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, timedelta
import random
import os
import json
import logging
import yaml
import base64
import traceback
from pathlib import Path
import time
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
from urllib.parse import unquote as decodeURIComponent
from collections import deque
from threading import Lock

# Load environment variables from .env file (for local development)
load_dotenv()

# Import custom modules
from logger_config import get_logger
from sharepoint_helper import SharePointHelper
from token_manager import get_token_manager

# Import utility modules
# Import background scheduler tasks
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get structured logger
app_logger = get_logger()

# ========================================
# Performance Metrics Storage
# ========================================
class PerformanceMetrics:
    """Thread-safe storage for upload performance metrics"""
    def __init__(self, max_entries=100):
        self.max_entries = max_entries
        self.uploads = deque(maxlen=max_entries)  # Recent attachment uploads
        self.submissions = deque(maxlen=max_entries)  # Recent form submissions
        self.lock = Lock()
        
    def record_submission(self, request_id: str, has_attachments: bool, 
                         attachments_count: int, duration: float, success: bool, 
                         error: str = None, user_ip: str = None):
        """Record form submission metrics"""
        with self.lock:
            self.submissions.append({
                'timestamp': datetime.now().isoformat(),
                'request_id': request_id,
                'has_attachments': has_attachments,
                'attachments_count': attachments_count,
                'duration_seconds': round(duration, 3),
                'success': success,
                'error': error,
                'user_ip': user_ip
            })
    
    def record_upload(self, request_id: str, filename: str, file_size: int, 
                     duration: float, success: bool, error: str = None):
        """Record single file upload metrics"""
        with self.lock:
            self.uploads.append({
                'timestamp': datetime.now().isoformat(),
                'request_id': request_id,
                'filename': filename,
                'file_size_bytes': file_size,
                'duration_seconds': round(duration, 3),
                'success': success,
                'error': error
            })
    
    def get_stats(self) -> dict:
        """Calculate aggregate statistics"""
        with self.lock:
            # Upload statistics (attachments only)
            upload_stats = {}
            if not self.uploads:
                upload_stats = {
                    'total_uploads': 0,
                    'successful_uploads': 0,
                    'failed_uploads': 0,
                    'avg_duration_seconds': 0,
                    'avg_file_size_mb': 0,
                    'recent_uploads': []
                }
            else:
                uploads_list = list(self.uploads)
                successful = [u for u in uploads_list if u['success']]
                failed = [u for u in uploads_list if not u['success']]
                
                avg_duration = sum(u['duration_seconds'] for u in uploads_list) / len(uploads_list)
                avg_size = sum(u['file_size_bytes'] for u in uploads_list) / len(uploads_list) / (1024 * 1024)
                
                upload_stats = {
                    'total_uploads': len(uploads_list),
                    'successful_uploads': len(successful),
                    'failed_uploads': len(failed),
                    'avg_duration_seconds': round(avg_duration, 3),
                    'avg_file_size_mb': round(avg_size, 2),
                    'min_duration_seconds': round(min(u['duration_seconds'] for u in uploads_list), 3),
                    'max_duration_seconds': round(max(u['duration_seconds'] for u in uploads_list), 3),
                    'recent_uploads': uploads_list[-20:]  # Last 20 uploads
                }
            
            # Submission statistics (all form submissions)
            submission_stats = {}
            if not self.submissions:
                submission_stats = {
                    'total_submissions': 0,
                    'successful_submissions': 0,
                    'failed_submissions': 0,
                    'with_attachments': 0,
                    'without_attachments': 0,
                    'avg_duration_seconds': 0,
                    'recent_submissions': []
                }
            else:
                submissions_list = list(self.submissions)
                successful = [s for s in submissions_list if s['success']]
                failed = [s for s in submissions_list if not s['success']]
                with_att = [s for s in submissions_list if s['has_attachments']]
                without_att = [s for s in submissions_list if not s['has_attachments']]
                
                avg_duration = sum(s['duration_seconds'] for s in submissions_list) / len(submissions_list)
                
                submission_stats = {
                    'total_submissions': len(submissions_list),
                    'successful_submissions': len(successful),
                    'failed_submissions': len(failed),
                    'with_attachments': len(with_att),
                    'without_attachments': len(without_att),
                    'avg_duration_seconds': round(avg_duration, 3),
                    'min_duration_seconds': round(min(s['duration_seconds'] for s in submissions_list), 3),
                    'max_duration_seconds': round(max(s['duration_seconds'] for s in submissions_list), 3),
                    'recent_submissions': submissions_list[-20:]  # Last 20 submissions
                }
            
            return {
                'uploads': upload_stats,
                'submissions': submission_stats
            }
    
    def reset(self):
        """Clear all stored metrics"""
        with self.lock:
            self.uploads.clear()
            self.submissions.clear()

# Global metrics instance
performance_metrics = PerformanceMetrics(max_entries=100)

# Load configuration
def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

config = load_config()
transport_config = config.get('default', {}).get('transport', {})
sharepoint_config = transport_config.get('sharepoint', {})  # SharePoint settings

# Import TransportRequestHandler for OOP-style processing
from utils.transport_handler import TransportRequestHandler

# Initialize Token Manager (if enabled)
token_manager_config = config.get('default', {}).get('token_manager', {})
if token_manager_config.get('enabled', True):
    logger.info("\033[94mâ„¹ Token Manager enabled - tokens will be fetched from REST API\033[0m")
    token_manager = get_token_manager(config.get('default', {}))
else:
    logger.info("\033[93mâš  Token Manager disabled - using SHAREPOINT_ACCESS_TOKEN from env\033[0m")
    token_manager = None

def get_access_token() -> str:
    """
    Uniwersalna funkcja do pobierania Access Token
    
    Returns:
        str: Access Token (z REST API lub z env variable)
        
    Raises:
        Exception: JeÅ›li nie udaÅ‚o siÄ™ pobraÄ‡ tokena
    """
    # Opcja 1: Token Manager (dynamiczne pobieranie z REST API)
    if token_manager:
        try:
            return token_manager.get_token()
        except Exception as e:
            logger.warning(f"\033[93mâš  Token Manager failed: {e}, falling back to env variable\033[0m")
    
    # Opcja 2: Fallback - token z zmiennej Å›rodowiskowej
    env_token = os.getenv('SHAREPOINT_ACCESS_TOKEN')
    if env_token:
        logger.debug("Using SHAREPOINT_ACCESS_TOKEN from environment variable")
        return env_token
    
    raise Exception(
        "No access token available. Either:\n"
        "1. Enable Token Manager in config.yaml and set RPA_BOT_PASSWORD env variable\n"
        "2. Set SHAREPOINT_ACCESS_TOKEN env variable manually"
    )

# Initialize TransportRequestHandler (single instance for entire app)
# All helpers (Excel, Email, JSON, Attachments) initialized ONCE here
# No need to pass 10+ parameters to every function anymore!
transport_handler = TransportRequestHandler(
    config=config,
    logger_instance=logger,
    app_logger_instance=app_logger,
    performance_metrics_instance=performance_metrics,
    get_access_token_func=get_access_token
)
logger.info("\033[92m✓ TransportRequestHandler initialized with all helpers\033[0m")

# Initialize SchedulerManager for background tasks
from utils.scheduler_manager import SchedulerManager
scheduler_manager = SchedulerManager(
    config=config,
    transport_config=transport_config,
    get_access_token_func=get_access_token,
    app_logger_instance=app_logger
)
logger.info("\033[92m✓ SchedulerManager initialized\033[0m")

# Get server config
server_config = transport_config.get('server', {})

app = FastAPI(
    title=transport_config.get('app_name', 'Transport Request API'), 
    version=transport_config.get('app_version', '1.0.0'),
    description="API for managing transport requests with file uploads and data processing",
    docs_url="/docs",  # Explicitly enable docs
    redoc_url="/redoc",  # Explicitly enable redoc
    openapi_url="/openapi.json",  # Explicitly enable OpenAPI
    servers=[
        {"url": server_config.get('production_url', 'https://your-production-server.yourdomain.com:8000'), "description": "Production server"},
        {"url": server_config.get('local_url', 'http://localhost:8010'), "description": "Local development"}
    ]
)

# Global exception handler to catch all unhandled errors and return JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = f"{type(exc).__name__}: {str(exc)}"
    logger.error(f"\033[91mâœ— Unhandled exception in {request.url.path}: {error_detail}\033[0m")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": error_detail,
            "type": type(exc).__name__,
            "detail": str(exc),
            "path": request.url.path
        }
    )

# CORS for frontend access (both local and production)
cors_config = transport_config.get('cors', {})
allowed_origins = cors_config.get('allowed_origins', ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class TransportRequest(BaseModel):
    deliveryNoteNumber: str
    truckLicensePlates: str
    trailerLicensePlates: str
    carrierCountry: str
    carrierTaxCode: str
    carrierFullName: str
    borderCrossing: str
    borderCrossingDate: str  # ISO date string
    email: str
    phoneNumber: Optional[str] = ''

    @field_validator('deliveryNoteNumber', 'truckLicensePlates', 'carrierCountry', 'carrierTaxCode', 'carrierFullName', 'borderCrossing', 'email')
    @classmethod
    def validate_non_empty_string(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Email cannot be empty")
        v = v.strip()
        # Simple email validation
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError("Invalid email format")
        return v
    
    @field_validator('phoneNumber')
    @classmethod
    def validate_phone_number(cls, v):
        if v:
            return v.strip()
        return ''

@app.options("/api/submit")
async def submit_options():
    """
    Handle preflight CORS requests for file uploads (multipart/form-data)
    """
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600"
        }
    )

@app.options("/api/debug/verify")
async def debug_verify_options():
    """
    Handle preflight CORS requests for debug verification
    """
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600"
        }
    )

@app.options("/api/debug/{path:path}")
async def debug_options(path: str):
    """
    Handle preflight CORS requests for all debug endpoints
    """
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Debug-Token",
            "Access-Control-Max-Age": "3600"
        }
    )

@app.post("/api/submit")
async def submit_transport_request(
    request: Request,
    background_tasks: BackgroundTasks,
    data: str = Form(...),  # JSON as form field (not file!)
    attachments: Optional[List[UploadFile]] = File(None)
):
    """
    Accepts JSON data (as form field) and optional files. Returns unique request ID immediately.
    Processing (attachments, Excel, email) happens in background.
    """
    start_time = time.time()
    user_ip = request.client.host if request.client else "unknown"
    
    # Ensure attachments is always a list (even if None was passed)
    if attachments is None:
        attachments = []
    
    logger.info("=== NEW SUBMIT REQUEST ===")
    logger.info(f"User IP: {user_ip}")
    logger.info(f"Received data: {data}")
    logger.info(f"Attachments: {[f.filename for f in attachments] if attachments else 'None'}")
    
    # Log WAF bypass headers for debugging
    waf_headers = {
        'X-Content-Type': request.headers.get('X-Content-Type'),
        'X-Request-Source': request.headers.get('X-Request-Source'),
        'X-Bypass-SQLI': request.headers.get('X-Bypass-SQLI'),
        'X-Data-Encoding': request.headers.get('X-Data-Encoding')
    }
    logger.info(f"WAF Bypass Headers: {waf_headers}")
    
    # Generate unique request ID first for logging
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    rand = random.randint(100, 999)
    request_id = f"REQ-{now}-{rand}"
    
    try:
        # Check if data is Base64 encoded
        is_base64_encoded = request.headers.get('X-Data-Encoding') == 'base64'
        
        if is_base64_encoded:
            logger.info("Detected Base64 encoded data, decoding...")
            try:
                # Decode Base64 to bytes, then decode as UTF-8 string, then unquote URI encoding
                decoded_base64_bytes = base64.b64decode(data)
                decoded_base64_string = decoded_base64_bytes.decode('utf-8')
                decoded_data = decodeURIComponent(decoded_base64_string)
                logger.info(f"Base64 decoded successfully: {decoded_data}")
                data_to_parse = decoded_data
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {decode_error}")
                raise HTTPException(status_code=400, detail=f"Base64 decode error: {decode_error}")
        else:
            logger.info("Using data as-is (not Base64 encoded)")
            data_to_parse = data
        
        # Parse JSON data
        data_dict = json.loads(data_to_parse)
        logger.info(f"Parsed JSON: {data_dict}")
        req = TransportRequest(**data_dict)
        logger.info("Data validation successful")
        logger.info(f"Generated request ID: {request_id}")
        
        # Log form submission attempt
        app_logger.log_form_submit(
            form_data=data_dict,
            attachment_name=", ".join([f.filename for f in attachments]) if attachments else None,
            status="PROCESSING",
            request_id=request_id,
            user_ip=user_ip
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        
        # Record failed submission metrics
        performance_metrics.record_submission(
            request_id=request_id,
            has_attachments=False,
            attachments_count=0,
            duration=time.time() - start_time,
            success=False,
            error=f"JSON decode error: {e}",
            user_ip=user_ip
        )
        
        # Log failed submission
        app_logger.log_form_submit(
            form_data={"raw_data": data, "processed_data": locals().get('data_to_parse', data)},
            status="ERROR",
            error_message=f"JSON decode error: {e}",
            request_id=request_id,
            user_ip=user_ip
        )
        
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        
    except Exception as e:
        logger.error(f"Data validation error: {e}")
        
        # Record failed submission metrics
        performance_metrics.record_submission(
            request_id=request_id,
            has_attachments=len(attachments) > 0 if attachments else False,
            attachments_count=len(attachments) if attachments else 0,
            duration=time.time() - start_time,
            success=False,
            error=f"Data validation error: {e}",
            user_ip=user_ip
        )
        
        # Log validation error
        try:
            parsed_data = json.loads(locals().get('data_to_parse', data))
        except:
            parsed_data = {"raw_data": data, "processed_data": locals().get('data_to_parse', data)}
            
        app_logger.log_form_submit(
            form_data=parsed_data,
            attachment_name=", ".join([f.filename for f in attachments]) if attachments else None,
            status="ERROR",
            error_message=f"Data validation error: {e}",
            request_id=request_id,
            user_ip=user_ip
        )
        
        raise HTTPException(status_code=400, detail=f"Invalid data: {e}")

    # Read attachment contents into memory for background processing
    attachments_data = []
    for idx, attachment in enumerate(attachments):
        if attachment and attachment.filename:
            content = await attachment.read()
            attachments_data.append({
                'filename': attachment.filename,
                'content': content,
                'index': idx
            })
    
    logger.info(f"Read {len(attachments_data)} attachments into memory for background processing")
    
    # Save to JSON backup immediately (via JSONHelper - clean & simple!)
    json_index = transport_handler.json_helper.save_initial_record(
        request_id=request_id,
        data_dict=data_dict,
        has_attachments=bool(len(attachments_data) > 0)
    )
    # All dependencies already encapsulated in handler - only 5 parameters!
    background_tasks.add_task(
        transport_handler.process_submission,
        request_id=request_id,
        data_dict=data_dict,
        attachments_data=attachments_data,
        user_ip=user_ip,
        json_index=json_index
    )
    
    # Calculate quick response time
    processing_time = int((time.time() - start_time) * 1000)  # milliseconds
    submission_duration = time.time() - start_time  # seconds for metrics
    
    # Record submission metrics
    performance_metrics.record_submission(
        request_id=request_id,
        has_attachments=len(attachments_data) > 0,
        attachments_count=len(attachments_data),
        duration=submission_duration,
        success=True,
        user_ip=user_ip
    )
    
    logger.info(f"=== REQUEST ACCEPTED (processing in background) === {request_id}")
    
    # Return immediate success response
    return JSONResponse({
        "success": True,
        "request_id": request_id,
        "message": "Request received and is being processed",
        "attachments_count": len(attachments_data),
        "processing_status": "background",
        "response_time_ms": processing_time
    })


@app.get("/")
def root():
    logger.info("Health check endpoint accessed")
    return {"message": "Transport backend running", "status": "healthy"}

@app.get("/api/health")
def health():
    logger.info("API health check accessed")
    return {"status": "healthy", "service": "transport-api", "version": "cors-fix-v2"}

@app.get("/api/version")
def version_info():
    """Return version and feature flags"""
    return {
        "version": "2.1.0-utf8-fix",
        "features": {
            "json_backup": True,
            "debug_mode": bool(os.getenv('DEBUG_SECRET_KEY')),
            "sharepoint_enabled": transport_config.get('sharepoint', {}).get('enabled', False),
            "base64_encoding": True,
            "utf8_support": True,
            "uri_decode": True
        },
        "paths": {
            "backend_dir": str(Path(__file__).parent),
            "cwd": str(Path.cwd()),
            "excel_file": transport_config.get('local_excel_file', './data/transport_requests.xlsx')
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/debug/docs")
def debug_docs(token: str = None):
    """Debug endpoint to check docs configuration (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    return {
        "docs_url": app.docs_url,
        "redoc_url": app.redoc_url, 
        "openapi_url": app.openapi_url,
        "title": app.title,
        "version": app.version,
        "routes": [{"path": route.path, "methods": list(route.methods) if hasattr(route, 'methods') else []} for route in app.routes]
    }

@app.get("/api/sharepoint/status")
def sharepoint_status():
    """
    Check SharePoint integration status - available from frontend
    Returns: token status, config status, connection test result
    """
    try:
        # Check configuration
        sharepoint_config = transport_config.get('sharepoint', {})
        enabled = sharepoint_config.get('enabled', False)
        
        # Check token
        try:
            access_token = get_access_token()
            has_token = True
            token_length = len(access_token)
            token_preview = access_token[:50] + "..."
            token_valid_format = access_token.startswith('eyJ')
        except Exception as token_error:
            access_token = None
            has_token = False
            token_length = 0
            token_preview = None
            token_valid_format = False
        
        # Try to test connection (if enabled)
        connection_test = None
        if enabled and has_token:
            try:
                sp = SharePointHelper(access_token)
                folder_url = sharepoint_config['folder_url']
                folder = sp.get_folder(folder_url)
                connection_test = {
                    "success": True,
                    "message": "Connection successful",
                    "folder_url": folder_url
                }
            except Exception as test_error:
                connection_test = {
                    "success": False,
                    "error": str(test_error),
                    "error_type": type(test_error).__name__
                }
        
        return {
            "sharepoint_integration": {
                "enabled": enabled,
                "configured": bool(sharepoint_config)
            },
            "token": {
                "present": has_token,
                "length": token_length,
                "preview": token_preview,
                "valid_format": token_valid_format
            },
            "config": {
                "folder_url": sharepoint_config.get('folder_url') if enabled else None,
                "excel_file_name": sharepoint_config.get('excel_file_name') if enabled else None,
                "worksheet_name": sharepoint_config.get('worksheet_name') if enabled else None
            },
            "connection_test": connection_test,
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"SharePoint status check failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "last_check": datetime.now().isoformat()
        }

@app.get("/api/token/info")
def token_info():
    """
    Get information about Token Manager status and current token
    Returns: token manager config, token status, expiry info
    """
    try:
        result = {
            "token_manager": {
                "enabled": bool(token_manager),
                "config": token_manager_config if token_manager else None
            },
            "token": {}
        }
        
        # If Token Manager is enabled, get detailed info
        if token_manager:
            result["token"] = token_manager.get_token_info()
        else:
            # Fallback: check env variable
            env_token = os.getenv('SHAREPOINT_ACCESS_TOKEN')
            result["token"] = {
                "source": "environment_variable",
                "has_token": bool(env_token),
                "token_preview": env_token[:50] + "..." if env_token else None,
                "length": len(env_token) if env_token else 0
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Token info failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.post("/api/token/refresh")
def token_refresh():
    """
    Force refresh token (fetch new from API)
    Returns: success status and new token info
    """
    try:
        if not token_manager:
            return {
                "success": False,
                "error": "Token Manager is disabled - cannot refresh token"
            }
        
        logger.info("\033[94mâ„¹ Manual token refresh requested\033[0m")
        new_token = token_manager.get_token(force_refresh=True)
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "token_preview": new_token[:50] + "...",
            "token_length": len(new_token),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.on_event("startup")
async def startup_event():
    """Initialize background scheduler on application startup"""
    # Get sync interval from config (default: 1 hour)
    sync_interval_hours = transport_config.get('sharepoint', {}).get('sync_interval_hours', 1)
    
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Add job to run sync periodically (with wrapper to pass parameters)
    def sync_wrapper():
        scheduler_manager.sync_json_to_sharepoint()
    
    scheduler.add_job(
        func=sync_wrapper,
        trigger=IntervalTrigger(hours=sync_interval_hours),
        id='sync_json_to_sharepoint',
        name='Sync JSON to SharePoint Excel',
        replace_existing=True
    )
    
    # Add job to cleanup old attachments (runs daily at 2 AM)
    cleanup_interval_hours = transport_config.get('sharepoint', {}).get('cleanup_interval_hours', 24)
    
    def cleanup_wrapper():
        scheduler_manager.cleanup_old_attachments()
    
    scheduler.add_job(
        func=cleanup_wrapper,
        trigger=IntervalTrigger(hours=cleanup_interval_hours),
        id='cleanup_old_attachments',
        name='Cleanup old SharePoint attachments',
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    logger.info(f"\033[94mâ„¹ Background scheduler started - sync interval: {sync_interval_hours} hour(s), cleanup interval: {cleanup_interval_hours} hour(s)\033[0m")
    app_logger.log_info("Background scheduler started", {
        'scheduler': 'background_tasks',
        'sync_interval_hours': sync_interval_hours,
        'cleanup_interval_hours': cleanup_interval_hours,
        'jobs': [
            {'id': 'sync_json_to_sharepoint', 'name': 'Sync JSON to SharePoint Excel'},
            {'id': 'cleanup_old_attachments', 'name': 'Cleanup old SharePoint attachments'}
        ]
    })
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    
    # Run initial sync on startup (after 30 seconds delay)
    scheduler.add_job(
        func=sync_wrapper,
        trigger='date',
        run_date=datetime.now() + timedelta(seconds=30),
        id='initial_sync',
        name='Initial sync on startup'
    )
    logger.info("\033[94mâ„¹ Initial sync scheduled for 30 seconds after startup\033[0m")


@app.get("/api/sync/trigger")
def trigger_manual_sync():
    """Manual endpoint to trigger JSON â†’ SharePoint sync"""
    try:
        scheduler_manager.sync_json_to_sharepoint()
        return {
            "success": True,
            "message": "Manual sync triggered successfully. Check logs for details."
        }
    except Exception as e:
        logger.error(f"Manual sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/cleanup/trigger")
def trigger_manual_cleanup():
    """Manual endpoint to trigger attachment cleanup"""
    try:
        scheduler_manager.cleanup_old_attachments()
        return {
            "success": True,
            "message": "Manual cleanup triggered successfully. Check logs for details."
        }
    except Exception as e:
        logger.error(f"Manual cleanup failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/debug/logger-status")
def debug_logger_status(token: str = None):
    """Check logger configuration and file status (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    try:
        # Get logger instance
        from logger_config import get_logger
        test_logger = get_logger()
        
        # Get log directory and file naming from config
        log_dir = test_logger.log_dir
        today = datetime.now().strftime("%Y%m%d")
        paths_config = transport_config.get('paths', {})
        log_prefix = paths_config.get('log_file_prefix', 'transport_app_')
        log_ext = paths_config.get('log_file_extension', '.jsonl')
        expected_file = log_dir / f"{log_prefix}{today}{log_ext}"
        
        # Check handlers
        handlers_info = []
        for handler in test_logger.logger.handlers:
            handler_info = {
                "type": type(handler).__name__,
                "level": handler.level
            }
            if hasattr(handler, 'baseFilename'):
                handler_info["file"] = handler.baseFilename
                handler_info["file_exists"] = Path(handler.baseFilename).exists()
            handlers_info.append(handler_info)
        
        # List files in log directory
        log_files = []
        if log_dir.exists():
            log_files = [str(f.name) for f in log_dir.iterdir() if f.is_file()]
        
        return {
            "log_dir": str(log_dir),
            "log_dir_exists": log_dir.exists(),
            "expected_file": str(expected_file),
            "expected_file_exists": expected_file.exists(),
            "handlers": handlers_info,
            "log_files": log_files,
            "backend_dir": str(Path(__file__).parent)
        }
    except Exception as e:
        logger.error(f"Logger status check failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/api/debug/enabled")
def debug_enabled(token: str = None):
    """Check if debug mode is enabled (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    # Check env variable first, then config
    env_debug = os.getenv('ENABLE_DEBUG_MODE', '').lower() in ['true', '1', 'yes']
    config_debug = transport_config.get('debug_mode', False)
    
    is_enabled = env_debug or config_debug
    
    return {
        "debug_enabled": is_enabled,
        "source": "env_variable" if env_debug else "config" if config_debug else "disabled"
    }

@app.get("/api/performance/metrics")
def get_performance_metrics(token: str = None):
    """
    Get upload performance metrics (requires valid debug token)
    
    Returns statistics about file uploads:
    - Total/successful/failed upload counts
    - Average upload duration and file size
    - Recent upload history (last 20)
    """
    # Require debug token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation - check format (token length from config)
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    try:
        stats = performance_metrics.get_stats()
        return {
            "success": True,
            "metrics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "metrics": None
        }

@app.post("/api/performance/reset")
def reset_performance_metrics(token: str = None):
    """
    Reset all performance metrics (requires valid debug token)
    Clears both upload and submission statistics
    """
    # Require debug token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    try:
        performance_metrics.reset()
        app_logger.log_info("Performance metrics reset via API")
        return {
            "success": True,
            "message": "Performance metrics have been reset",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to reset performance metrics: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/debug/verify")
def debug_verify(payload: dict):
    """Verify debug secret key and return session token"""
    secret_key = payload.get('secret_key', '')
    env_secret = os.getenv('DEBUG_SECRET_KEY', '')
    
    if not env_secret:
        raise HTTPException(status_code=500, detail="Debug secret key not configured")
    
    if secret_key == env_secret:
        # Generate simple session token (timestamp + hash)
        import hashlib
        timestamp = datetime.now().isoformat()
        debug_config = transport_config.get('debug', {})
        token_length = debug_config.get('token_length', 32)
        token = hashlib.sha256(f"{secret_key}{timestamp}".encode()).hexdigest()[:token_length]
        logger.info(f"\033[92mâœ“ Debug access granted (token: {token[:8]}...)\033[0m")
        return {
            "success": True,
            "token": token,
            "message": "Debug access granted"
        }
    else:
        logger.warning(f"\033[93mâš  Debug access denied (invalid key)\033[0m")
        raise HTTPException(status_code=403, detail="Invalid debug secret key")

@app.get("/api/data/json")
def get_json_data(token: str = None):
    """Get all records from transport_requests.json (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation - check format (token length from config)
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    try:
        # JSON backup path from config (managed by Jenkins docker cp)
        paths_config = transport_config.get('paths', {})
        json_path = Path(paths_config.get('json_backup_file', '/tmp/transport_requests.json'))
        
        logger.info(f"\033[94mℹ Looking for JSON backup at: {json_path}\033[0m")
        
        # Get debug info from JSONHelper (clean OOP approach)
        debug_info = transport_handler.json_helper.debug_info()
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "success": True,
                "total_records": len(data),
                "file_path": str(json_path),
                "records": data,
                "debug_info": debug_info
            }
        
        return {
            "success": False,
            "message": "JSON backup not found - will be created on first submit or restored from Jenkins backup",
            "debug_info": debug_info
        }
        
    except Exception as e:
        logger.error(f"Failed to read JSON backup: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

class DeleteRecordsRequest(BaseModel):
    request_ids: List[str]

@app.post("/api/data/json/delete")
def delete_json_records(request: DeleteRecordsRequest, token: str = None):
    """Delete selected records from transport_requests.json by Request_ID (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    try:
        paths_config = transport_config.get('paths', {})
        json_path = Path(paths_config.get('json_backup_file', '/tmp/transport_requests.json'))
        
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="JSON file not found")
        
        # Read current data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filter out selected records
        initial_count = len(data)
        request_ids_set = set(request.request_ids)
        filtered_data = [record for record in data if record.get('Request_ID') not in request_ids_set]
        deleted_count = initial_count - len(filtered_data)
        
        # Write back to file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\033[94mâ„¹ Deleted {deleted_count} records from JSON backup (requested: {len(request.request_ids)})\033[0m")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "remaining_records": len(filtered_data),
            "requested_ids": len(request.request_ids)
        }
        
    except Exception as e:
        logger.error(f"Failed to delete records: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/files")
def get_log_files(token: str = None):
    """Get list of available log files (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    try:
        backend_dir = Path(__file__).parent
        logs_dir = backend_dir / "logs"
        
        if not logs_dir.exists():
            return {
                "success": False,
                "message": "Logs directory not found",
                "files": []
            }
        
        # Get log file pattern from config
        paths_config = transport_config.get('paths', {})
        log_prefix = paths_config.get('log_file_prefix', 'transport_app_')
        log_ext = paths_config.get('log_file_extension', '.jsonl')
        log_pattern = f"{log_prefix}*{log_ext}"
        
        # Find all log files and get their info
        log_files = sorted(logs_dir.glob(log_pattern), reverse=True)
        
        files_info = []
        for log_file in log_files:
            stat = log_file.stat()
            files_info.append({
                "filename": log_file.name,
                "path": str(log_file),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "date": log_file.stem.replace(log_prefix, '')  # Extract date from filename
            })
        
        return {
            "success": True,
            "files": files_info,
            "total_files": len(files_info)
        }
    
    except Exception as e:
        logger.error(f"Failed to list log files: {e}")
        return {
            "success": False,
            "error": str(e),
            "files": []
        }

@app.get("/api/logs")
def get_logs(lines: int = 100, token: str = None, filename: str = None):
    """Get last N lines from application logs (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation - check format (token length from config)
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    try:
        # Get logs directory from config
        backend_dir = Path(__file__).parent
        logs_dir = backend_dir / "logs"
        
        # If specific filename provided, use it
        if filename:
            log_file = logs_dir / filename
            if not log_file.exists() or not log_file.is_file():
                raise HTTPException(status_code=404, detail=f"Log file not found: {filename}")
        else:
            # Find today's log file (format from config)
            today = datetime.now().strftime("%Y%m%d")
            paths_config = transport_config.get('paths', {})
            log_prefix = paths_config.get('log_file_prefix', 'transport_app_')
            log_ext = paths_config.get('log_file_extension', '.jsonl')
            log_file = logs_dir / f"{log_prefix}{today}{log_ext}"
        
        if not log_file.exists():
            # Try to find the most recent log file (using config pattern)
            paths_config = transport_config.get('paths', {})
            log_prefix = paths_config.get('log_file_prefix', 'transport_app_')
            log_ext = paths_config.get('log_file_extension', '.jsonl')
            log_pattern = f"{log_prefix}*{log_ext}"
            log_files = sorted(logs_dir.glob(log_pattern), reverse=True)
            if log_files:
                log_file = log_files[0]
            else:
                return {
                    "success": False,
                    "message": "No log files found",
                    "expected_file": f"{log_prefix}{today}{log_ext}",
                    "logs_dir_exists": logs_dir.exists(),
                    "files_in_logs_dir": [f.name for f in logs_dir.iterdir()] if logs_dir.exists() else []
                }
        
        # Read last N lines
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "success": True,
            "lines_requested": lines,
            "lines_returned": len(last_lines),
            "total_lines": len(all_lines),
            "log_file": str(log_file),
            "logs": "".join(last_lines)
        }
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {
            "success": False,
            "error": str(e),
            "log_file": str(log_file) if 'log_file' in locals() else "unknown"
        }

@app.delete("/api/logs/clear")
async def clear_logs(token: str = None):
    """Clear application logs (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation - check format (token length from config)
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    try:
        backend_dir = Path(__file__).parent
        logs_dir = backend_dir / "logs"
        
        if not logs_dir.exists():
            return {
                "success": False,
                "message": "Logs directory does not exist"
            }
        
        # Get log file pattern from config
        paths_config = transport_config.get('paths', {})
        log_prefix = paths_config.get('log_file_prefix', 'transport_app_')
        log_ext = paths_config.get('log_file_extension', '.jsonl')
        log_pattern = f"{log_prefix}*{log_ext}"
        
        # Find all log files matching pattern
        log_files = list(logs_dir.glob(log_pattern))
        
        if not log_files:
            return {
                "success": True,
                "message": "No log files to clear",
                "cleared_files": []
            }
        
        # Delete all log files
        cleared_files = []
        for log_file in log_files:
            try:
                log_file.unlink()
                cleared_files.append(log_file.name)
                logger.info(f"\033[94mâ„¹ Cleared log file: {log_file.name}\033[0m")
            except Exception as e:
                logger.error(f"Failed to delete {log_file.name}: {e}")
        
        # Reinitialize logger to create new file
        # Access the global app_logger (StructuredLogger instance)
        if hasattr(app_logger, 'logger') and hasattr(app_logger.logger, 'handlers'):
            app_logger.logger.handlers.clear()
            app_logger._setup_file_handlers()
            logger.info("\033[94mâ„¹ Logger reinitialized after clearing logs\033[0m")
        
        return {
            "success": True,
            "message": f"Cleared {len(cleared_files)} log file(s)",
            "cleared_files": cleared_files
        }
    except Exception as e:
        logger.error(f"Failed to clear logs: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/form-labels")
async def get_form_labels():
    """Get form labels configuration"""
    try:
        # Path to frontend public folder (where form-labels.json is stored)
        frontend_public = Path(__file__).parent.parent / "frontend" / "public" / "form-labels.json"
        
        if not frontend_public.exists():
            raise HTTPException(status_code=404, detail="Form labels file not found")
        
        with open(frontend_public, 'r', encoding='utf-8') as f:
            labels_data = json.load(f)
        
        return {
            "success": True,
            "labels": labels_data
        }
    except Exception as e:
        logger.error(f"\033[91mâœ— Failed to load form labels: {e}\033[0m")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/form-labels")
async def update_form_labels(labels_data: dict, token: str = None):
    """Update form labels configuration (requires valid debug token)"""
    # Require token authentication
    if not token:
        raise HTTPException(status_code=403, detail="Debug token required")
    
    # Simple token validation
    debug_config = transport_config.get('debug', {})
    expected_token_length = debug_config.get('token_length', 32)
    if len(token) != expected_token_length:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    try:
        # Path to frontend public folder
        frontend_public = Path(__file__).parent.parent / "frontend" / "public" / "form-labels.json"
        
        # Backup current labels
        if frontend_public.exists():
            backup_path = frontend_public.parent / f"form-labels.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import shutil
            shutil.copy2(frontend_public, backup_path)
            logger.info(f"\033[94mâ„¹ Created backup: {backup_path.name}\033[0m")
        
        # Write new labels
        with open(frontend_public, 'w', encoding='utf-8') as f:
            json.dump(labels_data, f, indent=2, ensure_ascii=False)
        
        logger.info("\033[92mâœ“ Form labels updated successfully\033[0m")
        
        return {
            "success": True,
            "message": "Form labels updated successfully",
            "backup_created": frontend_public.exists()
        }
    except Exception as e:
        logger.error(f"\033[91mâœ— Failed to update form labels: {e}\033[0m")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    server_config = transport_config.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 8000)
    uvicorn.run(app, host=host, port=port, reload=False)
