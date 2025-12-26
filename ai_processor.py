"""
Custom AI Engine for Email Response Generation
Implements intent classification, tone analysis, and natural language generation
"""

import re
import random
from datetime import datetime
import requests
import json

from config import Config

class EmailAI:
    """Custom AI engine for intelligent email response generation"""
    
    def __init__(self):
        # Intent keywords and patterns
        self.intent_patterns = {
            'question': [
                r'\?', r'\bwhat\b', r'\bwhen\b', r'\bwhere\b', r'\bwho\b', 
                r'\bwhy\b', r'\bhow\b', r'\bcould you\b', r'\bcan you\b',
                r'\bwould you\b', r'\bdo you\b', r'\bis there\b', r'\bare there\b'
            ],
            'request': [
                r'\bplease\b', r'\bcould you\b', r'\bwould you\b', r'\bcan you\b',
                r'\bneed\b', r'\brequire\b', r'\bwant\b', r'\bwish\b',
                r'\bsend me\b', r'\bprovide\b', r'\bshare\b'
            ],
            'complaint': [
                r'\bproblem\b', r'\bissue\b', r'\berror\b', r'\bwrong\b',
                r'\bnot working\b', r'\bfailed\b', r'\bdisappointed\b',
                r'\bunhappy\b', r'\bfrustrated\b', r'\bterrible\b'
            ],
            'support': [
                r'\bhelp\b', r'\bsupport\b', r'\bassist\b', r'\bguide\b',
                r'\btrouble\b', r'\bconfused\b', r'\bdon\'t understand\b'
            ],
            'casual': [
                r'\bhey\b', r'\bhi\b', r'\bhello\b', r'\bthanks\b',
                r'\bthank you\b', r'\bappreciate\b', r'\bcheers\b'
            ],
            'urgent': [
                r'\burgent\b', r'\basap\b', r'\bimmediately\b', r'\bquickly\b',
                r'\bright away\b', r'\bas soon as possible\b', r'\bpriority\b'
            ]
        }
        
        # Keyword extraction categories
        self.topic_keywords = {
            'technical': [r'\berror\b', r'\bbug\b', r'\bfix\b', r'\blogin\b', r'\bpassword\b', r'\baccess\b', r'\bweb\b', r'\bapp\b', r'\bserver\b'],
            'billing': [r'\binvoice\b', r'\bpayment\b', r'\bbilling\b', r'\bpricing\b', r'\bcost\b', r'\bcharge\b', r'\brefund\b'],
            'general': [r'\binformation\b', r'\bdetails\b', r'\bquestion\b', r'\bhelp\b', r'\bstatus\b', r'\bupdate\b'],
            'scheduling': [r'\bmeeting\b', r'\bschedule\b', r'\bcalendar\b', r'\bappointment\b', r'\btime\b', r'\bdate\b']
        }
        
        # Tone indicators
        self.tone_indicators = {
            'formal': [
                r'\bdear\b', r'\bsincerely\b', r'\bregards\b', r'\brespectfully\b',
                r'\bkindly\b', r'\bwould appreciate\b'
            ],
            'friendly': [
                r'\bhey\b', r'\bhi\b', r'\bthanks\b', r'\bawesome\b',
                r'\bgreat\b', r'\bcool\b', r'!', r'😊', r'👍'
            ],
            'professional': [
                r'\bregarding\b', r'\bpursuant\b', r'\bfurthermore\b',
                r'\bhowever\b', r'\btherefore\b', r'\brespectively\b'
            ]
        }
        
    def analyze_email(self, subject, body, sender_name=None):
        """
        Analyze email content and return intent, tone, and context
        
        Args:
            subject: Email subject line
            body: Email body content
            sender_name: Name of the sender (optional)
            
        Returns:
            dict: Analysis results with intent, tone, urgency, and context
        """
        text = f"{subject} {body}".lower()
        
        # Detect intent
        intent = self._detect_intent(text)
        
        # Detect tone
        tone = self._detect_tone(text)
        
        # Detect urgency
        urgency = self._detect_urgency(text)
        
        # Extract context
        context = {
            'has_question': bool(re.search(r'\?', text)),
            'sender_name': sender_name or self._extract_name(body),
            'subject': subject,
            'original_body': body,
            'is_urgent': urgency > 0.5,
            'word_count': len(text.split())
        }
        
        return {
            'intent': intent,
            'tone': tone,
            'urgency': urgency,
            'context': context
        }
    
    def _detect_intent(self, text):
        """Detect primary intent of the email"""
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            scores[intent] = score
        
        # Return intent with highest score, default to 'casual'
        if max(scores.values()) == 0:
            return 'casual'
        
        return max(scores, key=scores.get)
    
    def _detect_tone(self, text):
        """Detect tone of the email"""
        scores = {}
        
        for tone, patterns in self.tone_indicators.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            scores[tone] = score
        
        # Return tone with highest score, default to 'professional'
        if max(scores.values()) == 0:
            return 'professional'
        
        return max(scores, key=scores.get)
    
    def _detect_urgency(self, text):
        """Calculate urgency score (0.0 to 1.0)"""
        urgent_count = 0
        
        for pattern in self.intent_patterns['urgent']:
            urgent_count += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Normalize to 0-1 scale
        return min(urgent_count / 3.0, 1.0)

    def _extract_name(self, text):
        """Attempt to extract sender's name from email body"""
        # Look for common patterns like "Best regards, John" or "Thanks, Sarah"
        patterns = [
            r'(?:regards|sincerely|thanks|cheers),?\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+(?:here|speaking|writing)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None

    def _extract_keywords(self, text):
        """Extract specific keywords related to the email topic"""
        found_keywords = []
        for category, patterns in self.topic_keywords.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Clean the pattern to get the word
                    word = pattern.replace(r'\b', '').replace('\\', '')
                    found_keywords.append(word)
        return list(set(found_keywords))

    def _query_ollama(self, subject, body, sender_name):
        """Query local Ollama instance if enabled"""
        if not Config.USE_OLLAMA:
            return None
        
        try:
            prompt = f"""
            You are a professional AI Email Assistant. 
            Generate a concise, friendly, and professional response to the following email.
            
            SENDER: {sender_name or 'Someone'}
            SUBJECT: {subject}
            BODY: {body}
            
            RULES:
            1. Keep it under 3-4 sentences.
            2. Reference specific details from their message.
            3. Use a tone that matches the sender.
            4. Do not include subject lines or greetings in your JSON response, just the body text.
            """
            
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': Config.OLLAMA_MODEL,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Ollama query failed: {str(e)}")
            
        return None

    def generate_response(self, analysis):
        """
        Generate intelligent email response based on analysis
        
        Args:
            analysis: Analysis results from analyze_email()
            
        Returns:
            str: Generated response text
        """
        intent = analysis['intent']
        tone = analysis['tone']
        context = analysis['context']
        
        # Check if we should use Ollama (future integration)
        # ollama_response = self._query_ollama(context['subject'], context['original_body'], context['sender_name'])
        # if ollama_response: return ollama_response

        # Build response components
        greeting = self._generate_greeting(tone, context.get('sender_name'))
        
        # Generate intelligent body based on extracted keywords
        keywords = self._extract_keywords(context['original_body'])
        body = self._generate_contextual_body(intent, tone, context, keywords)
        
        closing = self._generate_closing(tone, context.get('is_urgent', False))
        
        # Combine components
        response = f"{greeting}\n\n{body}\n\n{closing}"
        
        return response

    def _generate_contextual_body(self, intent, tone, context, keywords):
        """Generate body text that references specific keywords found in the email"""
        
        # Start with a confirmation of understanding
        topic_ref = ""
        if keywords:
            topic_list = ", ".join(keywords[:2])
            topic_ref = f" regarding your message about {topic_list}"
        
        base_responses = {
            'question': [
                f"Thank you for reaching out with your question{topic_ref}. I've received your email and will get back to you with a detailed response shortly.",
                f"I appreciate your inquiry{topic_ref}. I'm currently reviewing the details and will provide you with a comprehensive answer as soon as possible."
            ],
            'request': [
                f"Thank you for your request{topic_ref}. I've noted the details and will process everything promptly.",
                f"I've received your message{topic_ref} and am currently looking into it for you."
            ],
            'complaint': [
                f"I sincerely apologize for the inconvenience regarding {keywords[0] if keywords else 'this issue'}. Your concern is important, and I'm investigating this right away.",
                f"Thank you for bringing this situation{topic_ref} to my attention. I understand your frustration and am working to resolve it quickly."
            ],
            'support': [
                f"Thank you for reaching out for help with {keywords[0] if keywords else 'your inquiry'}. I'm here to assist and will provide guidance shortly.",
                f"I've received your support request{topic_ref}. I'll get back to you with the technical details you need very soon."
            ],
            'casual': [
                f"Thanks for the email{topic_ref}! I've received your message and will get back to you soon.",
                f"Got your message{topic_ref}. I'll respond with more details shortly."
            ]
        }
        
        body = random.choice(base_responses.get(intent, base_responses['casual']))
        
        # Add dynamic follow-up based on keywords
        if 'login' in keywords or 'password' in keywords:
            body += " For security reasons, please ensure you aren't sharing sensitive credentials in clear text."
        elif 'meeting' in keywords or 'schedule' in keywords:
            body += " I'll check my availability and suggest some times that might work for us."
        elif 'invoice' in keywords or 'pricing' in keywords:
            body += " I'll review our latest records and provide a detailed breakdown for you."
            
        return body
    
    def _generate_greeting(self, tone, sender_name):
        """Generate appropriate greeting"""
        greetings = {
            'formal': [
                f"Dear {sender_name}," if sender_name else "Dear Sir/Madam,",
                f"Hello {sender_name}," if sender_name else "Hello,"
            ],
            'friendly': [
                f"Hi {sender_name}!" if sender_name else "Hi there!",
                f"Hey {sender_name}!" if sender_name else "Hey!",
                f"Hello {sender_name}!" if sender_name else "Hello!"
            ],
            'professional': [
                f"Hello {sender_name}," if sender_name else "Hello,",
                f"Hi {sender_name}," if sender_name else "Hi,"
            ]
        }
        
        return random.choice(greetings.get(tone, greetings['professional']))
    
    def _generate_body(self, intent, tone, context):
        """Generate response body based on intent and tone"""
        
        # Response templates by intent
        templates = {
            'question': [
                "Thank you for reaching out with your question. I've received your email and will get back to you with a detailed response shortly.",
                "I appreciate your inquiry. I'm currently reviewing your question and will provide you with a comprehensive answer as soon as possible.",
                "Thanks for your message. I've noted your question and will respond with the information you need very soon."
            ],
            'request': [
                "Thank you for your request. I've received your message and will process it promptly.",
                "I've received your request and am working on it. You'll hear back from me soon with an update.",
                "Thanks for reaching out. I'm looking into your request and will get back to you shortly."
            ],
            'complaint': [
                "I sincerely apologize for the inconvenience you've experienced. Your concern is important to me, and I'm looking into this matter right away.",
                "Thank you for bringing this to my attention. I understand your frustration and am working to resolve this issue as quickly as possible.",
                "I'm sorry to hear about the problem you're facing. I take this seriously and will investigate immediately to find a solution."
            ],
            'support': [
                "Thank you for reaching out for assistance. I'm here to help and will provide you with the guidance you need shortly.",
                "I've received your support request and am ready to help. I'll get back to you with detailed assistance very soon.",
                "Thanks for contacting me. I understand you need help, and I'll provide you with the support you need as quickly as possible."
            ],
            'casual': [
                "Thanks for your email! I've received your message and will get back to you soon.",
                "Hey! Got your message. I'll respond with more details shortly.",
                "Thanks for reaching out! I'll get back to you very soon."
            ],
            'urgent': [
                "I understand this is urgent. I've received your message and am prioritizing it. You'll hear from me very soon.",
                "Thank you for flagging this as urgent. I'm addressing it immediately and will respond as quickly as possible.",
                "I recognize the urgency of your message. I'm on it and will get back to you right away."
            ]
        }
        
        # Adjust tone
        body = random.choice(templates.get(intent, templates['casual']))
        
        # Add context-specific information
        if context.get('has_question'):
            body += " I'll make sure to address all your questions in my response."
        
        if context.get('is_urgent'):
            body += " I understand the time-sensitive nature of this matter."
        
        return body
    
    def _generate_closing(self, tone, is_urgent):
        """Generate appropriate closing"""
        closings = {
            'formal': [
                "Sincerely,\nAI Assistant",
                "Best regards,\nAI Assistant",
                "Respectfully,\nAI Assistant"
            ],
            'friendly': [
                "Cheers,\nAI Assistant",
                "Best,\nAI Assistant",
                "Talk soon,\nAI Assistant"
            ],
            'professional': [
                "Best regards,\nAI Assistant",
                "Kind regards,\nAI Assistant",
                "Regards,\nAI Assistant"
            ]
        }
        
        closing = random.choice(closings.get(tone, closings['professional']))
        
        if is_urgent:
            closing = "I'll be in touch very soon.\n\n" + closing
        
        return closing


# Singleton instance
email_ai = EmailAI()
