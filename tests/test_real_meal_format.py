"""
Test with actual database data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, Meal, FoodItem, User, Goal
from services.meal_processor import MealProcessor

def test_with_real_data():
    """Test formatting with real database meal"""
    
    with app.app_context():
        processor = MealProcessor()
        
        # Get the most recent completed meal
        meal = Meal.query.filter_by(
            processing_status='completed'
        ).order_by(Meal.timestamp.desc()).first()
        
        if not meal:
            print("❌ No completed meals found in database")
            return
        
        print("="*70)
        print(f"🔍 Testing with Meal ID: {meal.id}")
        print(f"   User ID: {meal.user_id}")
        print(f"   Type: {meal.meal_type}")
        print(f"   Time: {meal.timestamp}")
        print("="*70)
        
        # Get food items
        food_items = FoodItem.query.filter_by(meal_id=meal.id).all()
        
        if not food_items:
            print("❌ No food items found for this meal")
            return
        
        print(f"\n📋 Found {len(food_items)} food items\n")
        
        # Calculate totals
        total_calories = sum(item.calories for item in food_items)
        total_protein = sum(item.protein_g for item in food_items)
        total_carbs = sum(item.carbs_g for item in food_items)
        total_fat = sum(item.fat_g for item in food_items)
        
        # Get daily totals
        daily_totals = processor.get_daily_totals(meal.user_id)
        
        # Get goal
        goal = processor.get_active_goal(meal.user_id)
        
        # Get low confidence foods
        low_confidence_foods = [item.name for item in food_items if item.confidence_score < 0.6]
        
        # Format the message
        message = processor.format_meal_confirmation(
            food_items,
            total_calories,
            total_protein,
            total_carbs,
            total_fat,
            daily_totals,
            goal,
            low_confidence_foods,
            meal.meal_type
        )
        
        print("="*70)
        print("📱 New Format Message:")
        print("="*70)
        print(message)
        print("="*70)
        print("✅ Test complete!")
        print("="*70)

if __name__ == '__main__':
    test_with_real_data()
