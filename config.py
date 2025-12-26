"""
Configuration management for AI Email Auto-Reply Application
Handles environment variables and default settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Email monitoring settings
    MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', '30'))  # seconds
    MAX_EMAILS_PER_CHECK = int(os.getenv('MAX_EMAILS_PER_CHECK', '10'))
    
    # AI Settings
    USE_OLLAMA = os.getenv('USE_OLLAMA', 'False').lower() == 'true'
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
    
    # Session settings
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hour in seconds
    PERMANENT_SESSION_LIFETIME = SESSION_TIMEOUT
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5001').split(',')
    
    # Email provider configurations
    EMAIL_PROVIDERS = {
        'gmail': {
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587
        },
        'outlook': {
            'imap_server': 'outlook.office365.com',
            'imap_port': 993,
            'smtp_server': 'smtp.office365.com',
            'smtp_port': 587
        },
        'yahoo': {
            'imap_server': 'imap.mail.yahoo.com',
            'imap_port': 993,
            'smtp_server': 'smtp.mail.yahoo.com',
            'smtp_port': 587
        }
    }
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'email_autoreply.log')
    
    @staticmethod
    def get_email_provider(email_address):
        """Detect email provider from email address"""
        domain = email_address.split('@')[-1].lower()
        
        if 'gmail' in domain:
            return Config.EMAIL_PROVIDERS['gmail']
        elif 'outlook' in domain or 'hotmail' in domain or 'live' in domain:
            return Config.EMAIL_PROVIDERS['outlook']
        elif 'yahoo' in domain:
            return Config.EMAIL_PROVIDERS['yahoo']
        else:
            # Default to Gmail settings for unknown providers
            return Config.EMAIL_PROVIDERS['gmail']
