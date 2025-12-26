"""
Email Service Module
Handles IMAP (reading) and SMTP (sending) operations
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import logging
from datetime import datetime
import json
import os
import threading

from config import Config
from ai_processor import email_ai
from email_template import generate_html_email, generate_plain_text

# Configure logging
logger = logging.getLogger(__name__)


class EmailService:
    """Manages email operations via IMAP and SMTP"""
    
    def __init__(self, email_address, app_password):
        """
        Initialize email service
        
        Args:
            email_address: User's email address
            app_password: App-specific password
        """
        self.email_address = email_address
        self.app_password = app_password
        self.provider_config = Config.get_email_provider(email_address)
        
        self.imap_connection = None
        self.smtp_connection = None
        self.is_connected = False
        
        # Thread safety lock
        self.lock = threading.Lock()
        
        # Track processed emails to avoid duplicates
        self.processed_emails_file = 'processed_emails.json'
        self.processed_emails = self._load_processed_emails()
        
    def connect(self):
        """
        Establish IMAP and SMTP connections
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Connect to IMAP
            logger.info(f"Connecting to IMAP server: {self.provider_config['imap_server']}")
            self.imap_connection = imaplib.IMAP4_SSL(
                self.provider_config['imap_server'],
                self.provider_config['imap_port']
            )
            self.imap_connection.login(self.email_address, self.app_password)
            logger.info("IMAP connection successful")
            
            # Test SMTP connection
            logger.info(f"Testing SMTP server: {self.provider_config['smtp_server']}")
            smtp = smtplib.SMTP(
                self.provider_config['smtp_server'],
                self.provider_config['smtp_port']
            )
            smtp.starttls()
            smtp.login(self.email_address, self.app_password)
            smtp.quit()
            logger.info("SMTP connection successful")
            
            self.is_connected = True
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP connection failed: {str(e)}")
            self.is_connected = False
            return False
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            self.is_connected = False
            return False
    
    def ensure_connection(self):
        """Ensure email connections are active, reconnect if necessary"""
        with self.lock:
            if not self.is_connected:
                logger.info("Connection lost, attempting to reconnect...")
                return self.connect()
            
            try:
                # Check IMAP connection with a simple NOOP
                self.imap_connection.noop()
                return True
            except:
                logger.warning("IMAP connection check failed, reconnecting...")
                self.is_connected = False
                return self.connect()
    
    def disconnect(self):
        """Close all connections"""
        try:
            if self.imap_connection:
                self.imap_connection.logout()
            if self.smtp_connection:
                self.smtp_connection.quit()
            self.is_connected = False
            logger.info("Disconnected from email servers")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
    
    def check_new_emails(self, max_emails=10):
        """
        Check for new unread emails
        
        Args:
            max_emails: Maximum number of emails to process
            
        Returns:
            list: List of new email data dictionaries
        """
        if not self.ensure_connection():
            logger.warning("Could not ensure connection for checking emails")
            return []
        
        try:
            with self.lock:
                # Select inbox
                self.imap_connection.select('INBOX')
                
                # Search for unread emails
                status, messages = self.imap_connection.search(None, 'UNSEEN')
                
                if status != 'OK':
                    logger.error("Failed to search for emails")
                    return []
                
                email_ids = messages[0].split()
                
                if not email_ids:
                    logger.info("No new emails found")
                    return []
                
                # Limit number of emails to process
                email_ids = email_ids[-max_emails:]
                logger.info(f"Found {len(email_ids)} unread email IDs: {email_ids}")
                
                new_emails = []
                
                for email_id in email_ids:
                    email_data = self._fetch_email_internal(email_id)
                    if email_data:
                        if email_data['message_id'] not in self.processed_emails:
                            new_emails.append(email_data)
                        else:
                            logger.debug(f"Email {email_data['message_id']} already processed")
                    else:
                        logger.warning(f"Failed to fetch email data for ID {email_id}")
                
                logger.info(f"Found {len(new_emails)} new unprocessed emails")
                return new_emails
            
        except Exception as e:
            logger.error(f"Error checking emails: {str(e)}")
            return []
    
    def _fetch_email_internal(self, email_id):
        """
        Fetch and parse a single email
        
        Args:
            email_id: Email ID to fetch
            
        Returns:
            dict: Parsed email data
        """
        try:
            status, msg_data = self.imap_connection.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                logger.error(f"Fetch failed for ID {email_id}: status={status}")
                return None
            
            if not msg_data or not msg_data[0]:
                logger.error(f"No message data returned for ID {email_id}")
                return None
            
            # Parse email
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Extract headers
            subject = self._decode_header(email_message['Subject'])
            from_header = self._decode_header(email_message['From'])
            message_id = email_message['Message-ID']
            date = email_message['Date']
            
            # Extract sender name and email
            sender_name, sender_email = self._parse_from_header(from_header)
            
            # Extract body
            body = self._extract_body(email_message)
            
            return {
                'id': email_id.decode(),
                'message_id': message_id,
                'subject': subject,
                'from': from_header,
                'sender_name': sender_name,
                'sender_email': sender_email,
                'date': date,
                'body': body
            }
            
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {str(e)}")
            return None
    
    def _decode_header(self, header):
        """Decode email header"""
        if header is None:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(encoding or 'utf-8')
                except:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string
    
    def _parse_from_header(self, from_header):
        """Extract name and email from From header"""
        try:
            # Parse "Name <email@example.com>" format
            if '<' in from_header and '>' in from_header:
                name = from_header.split('<')[0].strip().strip('"')
                email_addr = from_header.split('<')[1].split('>')[0].strip()
                return name, email_addr
            else:
                return "", from_header.strip()
        except:
            return "", from_header
    
    def _extract_body(self, email_message):
        """Extract email body text"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Get text/plain parts
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode()
                    except:
                        pass
        else:
            try:
                body = email_message.get_payload(decode=True).decode()
            except:
                body = str(email_message.get_payload())
        
        return body.strip()
    
    def send_reply(self, to_email, subject, response_text, original_message_id=None):
        """
        Send an HTML email reply
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            response_text: AI-generated response text
            original_message_id: Message ID of original email (for threading)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.ensure_connection():
            logger.error("Could not ensure connection for sending reply")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
            
            # Add threading headers
            if original_message_id:
                msg['In-Reply-To'] = original_message_id
                msg['References'] = original_message_id
            
            # Generate plain text and HTML versions
            plain_text = generate_plain_text(response_text)
            html_content = generate_html_email(response_text, subject)
            
            # Attach both versions
            part1 = MIMEText(plain_text, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            smtp = smtplib.SMTP(
                self.provider_config['smtp_server'],
                self.provider_config['smtp_port']
            )
            smtp.starttls()
            smtp.login(self.email_address, self.app_password)
            smtp.send_message(msg)
            smtp.quit()
            
            logger.info(f"Reply sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending reply: {str(e)}")
            return False
    
    def process_email(self, email_data):
        """
        Process an email: analyze with AI and send reply
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            dict: Processing result
        """
        try:
            logger.info(f"Processing email from {email_data['sender_email']}")
            
            # Analyze email with AI
            analysis = email_ai.analyze_email(
                subject=email_data['subject'],
                body=email_data['body'],
                sender_name=email_data['sender_name']
            )
            
            # Generate response
            response_text = email_ai.generate_response(analysis)
            
            # Send reply
            success = self.send_reply(
                to_email=email_data['sender_email'],
                subject=email_data['subject'],
                response_text=response_text,
                original_message_id=email_data['message_id']
            )
            
            if success:
                # Mark as processed
                self._mark_as_processed(email_data['message_id'])
                
                result = {
                    'success': True,
                    'email_id': email_data['id'],
                    'sender': email_data['sender_email'],
                    'subject': email_data['subject'],
                    'intent': analysis['intent'],
                    'tone': analysis['tone'],
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Successfully processed email {email_data['id']}")
                return result
            else:
                return {
                    'success': False,
                    'error': 'Failed to send reply',
                    'email_id': email_data['id']
                }
                
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'email_id': email_data.get('id', 'unknown')
            }
    
    def _load_processed_emails(self):
        """Load list of processed email IDs"""
        try:
            if os.path.exists(self.processed_emails_file):
                with open(self.processed_emails_file, 'r') as f:
                    return set(json.load(f))
        except Exception as e:
            logger.error(f"Error loading processed emails: {str(e)}")
        
        return set()
    
    def _mark_as_processed(self, message_id):
        """Mark an email as processed"""
        self.processed_emails.add(message_id)
        self._save_processed_emails()
    
    def _save_processed_emails(self):
        """Save processed email IDs to file"""
        try:
            with open(self.processed_emails_file, 'w') as f:
                json.dump(list(self.processed_emails), f)
        except Exception as e:
            logger.error(f"Error saving processed emails: {str(e)}")
    
    def get_status(self):
        """Get current connection status"""
        return {
            'connected': self.is_connected,
            'email': self.email_address,
            'provider': self.provider_config['imap_server'],
            'processed_count': len(self.processed_emails)
        }
