"""
Advanced logging system for Transport Request Management System
Provides structured logging with JSON format and CSV export capabilities
"""

import logging
import json
import csv
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Register custom SUCCESS log level (25 = between INFO and WARNING)
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, 'SUCCESS')
import traceback


class StructuredLogger:
    """Advanced logger with JSON and CSV output capabilities"""
    
    def __init__(self, log_dir: str = "logs", app_name: str = "transport_app", log_retention_days: int = 60):
        # Ensure logs are always relative to backend directory
        backend_dir = Path(__file__).parent
        self.log_dir = backend_dir / log_dir
        self.app_name = app_name
        self.log_dir.mkdir(exist_ok=True)

        # Usuwanie starych plików logów (starszych niż log_retention_days)
        self._cleanup_old_logs(log_retention_days)

        # Setup structured logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Setup file handlers
        self._setup_file_handlers()

    def _cleanup_old_logs(self, retention_days: int):
        """Delete log files older than retention_days from log_dir"""
        now = datetime.now()
        for file in self.log_dir.glob(f"{self.app_name}_*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if (now - mtime).days > retention_days:
                    file.unlink()
            except Exception:
                pass
        
    def _setup_file_handlers(self):
        """Setup file handlers for different log formats"""
        today = datetime.now().strftime("%Y%m%d")
        
        # Console handler FIRST - so we can see what's happening
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(console_handler)
        
        # Ensure log directory exists with proper permissions
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Create a test file to ensure we have write permissions
            test_file = self.log_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            self.logger.info(f"\033[92m✓ Log directory verified: {self.log_dir}\033[0m")
        except Exception as e:
            self.logger.warning(f"\033[93m⚠ Cannot write to logs directory {self.log_dir}: {e}\033[0m")
            # Fallback to /tmp for container environments
            self.log_dir = Path("/tmp/logs")
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.logger.warning(f"Using fallback log directory: {self.log_dir}")
        
        # JSON log handler
        json_log_path = self.log_dir / f"{self.app_name}_{today}.jsonl"
        try:
            json_handler = logging.FileHandler(json_log_path, encoding='utf-8')
            json_handler.setFormatter(self._get_json_formatter())
            self.logger.addHandler(json_handler)
            self.logger.info(f"\033[92m✓ JSON log handler initialized: {json_log_path}\033[0m")
            
            # Write a test log entry to ensure file is created immediately
            self.logger.info("\033[94mℹ Logger initialized - test entry\033[0m")
            # Force flush to disk
            for handler in self.logger.handlers:
                handler.flush()
        except Exception as e:
            self.logger.error(f"\033[91m✗ Failed to create JSON log handler: {e}\033[0m")
            # Continue without file logging - at least console will work
        
    def _get_json_formatter(self):
        """Custom JSON formatter"""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                
                # Add extra fields if present
                if hasattr(record, 'extra_data'):
                    log_entry.update(record.extra_data)
                    
                return json.dumps(log_entry, ensure_ascii=False)
                
        return JSONFormatter()
    
    def log_form_submit(
        self, 
        form_data: Dict[str, Any], 
        attachment_name: Optional[str] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        sharepoint_saved: bool = False,
        sharepoint_error: Optional[str] = None
    ):
        """Log form submission with structured data"""
        
        log_data = {
            'event_type': 'FORM_SUBMIT',
            'request_id': request_id,
            'user_ip': user_ip,
            'form_data': {
                'delivery_note': form_data.get('deliveryNoteNumber', ''),
                'truck_plates': form_data.get('truckLicensePlates', ''),
                'trailer_plates': form_data.get('trailerLicensePlates', ''),
                'carrier_country': form_data.get('carrierCountry', ''),
                'carrier_tax_code': form_data.get('carrierTaxCode', ''),
                'carrier_name': form_data.get('carrierFullName', ''),
                'border_crossing': form_data.get('borderCrossing', ''),
                'crossing_date': form_data.get('borderCrossingDate', ''),
                'email': form_data.get('email', ''),
                'phone_number': form_data.get('phoneNumber', '')
            },
            'attachment': {
                'has_attachment': attachment_name is not None,
                'filename': attachment_name,
                'size_bytes': getattr(form_data, 'attachment_size', None)
            },
            'sharepoint': {
                'saved': sharepoint_saved,
                'error': sharepoint_error
            },
            'status': status,
            'error_message': error_message,
            'processing_time_ms': getattr(form_data, 'processing_time', None)
        }
        
        # Create log record with extra data
        # Use custom SUCCESS level (25) for successful submissions, ERROR for failures, INFO for processing
        if status == "ERROR":
            log_level = logging.ERROR
        elif status == "SUCCESS":
            log_level = 25  # Custom SUCCESS level (between INFO=20 and WARNING=30)
        else:
            log_level = logging.INFO
            
        record = logging.LogRecord(
            name=self.logger.name,
            level=log_level,
            pathname="",
            lineno=0,
            msg=f"Form submission {status}: {request_id}",
            args=(),
            exc_info=None
        )
        record.extra_data = log_data
        
        self.logger.handle(record)
        
        # CSV logging disabled - all data is in JSONL format
        # self._write_csv_log(log_data)
    
    def _write_csv_log(self, log_data: Dict[str, Any]):
        """Write log entry to CSV file for easy analysis"""
        today = datetime.now().strftime("%Y%m%d")
        csv_file = self.log_dir / f"form_submissions_{today}.csv"
        
        # CSV headers
        headers = [
            'timestamp', 'event_type', 'request_id', 'user_ip', 'status',
            'delivery_note', 'truck_plates', 'trailer_plates', 
            'carrier_country', 'carrier_name', 'border_crossing', 'crossing_date',
            'has_attachment', 'attachment_filename', 'sharepoint_saved', 'sharepoint_error', 'error_message'
        ]
        
        # Check if file exists to determine if we need headers
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers if file is new
            if not file_exists:
                writer.writerow(headers)
            
            # Write data row
            writer.writerow([
                datetime.now().isoformat(),
                log_data['event_type'],
                log_data['request_id'],
                log_data['user_ip'],
                log_data['status'],
                log_data['form_data']['delivery_note'],
                log_data['form_data']['truck_plates'],
                log_data['form_data']['trailer_plates'],
                log_data['form_data']['carrier_country'],
                log_data['form_data']['carrier_name'],
                log_data['form_data']['border_crossing'],
                log_data['form_data']['crossing_date'],
                log_data['attachment']['has_attachment'],
                log_data['attachment']['filename'],
                log_data['sharepoint']['saved'],
                log_data['sharepoint']['error'],
                log_data['error_message']
            ])
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with full context"""
        error_data = {
            'event_type': 'ERROR',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg=f"Error occurred: {str(error)}",
            args=(),
            exc_info=None
        )
        record.extra_data = error_data
        
        self.logger.handle(record)
    
    def log_info(self, message: str, extra_data: Dict[str, Any] = None):
        """Log general information"""
        log_data = {
            'event_type': 'INFO',
            'extra_data': extra_data or {}
        }
        
        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = log_data
        
        self.logger.handle(record)


# Global logger instance
app_logger = None


def get_logger() -> StructuredLogger:
    """Get the application logger instance (reads config on first call)"""
    global app_logger
    if app_logger is None:
        # Load config to get retention_days
        config_path = Path(__file__).parent / "config.yaml"
        retention_days = 60  # Default fallback
        app_name = "transport_app"  # Default fallback
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logging_config = config.get('default', {}).get('transport', {}).get('logging', {})
                retention_days = logging_config.get('retention_days', 60)
                app_name = logging_config.get('app_name', 'transport_app')
        except Exception as e:
            print(f"Warning: Could not load logging config from config.yaml: {e}")
            print(f"Using default retention_days={retention_days}, app_name={app_name}")
        
        app_logger = StructuredLogger(
            log_dir="logs",
            app_name=app_name,
            log_retention_days=retention_days
        )
    
    return app_logger