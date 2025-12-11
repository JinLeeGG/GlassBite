"""
Test meal details functionality with the 12-item lunch
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Meal, FoodItem, FoodNutrient
from services.meal_processor import meal_processor
from services.chatbot_service import chatbot_service
from datetime import datetime

def test_lunch_details():
    """Test the detail command with the 12-item lunch"""
    
    with app.app_context():
        # 1. Get user
        test_phone = "whatsapp:+12233392848"
        user = User.query.filter_by(phone_number=test_phone).first()
        
        if not user:
            print("❌ User not found")
            return
        
        print(f"✓ Found user: {user.id}")
        
        # 2. Get lunch meal (meal_id = 205 based on logs)
        lunch_meal = Meal.query.filter_by(id=205, user_id=user.id).first()
        
        if not lunch_meal:
            print("❌ Lunch meal (ID=205) not found")
            # Try to find any lunch
            lunch_meal = Meal.query.filter_by(
                user_id=user.id,
                meal_type='lunch',
                processing_status='completed'
            ).order_by(Meal.timestamp.desc()).first()
            
            if not lunch_meal:
                print("❌ No lunch meals found")
                return
        
        print(f"✓ Found lunch meal: ID={lunch_meal.id}, Type={lunch_meal.meal_type}")
        
        # 3. Get food items
        food_items = FoodItem.query.filter_by(meal_id=lunch_meal.id).all()
        print(f"✓ Found {len(food_items)} food items:")
        
        for item in food_items:
            print(f"  - {item.name} ({item.portion_size_grams}g)")
        
        # 4. Test get_meal_details
        print("\n" + "="*60)
        print("TESTING DETAIL MESSAGES (5 items per message)")
        print("="*60)
        
        try:
            detail_messages = meal_processor.get_meal_details(lunch_meal.id, user.id)
            
            if detail_messages:
                print(f"\n✓ Generated {len(detail_messages)} messages\n")
                
                for i, msg in enumerate(detail_messages, 1):
                    print(f"\n{'='*60}")
                    print(f"MESSAGE {i}/{len(detail_messages)}")
                    print(f"{'='*60}")
                    print(msg)
                    print(f"\nLength: {len(msg)} chars")
                    
                    # Check if within Twilio limit
                    if len(msg) > 1600:
                        print(f"⚠️ WARNING: Exceeds 1600 char limit!")
                    else:
                        print(f"✓ Safe (under 1600 limit)")
            else:
                print("❌ No detail messages returned")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_lunch_details()
