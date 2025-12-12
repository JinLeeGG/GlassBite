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
from services.allergen_service import detect_ingredients, validate_meal, parse_user_restrictions, allergen_service
from database_utils import get_or_create_user

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
            user = get_or_create_user(phone_number)
            
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
                        # Parse user dietary restrictions FIRST
            user_restrictions = parse_user_restrictions(user.dietary_restrictions or '')
            logger.info(f"User restrictions: {user_restrictions}")
            
            # IMMEDIATE ALLERGEN DETECTION (before USDA lookup)
            logger.info("Detecting allergens in detected foods...")
            for food in detected_foods:
                ingredients = food.get('ingredients', [])
                allergen_info = detect_ingredients(food['name'], ingredients)
                food['detected_allergens'] = allergen_info['detected_allergens']
                food['detected_ingredients'] = allergen_info['detected_ingredients']
                logger.info(f"Food '{food['name']}' allergens: {food['detected_allergens']}")
            
            # VALIDATE MEAL AGAINST USER RESTRICTIONS
            validation_result = validate_meal(detected_foods, user_restrictions)
            
            # BLOCK MEAL IF ALLERGEN VIOLATIONS DETECTED
            if validation_result['has_violations']:
                logger.warning(f"Allergen violations detected for user {user.id} - BLOCKING MEAL")
                
                # Mark meal as failed (not logged)
                meal.processing_status = 'failed'
                db.session.commit()
                
                # Send allergen alert
                alert_message = allergen_service.format_alert_message(validation_result)
                
                # Add blocking message
                alert_message += "\n\n🚫 MEAL NOT LOGGED\n"
                alert_message += "This meal was not added to your diary due to dietary restriction violations.\n\n"
                alert_message += "If this was incorrect, please update your restrictions with:\n"
                alert_message += '"Remove [restriction name]"'
                
                send_whatsapp_message(phone_number, alert_message)
                logger.info("Allergen alert sent and meal processing stopped")
                
                # STOP PROCESSING - Do not log meal to database
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
        return message, meal.id
    
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
    
    def get_meal_details(self, meal_id, user_id):
        """Get detailed information for a specific meal (for 'detail' command)"""
        meal = Meal.query.filter_by(id=meal_id, user_id=user_id).first()
        
        if not meal:
            return None
        
        # Get food items for this meal
        food_items = FoodItem.query.filter_by(meal_id=meal.id).all()
        
        if not food_items:
            return None
        
        # Calculate totals
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
        
        # Get daily totals and goal
        daily_totals = self.get_daily_totals(user_id)
        active_goal = self.get_active_goal(user_id)
        
        # Format detailed messages
        messages = self.format_meal_details(
            food_items,
            total_calories,
            total_protein,
            total_carbs,
            total_fat,
            total_fiber,
            total_sugar,
            total_sodium,
            daily_totals,
            active_goal,
            meal.meal_type
        )
        
        return messages
    
    def format_meal_confirmation(self, food_items, total_calories, total_protein,
                                 total_carbs, total_fat, daily_totals, goal, 
                                 low_confidence_foods, meal_type, allergen_summary=None):
        """Create concise confirmation message with allergen warnings"""
        
        meal_name = meal_type.title()
        item_count = len(food_items)
        
        message = f"✓ {meal_name} logged ({item_count} items)\n"
        
        # Add allergen warning prominently if present
        if allergen_summary:
            message += f"\n🚨 {allergen_summary}\n"
        message += f"Meal: {total_calories:.0f} cal | {total_protein:.0f}g protein | {total_carbs:.0f}g carbs\n"
        message += f"Today: {daily_totals['calories']:.0f} cal | {daily_totals['protein']:.0f}g protein | {daily_totals['carbs']:.0f}g carbs\n"
        
        # Goal progress (compact)
        if goal:
            remaining = goal.target_value - daily_totals['calories']
            percentage = (daily_totals['calories'] / goal.target_value) * 100
            
            status = "+" if remaining < 0 else ""
            message += f"\nGoal: {goal.target_value:.0f} cal ({percentage:.0f}%) {status}{abs(remaining):.0f} {'over' if remaining < 0 else 'left'}"
            
            # Brief status emoji
            if percentage < 90:
                message += " 💪"
            elif percentage < 110:
                message += " 🎯"
            else:
                message += " ⚠️"
            message += "\n"
        
        # Warnings (compact)
        warnings = []
        daily_sodium = daily_totals.get('sodium', 0)
        if daily_sodium > 2300:
            warnings.append("High sodium")
        if low_confidence_foods:
            warnings.append(f"Unsure: {low_confidence_foods[0]}")
        
        if warnings:
            message += f"\n⚠️ {' | '.join(warnings)}\n"
        
        # Offer detailed breakdown
        message += f"\nReply 'detail' or 'list' for full breakdown"
        if item_count > 10:
            total_messages = (item_count + 4) // 5  # 5 items per message
            message += f" ({total_messages} messages)"
        message += "\nChange type? Reply: breakfast/lunch/dinner/snack"
        
        return message
    
    def format_meal_details(self, food_items, total_calories, total_protein,
                           total_carbs, total_fat, total_fiber, total_sugar,
                           total_sodium, daily_totals, goal, meal_type):
        """Create detailed breakdown split into multiple messages (5 items per message)"""
        
        ITEMS_PER_MESSAGE = 5
        messages = []
        total_batches = (len(food_items) + ITEMS_PER_MESSAGE - 1) // ITEMS_PER_MESSAGE
        
        for batch_num in range(total_batches):
            start_idx = batch_num * ITEMS_PER_MESSAGE
            end_idx = min(start_idx + ITEMS_PER_MESSAGE, len(food_items))
            batch_items = food_items[start_idx:end_idx]
            
            message = f"{meal_type.title()} Details [{batch_num + 1}/{total_batches}]\n\n"
            
            for item in batch_items:
                n = item.nutrients
                if n:
                    message += f"{item.name} ({item.portion_size_grams:.0f}g)\n"
                    message += f"{n.calories:.0f} cal | {n.protein_g:.0f}g protein | {n.carbs_g:.0f}g carbs | {n.fat_g:.0f}g fat\n"
                    message += f"Fiber: {n.fiber_g:.0f}g | Sugar: {n.sugar_g:.0f}g | Sodium: {n.sodium_mg:.0f}mg\n\n"
            
            # Last message includes totals
            if batch_num == total_batches - 1:
                message += "═══════════════════\n"
                message += f"MEAL TOTAL:\n"
                message += f"{total_calories:.0f} cal | {total_protein:.0f}g protein | {total_carbs:.0f}g carbs | {total_fat:.0f}g fat\n"
                message += f"Fiber: {total_fiber:.0f}g | Sugar: {total_sugar:.0f}g | Sodium: {total_sodium:.0f}mg\n\n"
                
                message += f"TODAY'S TOTAL:\n"
                message += f"{daily_totals['calories']:.0f} cal | {daily_totals['protein']:.0f}g protein | {daily_totals['carbs']:.0f}g carbs | {daily_totals['fat']:.0f}g fat\n"
                
                if goal and goal.target_value:
                    remaining = goal.target_value - daily_totals['calories']
                    percentage = (daily_totals['calories'] / goal.target_value) * 100
                    message += f"\nGoal: {goal.target_value:.0f} cal → {percentage:.0f}% "
                    if remaining < 0:
                        message += f"(Over by {abs(remaining):.0f} cal) ⚠️\n"
                    else:
                        message += f"({remaining:.0f} cal left) 💪\n"
                
                # Final warnings
                daily_sodium = daily_totals.get('sodium', 0)
                if daily_sodium > 2300:
                    message += f"\nHigh sodium warning: {daily_sodium:.0f}mg (Recommended: <2300mg)"
            
            messages.append(message)
        
        return messages


# Singleton instance
meal_processor = MealProcessor()

def process_meal(phone_number, voice_note_text, image_url):
    """Helper function for meal processing"""
    return meal_processor.process_meal(phone_number, voice_note_text, image_url)
