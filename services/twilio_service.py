"""
Twilio Service for WhatsApp messaging
Handles sending messages to users
"""

from twilio.rest import Client
from config import Config
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    """Service for sending WhatsApp messages via Twilio"""
    
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_WHATSAPP_NUMBER
    
    def send_message(self, to_phone_number, message_text):
        """
        Send a WhatsApp message to a user
        
        Args:
            to_phone_number: Phone number with whatsapp: prefix
            message_text: Message content to send
        
        Returns:
            Message SID if successful, None otherwise
        """
        try:
            # Ensure phone number has whatsapp: prefix
            if not to_phone_number.startswith('whatsapp:'):
                to_phone_number = f'whatsapp:{to_phone_number}'
            
            message = self.client.messages.create(
                from_=self.from_number,
                body=message_text,
                to=to_phone_number
            )
            
            logger.info(f"Message sent to {to_phone_number}: {message.sid}")
            return message.sid
            
        except Exception as e:
            logger.error(f"Failed to send message to {to_phone_number}: {e}")
            return None
    
    def get_twilio_auth(self):
        """
        Get Twilio authentication tuple for downloading media
        
        Returns:
            Tuple of (account_sid, auth_token)
        """
        return (Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)


# Singleton instance
twilio_service = TwilioService()

def send_whatsapp_message(phone_number, message):
    """Helper function for easy message sending"""
    return twilio_service.send_message(phone_number, message)

def get_twilio_auth():
    """Helper function to get auth credentials"""
    return twilio_service.get_twilio_auth()
