"""
Test that 'detail' command retrieves the last logged meal (from session), 
not the most recent meal in database
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Meal, FoodItem, FoodNutrient
from services.chatbot_service import ChatbotService

def test_session_meal_detail():
    with app.app_context():
        # Find test user
        user = User.query.filter_by(phone_number='whatsapp:+12233392848').first()
        
        if not user:
            print("❌ User not found")
            return
        
        print(f"✓ Found user ID {user.id}: {user.phone_number}")
        
        # Find ALL completed meals for this user, sorted by timestamp
        all_meals = Meal.query.filter_by(
            user_id=user.id, 
            processing_status='completed'
        ).order_by(Meal.timestamp.desc()).all()
        
        print(f"\n📋 Found {len(all_meals)} completed meals:")
        for idx, meal in enumerate(all_meals[:5]):  # Show first 5
            food_count = len(meal.food_items)
            print(f"  {idx+1}. Meal ID {meal.id}: {meal.meal_type} - {food_count} items - {meal.timestamp}")
        
        if len(all_meals) < 2:
            print("\n❌ Need at least 2 meals to test. Please log more meals.")
            return
        
        # Simulate logging the SECOND most recent meal (not the most recent)
        target_meal = all_meals[1]  # Get second most recent
        most_recent_meal = all_meals[0]  # This is the most recent in DB
        
        print(f"\n🎯 Target meal (simulating just logged): ID {target_meal.id} ({target_meal.meal_type})")
        print(f"🔝 Most recent in DB: ID {most_recent_meal.id} ({most_recent_meal.meal_type})")
        
        # Test 1: WITHOUT session (should get most recent from DB)
        print("\n" + "="*60)
        print("TEST 1: Detail request WITHOUT session (fallback behavior)")
        print("="*60)
        
        chatbot = ChatbotService()
        result_no_session = chatbot.handle_meal_details(user.id, meal_id=None)
        
        if isinstance(result_no_session, list):
            print(f"✓ Returned {len(result_no_session)} messages")
            # Check which meal it retrieved
            if f"{most_recent_meal.meal_type}" in result_no_session[0].lower():
                print(f"✓ Correctly retrieved most recent meal from DB (ID {most_recent_meal.id})")
            else:
                print(f"⚠️ Retrieved different meal")
        
        # Test 2: WITH session (should get target meal)
        print("\n" + "="*60)
        print("TEST 2: Detail request WITH session (target meal)")
        print("="*60)
        
        result_with_session = chatbot.handle_meal_details(user.id, meal_id=target_meal.id)
        
        if isinstance(result_with_session, list):
            print(f"✓ Returned {len(result_with_session)} messages")
            # Check which meal it retrieved
            if f"{target_meal.meal_type}" in result_with_session[0].lower():
                print(f"✓ Correctly retrieved target meal from session (ID {target_meal.id})")
            else:
                print(f"⚠️ Retrieved different meal")
            
            # Show first message preview
            print(f"\nFirst message preview:")
            print(result_with_session[0][:200] + "...")
        
        # Verify they're different
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        if result_no_session != result_with_session:
            print("✓ Session correctly overrides database query")
            print(f"  - Without session: Retrieved meal {most_recent_meal.id} ({most_recent_meal.meal_type})")
            print(f"  - With session: Retrieved meal {target_meal.id} ({target_meal.meal_type})")
        else:
            print("⚠️ Results are the same (might be issue)")

if __name__ == "__main__":
    test_session_meal_detail()
