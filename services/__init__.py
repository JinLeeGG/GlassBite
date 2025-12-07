"""
GlassBite Services Module
Provides easy imports for all service components
"""

from .gemini_service import analyze_food_image, detect_non_food_image
from .usda_service import get_nutrition_data
from .twilio_service import send_whatsapp_message, get_twilio_auth
from .chatbot_service import handle_chatbot_question
from .meal_processor import process_meal

__all__ = [
    'analyze_food_image',
    'detect_non_food_image',
    'get_nutrition_data',
    'send_whatsapp_message',
    'get_twilio_auth',
    'handle_chatbot_question',
    'process_meal'
]
