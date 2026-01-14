"""
TransportRequestHandler - Main handler for transport request processing
Orchestrates all helpers (Excel, Email, JSON, Attachments)
Single point of initialization - no more passing 10+ parameters everywhere!
"""
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from .helpers import ExcelHelper, EmailHelper, JSONHelper, AttachmentHelper

logger = logging.getLogger(__name__)


class TransportRequestHandler:
    """
    Main handler for transport request processing
    Encapsulates all dependencies and orchestrates the workflow
    """
    
    def __init__(self, config: dict, logger_instance, app_logger_instance,
                 performance_metrics_instance, get_access_token_func):
        """
        Initialize handler with all dependencies (ONCE at startup!)
        
        Args:
            config: Full configuration dict
            logger_instance: Standard logger
            app_logger_instance: Structured app logger
            performance_metrics_instance: Performance metrics tracker
            get_access_token_func: Function to get access token
        """
        self.config = config
        self.transport_config = config.get('default', {}).get('transport', {})
        self.sharepoint_config = self.transport_config.get('sharepoint', {})
        
        self.logger = logger_instance
        self.app_logger = app_logger_instance
        self.metrics = performance_metrics_instance
        self.get_access_token = get_access_token_func
        
        # Initialize helpers (ONCE!)
        self.excel = ExcelHelper(
            config=config,
            transport_config=self.transport_config,
            get_access_token_func=get_access_token_func,
            logger_instance=logger_instance,
            app_logger_instance=app_logger_instance
        )
        
        self.email = EmailHelper(
            config=config,
            transport_config=self.transport_config,
            get_access_token_func=get_access_token_func,
            logger_instance=logger_instance,
            app_logger_instance=app_logger_instance
        )
        
        self.json_helper = JSONHelper(
            transport_config=self.transport_config,
            logger_instance=logger_instance
        )
        
        self.attachments = AttachmentHelper(
            sharepoint_config=self.sharepoint_config,
            get_access_token_func=get_access_token_func,
            logger_instance=logger_instance,
            performance_metrics_instance=performance_metrics_instance
        )
    
    async def process_submission(self, request_id: str, data_dict: dict,
                                attachments_data: List[dict], user_ip: str,
                                json_index: int = None):
        """
        Background task to process submission: Excel → Attachments → Email
        
        Args:
            request_id: Request identifier
            data_dict: Form data
            attachments_data: List of attachment dicts with 'filename', 'content', 'index'
            user_ip: User IP address
            json_index: Index in JSON backup file
        """
        try:
            self.logger.info(f"\033[94mℹ Background processing started for {request_id}\033[0m")
            
            # STEP 1: Save to Excel FIRST
            has_attachment_pending = len(attachments_data) > 0
            self.logger.info(f"\033[94mℹ Saving to Excel (attachments: {'pending' if has_attachment_pending else 'none'})...\033[0m")
            
            excel_result = self.excel.save_to_excel(
                request_id=request_id,
                data=data_dict,
                has_attachment=has_attachment_pending,
                attachment_error="Processing..." if has_attachment_pending else None,
                json_index=json_index,
                update_json_sync_status_func=self.json_helper.update_sync_status,
                attachment_status='Processing' if has_attachment_pending else None
            )
            self.logger.info(f"\033[92m✓ Background: Excel saved\033[0m")
            
            # STEP 2: Process attachments in parallel
            attachments_saved = []
            attachments_errors = []
            
            if self.sharepoint_config.get('enabled', True) and attachments_data:
                self.logger.info(f"Processing {len(attachments_data)} attachments (PARALLEL)")
                
                # Upload in parallel using ThreadPoolExecutor
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=3) as executor:
                    upload_tasks = [
                        loop.run_in_executor(
                            executor,
                            self.attachments.upload_single_attachment,
                            att_data,
                            request_id
                        )
                        for att_data in attachments_data
                    ]
                    
                    # Wait for all uploads
                    results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                    
                    # Process results
                    for result in results:
                        if isinstance(result, Exception):
                            attachments_errors.append(str(result))
                        else:
                            success, filename, error = result
                            if success:
                                attachments_saved.append(filename)
                            else:
                                attachments_errors.append(error)
                
                self.logger.info(f"\033[92m✓ Background: Attachments processed ({len(attachments_saved)} saved, {len(attachments_errors)} failed)\033[0m")
            
            # STEP 3: Update Excel with final attachment status
            has_attachment = len(attachments_saved) > 0
            attachment_error = "; ".join(attachments_errors) if attachments_errors else None
            
            if has_attachment_pending:
                self.logger.info(f"\033[94mℹ Updating Excel with final attachment status...\033[0m")
                self.excel.update_attachment_status(
                    request_id=request_id,
                    has_attachment=has_attachment,
                    attachment_error=attachment_error
                )
                self.logger.info(f"\033[92m✓ Background: Excel updated with attachment status\033[0m")
            
            # Update JSON with attachment status
            if json_index is not None:
                try:
                    self.json_helper.update_attachment_status(
                        request_id=request_id,
                        record_index=json_index,
                        attachments_saved=attachments_saved,
                        attachments_errors=attachments_errors
                    )
                except Exception as update_error:
                    self.logger.warning(f"Failed to update JSON: {update_error}")
            
            # STEP 4: Log completion
            if self.app_logger:
                self.app_logger.log_form_submit(
                    form_data=data_dict,
                    attachment_name=", ".join(attachments_saved) if attachments_saved else None,
                    status="SUCCESS",
                    request_id=request_id,
                    user_ip=user_ip,
                    sharepoint_saved=excel_result.get('sharepoint_saved', False),
                    sharepoint_error=excel_result.get('sharepoint_error')
                )
            
            # STEP 5: Send confirmation email
            user_email = data_dict.get('email')
            if user_email:
                try:
                    self.email.send_confirmation(
                        request_id=request_id,
                        data=data_dict,
                        user_email=user_email,
                        has_attachment=has_attachment,
                        attachment_error=attachment_error,
                        attachments_saved=attachments_saved
                    )
                except Exception as email_error:
                    self.logger.error(f"\033[91m✗ Email send failed: {email_error}\033[0m")
            
            self.logger.info(f"\033[92m✓ Background processing completed for {request_id}\033[0m")
            
        except Exception as bg_error:
            self.logger.error(f"\033[91m✗ Background processing failed for {request_id}: {bg_error}\033[0m", exc_info=True)
            if self.app_logger:
                self.app_logger.log_error(f"Background processing failed: {bg_error}", {
                    'request_id': request_id,
                    'error': str(bg_error)
                })
