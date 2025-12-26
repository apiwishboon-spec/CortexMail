# AI Email Auto-Reply Application

A production-ready AI-powered automatic email reply system with real SMTP/IMAP integration, intelligent response generation, and a modern web interface.

## Features

- 🤖 **Custom AI Engine** - Intent detection, tone analysis, and natural language response generation
- 📧 **Real Email Integration** - Full IMAP/SMTP support for Gmail, Outlook, Yahoo, and more
- ⚡ **Real-time Monitoring** - Automatic inbox checking with configurable intervals
- 🎨 **Beautiful HTML Emails** - Professional card-based email templates
- 🌐 **Modern Web Interface** - Responsive login and dashboard pages
- 🔒 **Secure** - Session management and app password authentication

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Email account with app password enabled (for Gmail: https://myaccount.google.com/apppasswords)

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd "/Users/boon/Desktop/SynapseMail/GOOGLE ANTIGRAVITY"
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional)**
   ```bash
   cp .env.example .env
   # Edit .env file with your preferred settings
   ```

### Running the Application

1. **Start the server**
   ```bash
   python app.py
   ```

2. **Open your browser**
   ```
   http://localhost:5001
   ```

3. **Login with your email credentials**
   - Email: your.email@gmail.com
   - App Password: your-app-specific-password

4. **Enable auto-reply from the dashboard**

## Project Structure

```
.
├── app.py                  # Flask web server with REST API
├── config.py              # Configuration management
├── ai_processor.py        # Custom AI engine for response generation
├── email_service.py       # IMAP/SMTP email operations
├── email_template.py      # HTML email template generator
├── monitor_service.py     # Background email monitoring
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
└── static/
    ├── index.html        # Login page
    ├── dashboard.html    # Dashboard interface
    ├── css/
    │   └── styles.css    # Complete styling
    └── js/
        └── app.js        # Frontend application logic
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
SECRET_KEY=your-secret-key-change-this
MONITOR_INTERVAL=30              # Check emails every 30 seconds
MAX_EMAILS_PER_CHECK=10         # Process up to 10 emails per check
SESSION_TIMEOUT=3600            # Session timeout in seconds
LOG_LEVEL=INFO                  # Logging level
```

### Email Providers

The application automatically detects your email provider and uses the appropriate settings:

- **Gmail**: imap.gmail.com / smtp.gmail.com
- **Outlook**: outlook.office365.com / smtp.office365.com
- **Yahoo**: imap.mail.yahoo.com / smtp.mail.yahoo.com

## How It Works

1. **Login**: User enters email and app password
2. **Connection**: System establishes IMAP/SMTP connections
3. **Monitoring**: Background service checks inbox every 30 seconds (configurable)
4. **Analysis**: Custom AI analyzes email intent and tone
5. **Generation**: AI generates context-aware response
6. **Sending**: Response wrapped in HTML template and sent via SMTP
7. **Tracking**: Email marked as processed to avoid duplicates

## AI Engine

The custom AI engine includes:

- **Intent Classification**: Detects questions, requests, complaints, support needs, etc.
- **Tone Analysis**: Identifies formal, friendly, professional, or casual tones
- **Response Generation**: Creates natural, human-like replies
- **Context Awareness**: Extracts sender name, subject references, urgency

## API Endpoints

- `POST /api/login` - Authenticate and connect to email
- `GET /api/status` - Get connection and auto-reply status
- `POST /api/toggle-autoreply` - Enable/disable auto-reply
- `GET /api/recent-emails` - Get recently processed emails
- `POST /api/check-now` - Manually trigger email check
- `POST /api/logout` - Logout and cleanup

## Security Notes

- **Never commit your `.env` file** - It contains sensitive configuration
- **Use app-specific passwords** - Not your regular email password
- **Enable 2FA** - Required for app passwords on most providers
- **Keep dependencies updated** - Run `pip install --upgrade -r requirements.txt`

## Troubleshooting

### Connection Failed

- Verify you're using an app-specific password, not your regular password
- Ensure 2-factor authentication is enabled on your account
- Check that IMAP/SMTP access is enabled in your email settings

### No Emails Being Processed

- Verify auto-reply is enabled in the dashboard
- Check the logs in `email_autoreply.log`
- Ensure you have unread emails in your inbox
- Try clicking "Check Emails Now" button

### Port Already in Use

If port 5000 is already in use, modify `app.py`:
```python
app.run(debug=Config.DEBUG, host='0.0.0.0', port=5001)
```

## Development

### Running in Debug Mode

Edit `.env`:
```env
DEBUG=True
```

### Viewing Logs

```bash
tail -f email_autoreply.log
```

### Testing Email Sending

1. Enable auto-reply
2. Send a test email to your account from another email
3. Check the dashboard for processed emails
4. Verify the auto-reply was received

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
1. Check the logs in `email_autoreply.log`
2. Verify your email provider settings
3. Ensure all dependencies are installed correctly
