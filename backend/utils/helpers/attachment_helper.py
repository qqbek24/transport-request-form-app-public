"""
AttachmentHelper - Encapsulates attachment upload operations
No need to pass config/logger to every method - stored in instance
"""
import logging
from typing import List, Dict, Tuple
import os
import tempfile
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class AttachmentHelper:
    """Handles attachment uploads to SharePoint"""
    
    def __init__(self, sharepoint_config: dict, get_access_token_func,
                 logger_instance=None, performance_metrics_instance=None):
        """
        Initialize Attachment helper
        
        Args:
            sharepoint_config: SharePoint configuration
            get_access_token_func: Function to get access token
            logger_instance: Standard logger
            performance_metrics_instance: Performance metrics tracker
        """
        self.sharepoint_config = sharepoint_config
        self.get_access_token = get_access_token_func
        self.logger = logger_instance or logger
        self.metrics = performance_metrics_instance
        
    def upload_single_attachment(self, att_data: dict, request_id: str) -> Tuple[bool, str, str]:
        """
        Upload single attachment to SharePoint
        
        Args:
            att_data: Dict with 'filename', 'content', 'index'
            request_id: Request identifier
            
        Returns:
            tuple: (success: bool, filename: str, error: str or None)
        """
        from sharepoint_helper import SharePointHelper
        
        idx = att_data['index']
        filename = att_data['filename']
        content = att_data['content']
        file_size = len(content)
        
        upload_start = time.time()
        
        try:
            ext = os.path.splitext(filename)[1]
            new_filename = f"attachment_{request_id}_{idx+1}{ext}"
            
            # Get access token
            access_token = self.get_access_token()
            sp_helper = SharePointHelper(access_token)
            
            # Get folder URL
            sp_folder_url = self.sharepoint_config.get('folder_url')
            if not sp_folder_url:
                raise ValueError("SharePoint folder_url not configured")
            
            # Construct attachments subfolder URL
            sp_attachments_url = f"{sp_folder_url}/attachments"
            
            # Get or create attachments folder
            try:
                attachments_folder = sp_helper.get_folder(sp_attachments_url)
            except Exception:
                parent_folder = sp_helper.get_folder(sp_folder_url)
                attachments_folder = sp_helper.create_folder(parent_folder, "attachments", conflict_behavior="fail")
            
            # Upload using temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(content)
                temp_path = Path(temp_file.name)
            
            try:
                sp_file = sp_helper.upload_file(temp_path, attachments_folder, custom_filename=new_filename)
                upload_duration = time.time() - upload_start
                self.logger.info(f"\033[92m✓ Background: Attachment {idx+1} uploaded: {new_filename} ({upload_duration:.2f}s)\033[0m")
                
                # Record success metrics
                if self.metrics:
                    self.metrics.record_upload(
                        request_id=request_id,
                        filename=new_filename,
                        file_size=file_size,
                        duration=upload_duration,
                        success=True
                    )
                
                return (True, new_filename, None)
            finally:
                if temp_path.exists():
                    temp_path.unlink()
                    
        except Exception as att_error:
            upload_duration = time.time() - upload_start
            error_msg = f"Attachment upload failed for {filename}: {att_error}"
            self.logger.error(f"\033[91m✗ Background: {error_msg} ({upload_duration:.2f}s)\033[0m")
            
            # Record failure metrics
            if self.metrics:
                self.metrics.record_upload(
                    request_id=request_id,
                    filename=filename,
                    file_size=file_size,
                    duration=upload_duration,
                    success=False,
                    error=str(att_error)
                )
            
            return (False, filename, error_msg)
