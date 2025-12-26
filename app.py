"""
Flask Web Application
Main backend server with REST API endpoints
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from datetime import timedelta
import logging
import os

from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ],
    force=True  # Ensure this config overrides any previous ones
)
logger = logging.getLogger(__name__)

from email_service import EmailService
from monitor_service import EmailMonitor

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=Config.SESSION_TIMEOUT)

# Enable CORS
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# Global services (stored per session)
email_services = {}
email_monitors = {}


@app.route('/')
def index():
    """Serve login page"""
    return send_from_directory('static', 'index.html')


@app.route('/dashboard')
def dashboard():
    """Serve dashboard page"""
    return send_from_directory('static', 'dashboard.html')


@app.route('/api/login', methods=['POST'])
def login():
    """
    Authenticate user and establish email connection
    
    Request body:
        {
            "email": "user@example.com",
            "password": "app-password"
        }
    
    Returns:
        {
            "success": true/false,
            "message": "...",
            "email": "user@example.com"
        }
    """
    try:
        data = request.get_json()
        email_address = data.get('email')
        app_password = data.get('password')
        
        if not email_address or not app_password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        # Create email service
        email_service = EmailService(email_address, app_password)
        
        # Test connection
        if not email_service.connect():
            return jsonify({
                'success': False,
                'message': 'Failed to connect. Please check your credentials and ensure you are using an app password.'
            }), 401
        
        # Store in session
        session['email'] = email_address
        session.permanent = True
        
        # Store service instances
        session_id = session.sid if hasattr(session, 'sid') else email_address
        email_services[session_id] = email_service
        
        # Create and start monitor
        monitor = EmailMonitor(
            email_service,
            interval=Config.MONITOR_INTERVAL,
            max_emails_per_check=Config.MAX_EMAILS_PER_CHECK
        )
        monitor.start()
        email_monitors[session_id] = monitor
        
        logger.info(f"User logged in: {email_address}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'email': email_address
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user and cleanup resources"""
    try:
        session_id = session.sid if hasattr(session, 'sid') else session.get('email')
        
        # Stop monitor
        if session_id in email_monitors:
            email_monitors[session_id].stop()
            del email_monitors[session_id]
        
        # Disconnect email service
        if session_id in email_services:
            email_services[session_id].disconnect()
            del email_services[session_id]
        
        email = session.get('email', 'unknown')
        session.clear()
        
        logger.info(f"User logged out: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Get current email connection and auto-reply status
    
    Returns:
        {
            "connected": true/false,
            "email": "user@example.com",
            "autoreply_enabled": true/false,
            "monitor_running": true/false,
            "processed_count": 10
        }
    """
    try:
        if 'email' not in session:
            return jsonify({
                'connected': False,
                'message': 'Not logged in'
            }), 401
        
        session_id = session.sid if hasattr(session, 'sid') else session.get('email')
        
        email_service = email_services.get(session_id)
        monitor = email_monitors.get(session_id)
        
        if not email_service or not monitor:
            # Try to get some info from disk even if not initialized
            processed_count = 0
            if os.path.exists('processed_emails.json'):
                try:
                    with open('processed_emails.json', 'r') as f:
                        processed_count = len(json.load(f))
                except:
                    pass
            
            return jsonify({
                'connected': False,
                'email': session.get('email'),
                'autoreply_enabled': False,
                'monitor_running': False,
                'processed_count': processed_count,
                'message': 'Service re-authentication required after restart'
            })
        
        service_status = email_service.get_status()
        monitor_status = monitor.get_status()
        
        return jsonify({
            'connected': service_status['connected'],
            'email': service_status['email'],
            'autoreply_enabled': monitor_status['is_enabled'],
            'monitor_running': monitor_status['is_running'],
            'processed_count': service_status['processed_count']
        })
        
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/toggle-autoreply', methods=['POST'])
def toggle_autoreply():
    """
    Enable or disable auto-reply
    
    Request body:
        {
            "enabled": true/false
        }
    
    Returns:
        {
            "success": true/false,
            "enabled": true/false
        }
    """
    try:
        if 'email' not in session:
            return jsonify({
                'success': False,
                'message': 'Not logged in'
            }), 401
        
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        session_id = session.sid if hasattr(session, 'sid') else session.get('email')
        monitor = email_monitors.get(session_id)
        
        if not monitor:
            return jsonify({
                'success': False,
                'message': 'Monitor not initialized'
            }), 500
        
        if enabled:
            monitor.enable()
        else:
            monitor.disable()
        
        logger.info(f"Auto-reply {'enabled' if enabled else 'disabled'} for {session.get('email')}")
        
        return jsonify({
            'success': True,
            'enabled': enabled
        })
        
    except Exception as e:
        logger.error(f"Toggle autoreply error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/recent-emails', methods=['GET'])
def get_recent_emails():
    """
    Get recently processed emails
    
    Query params:
        limit: Number of emails to return (default: 20)
    
    Returns:
        {
            "success": true,
            "emails": [...]
        }
    """
    try:
        if 'email' not in session:
            return jsonify({
                'success': False,
                'message': 'Not logged in'
            }), 401
        
        limit = request.args.get('limit', 20, type=int)
        
        session_id = session.sid if hasattr(session, 'sid') else session.get('email')
        monitor = email_monitors.get(session_id)
        
        if not monitor:
            # Try to load history from disk if monitor is not in memory
            recent_emails = EmailMonitor.load_recent_history(limit)
            return jsonify({
                'success': True,
                'emails': recent_emails,
                'reauth_required': True
            })
        
        recent_emails = monitor.get_recent_emails(limit)
        
        return jsonify({
            'success': True,
            'emails': recent_emails
        })
        
    except Exception as e:
        logger.error(f"Get recent emails error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/check-now', methods=['POST'])
def check_now():
    """
    Manually trigger email check
    
    Returns:
        {
            "success": true,
            "message": "Check completed",
            "new_emails": 5
        }
    """
    try:
        if 'email' not in session:
            return jsonify({
                'success': False,
                'message': 'Not logged in'
            }), 401
        
        session_id = session.sid if hasattr(session, 'sid') else session.get('email')
        email_service = email_services.get(session_id)
        
        if not email_service:
            return jsonify({
                'success': False,
                'message': 'Service not initialized'
            }), 500
        
        new_emails = email_service.check_new_emails(Config.MAX_EMAILS_PER_CHECK)
        
        return jsonify({
            'success': True,
            'message': 'Check completed',
            'new_emails': len(new_emails)
        })
        
    except Exception as e:
        logger.error(f"Check now error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("Starting AI Email Auto-Reply Application")
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5001)
