"""
SharePoint Helper - simplified class for SharePoint integration via MS Graph API
Standalone implementation without external dependencies.
"""

import requests
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SharePointHelper:
    """Helper class for SharePoint/Teams integration via MS Graph API"""
    
    def __init__(self, access_token: str):
        """
        Initialize SharePoint Helper
        
        Args:
            access_token: Azure AD access token for MS Graph API
        """
        self.access_token = access_token
        self.access_token_expired_date = datetime.now() + timedelta(hours=2)
        self.base_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
    
    def get_access_token(self) -> str:
        """
        Get current access token
        
        Returns:
            str: Access token
        """
        return self.access_token
    
    def get_folder(self, url: str) -> Dict[str, Any]:
        """
        Get folder/file object from SharePoint by URL
        
        Args:
            url: SharePoint URL (can be sharing link or direct path)
            
        Returns:
            dict: Folder/file object with 'id', 'name', 'webUrl', etc.
            
        Example:
            folder = sp.get_folder("https://yourcompany.sharepoint.com/sites/...")
        """
        try:
            msgraph_url = self._sharepoint_to_msgraph(url)
            logger.info(f"Getting folder: {msgraph_url}")
            
            response = requests.get(msgraph_url, headers=self.base_headers)
            
            if response.status_code == 200:
                folder_data = response.json()
                logger.info(f"\033[92m✓ Folder retrieved: {folder_data.get('name', 'Unknown')}\033[0m")
                return folder_data
            else:
                error_msg = f"Error getting folder: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to get folder: {e}")
            raise
    
    def download_file(self, folder: Dict[str, Any], local_path: Path) -> Path:
        """
        Download file from SharePoint to local path
        
        Args:
            folder: Folder/file object from get_folder()
            local_path: Local path where to save the file
            
        Returns:
            Path: Path to downloaded file
        """
        try:
            # Get download URL
            download_url = folder.get('@microsoft.graph.downloadUrl')
            if not download_url:
                raise ValueError("No download URL in folder object")
            
            logger.info(f"Downloading file: {folder.get('name', 'Unknown')}")
            
            response = requests.get(download_url)
            
            if response.status_code == 200:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"\033[92m✓ File downloaded to: {local_path}\033[0m")
                return local_path
            else:
                error_msg = f"Download failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise
    
    def download_file_from_folder(self, download_path: str, folder: Dict[str, Any], file_name: str) -> Path:
        """
        Download specific file from a folder
        
        Args:
            download_path: Local directory path
            folder: Parent folder object
            file_name: Name of file to download
            
        Returns:
            Path: Path to downloaded file
        """
        try:
            # Build MS Graph URL for the file
            url = folder['webUrl']
            msgraph_command = self._sharepoint_to_msgraph(url)
            
            # Remove trailing colon if present
            if msgraph_command.endswith(':'):
                msgraph_command = msgraph_command[:-1]
            
            # Add file name
            file_url = f"{msgraph_command}/{file_name}:/content"
            
            logger.info(f"Downloading file: {file_name}")
            
            response = requests.get(file_url, headers=self.base_headers)
            
            if response.status_code == 200:
                download_dir = Path(download_path)
                download_dir.mkdir(parents=True, exist_ok=True)
                local_path = download_dir / file_name
                
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"\033[92m✓ File downloaded to: {local_path}\033[0m")
                return local_path
            else:
                error_msg = f"Download failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to download file from folder: {e}")
            raise
    
    def upload_file(self, file_path: Path, folder: Dict[str, Any], custom_filename: str = None) -> Dict[str, Any]:
        """
        Upload file to SharePoint folder
        
        Args:
            file_path: Path to local file to upload
            folder: Target folder object from get_folder()
            custom_filename: Optional custom filename (if None, uses file_path.name)
            
        Returns:
            dict: Uploaded file object
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Use custom filename or original filename
            upload_filename = custom_filename if custom_filename else file_path.name
            
            # Build upload URL
            url = folder['webUrl']
            msgraph_url = self._sharepoint_to_msgraph(url)
            
            # Remove trailing colon if present
            if msgraph_url.endswith(':'):
                msgraph_url = msgraph_url[:-1]
            
            upload_url = f"{msgraph_url}/{upload_filename}:/content"
            
            logger.info(f"Uploading file: {upload_filename}")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream"
            }
            
            with open(file_path, 'rb') as f:
                response = requests.put(upload_url, data=f, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.info(f"\033[92m✓ File uploaded: {upload_filename}\033[0m")
                return response.json()
            else:
                error_msg = f"Upload failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def add_excel_row(self, folder_url: str, excel_file_name: str, worksheet_name: str, row_values: list) -> Dict[str, Any]:
        """
        Add a row to Excel file using Microsoft Graph Excel API (works even if file is open)
        
        Args:
            folder_url: SharePoint folder URL
            excel_file_name: Name of Excel file
            worksheet_name: Name of worksheet
            row_values: List of cell values for the new row
            
        Returns:
            dict: Response from API with added row info
            
        Example:
            sp.add_excel_row(
                "https://yourcompany.sharepoint.com/.../folder",
                "data.xlsx",
                "Sheet1",
                ["REQ-123", "2025-11-14", "Value1", "Value2"]
            )
        """
        try:
            # Get file item ID
            msgraph_folder = self._sharepoint_to_msgraph(folder_url)
            if msgraph_folder.endswith(':'):
                msgraph_folder = msgraph_folder[:-1]
            
            file_url = f"{msgraph_folder}/{excel_file_name}"
            
            logger.info(f"Excel API: Getting file metadata for {excel_file_name}")
            file_response = requests.get(file_url, headers=self.base_headers)
            
            if file_response.status_code != 200:
                raise Exception(f"Failed to get file: {file_response.status_code} - {file_response.text}")
            
            file_data = file_response.json()
            drive_id = file_data['parentReference']['driveId']
            item_id = file_data['id']
            
            # Build Excel API URL for adding row
            # https://graph.microsoft.com/v1.0/drives/{drive-id}/items/{item-id}/workbook/worksheets/{worksheet}/tables/{table}/rows/add
            # OR for direct range: /workbook/worksheets/{worksheet}/range(address='A1:Z1')/insert
            
            # Use Table API if table exists, otherwise use Range API
            excel_api_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets/{worksheet_name}/range"
            
            # Find last row by checking Request ID column (column A) instead of usedRange
            # This prevents issues with formatted empty cells extending usedRange
            logger.info(f"Excel API: Finding last row with data in column A (Request ID)")
            
            # First get usedRange to know the dynamic range to check
            used_range_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets/{worksheet_name}/usedRange"
            range_response = requests.get(used_range_url, headers=self.base_headers)
            
            if range_response.status_code == 200:
                used_range = range_response.json()
                max_row = used_range['rowCount']  # Get total rows in usedRange
                logger.info(f"Excel API: UsedRange has {max_row} rows total")
                
                # Now get column A values up to usedRange limit
                col_a_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets/{worksheet_name}/range(address='A1:A{max_row}')"
                col_a_response = requests.get(col_a_url, headers=self.base_headers)
                
                if col_a_response.status_code == 200:
                    col_a_data = col_a_response.json()
                    values = col_a_data.get('values', [])
                    
                    # Find last non-empty row in column A (scan backwards for efficiency)
                    last_row = 1  # Default to header row
                    for idx in range(len(values) - 1, -1, -1):  # Scan backwards
                        row = values[idx]
                        if row and row[0] and str(row[0]).strip():  # Check if cell has value
                            last_row = idx + 1  # +1 because Excel rows are 1-indexed
                            break
                    
                    logger.info(f"Excel API: Last row with data in column A: {last_row} (out of {max_row} total)")
                else:
                    # If column A check fails, use usedRange value
                    logger.warning(f"Excel API: Could not get column A, using usedRange value: {max_row}")
                    last_row = max_row
            else:
                # Fallback: default to row 1 if everything fails
                logger.warning(f"Excel API: Could not get usedRange, defaulting to row 1")
                last_row = 1
            
            # Calculate next row
            next_row = last_row + 1
            
            # Build column range (A to column letter based on row_values length)
            def col_letter(n):
                """Convert column number to Excel column letter (1='A', 27='AA', etc.)"""
                result = ""
                while n > 0:
                    n -= 1
                    result = chr(65 + (n % 26)) + result
                    n //= 26
                return result
            
            last_col = col_letter(len(row_values))
            cell_range = f"A{next_row}:{last_col}{next_row}"
            
            logger.info(f"Excel API: Inserting row at range {cell_range}")
            
            # Update the range with new values
            update_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets/{worksheet_name}/range(address='{cell_range}')"
            
            # Prepare payload - values must be 2D array
            payload = {
                "values": [row_values]  # Wrap in array for single row
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.patch(update_url, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.info(f"\033[92m✓ Excel API: Row added successfully at {cell_range}\033[0m")
                return response.json()
            else:
                error_msg = f"Excel API failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to add Excel row via API: {e}")
            raise
    
    def update_excel_row_by_id(self, folder_url: str, excel_file_name: str, 
                               worksheet_name: str, id_column: str, id_value: str,
                               updates: Dict[str, str]) -> Dict[str, Any]:
        """
        Update specific cells in an Excel row identified by ID value
        
        Args:
            folder_url: SharePoint folder URL
            excel_file_name: Name of Excel file
            worksheet_name: Name of worksheet
            id_column: Column letter containing ID (e.g., 'A')
            id_value: Value to search for (e.g., request_id)
            updates: Dict mapping column letters to new values (e.g., {'L': 'Yes', 'M': 'Saved'})
            
        Returns:
            dict: Response from API
            
        Example:
            sp.update_excel_row_by_id(
                "https://yourcompany.sharepoint.com/.../folder",
                "data.xlsx",
                "Sheet1",
                "A",
                "REQ-20251205-123",
                {'L': 'Yes', 'M': 'Saved', 'N': ''}
            )
        """
        try:
            # Get file item ID
            msgraph_folder = self._sharepoint_to_msgraph(folder_url)
            if msgraph_folder.endswith(':'):
                msgraph_folder = msgraph_folder[:-1]
            
            file_url = f"{msgraph_folder}/{excel_file_name}"
            
            logger.info(f"Excel API: Getting file metadata for {excel_file_name}")
            file_response = requests.get(file_url, headers=self.base_headers)
            
            if file_response.status_code != 200:
                raise Exception(f"Failed to get file: {file_response.status_code} - {file_response.text}")
            
            file_data = file_response.json()
            drive_id = file_data['parentReference']['driveId']
            item_id = file_data['id']
            
            # Find row by searching ID column
            logger.info(f"Excel API: Searching for {id_value} in column {id_column}")
            
            # Get usedRange to know how many rows to check
            used_range_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets/{worksheet_name}/usedRange"
            range_response = requests.get(used_range_url, headers=self.base_headers)
            
            if range_response.status_code != 200:
                raise Exception(f"Failed to get usedRange: {range_response.status_code}")
            
            used_range = range_response.json()
            max_row = used_range['rowCount']
            
            # Get ID column values
            id_col_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets/{worksheet_name}/range(address='{id_column}1:{id_column}{max_row}')"
            id_col_response = requests.get(id_col_url, headers=self.base_headers)
            
            if id_col_response.status_code != 200:
                raise Exception(f"Failed to get ID column: {id_col_response.status_code}")
            
            id_col_data = id_col_response.json()
            values = id_col_data.get('values', [])
            
            # Find matching row
            target_row = None
            for idx, row in enumerate(values):
                if row and row[0] and str(row[0]).strip() == str(id_value).strip():
                    target_row = idx + 1  # +1 because Excel is 1-indexed
                    break
            
            if target_row is None:
                raise Exception(f"Row with {id_column}='{id_value}' not found")
            
            logger.info(f"Excel API: Found {id_value} at row {target_row}, updating cells...")
            
            # Update each specified cell
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            for col_letter, new_value in updates.items():
                cell_address = f"{col_letter}{target_row}"
                update_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook/worksheets/{worksheet_name}/range(address='{cell_address}')"
                
                payload = {
                    "values": [[new_value]]
                }
                
                response = requests.patch(update_url, json=payload, headers=headers)
                
                if response.status_code not in [200, 201]:
                    logger.warning(f"Failed to update {cell_address}: {response.status_code}")
                else:
                    logger.debug(f"Updated {cell_address} = '{new_value}'")
            
            logger.info(f"\033[92m✓ Excel API: Row {target_row} updated successfully\033[0m")
            return {'success': True, 'row': target_row}
            
        except Exception as e:
            logger.error(f"Failed to update Excel row: {e}")
            raise
                
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def get_folder_childrens(self, folder: Dict[str, Any]) -> list:
        """
        Get list of children (files/folders) from a folder
        
        Args:
            folder: Parent folder object
            
        Returns:
            list: List of child objects
        """
        try:
            url = folder['webUrl']
            msgraph_command = self._sharepoint_to_msgraph(url)
            
            # Add /children to get folder contents
            children_url = f"{msgraph_command}/children"
            
            logger.info(f"Getting folder children: {folder.get('name', 'Unknown')}")
            
            response = requests.get(children_url, headers=self.base_headers)
            
            if response.status_code == 200:
                children = response.json().get('value', [])
                logger.info(f"\033[92m✓ Found {len(children)} items in folder\033[0m")
                return children
            else:
                error_msg = f"Failed to get children: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to get folder children: {e}")
            raise
    
    def is_file_exists(self, folder: Dict[str, Any], file_name: str) -> bool:
        """
        Check if file exists in folder
        
        Args:
            folder: Parent folder object
            file_name: Name of file to check
            
        Returns:
            bool: True if file exists
        """
        try:
            children = self.get_folder_childrens(folder)
            for child in children:
                if child.get('name') == file_name:
                    logger.info(f"\033[92m✓ File exists: {file_name}\033[0m")
                    return True
            
            logger.info(f"\033[94mℹ File not found: {file_name}\033[0m")
            return False
            
        except Exception as e:
            logger.error(f"Failed to check file existence: {e}")
            return False
    
    def _sharepoint_to_msgraph(self, url: str) -> str:
        """
        Convert SharePoint URL to MS Graph API URL
        
        Args:
            url: SharePoint URL
            
        Returns:
            str: MS Graph API URL
        """
        # Remove query parameters (?...)
        url = re.sub(r'\?.*', '', url)
        
        # Decode URL encoding
        url = url.replace("%20", " ")
        url = url.replace("%2F", "/")
        url = url.replace("%5F", "_")
        url = url.replace("%2D", "-")
        
        # Extract site name and relative path
        # Pattern: https://yourcompany.sharepoint.com/sites/{site_name}/{relative_path}
        match = re.search(r'sites/([^/]+)/(.*)', url)
        if not match:
            raise ValueError(f"Invalid SharePoint URL format: {url}")
        
        site_name = match.group(1)
        relative_path = match.group(2)
        
        # Get site_id
        site_id = self._get_site_id(site_name)
        
        # Remove "Shared Documents/" from relative path
        relative_path = relative_path.replace("Shared Documents/", "")
        
        # Build MS Graph URL
        msgraph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{relative_path}:"
        
        logger.debug(f"Converted URL: {url} -> {msgraph_url}")
        
        return msgraph_url
    
    def create_folder(self, parent_folder: Dict[str, Any], child_folder_name: str, 
                     conflict_behavior: str = "rename") -> Dict[str, Any]:
        """
        Create new folder in SharePoint
        
        Args:
            parent_folder: Parent folder object
            child_folder_name: Name for new folder
            conflict_behavior: 'rename' (add number if exists), 'fail', or 'replace'
            
        Returns:
            dict: New folder object
        """
        try:
            url = parent_folder['webUrl']
            msgraph_command = self._sharepoint_to_msgraph(url)
            
            # Add /children endpoint
            create_url = f"{msgraph_command}/children"
            
            logger.info(f"Creating folder: {child_folder_name}")
            
            data = {
                "name": child_folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": conflict_behavior
            }
            
            response = requests.post(create_url, headers=self.base_headers, json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"\033[92m✓ Folder created: {child_folder_name}\033[0m")
                return response.json()
            else:
                error_msg = f"Failed to create folder: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            raise
    
    def _get_site_id(self, site_name: str) -> str:
        """
        Get SharePoint site ID from site name
        
        Args:
            site_name: Name of SharePoint site
            
        Returns:
            str: Site ID
        """
        # Try option 1: Search by name
        try:
            url = f"https://graph.microsoft.com/v1.0/sites?search={site_name}"
            logger.debug(f"Trying site search: {url}")
            response = requests.get(url, headers=self.base_headers)
            logger.debug(f"Search response status: {response.status_code}")
            
            if response.status_code == 200:
                sites = response.json().get('value', [])
                logger.debug(f"Found {len(sites)} sites")
                if sites:
                    site_id = sites[0]['id']
                    logger.info(f"\033[92m✓ Site ID found (search): {site_id}\033[0m")
                    return site_id
            else:
                logger.warning(f"Search failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.debug(f"Site search failed: {e}")
        
        # Try option 2: Direct path
        try:
            url = f"https://graph.microsoft.com/v1.0/sites/yourcompany.sharepoint.com:/sites/{site_name}"
            logger.debug(f"Trying direct lookup: {url}")
            response = requests.get(url, headers=self.base_headers)
            logger.debug(f"Direct response status: {response.status_code}")
            
            if response.status_code == 200:
                site_id = response.json()['id']
                logger.info(f"\033[92m✓ Site ID found (direct): {site_id}\033[0m")
                return site_id
            else:
                logger.warning(f"Direct lookup failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.debug(f"Direct site lookup failed: {e}")
        
        raise Exception(f"Cannot get site_id for site: {site_name}")
    
    def delete_file(self, file_item: Dict[str, Any]) -> bool:
        """
        Delete a file from SharePoint
        
        Args:
            file_item: File item object with 'id' and '@microsoft.graph.downloadUrl'
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            file_id = file_item.get('id')
            if not file_id:
                raise ValueError("File item must have 'id' field")
            
            # Extract site_id and drive_id from the downloadUrl or use API
            # Build delete URL: /drives/{drive-id}/items/{item-id}
            delete_url = f"https://graph.microsoft.com/v1.0/drives/{file_item.get('parentReference', {}).get('driveId')}/items/{file_id}"
            
            logger.info(f"Deleting file: {file_item.get('name', 'Unknown')}")
            
            response = requests.delete(delete_url, headers=self.base_headers)
            
            if response.status_code in [200, 204]:
                logger.info(f"\033[92m✓ File deleted: {file_item.get('name')}\033[0m")
                return True
            else:
                error_msg = f"Failed to delete file: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def get_files_older_than(self, folder: Dict[str, Any], days: int = 90) -> list:
        """
        Get files from folder that are older than specified days
        
        Args:
            folder: Folder object
            days: Number of days threshold (default: 90 = 3 months)
            
        Returns:
            list: List of file items older than threshold
        """
        try:
            from datetime import datetime, timezone
            
            children = self.get_folder_childrens(folder)
            old_files = []
            threshold_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            for child in children:
                # Skip folders, only process files
                if 'folder' in child:
                    continue
                
                # Check creation date
                created_str = child.get('createdDateTime')
                if created_str:
                    created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                    if created_date < threshold_date:
                        old_files.append(child)
            
            logger.info(f"\033[94mℹ Found {len(old_files)} files older than {days} days\033[0m")
            return old_files
            
        except Exception as e:
            logger.error(f"Failed to get old files: {e}")
            return []

    def send_email(self, sender_email: str, to_recipients: list, subject: str, 
                   html_body: str, cc_recipients: list = None) -> Dict[str, Any]:
        """
        Send email using MS Graph API (same token as SharePoint)
        
        Args:
            sender_email: Email address of sender (must have permissions)
            to_recipients: List of recipient email addresses
            subject: Email subject
            html_body: HTML content of email
            cc_recipients: Optional list of CC email addresses
            
        Returns:
            dict: Response from Graph API
            
        Raises:
            Exception: If email send fails
            
        Example:
            sp.send_email(
                sender_email="transport-app@yourdomain.com",
                to_recipients=["user@example.com"],
                subject="Test",
                html_body="<h1>Hello</h1>",
                cc_recipients=["cc@example.com"]
            )
        """
        try:
            # Build recipient list
            to_list = [{"emailAddress": {"address": email}} for email in to_recipients]
            cc_list = [{"emailAddress": {"address": email}} for email in cc_recipients] if cc_recipients else []
            
            # Construct email message
            email_message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": html_body
                    },
                    "toRecipients": to_list,
                    "ccRecipients": cc_list
                },
                "saveToSentItems": "true"
            }
            
            # MS Graph API endpoint for sending email
            # Use /users/{userId}/sendMail endpoint
            graph_url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
            
            logger.info(f"\033[94mℹ Sending email via MS Graph API to {to_recipients}\033[0m")
            logger.debug(f"Graph URL: {graph_url}")
            
            # Send POST request
            response = requests.post(
                graph_url,
                headers={
                    **self.base_headers,
                    "Content-Type": "application/json"
                },
                json=email_message
            )
            
            # Check response (202 = Accepted, 200 = OK)
            if response.status_code in [200, 202]:
                logger.info(f"\033[92m✓ Email sent successfully via MS Graph API\033[0m")
                return {"success": True, "status_code": response.status_code}
            else:
                error_msg = f"MS Graph API error: {response.status_code} - {response.text}"
                logger.error(f"\033[91m✗ {error_msg}\033[0m")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"\033[91m✗ Failed to send email via MS Graph: {e}\033[0m")
            raise


