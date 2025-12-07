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
        required = [
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'GEMINI_API_KEY',
            'USDA_API_KEY'
        ]
        
        missing = []
        for key in required:
            if not os.getenv(key):
                missing.append(key)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
