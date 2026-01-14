"""
EmailHelper - Encapsulates email sending logic
No need to pass config/logger to every method - stored in instance
"""
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


def parse_email_list(email_input) -> list:
    """
    Universal helper to convert email string or list to list of emails.
    Handles:
    - Single email: 'user@example.com' -> ['user@example.com']
    - Semicolon-separated: 'user1@example.com;user2@example.com' -> ['user1@example.com', 'user2@example.com']
    - Already a list: ['user@example.com'] -> ['user@example.com']
    - None/empty: None -> []
    """
    if not email_input:
        return []
    
    if isinstance(email_input, list):
        return [email.strip() for email in email_input if email and email.strip()]
    
    if isinstance(email_input, str):
        return [email.strip() for email in email_input.split(';') if email.strip()]
    
    return []


class EmailHelper:
    """Handles email sending via MS Graph API"""
    
    def __init__(self, config: dict, transport_config: dict, get_access_token_func,
                 logger_instance=None, app_logger_instance=None):
        """
        Initialize Email helper with configuration and dependencies
        
        Args:
            config: Full configuration dict
            transport_config: Transport section of config
            get_access_token_func: Function to get SharePoint access token
            logger_instance: Standard logger
            app_logger_instance: Structured app logger
        """
        self.config = config
        self.transport_config = transport_config
        self.email_config = transport_config.get('email', {})
        self.get_access_token = get_access_token_func
        self.logger = logger_instance or logger
        self.app_logger = app_logger_instance
        
    def send_confirmation(self, request_id: str, data: dict, user_email: str,
                         has_attachment: bool, attachment_error: str = None,
                         attachments_saved: List[str] = None):
        """
        Send confirmation email to user
        
        Args:
            request_id: Request identifier
            data: Form data
            user_email: Recipient email
            has_attachment: Whether attachments were saved
            attachment_error: Error message if failed
            attachments_saved: List of saved attachment filenames
        """
        try:
            # Check if email sending is enabled
            if not self.email_config.get('enabled', True):
                self.logger.info("\033[94mℹ Email sending disabled in config\033[0m")
                return
            
            # Get email settings
            sender_email = self.email_config.get('sender_email', 'transport-app@yourdomain.com')
            sender_name = self.email_config.get('sender_name', 'UIT RO Transport System')
            cc_email = self.email_config.get('cc_email', '')
            
            # Check if user email is in test_emails lists (dev/test/prod modes)
            user_email_lower = user_email.lower()
            detected_mode = None
            
            for mode in ['dev', 'test', 'prod']:
                mode_config = self.config.get(mode, {})
                test_emails = mode_config.get('test_emails', [])
                test_emails_lower = [email.lower() for email in test_emails]
                
                if user_email_lower in test_emails_lower:
                    detected_mode = mode
                    cc_email = mode_config.get('cc_email', cc_email)
                    self.logger.info(f"\033[93m⚠ {mode.upper()} MODE detected ({user_email}) - using CC: {cc_email}\033[0m")
                    break
            
            if not detected_mode:
                self.logger.info(f"\033[94mℹ Production mode - using default CC: {cc_email}\033[0m")
            
            subject_template = self.email_config.get('subject_template', 'Transport Request Confirmation - {request_id}')
            
            # Load HTML template
            template_path = Path(__file__).parent.parent.parent / 'res' / 'confirmation_email.html'
            if not template_path.exists():
                self.logger.error(f"\033[91m✗ Email template not found: {template_path}\033[0m")
                return
            
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            # Prepare attachment status text
            if has_attachment and attachments_saved:
                attachment_status = f"✓ Successfully saved ({len(attachments_saved)} file(s))"
            elif attachment_error:
                attachment_status = f"✗ Upload failed: {attachment_error}"
            else:
                attachment_status = "No attachments"
            
            # Replace placeholders
            html_body = html_template.replace('{{request_id}}', request_id)
            html_body = html_body.replace('{{delivery_note}}', data.get('deliveryNoteNumber', 'N/A'))
            html_body = html_body.replace('{{truck_plates}}', data.get('truckLicensePlates', 'N/A'))
            html_body = html_body.replace('{{trailer_plates}}', data.get('trailerLicensePlates', 'N/A'))
            html_body = html_body.replace('{{carrier_country}}', data.get('carrierCountry', 'N/A'))
            html_body = html_body.replace('{{carrier_tax_code}}', data.get('carrierTaxCode', 'N/A'))
            html_body = html_body.replace('{{carrier_name}}', data.get('carrierFullName', 'N/A'))
            html_body = html_body.replace('{{border_crossing}}', data.get('borderCrossing', 'N/A'))
            html_body = html_body.replace('{{crossing_date}}', data.get('borderCrossingDate', 'N/A'))
            html_body = html_body.replace('{{email}}', data.get('email', 'N/A'))
            html_body = html_body.replace('{{phone_number}}', data.get('phoneNumber', 'N/A') or 'Not provided')
            html_body = html_body.replace('{{attachment_status}}', attachment_status)
            
            # Prepare recipient lists
            to_recipients = parse_email_list(user_email)
            cc_recipients = parse_email_list(cc_email) or None
            subject = subject_template.format(request_id=request_id)
            
            # Get access token and send
            from sharepoint_helper import SharePointHelper
            access_token = self.get_access_token()
            sp = SharePointHelper(access_token)
            
            self.logger.info(f"\033[94mℹ Sending confirmation email to {user_email} (CC: {cc_email or 'none'})\033[0m")
            
            sp.send_email(
                sender_email=sender_email,
                to_recipients=to_recipients,
                subject=subject,
                html_body=html_body,
                cc_recipients=cc_recipients
            )
            
            self.logger.info(f"\033[92m✓ Confirmation email sent successfully to {user_email}\033[0m")
            
            if self.app_logger:
                self.app_logger.log_info(
                    f"Confirmation email sent for {request_id}",
                    {
                        'request_id': request_id,
                        'recipient': user_email,
                        'cc': cc_email,
                        'email_status': 'sent',
                        'method': 'ms_graph_api'
                    }
                )
            
        except Exception as e:
            self.logger.error(f"\033[91m✗ Failed to send confirmation email: {e}\033[0m", exc_info=True)
            if self.app_logger:
                self.app_logger.log_error(
                    f"Email send failed for {request_id}",
                    {
                        'request_id': request_id,
                        'recipient': user_email,
                        'error': str(e),
                        'email_status': 'failed',
                        'method': 'ms_graph_api'
                    }
                )
