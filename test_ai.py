
from ai_processor import email_ai

def test_ai():
    test_cases = [
        {
            "sender": "John Smith",
            "subject": "Login issues",
            "body": "Hey, I'm having trouble with the login page. It keeps saying error 404. Can you help with my password?"
        },
        {
            "sender": "Alice Johnson",
            "subject": "Invoice for project X",
            "body": "Hi, I haven't received the invoice for last month. Can you check the pricing and send it asap?"
        },
        {
            "sender": "Bob",
            "subject": "Meeting tomorrow",
            "body": "Can we schedule a time for a quick meeting on our calendar tomorrow?"
        }
    ]
    
    print("=== AI RESPONSE VERIFICATION ===\n")
    
    for i, case in enumerate(test_cases, 1):
        print(f"TEST CASE {i}:")
        print(f"Sender: {case['sender']}")
        print(f"Body: {case['body']}")
        
        analysis = email_ai.analyze_email(case['subject'], case['body'], case['sender'])
        response = email_ai.generate_response(analysis)
        
        print(f"Generated Response:\n{'-'*20}\n{response}\n{'-'*20}\n")

if __name__ == "__main__":
    test_ai()
