"""
Test meal details functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Meal, FoodItem, FoodNutrient
from services.meal_processor import meal_processor
from services.chatbot_service import chatbot_service
from datetime import datetime

def test_meal_details():
    """Test the detail command functionality"""
    
    with app.app_context():
        # 1. Get or create test user
        test_phone = "whatsapp:+12233392848"
        user = User.query.filter_by(phone_number=test_phone).first()
        
        if not user:
            print("❌ User not found. Please log a meal first.")
            return
        
        print(f"✓ Found user: {user.id}")
        
        # 2. Get most recent completed meal
        recent_meal = Meal.query.filter_by(
            user_id=user.id,
            processing_status='completed'
        ).order_by(Meal.timestamp.desc()).first()
        
        if not recent_meal:
            print("❌ No completed meals found")
            return
        
        print(f"✓ Found recent meal: ID={recent_meal.id}, Type={recent_meal.meal_type}")
        
        # 3. Get food items
        food_items = FoodItem.query.filter_by(meal_id=recent_meal.id).all()
        print(f"✓ Found {len(food_items)} food items")
        
        for item in food_items[:3]:  # Show first 3
            print(f"  - {item.name} ({item.portion_size_grams}g)")
        
        # 4. Test classify_question
        print("\n--- Testing classify_question ---")
        question_type, params = chatbot_service.classify_question("detail")
        print(f"Question type: {question_type}")
        print(f"Params: {params}")
        
        # 5. Test handle_meal_details
        print("\n--- Testing handle_meal_details ---")
        try:
            result = chatbot_service.handle_meal_details(user.id)
            
            if isinstance(result, list):
                print(f"✓ Got {len(result)} messages")
                for i, msg in enumerate(result, 1):
                    print(f"\n=== Message {i}/{len(result)} ===")
                    print(msg)
                    print(f"Length: {len(msg)} chars")
            else:
                print(f"❌ Expected list, got: {type(result)}")
                print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. Test get_meal_details directly
        print("\n--- Testing get_meal_details directly ---")
        try:
            detail_messages = meal_processor.get_meal_details(recent_meal.id, user.id)
            
            if detail_messages:
                print(f"✓ Got {len(detail_messages)} detail messages")
                for i, msg in enumerate(detail_messages, 1):
                    print(f"\n=== Detail Message {i}/{len(detail_messages)} ===")
                    print(msg[:200] + "..." if len(msg) > 200 else msg)
                    print(f"Length: {len(msg)} chars")
            else:
                print("❌ No detail messages returned")
        except Exception as e:
            print(f"❌ Error in get_meal_details: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_meal_details()
