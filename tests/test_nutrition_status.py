"""
Test nutrition status feature
Tests classification patterns and output format
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.chatbot_service import chatbot_service
from models import db, User, Meal, FoodItem, FoodNutrient, Goal
from datetime import datetime, timedelta
from config import Config
from flask import Flask

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def test_classification_patterns():
    """Test that nutrition status commands are classified correctly"""
    print("\n" + "="*80)
    print("TESTING CLASSIFICATION PATTERNS")
    print("="*80)
    
    test_cases = [
        # Daily patterns
        ("nutrition status", "nutrition_status", 1),
        ("show my nutrition status", "nutrition_status", 1),
        ("my nutrients", "nutrition_status", 1),
        ("show nutrients", "nutrition_status", 1),
        ("nutrient status", "nutrition_status", 1),
        ("my nutrition", "nutrition_status", 1),
        ("what nutrients have i consumed", "nutrition_status", 1),
        
        # Weekly patterns
        ("nutrition week", "nutrition_status", 7),
        ("weekly nutrients", "nutrition_status", 7),
        ("week nutrients", "nutrition_status", 7),
        ("weekly nutrition", "nutrition_status", 7),
        ("nutrition this week", "nutrition_status", 7),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_type, expected_days in test_cases:
        question_type, params = chatbot_service.classify_question(message)
        days = params.get('days', None)
        
        if question_type == expected_type and days == expected_days:
            print(f"✅ PASS: '{message}' → {question_type} (days={days})")
            passed += 1
        else:
            print(f"❌ FAIL: '{message}' → {question_type} (days={days}), expected {expected_type} (days={expected_days})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_nutrition_status_output():
    """Test nutrition status output format"""
    print("\n" + "="*80)
    print("TESTING NUTRITION STATUS OUTPUT")
    print("="*80)
    
    with app.app_context():
        # Create test user
        user = User.query.filter_by(phone_number='+1234567890').first()
        if not user:
            user = User(
                phone_number='+1234567890',
                dietary_restrictions=''
            )
            db.session.add(user)
            db.session.commit()
        
        # Create test meal with nutrients
        meal = Meal(
            user_id=user.id,
            timestamp=datetime.now(),
            meal_type='lunch',
            processing_status='completed'
        )
        db.session.add(meal)
        db.session.flush()
        
        # Add food item
        food_item = FoodItem(
            meal_id=meal.id,
            food_name='Test Chicken Breast',
            quantity='200g',
            fdc_id='123456'
        )
        db.session.add(food_item)
        db.session.flush()
        
        # Add all 25 nutrients
        nutrients_data = [
            ('calories', 330, 'kcal'),
            ('protein', 62, 'g'),
            ('carbs', 0, 'g'),
            ('fat', 7, 'g'),
            ('fiber', 0, 'g'),
            ('sugar', 0, 'g'),
            ('sodium', 148, 'mg'),
            ('vitamin_a', 16, 'µg'),
            ('vitamin_c', 0, 'mg'),
            ('vitamin_d', 0.2, 'µg'),
            ('vitamin_e', 0.5, 'mg'),
            ('vitamin_k', 0, 'µg'),
            ('thiamin', 0.15, 'mg'),
            ('riboflavin', 0.23, 'mg'),
            ('niacin', 18.8, 'mg'),
            ('vitamin_b6', 1.2, 'mg'),
            ('folate', 9, 'µg'),
            ('vitamin_b12', 0.67, 'µg'),
            ('calcium', 15, 'mg'),
            ('iron', 1.04, 'mg'),
            ('magnesium', 64, 'mg'),
            ('phosphorus', 392, 'mg'),
            ('potassium', 740, 'mg'),
            ('zinc', 1.96, 'mg'),
            ('saturated_fat', 1.9, 'g'),
            ('monounsaturated_fat', 2.6, 'g'),
            ('polyunsaturated_fat', 1.5, 'g'),
            ('cholesterol', 146, 'mg'),
        ]
        
        for nutrient_name, amount, unit in nutrients_data:
            nutrient = FoodNutrient(
                food_item_id=food_item.id,
                nutrient_name=nutrient_name,
                amount=amount,
                unit=unit
            )
            db.session.add(nutrient)
        
        db.session.commit()
        
        # Test daily status
        print("\n--- DAILY STATUS ---")
        response = chatbot_service.handle_nutrition_status(user.id, days=1)
        print(response)
        
        # Verify format
        assert "🍽️ *Nutrition Status - Today*" in response
        assert "📊 *Daily Goals:*" in response
        assert "💪 *Other Macros:*" in response
        assert "🌟 *Vitamins:*" in response
        assert "⚡ *Minerals:*" in response
        assert "🥑 *Fats:*" in response
        
        # Verify goals have percentages
        assert "Calories:" in response and "%" in response
        assert "Protein:" in response and "%" in response
        assert "Carbs:" in response and "%" in response
        
        # Verify other nutrients don't have percentages (after goals section)
        lines = response.split('\n')
        in_goals_section = False
        in_other_sections = False
        
        for line in lines:
            if "📊 *Daily Goals:*" in line:
                in_goals_section = True
                in_other_sections = False
            elif any(section in line for section in ["💪 *Other Macros:*", "🌟 *Vitamins:*", "⚡ *Minerals:*", "🥑 *Fats:*"]):
                in_goals_section = False
                in_other_sections = True
            
            # In other sections, nutrients should NOT have percentages
            if in_other_sections and ":" in line and line.strip():
                # Skip section headers
                if "*" not in line:
                    assert "%" not in line, f"Found percentage in non-goals section: {line}"
        
        print("\n✅ Daily format correct!")
        
        # Test weekly status
        print("\n--- WEEKLY STATUS ---")
        response = chatbot_service.handle_nutrition_status(user.id, days=7)
        print(response)
        
        assert "🍽️ *Nutrition Status - This Week*" in response
        print("\n✅ Weekly format correct!")
        
        # Clean up
        db.session.delete(meal)
        db.session.commit()
        
        print("\n✅ All output tests passed!")
        return True


def test_with_goals():
    """Test nutrition status with custom goals"""
    print("\n" + "="*80)
    print("TESTING WITH CUSTOM GOALS")
    print("="*80)
    
    with app.app_context():
        user = User.query.filter_by(phone_number='+1234567890').first()
        
        # Set custom goals
        goals_data = [
            ('calories', 2500),
            ('protein', 150),
            ('carbs', 250),
        ]
        
        for nutrient_name, target in goals_data:
            goal = Goal.query.filter_by(user_id=user.id, nutrient_name=nutrient_name).first()
            if goal:
                goal.target_amount = target
            else:
                goal = Goal(
                    user_id=user.id,
                    nutrient_name=nutrient_name,
                    target_amount=target
                )
                db.session.add(goal)
        
        db.session.commit()
        
        # Create test meal
        meal = Meal(
            user_id=user.id,
            timestamp=datetime.now(),
            meal_type='dinner',
            processing_status='completed'
        )
        db.session.add(meal)
        db.session.flush()
        
        food_item = FoodItem(
            meal_id=meal.id,
            food_name='Test Meal',
            quantity='1 serving',
            fdc_id='789'
        )
        db.session.add(food_item)
        db.session.flush()
        
        # Add nutrients that hit 75% of custom goals
        nutrients = [
            ('calories', 1875, 'kcal'),  # 75% of 2500
            ('protein', 112.5, 'g'),      # 75% of 150
            ('carbs', 187.5, 'g'),        # 75% of 250
        ]
        
        for nutrient_name, amount, unit in nutrients:
            nutrient = FoodNutrient(
                food_item_id=food_item.id,
                nutrient_name=nutrient_name,
                amount=amount,
                unit=unit
            )
            db.session.add(nutrient)
        
        db.session.commit()
        
        # Test output
        response = chatbot_service.handle_nutrition_status(user.id, days=1)
        print(response)
        
        # Verify custom targets are used
        assert "1875.0/2500.0" in response or "1875/2500" in response
        assert "112.5/150.0" in response or "112.5/150" in response
        assert "187.5/250.0" in response or "187.5/250" in response
        
        # Verify emoji indicators (75% should be 🟢)
        assert "🟢 Calories:" in response
        assert "🟢 Protein:" in response
        assert "🟢 Carbs:" in response
        
        # Clean up
        db.session.delete(meal)
        db.session.commit()
        
        print("\n✅ Custom goals test passed!")
        return True


if __name__ == '__main__':
    print("\n" + "="*80)
    print("NUTRITION STATUS FEATURE TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Classification patterns
        test1 = test_classification_patterns()
        
        # Test 2: Output format
        test2 = test_nutrition_status_output()
        
        # Test 3: Custom goals
        test3 = test_with_goals()
        
        print("\n" + "="*80)
        if test1 and test2 and test3:
            print("✅ ALL TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
