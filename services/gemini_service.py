"""
Gemini AI Service for food image analysis
Uses Google's Gemini 1.5 Flash model to identify foods and estimate portions
"""

import google.generativeai as genai
import requests
import json
import logging
from PIL import Image
from io import BytesIO
from config import Config

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=Config.GEMINI_API_KEY)

class GeminiService:
    """Service for analyzing food images with Gemini AI"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro-latest')
    
    def analyze_food_image(self, image_url, voice_note_text, twilio_auth):
        """
        Analyze a food image and return structured food data
        
        Args:
            image_url: URL of the food image from Twilio
            voice_note_text: User's description of the meal
            twilio_auth: Tuple of (account_sid, auth_token) for authentication
        
        Returns:
            List of detected foods with structure:
            [
                {
                    "name": "grilled chicken breast",
                    "portion_grams": 150,
                    "confidence": 0.92
                },
                ...
            ]
        """
        try:
            # Download image from Twilio
            logger.info(f"Downloading image from: {image_url}")
            response = requests.get(image_url, auth=twilio_auth, timeout=30)
            response.raise_for_status()
            
            # Load image
            image = Image.open(BytesIO(response.content))
            
            # Create detailed prompt for Gemini
            prompt = self._create_analysis_prompt(voice_note_text)
            
            # Generate content with Gemini
            logger.info("Sending image to Gemini for analysis...")
            response = self.model.generate_content([prompt, image])
            
            # Parse JSON response
            foods = self._parse_gemini_response(response.text)
            
            logger.info(f"Detected {len(foods)} food items")
            return foods
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            raise Exception("Could not download food image")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.error(f"Raw response: {response.text}")
            raise Exception("AI returned invalid response format")
        
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise
    
    def _create_analysis_prompt(self, voice_note_text):
        """Create the prompt for Gemini analysis"""
        
        user_context = f'User described it as: "{voice_note_text}"' if voice_note_text else "No user description provided."
        
        prompt = f"""Analyze this food image. {user_context}

Identify all visible food items and estimate portion sizes in grams.

CRITICAL: Return ONLY a valid JSON array. No markdown formatting, no code blocks, no explanations.

Format:
[
  {{
    "name": "specific food name (e.g., grilled chicken breast, not just chicken)",
    "portion_grams": estimated_weight_in_grams,
    "confidence": score_between_0_and_1
  }}
]

Guidelines:
- Be specific: "grilled chicken breast" not "chicken"
- Use standard serving sizes as reference:
  * Standard plate diameter = 10 inches (25cm)
  * Fist = ~150g, Palm = ~100g, Thumb = ~30g
- Consider visible indicators: plate coverage, thickness, density
- Estimate conservatively - better to underestimate than overestimate
- Common portion examples:
  * Chicken breast: 120-180g
  * Rice (1 cup cooked): 150-200g
  * Vegetables (side): 75-150g
  * Steak: 200-250g
  * Pasta (cooked): 140-200g

Return ONLY the JSON array, starting with [ and ending with ]."""

        return prompt
    
    def _parse_gemini_response(self, response_text):
        """
        Parse Gemini's response and extract JSON
        
        Args:
            response_text: Raw text response from Gemini
        
        Returns:
            List of food dictionaries
        """
        # Clean up response - remove markdown code blocks if present
        cleaned = response_text.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith('```'):
            # Find the actual JSON content
            lines = cleaned.split('\n')
            json_lines = []
            in_code_block = False
            
            for line in lines:
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or (not line.startswith('```')):
                    json_lines.append(line)
            
            cleaned = '\n'.join(json_lines).strip()
        
        # Parse JSON
        try:
            foods = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON array from text
            start_idx = cleaned.find('[')
            end_idx = cleaned.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = cleaned[start_idx:end_idx]
                foods = json.loads(json_str)
            else:
                raise
        
        # Validate structure
        if not isinstance(foods, list):
            raise ValueError("Response is not a list")
        
        for food in foods:
            if not all(k in food for k in ['name', 'portion_grams', 'confidence']):
                raise ValueError(f"Food item missing required fields: {food}")
        
        return foods
    
    def detect_non_food_image(self, detected_foods):
        """
        Check if image actually contains food
        
        Args:
            detected_foods: List of detected food items
        
        Returns:
            True if image doesn't appear to contain food
        """
        if not detected_foods or len(detected_foods) == 0:
            return True
        
        # Check average confidence
        avg_confidence = sum(f['confidence'] for f in detected_foods) / len(detected_foods)
        
        if avg_confidence < 0.3:
            return True
        
        return False


# Singleton instance
gemini_service = GeminiService()

def analyze_food_image(image_url, voice_note_text, twilio_auth):
    """Helper function for food image analysis"""
    return gemini_service.analyze_food_image(image_url, voice_note_text, twilio_auth)

def detect_non_food_image(detected_foods):
    """Helper function to check if image contains food"""
    return gemini_service.detect_non_food_image(detected_foods)
