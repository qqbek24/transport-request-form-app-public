"""
JSONHelper - Encapsulates JSON backup operations
No need to pass config/logger to every method - stored in instance
"""
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class JSONHelper:
    """Handles JSON backup file operations"""
    
    def __init__(self, transport_config: dict, logger_instance=None):
        """
        Initialize JSON helper with configuration
        
        Args:
            transport_config: Transport section of config
            logger_instance: Standard logger
        """
        self.transport_config = transport_config
        self.logger = logger_instance or logger
        
        # Get JSON path from config
        paths_config = transport_config.get('paths', {})
        self.json_path = Path(paths_config.get('json_backup_file', '/tmp/transport_requests.json'))
    
    def save_initial_record(self, request_id: str, data_dict: dict, 
                           has_attachments: bool = False) -> Optional[int]:
        """
        Save initial transport request to JSON backup file
        
        Args:
            request_id: Request identifier
            data_dict: Form data dictionary
            has_attachments: Whether request has attachments (will show 'Processing' if True)
            
        Returns:
            int: Index of saved record in JSON array, or None if save failed
        """
        try:
            # Load existing data
            existing_data = []
            if self.json_path.exists():
                try:
                    with open(self.json_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception as load_error:
                    self.logger.warning(f"Could not load existing JSON, starting fresh: {load_error}")
            
            # Create new record
            row_data = {
                'Request_ID': request_id,
                'Timestamp': datetime.now().isoformat(),
                'Delivery_Note_Number': data_dict.get('deliveryNoteNumber', ''),
                'Truck_License_Plates': data_dict.get('truckLicensePlates', ''),
                'Trailer_License_Plates': data_dict.get('trailerLicensePlates', ''),
                'Carrier_Country': data_dict.get('carrierCountry', ''),
                'Carrier_Tax_Code': data_dict.get('carrierTaxCode', ''),
                'Carrier_Full_Name': data_dict.get('carrierFullName', ''),
                'Border_Crossing': data_dict.get('borderCrossing', ''),
                'Border_Crossing_Date': data_dict.get('borderCrossingDate', ''),
                'Email': data_dict.get('email', ''),
                'Phone_Number': data_dict.get('phoneNumber', ''),
                'Has_Attachment': 'Processing' if has_attachments else 'No',
                'Attachment_Status': 'Processing' if has_attachments else 'None',
                'Attachment_Error': '',
                'SharePoint_Synced': False
            }
            
            existing_data.append(row_data)
            json_index = len(existing_data) - 1
            
            # Save to file with fsync for immediate persistence
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            os.chmod(self.json_path, 0o644)
            self.logger.info(f"\033[92m✓ JSON backup saved for {request_id} (index: {json_index})\033[0m")
            
            return json_index
            
        except Exception as json_error:
            self.logger.error(f"\033[91m✗ Failed to save JSON backup: {json_error}\033[0m")
            return None
        
    def update_sync_status(self, request_id: str, record_index: int, synced: bool):
        """
        Update SharePoint sync status in JSON backup
        
        Args:
            request_id: Request identifier
            record_index: Index of record in JSON array
            synced: True if synced to SharePoint
        """
        try:
            if not self.json_path.exists():
                self.logger.warning(f"JSON backup file not found: {self.json_path}")
                return
            
            # Load JSON
            with open(self.json_path, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            # Update specific record
            if 0 <= record_index < len(records):
                records[record_index]['SharePoint_Synced'] = synced
                
                # Save updated JSON
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
                
                os.chmod(self.json_path, 0o644)
                self.logger.info(f"\033[92m✓ Updated sync status in JSON for {request_id}: synced={synced}\033[0m")
            else:
                self.logger.warning(f"Invalid record index {record_index} for {request_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to update JSON sync status: {e}")
    
    def update_attachment_status(self, request_id: str, record_index: int,
                                 attachments_saved: List[str], attachments_errors: List[str]):
        """
        Update attachment status in JSON backup
        
        Args:
            request_id: Request identifier
            record_index: Index of record in JSON array
            attachments_saved: List of successfully saved attachments
            attachments_errors: List of attachment errors
        """
        try:
            if not self.json_path.exists():
                return
            
            with open(self.json_path, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            if 0 <= record_index < len(records):
                has_attachment = len(attachments_saved) > 0
                records[record_index]['Has_Attachment'] = 'Yes' if has_attachment else 'No'
                records[record_index]['Attachment_Status'] = 'Saved' if has_attachment else ('Failed' if attachments_errors else 'None')
                records[record_index]['Attachment_Error'] = "; ".join(attachments_errors) if attachments_errors else ''
                
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
                
                os.chmod(self.json_path, 0o644)
                self.logger.info(f"\033[92m✓ Updated attachment status in JSON for {request_id}\033[0m")
        except Exception as e:
            self.logger.error(f"Failed to update JSON attachment status: {e}")
                
    def debug_info(self) -> dict:
        """
        Get debug information about JSON backup file
        Used by debug endpoints to check file status
        
        Returns:
            dict: Debug information including path, existence, size, modified time
        """
        debug_info = {
            "path": str(self.json_path),
            "exists": self.json_path.exists(),
            "note": "JSON backup stored in /tmp/ (managed by Jenkins docker cp)",
            "cwd": str(Path.cwd())
        }
        
        if self.json_path.exists():
            try:
                stats = self.json_path.stat()
                debug_info["status"] = "found"
                debug_info["file_size"] = stats.st_size
                debug_info["modified"] = stats.st_mtime
                self.logger.info(f"\033[92m✓ JSON backup found at: {self.json_path}\033[0m")
            except Exception as e:
                debug_info["status"] = "error"
                debug_info["error"] = str(e)
        else:
            debug_info["status"] = "not_found"
            debug_info["note"] = "JSON backup will be created on first submit or restored from Jenkins backup"
            self.logger.warning(f"\033[93m⚠ JSON backup NOT found at: {self.json_path}\033[0m")
        
        return debug_info