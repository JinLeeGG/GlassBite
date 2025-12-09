"""
Meal Processing Service
Handles the complete pipeline: Image → Gemini → USDA → Database
"""

import logging
from datetime import datetime, date
from models import db, User, Meal, FoodItem, FoodNutrient, DailySummary
from services.gemini_service import analyze_food_image, detect_non_food_image
from services.usda_service import get_nutrition_data
from services.twilio_service import send_whatsapp_message, get_twilio_auth

logger = logging.getLogger(__name__)

class MealProcessor:
    """Service for processing meal photos"""
    
    def process_meal(self, phone_number, voice_note_text, image_url):
        """
        Complete pipeline: Image → Gemini → USDA → Database
        
        Args:
            phone_number: User's phone number
            voice_note_text: User's voice description of the meal
            image_url: URL of the meal photo
        
        Returns:
            Success message or error message
        """
        try:
            # 1. Get or create user
            user = self.get_or_create_user(phone_number)
            
            # 2. Send immediate response
            send_whatsapp_message(phone_number, "Analyzing your meal...")
            
            # 3. Create meal record
            meal = Meal(
                user_id=user.id,
                voice_note_text=voice_note_text,
                image_url=image_url,
                processing_status='pending',
                meal_type=self.determine_meal_type(),
                timestamp=datetime.now()
            )
            db.session.add(meal)
            db.session.commit()
            
            # 4. Analyze image with Gemini
            logger.info(f"Processing meal {meal.id} for user {user.id}")
            detected_foods = analyze_food_image(
                image_url,
                voice_note_text,
                get_twilio_auth()
            )
            
            # Check if image contains food
            if detect_non_food_image(detected_foods):
                meal.processing_status = 'failed'
                db.session.commit()
                send_whatsapp_message(
                    phone_number,
                    "I don't see any food in this image. Please send a clear photo of your meal."
                )
                return
            
            # 5. Get nutrition for each food
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            total_fiber = 0
            total_sugar = 0
            total_sodium = 0
            food_names = []
            low_confidence_foods = []
            
            for food_data in detected_foods:
                nutrition = get_nutrition_data(
                    food_data['name'],
                    food_data['portion_grams']
                )
                
                if nutrition:
                    # Save FoodItem to database
                    food_item = FoodItem(
                        meal_id=meal.id,
                        name=food_data['name'],
                        portion_size_grams=food_data['portion_grams'],
                        confidence_score=food_data['confidence']
                    )
                    db.session.add(food_item)
                    db.session.flush()  # Get food_item.id
                    
                    # Save detailed nutrients to FoodNutrient table
                    extra_nutrients = nutrition.get('extra_nutrients', {})
                    
                    food_nutrient = FoodNutrient(
                        food_item_id=food_item.id,
                        # Tier 1: Essential Macronutrients
                        calories=nutrition.get('calories'),
                        protein_g=nutrition.get('protein_g'),
                        carbs_g=nutrition.get('carbs_g'),
                        fat_g=nutrition.get('fat_g'),
                        fiber_g=nutrition.get('fiber_g'),
                        sugar_g=nutrition.get('sugar_g'),
                        sodium_mg=nutrition.get('sodium_mg'),
                        potassium_mg=extra_nutrients.get('potassium_mg'),
                        calcium_mg=extra_nutrients.get('calcium_mg'),
                        iron_mg=extra_nutrients.get('iron_mg'),
                        # Tier 2: Important Micronutrients
                        vitamin_c_mg=extra_nutrients.get('vitamin_c_mg'),
                        vitamin_d_ug=extra_nutrients.get('vitamin_d_ug'),
                        vitamin_a_ug=extra_nutrients.get('vitamin_a_ug'),
                        vitamin_b12_ug=extra_nutrients.get('vitamin_b12_ug'),
                        magnesium_mg=extra_nutrients.get('magnesium_mg'),
                        zinc_mg=extra_nutrients.get('zinc_mg'),
                        phosphorus_mg=extra_nutrients.get('phosphorus_mg'),
                        cholesterol_mg=extra_nutrients.get('cholesterol_mg'),
                        # Tier 3: Supplementary Nutrients
                        saturated_fat_g=extra_nutrients.get('saturated_fat_g'),
                        monounsaturated_fat_g=extra_nutrients.get('monounsaturated_fat_g'),
                        polyunsaturated_fat_g=extra_nutrients.get('polyunsaturated_fat_g'),
                        folate_ug=extra_nutrients.get('folate_ug'),
                        vitamin_b6_mg=extra_nutrients.get('vitamin_b6_mg'),
                        choline_mg=extra_nutrients.get('choline_mg'),
                        selenium_ug=extra_nutrients.get('selenium_ug')
                    )
                    db.session.add(food_nutrient)
                    
                    # Accumulate totals
                    total_calories += nutrition['calories']
                    total_protein += nutrition['protein_g']
                    total_carbs += nutrition['carbs_g']
                    total_fat += nutrition['fat_g']
                    total_fiber += nutrition.get('fiber_g', 0)
                    total_sugar += nutrition.get('sugar_g', 0)
                    total_sodium += nutrition.get('sodium_mg', 0)
                    
                    food_names.append(
                        f"{food_data['name']} ({food_data['portion_grams']:.0f}g)"
                    )
                    
                    # Track low confidence detections
                    if food_data['confidence'] < 0.6:
                        low_confidence_foods.append(food_data['name'])
            
            # 6. Mark meal as analyzed (waiting for meal type)
            meal.processing_status = 'analyzed'
            meal.meal_type = 'pending'  # Waiting for user input
            db.session.commit()
            
            # 7. Ask user for meal type (voice-friendly, concise)
            food_list = "\n".join([f"{name}" for name in food_names])
            message = f"Got it! I detected:\n{food_list}\n"
            message += f"\nTotal: {total_calories:.0f} calories, {total_protein:.0f}g protein\n\n"
            message += "Is this breakfast, lunch, dinner, or snack?"
            
            send_whatsapp_message(phone_number, message)
            logger.info(f"Meal {meal.id} analyzed, waiting for meal type confirmation")
            
        except Exception as e:
            logger.error(f"Error processing meal: {e}", exc_info=True)
            
            # Mark meal as failed
            if 'meal' in locals():
                meal.processing_status = 'failed'
                db.session.commit()
            
            send_whatsapp_message(
                phone_number,
                "Sorry, I couldn't analyze your meal. Please try again with better lighting."
            )
    
    def get_or_create_user(self, phone_number):
        """Get existing user or create new one"""
        
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
    
    def determine_meal_type(self):
        """Determine meal type based on time of day"""
        hour = datetime.now().hour
        
        if 5 <= hour < 11:
            return 'breakfast'
        elif 11 <= hour < 15:
            return 'lunch'
        elif 15 <= hour < 18:
            return 'snack'
        elif 18 <= hour <= 23:
            return 'dinner'
        else:
            return 'snack'
    
    def extract_meal_type_from_text(self, text):
        """Extract meal type from user text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # English keywords
        if 'breakfast' in text_lower or 'morning' in text_lower:
            return 'breakfast'
        elif 'lunch' in text_lower or 'noon' in text_lower:
            return 'lunch'
        elif 'dinner' in text_lower or 'supper' in text_lower or 'evening' in text_lower:
            return 'dinner'
        elif 'snack' in text_lower:
            return 'snack'
        
        return None
    
    def complete_meal_processing(self, user_id, meal_type):
        """Complete meal processing after receiving meal type from user"""
        # Find the most recent analyzed meal waiting for confirmation
        meal = Meal.query.filter_by(
            user_id=user_id,
            processing_status='analyzed',
            meal_type='pending'
        ).order_by(Meal.timestamp.desc()).first()
        
        if not meal:
            return None
        
        # Update meal type and mark as completed
        meal.meal_type = meal_type
        meal.processing_status = 'completed'
        
        # Get food items for this meal
        food_items = FoodItem.query.filter_by(meal_id=meal.id).all()
        
        # Calculate totals from FoodNutrient table
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0
        total_sugar = 0
        total_sodium = 0
        
        for item in food_items:
            if item.nutrients:
                total_calories += item.nutrients.calories or 0
                total_protein += item.nutrients.protein_g or 0
                total_carbs += item.nutrients.carbs_g or 0
                total_fat += item.nutrients.fat_g or 0
                total_fiber += item.nutrients.fiber_g or 0
                total_sugar += item.nutrients.sugar_g or 0
                total_sodium += item.nutrients.sodium_mg or 0
        
        food_names = [f"{item.name} ({item.portion_size_grams:.0f}g)" for item in food_items]
        low_confidence_foods = [item.name for item in food_items if item.confidence_score < 0.6]
        
        db.session.commit()
        
        # Update daily summary
        self.update_daily_summary(
            user_id,
            meal.timestamp.date(),
            total_calories,
            total_protein,
            total_carbs,
            total_fat,
            total_fiber,
            total_sugar,
            total_sodium
        )
        
        # Get updated daily totals and goal
        daily_totals = self.get_daily_totals(user_id)
        active_goal = self.get_active_goal(user_id)
        
        # Format confirmation message
        message = self.format_meal_confirmation(
            food_items,
            total_calories,
            total_protein,
            total_carbs,
            total_fat,
            daily_totals,
            active_goal,
            low_confidence_foods,
            meal_type
        )
        
        logger.info(f"Completed meal {meal.id} as {meal_type}")
        return message
    
    def update_meal_type(self, user_id, new_meal_type):
        """Update the most recent meal's type"""
        meal = Meal.query.filter_by(
            user_id=user_id,
            processing_status='completed'
        ).order_by(Meal.timestamp.desc()).first()
        
        if not meal:
            return None
        
        old_type = meal.meal_type
        meal.meal_type = new_meal_type
        db.session.commit()
        
        logger.info(f"Updated meal {meal.id} type from {old_type} to {new_meal_type}")
        return meal
    
    def update_daily_summary(self, user_id, target_date, calories, protein,
                            carbs, fat, fiber, sugar, sodium):
        """Update or create daily summary"""
        
        summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=target_date
        ).first()
        
        if not summary:
            summary = DailySummary(
                user_id=user_id,
                date=target_date,
                total_calories=0,
                total_protein=0,
                total_carbs=0,
                total_fat=0,
                total_fiber=0,
                total_sugar=0,
                total_sodium=0,
                meal_count=0
            )
            db.session.add(summary)
        
        # Add to totals
        summary.total_calories += calories
        summary.total_protein += protein
        summary.total_carbs += carbs
        summary.total_fat += fat
        summary.total_fiber += fiber
        summary.total_sugar += sugar
        summary.total_sodium += sodium
        summary.meal_count += 1
        
        db.session.commit()
        logger.info(f"Updated daily summary for user {user_id}, date {target_date}")
    
    def get_daily_totals(self, user_id):
        """Get today's nutrition totals"""
        
        summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=datetime.now().date()
        ).first()
        
        if not summary:
            return {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0,
                'sugar': 0,
                'sodium': 0
            }
        
        return {
            'calories': summary.total_calories,
            'protein': summary.total_protein,
            'carbs': summary.total_carbs,
            'fat': summary.total_fat,
            'fiber': summary.total_fiber,
            'sugar': summary.total_sugar,
            'sodium': summary.total_sodium
        }
    
    def get_active_goal(self, user_id):
        """Get user's active calorie goal"""
        from models import Goal
        
        goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type='calorie_target',
            is_active=True
        ).first()
        
        return goal
    
    def format_meal_confirmation(self, food_items, total_calories, total_protein,
                                 total_carbs, total_fat, daily_totals, goal, 
                                 low_confidence_foods, meal_type):
        """Create well-formatted confirmation message (voice-friendly)"""
        
        meal_name = meal_type.title()
        
        message = f"Meal logged as {meal_name}.\n"
        message += "Wrong? Reply: 'change to breakfast', 'lunch', 'dinner', or 'snack'\n\n"
        
        # Food list with individual nutrients (Tier 1: calories, protein, carbs, fat, fiber, sugar, sodium)
        message += "You had:\n"
        meal_fiber_total = 0
        meal_sugar_total = 0
        meal_sodium_total = 0
        
        for item in food_items:
            message += f"{item.name} ({item.portion_size_grams:.0f}g)\n"
            if item.nutrients:
                # Extract fiber and sugar for carbs context
                fiber = item.nutrients.fiber_g or 0
                sugar = item.nutrients.sugar_g or 0
                sodium = item.nutrients.sodium_mg or 0
                
                meal_fiber_total += fiber
                meal_sugar_total += sugar
                meal_sodium_total += sodium
                
                # Format carbs with fiber/sugar context
                carbs_detail = f"{item.nutrients.carbs_g:.0f}g carbs"
                if fiber > 0 and sugar > 0:
                    carbs_detail += f" ({fiber:.0f}g fiber, {sugar:.0f}g sugar)"
                elif fiber > 0:
                    carbs_detail += f" ({fiber:.0f}g fiber)"
                elif sugar > 0:
                    carbs_detail += f" ({sugar:.0f}g sugar)"
                
                message += f"  {item.nutrients.calories:.0f} cal | {item.nutrients.protein_g:.0f}g protein | {carbs_detail} | {item.nutrients.fat_g:.0f}g fat | {sodium:.0f}mg sodium\n"
        
        # This meal totals with fiber context
        message += f"\n--- This Meal Total ---\n"
        carbs_meal_detail = f"{total_carbs:.0f}g carbs"
        if meal_fiber_total > 0:
            carbs_meal_detail += f" ({meal_fiber_total:.0f}g fiber)"
        message += f"{total_calories:.0f} cal | {total_protein:.0f}g protein | {carbs_meal_detail} | {total_fat:.0f}g fat | {meal_sodium_total:.0f}mg sodium\n"
        
        # Daily totals with fiber context
        message += f"\n--- Today's Total ---\n"
        daily_fiber = daily_totals.get('fiber', 0)
        daily_sodium = daily_totals.get('sodium', 0)
        carbs_daily_detail = f"{daily_totals['carbs']:.0f}g carbs"
        if daily_fiber > 0:
            carbs_daily_detail += f" ({daily_fiber:.0f}g fiber)"
        message += f"{daily_totals['calories']:.0f} cal | {daily_totals['protein']:.0f}g protein | {carbs_daily_detail} | {daily_totals['fat']:.0f}g fat | {daily_sodium:.0f}mg sodium\n"
        
        # Goal progress
        if goal:
            remaining = goal.target_value - daily_totals['calories']
            percentage = (daily_totals['calories'] / goal.target_value) * 100
            
            message += f"\nGoal: {goal.target_value:.0f} calories\n"
            message += f"Progress: {percentage:.0f}%\n"
            
            if remaining > 0:
                message += f"{remaining:.0f} calories remaining\n"
            else:
                message += f"{abs(remaining):.0f} calories over goal\n"
            
            # Sodium warning if high
            daily_sodium = daily_totals.get('sodium', 0)
            if daily_sodium > 2300:
                message += f"\nHigh sodium intake today (recommended: 2300mg daily)."
            
            # Motivational message
            if percentage < 50:
                message += "\nKeep going!"
            elif percentage < 90:
                message += "\nGreat progress!"
            elif percentage < 110:
                message += "\nAlmost there!"
            else:
                message += "\nOver goal. Consider lighter meals."
        
        # Low confidence warning
        if low_confidence_foods:
            message += f"\n\nNot completely sure about: {', '.join(low_confidence_foods[:2])}"
            message += "\nSend a clearer photo next time for better accuracy."
        
        return message


# Singleton instance
meal_processor = MealProcessor()

def process_meal(phone_number, voice_note_text, image_url):
    """Helper function for meal processing"""
    return meal_processor.process_meal(phone_number, voice_note_text, image_url)
