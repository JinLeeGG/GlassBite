"""
Configuration file for GlassBite AI Chatbot
Loads environment variables and API credentials
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/glassbite_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # Log SQL queries in development
    
    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
    
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    USDA_API_KEY = os.getenv('USDA_API_KEY')
    
    @staticmethod
    def validate():
        """Validate that all required configuration is present"""
        required_keys = {
            'TWILIO_ACCOUNT_SID': 'WhatsApp messaging (Twilio)',
            'TWILIO_AUTH_TOKEN': 'WhatsApp authentication (Twilio)',
            'GEMINI_API_KEY': 'Image analysis (Google Gemini AI)',
            'USDA_API_KEY': 'Nutrition data (USDA FoodData Central)'
        }
        
        missing = []
        for key, service in required_keys.items():
            if not os.getenv(key):
                missing.append(f"{key} ({service})")
        
        if missing:
            error_msg = f"Missing required environment variables:\n"
            for item in missing:
                error_msg += f"  - {item}\n"
            raise ValueError(error_msg)
    
    @staticmethod
    def validate_service(service_name):
        """Validate configuration for a specific service
        
        Args:
            service_name: 'twilio', 'gemini', or 'usda'
        
        Raises:
            ValueError: If required keys for the service are missing
        """
        service_keys = {
            'twilio': ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN'],
            'gemini': ['GEMINI_API_KEY'],
            'usda': ['USDA_API_KEY']
        }
        
        if service_name not in service_keys:
            raise ValueError(f"Unknown service: {service_name}")
        
        missing = [key for key in service_keys[service_name] if not os.getenv(key)]
        
        if missing:
            raise ValueError(
                f"Cannot initialize {service_name.upper()} service. "
                f"Missing: {', '.join(missing)}"
            )
        
        return True
