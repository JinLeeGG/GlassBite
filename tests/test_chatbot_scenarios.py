"""
Test chatbot conversation scenarios
Tests all user interaction cases to ensure proper responses
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, date, timedelta
from models import db, User, Meal, Goal, DailySummary
from services.chatbot_service import ChatbotService

def test_goal_scenarios():
    """Test all goal-related scenarios"""
    from app import app
    
    with app.app_context():
        # Setup test user
        test_phone = "whatsapp:+1234567890"
        user = User.query.filter_by(phone_number=test_phone).first()
        if not user:
            user = User(phone_number=test_phone)
            db.session.add(user)
            db.session.commit()
        
        # Clean up existing goals
        Goal.query.filter_by(user_id=user.id).delete()
        DailySummary.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        chatbot = ChatbotService()
        
        print("=" * 60)
        print("TEST 1: Setting calorie goal")
        print("=" * 60)
        response = chatbot.handle_goal_setting(user.id, "My goal is 2000 calories")
        print(response)
        assert "2000 calories" in response
        assert "Goal set" in response
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 2: Setting protein goal")
        print("=" * 60)
        response = chatbot.handle_goal_setting(user.id, "My protein goal is 150g")
        print(response)
        assert "150" in response
        assert "protein" in response
        assert "2000 calories" in response  # Should show both goals
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 3: Setting carb goal")
        print("=" * 60)
        response = chatbot.handle_goal_setting(user.id, "My carb goal is 250g")
        print(response)
        assert "250" in response
        assert "carb" in response.lower()
        assert "2000 calories" in response  # Should show all 3 goals
        assert "150" in response
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 4: Progress without meals (no data)")
        print("=" * 60)
        response = chatbot.handle_goal_progress(user.id)
        print(response)
        assert "No meals logged today" in response
        assert "2000 calories" in response
        assert "150g" in response
        assert "250g" in response
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 5: Progress with meals")
        print("=" * 60)
        # Create a daily summary
        summary = DailySummary(
            user_id=user.id,
            date=date.today(),
            total_calories=1500,
            total_protein=100,
            total_carbs=200,
            total_fat=50,
            meal_count=3
        )
        db.session.add(summary)
        db.session.commit()
        
        response = chatbot.handle_goal_progress(user.id)
        print(response)
        
        # Check all three goals are shown
        assert "Calorie Goal" in response
        assert "2000 calories" in response
        assert "1500 calories" in response
        assert "75%" in response  # 1500/2000
        
        assert "Protein Goal" in response
        assert "150g" in response
        assert "100g" in response
        assert "67%" in response  # 100/150
        
        assert "Carb Goal" in response
        assert "250g" in response
        assert "200g" in response
        assert "80%" in response  # 200/250
        
        assert "remaining" in response.lower()
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 6: Updating existing goal")
        print("=" * 60)
        response = chatbot.handle_goal_setting(user.id, "My goal is 2500 calories")
        print(response)
        assert "2500 calories" in response
        
        # Verify old goal is deactivated
        old_goal = Goal.query.filter_by(
            user_id=user.id,
            goal_type='calorie_target',
            target_value=2000
        ).first()
        assert old_goal is None or old_goal.is_active == False
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 7: Progress over goal")
        print("=" * 60)
        # Update summary to be over goals
        summary.total_calories = 3000
        summary.total_protein = 200
        summary.total_carbs = 300
        db.session.commit()
        
        response = chatbot.handle_goal_progress(user.id)
        print(response)
        assert "over goal" in response.lower()
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 8: No goals set")
        print("=" * 60)
        # Delete all goals
        Goal.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        response = chatbot.handle_goal_progress(user.id)
        print(response)
        assert "haven't set any goals" in response.lower()
        print("✅ PASSED\n")


def test_summary_scenarios():
    """Test daily summary scenarios"""
    from app import app
    
    with app.app_context():
        test_phone = "whatsapp:+1234567890"
        user = User.query.filter_by(phone_number=test_phone).first()
        
        chatbot = ChatbotService()
        
        # Clean up
        DailySummary.query.filter_by(user_id=user.id).delete()
        Goal.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        print("=" * 60)
        print("TEST 9: Summary without meals")
        print("=" * 60)
        response = chatbot.handle_daily_summary(user.id, 'today')
        print(response)
        assert "haven't logged any meals" in response.lower()
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 10: Today's summary with meals")
        print("=" * 60)
        summary = DailySummary(
            user_id=user.id,
            date=date.today(),
            total_calories=1800,
            total_protein=120,
            total_carbs=180,
            total_fat=60,
            meal_count=4
        )
        db.session.add(summary)
        db.session.commit()
        
        response = chatbot.handle_daily_summary(user.id, 'today')
        print(response)
        assert "Today's Summary" in response
        assert "1800" in response
        assert "120g protein" in response
        assert "180g carbs" in response
        assert "60g fat" in response
        assert "4" in response  # meal count
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 11: Summary with goal tracking")
        print("=" * 60)
        # Add a calorie goal
        goal = Goal(
            user_id=user.id,
            goal_type='calorie_target',
            target_value=2000,
            is_active=True
        )
        db.session.add(goal)
        db.session.commit()
        
        response = chatbot.handle_daily_summary(user.id, 'today')
        print(response)
        assert "Goal: 2000 calories" in response
        assert "Progress:" in response
        assert "remaining" in response.lower()
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 12: Yesterday's summary")
        print("=" * 60)
        yesterday_summary = DailySummary(
            user_id=user.id,
            date=date.today() - timedelta(days=1),
            total_calories=2200,
            total_protein=140,
            total_carbs=220,
            total_fat=70,
            meal_count=5
        )
        db.session.add(yesterday_summary)
        db.session.commit()
        
        response = chatbot.handle_daily_summary(user.id, 'yesterday')
        print(response)
        assert "Yesterday" in response
        assert "2200" in response
        print("✅ PASSED\n")


def test_edge_cases():
    """Test edge cases and error handling"""
    from app import app
    
    with app.app_context():
        test_phone = "whatsapp:+1234567890"
        user = User.query.filter_by(phone_number=test_phone).first()
        
        chatbot = ChatbotService()
        
        print("=" * 60)
        print("TEST 13: Goal setting without number")
        print("=" * 60)
        response = chatbot.handle_goal_setting(user.id, "My goal is lots of calories")
        print(response)
        assert "specify a number" in response.lower()
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 14: Zero division protection")
        print("=" * 60)
        # Create goal with 0 value (edge case)
        Goal.query.filter_by(user_id=user.id).delete()
        zero_goal = Goal(
            user_id=user.id,
            goal_type='calorie_target',
            target_value=0,
            is_active=True
        )
        db.session.add(zero_goal)
        db.session.commit()
        
        # Should not crash
        response = chatbot.handle_goal_progress(user.id)
        print(response)
        print("✅ PASSED (no crash)\n")


def test_all_goal_types():
    """Verify all 3 goal types work independently"""
    from app import app
    
    with app.app_context():
        test_phone = "whatsapp:+1234567890"
        user = User.query.filter_by(phone_number=test_phone).first()
        
        chatbot = ChatbotService()
        
        # Clean up
        Goal.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        print("=" * 60)
        print("TEST 15: Only calorie goal")
        print("=" * 60)
        goal = Goal(
            user_id=user.id,
            goal_type='calorie_target',
            target_value=2000,
            is_active=True
        )
        db.session.add(goal)
        db.session.commit()
        
        response = chatbot.handle_goal_progress(user.id)
        print(response)
        assert "Calorie goal" in response or "Calorie Goal" in response
        assert "Protein" not in response
        assert "Carb" not in response
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 16: Only protein goal")
        print("=" * 60)
        Goal.query.filter_by(user_id=user.id).delete()
        goal = Goal(
            user_id=user.id,
            goal_type='protein_target',
            target_value=150,
            is_active=True
        )
        db.session.add(goal)
        db.session.commit()
        
        response = chatbot.handle_goal_progress(user.id)
        print(response)
        assert "Protein goal" in response or "Protein Goal" in response
        assert "Calorie" not in response
        assert "Carb" not in response
        print("✅ PASSED\n")
        
        print("=" * 60)
        print("TEST 17: Only carb goal")
        print("=" * 60)
        Goal.query.filter_by(user_id=user.id).delete()
        goal = Goal(
            user_id=user.id,
            goal_type='carb_target',
            target_value=250,
            is_active=True
        )
        db.session.add(goal)
        db.session.commit()
        
        response = chatbot.handle_goal_progress(user.id)
        print(response)
        assert "Carb goal" in response or "Carb Goal" in response
        assert "Calorie" not in response
        assert "Protein" not in response
        print("✅ PASSED\n")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("CHATBOT SCENARIO TESTS")
    print("="*60 + "\n")
    
    try:
        test_goal_scenarios()
        test_summary_scenarios()
        test_edge_cases()
        test_all_goal_types()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        raise
