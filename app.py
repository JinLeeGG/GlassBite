"""
GlassBite AI Chatbot - Main Flask Application
A conversational nutrition tracking system using smart glasses + WhatsApp
"""

from flask import Flask, request, jsonify
from config import Config
from models import db, User
from services.meal_processor import process_meal
from services.chatbot_service import handle_chatbot_question
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")


@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'app': 'GlassBite AI Chatbot',
        'version': '1.0.0'
    })


@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Receive messages from WhatsApp via Twilio
    
    Handles:
    - Photos with voice notes (meal logging)
    - Text messages (chatbot questions)
    """
    try:
        # Get data from Twilio
        phone_number = request.form.get('From')
        message_text = request.form.get('Body', '').strip()
        num_media = int(request.form.get('NumMedia', 0))
        
        logger.info(f"Received message from {phone_number}, media: {num_media}")
        
        # If it's a photo (meal logging)
        if num_media > 0:
            image_url = request.form.get('MediaUrl0')
            logger.info(f"Processing meal photo: {image_url}")
            
            # Process in background (in production, use Celery or similar)
            try:
                process_meal(phone_number, message_text, image_url)
            except Exception as e:
                logger.error(f"Error processing meal: {e}", exc_info=True)
        
        # If it's just text (chatbot question)
        elif message_text:
            logger.info(f"Processing chatbot question: {message_text}")
            
            # Get or create user
            user = get_or_create_user(phone_number)
            
            # Check if user has a pending meal waiting for meal type
            from models import Meal
            pending_meal = Meal.query.filter_by(
                user_id=user.id,
                processing_status='analyzed',
                meal_type='pending'
            ).order_by(Meal.timestamp.desc()).first()
            
            if pending_meal:
                # User is responding to meal type question
                from services.meal_processor import meal_processor
                meal_type = meal_processor.extract_meal_type_from_text(message_text)
                
                if meal_type:
                    # Complete the meal processing
                    confirmation_message = meal_processor.complete_meal_processing(user.id, meal_type)
                    
                    if confirmation_message:
                        from services.twilio_service import send_whatsapp_message
                        send_whatsapp_message(phone_number, confirmation_message)
                    else:
                        from services.twilio_service import send_whatsapp_message
                        send_whatsapp_message(
                            phone_number,
                            "Couldn't complete meal logging. Please try again."
                        )
                else:
                    # Invalid meal type response
                    from services.twilio_service import send_whatsapp_message
                    send_whatsapp_message(
                        phone_number,
                        "Please reply with: breakfast, lunch, dinner, or snack. You can also use numbers 1 through 4."
                    )
            # Check if it's a meal type change request
            elif 'change to' in message_text.lower():
                from services.meal_processor import meal_processor
                new_type = meal_processor.extract_meal_type_from_text(message_text)
                
                if new_type:
                    updated_meal = meal_processor.update_meal_type(user.id, new_type)
                    
                    if updated_meal:
                        from services.twilio_service import send_whatsapp_message
                        send_whatsapp_message(
                            phone_number,
                            f"Updated! Your last meal is now logged as {new_type.title()}."
                        )
                    else:
                        from services.twilio_service import send_whatsapp_message
                        send_whatsapp_message(
                            phone_number,
                            "No recent meal found to update."
                        )
                else:
                    from services.twilio_service import send_whatsapp_message
                    send_whatsapp_message(
                        phone_number,
                        "Please specify: 'change to breakfast', 'change to lunch', 'change to dinner', or 'change to snack'"
                    )
            else:
                # Handle the question
                try:
                    response = handle_chatbot_question(user.id, phone_number, message_text)
                    
                    # Send response
                    from services.twilio_service import send_whatsapp_message
                    send_whatsapp_message(phone_number, response)
                except Exception as e:
                    logger.error(f"Error handling question: {e}", exc_info=True)
                    from services.twilio_service import send_whatsapp_message
                    send_whatsapp_message(
                        phone_number,
                        "Sorry, I encountered an error. Please try again."
                    )
        else:
            logger.warning(f"Received empty message from {phone_number}")
        
        # Always return 200 to Twilio
        return '', 200
        
    except Exception as e:
        logger.error(f"Error in webhook: {e}", exc_info=True)
        return '', 200  # Still return 200 to avoid retries


@app.route('/test/meal', methods=['POST'])
def test_meal():
    """Test endpoint for meal processing (development only)"""
    if not app.config['DEBUG']:
        return jsonify({'error': 'Only available in debug mode'}), 403
    
    data = request.json
    phone_number = data.get('phone_number')
    voice_note = data.get('voice_note', '')
    image_url = data.get('image_url')
    
    if not phone_number or not image_url:
        return jsonify({'error': 'phone_number and image_url required'}), 400
    
    try:
        process_meal(phone_number, voice_note, image_url)
        return jsonify({'status': 'processing'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/test/question', methods=['POST'])
def test_question():
    """Test endpoint for chatbot questions (development only)"""
    if not app.config['DEBUG']:
        return jsonify({'error': 'Only available in debug mode'}), 403
    
    data = request.json
    phone_number = data.get('phone_number')
    question = data.get('question')
    
    if not phone_number or not question:
        return jsonify({'error': 'phone_number and question required'}), 400
    
    try:
        user = get_or_create_user(phone_number)
        response = handle_chatbot_question(user.id, phone_number, question)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def stats():
    """Get application statistics"""
    try:
        from models import Meal, FoodItem
        
        total_users = User.query.count()
        total_meals = Meal.query.filter_by(processing_status='completed').count()
        total_foods = FoodItem.query.count()
        
        return jsonify({
            'total_users': total_users,
            'total_meals': total_meals,
            'total_foods': total_foods
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Could not retrieve stats'}), 500


def get_or_create_user(phone_number):
    """Helper function to get or create user"""
    # Ensure phone number has whatsapp: prefix
    if not phone_number.startswith('whatsapp:'):
        phone_number = f'whatsapp:{phone_number}'
    
    user = User.query.filter_by(phone_number=phone_number).first()
    
    if not user:
        user = User(phone_number=phone_number)
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created new user: {phone_number}")
    
    return user


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Validate configuration before starting
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please set all required environment variables in .env file")
        exit(1)
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )
