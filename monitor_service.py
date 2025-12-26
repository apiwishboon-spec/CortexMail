"""
Email Monitoring Service
Background service that periodically checks for new emails
"""

import threading
import time
import logging
from datetime import datetime
import json
import os
import threading

logger = logging.getLogger(__name__)


class EmailMonitor:
    """Background email monitoring service"""
    
    def __init__(self, email_service, interval=30, max_emails_per_check=10):
        """
        Initialize email monitor
        
        Args:
            email_service: EmailService instance
            interval: Check interval in seconds
            max_emails_per_check: Maximum emails to process per check
        """
        self.email_service = email_service
        self.interval = interval
        self.max_emails_per_check = max_emails_per_check
        
        self.is_running = False
        self.is_enabled = False
        self.monitor_thread = None
        
        # History persistence
        self.history_file = 'processed_history.json'
        self.lock = threading.Lock()
        self.recent_processed = self._load_history()
        self.max_recent = 50  # Keep last 50 processed emails
        
    def start(self):
        """Start the monitoring service"""
        if self.is_running:
            logger.warning("Monitor is already running")
            return
        
        self.is_running = True
        self.is_enabled = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Email monitoring started")
    
    def stop(self):
        """Stop the monitoring service"""
        self.is_running = False
        self.is_enabled = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Email monitoring stopped")
    
    def enable(self):
        """Enable auto-reply (monitoring continues but processing is enabled)"""
        self.is_enabled = True
        logger.info("Auto-reply enabled")
    
    def disable(self):
        """Disable auto-reply (monitoring continues but processing is paused)"""
        self.is_enabled = False
        logger.info("Auto-reply disabled")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Monitor loop started (interval: {self.interval}s)")
        
        while self.is_running:
            try:
                if self.is_enabled:
                    self._check_and_process()
                
                # Sleep in small increments to allow quick shutdown
                for _ in range(self.interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def _check_and_process(self):
        """Check for new emails and process them"""
        try:
            # Check for new emails
            new_emails = self.email_service.check_new_emails(self.max_emails_per_check)
            
            if not new_emails:
                return
            
            logger.info(f"Processing {len(new_emails)} new emails")
            
            # Process each email
            for email_data in new_emails:
                if not self.is_enabled:
                    logger.info("Auto-reply disabled, stopping processing")
                    break
                
                result = self.email_service.process_email(email_data)
                
                if result['success']:
                    # Add to recent processed list
                    self._add_to_recent(result)
                    logger.info(f"Successfully processed email from {result['sender']}")
                else:
                    logger.error(f"Failed to process email: {result.get('error', 'Unknown error')}")
                
                # Small delay between processing emails
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error checking and processing emails: {str(e)}")
    
    def _add_to_recent(self, result):
        """Add processed email to recent list and persist"""
        with self.lock:
            self.recent_processed.insert(0, result)
            
            # Keep only the most recent
            if len(self.recent_processed) > self.max_recent:
                self.recent_processed = self.recent_processed[:self.max_recent]
            
            self._save_history()
    
    def _load_history(self):
        """Load processed history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading processed history: {str(e)}")
        
        return []
    
    def _save_history(self):
        """Save processed history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.recent_processed, f)
        except Exception as e:
            logger.error(f"Error saving processed history: {str(e)}")
    
    @staticmethod
    def load_recent_history(limit=20):
        """Static method to load history from disk without an instance"""
        history_file = 'processed_history.json'
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    return history[:limit]
        except Exception as e:
            logger.error(f"Error loading processed history statically: {str(e)}")
        return []

    def get_recent_emails(self, limit=20):
        """
        Get recently processed emails
        
        Args:
            limit: Maximum number of emails to return
            
        Returns:
            list: Recent processed emails
        """
        with self.lock:
            # If memory is empty but we have a file, reload just in case
            if not self.recent_processed and os.path.exists(self.history_file):
                self.recent_processed = self._load_history()
            return self.recent_processed[:limit]
    def get_status(self):
        """Get monitor status"""
        with self.lock:
            return {
                'is_running': self.is_running,
                'is_enabled': self.is_enabled,
                'interval': self.interval,
                'recent_count': len(self.recent_processed)
            }
