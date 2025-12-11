"""
Test that last_meal_id is stored in database and retrieved correctly
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Meal
from services.chatbot_service import ChatbotService

def test_db_meal_detail():
    with app.app_context():
        # Find test user
        user = User.query.filter_by(phone_number='whatsapp:+12233392848').first()
        
        if not user:
            print("❌ User not found")
            return
        
        print(f"✓ Found user ID {user.id}: {user.phone_number}")
        print(f"  Current last_meal_id: {user.last_meal_id}")
        
        # Get all meals
        all_meals = Meal.query.filter_by(
            user_id=user.id, 
            processing_status='completed'
        ).order_by(Meal.timestamp.desc()).all()
        
        print(f"\n📋 Total meals: {len(all_meals)}")
        for idx, meal in enumerate(all_meals[:3]):
            food_count = len(meal.food_items)
            marker = " ← STORED" if user.last_meal_id == meal.id else ""
            print(f"  {idx+1}. Meal ID {meal.id}: {meal.meal_type} ({food_count} items){marker}")
        
        if len(all_meals) < 2:
            print("\n❌ Need at least 2 meals to test")
            return
        
        # Test: Update user.last_meal_id to second meal
        target_meal = all_meals[1]
        print(f"\n🔄 Setting user.last_meal_id to {target_meal.id} ({target_meal.meal_type})")
        user.last_meal_id = target_meal.id
        db.session.commit()
        
        # Refresh user from DB
        db.session.refresh(user)
        print(f"✓ Confirmed: user.last_meal_id = {user.last_meal_id}")
        
        # Test: Call handle_meal_details with user_id (should auto-retrieve from user object)
        print(f"\n🧪 Testing handle_meal_details with auto-retrieval from user.last_meal_id")
        chatbot = ChatbotService()
        
        # This should use user.last_meal_id
        result = chatbot.route_to_handler(user.id, 'meal_details', {})
        
        if isinstance(result, list):
            print(f"✓ Returned {len(result)} messages")
            if f"{target_meal.meal_type}" in result[0].lower():
                print(f"✅ SUCCESS! Retrieved correct meal (ID {target_meal.id}, {target_meal.meal_type})")
            else:
                print(f"❌ FAILED: Retrieved wrong meal")
            
            print(f"\nFirst message preview:")
            print(result[0][:150] + "...")
        else:
            print(f"⚠️ Result is not a list: {type(result)}")

if __name__ == "__main__":
    test_db_meal_detail()
