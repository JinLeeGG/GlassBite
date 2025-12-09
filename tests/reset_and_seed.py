"""
Reset database and seed with test data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from models import db, User, Meal, FoodItem, FoodNutrient, DailySummary, Goal
from config import Config
import random

def get_test_phone_number():
    """Get WhatsApp test number from environment"""
    return os.getenv('TEST_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # Default to Twilio sandbox

def clear_all_data():
    """Clear ALL data and users (complete reset)"""
    print("🗑️  Clearing all data...")
    
    # Delete in correct order (respecting foreign keys)
    FoodNutrient.query.delete()
    FoodItem.query.delete()
    Meal.query.delete()
    DailySummary.query.delete()
    Goal.query.delete()
    User.query.delete()
    
    db.session.commit()
    print("✅ All data cleared!")

def seed_test_data():
    """Add realistic test data"""
    print("🌱 Seeding test data...")
    
    # Clear all existing data first
    clear_all_data()
    
    # Get WhatsApp number from environment
    test_phone = get_test_phone_number()
    print(f"📱 Using WhatsApp number: {test_phone}")
    
    # Create fresh user with WhatsApp number from environment
    user = User(
        phone_number=test_phone,
        dietary_restrictions="",
        created_at=datetime.now() - timedelta(days=14)
    )
    db.session.add(user)
    db.session.commit()
    print(f"✅ Created test user: {user.phone_number}")
    
    # Sample meals for the last 7 days
    meal_templates = [
        # Breakfast options
        [
            ("Scrambled eggs", 100, 155, 13, 1, 11),
            ("Whole wheat toast", 60, 160, 6, 28, 3),
            ("Banana", 120, 105, 1, 27, 0),
        ],
        [
            ("Greek yogurt", 150, 100, 15, 6, 0),
            ("Granola", 50, 220, 5, 38, 8),
            ("Blueberries", 100, 57, 1, 15, 0),
        ],
        [
            ("Oatmeal", 200, 150, 5, 27, 3),
            ("Almonds", 30, 170, 6, 6, 15),
            ("Apple", 150, 78, 0, 21, 0),
        ],
        
        # Lunch options
        [
            ("Grilled chicken breast", 150, 248, 47, 0, 5),
            ("Brown rice", 150, 170, 4, 35, 1),
            ("Steamed broccoli", 100, 35, 3, 7, 0),
        ],
        [
            ("Turkey sandwich", 200, 320, 28, 35, 9),
            ("Baby carrots", 100, 41, 1, 10, 0),
            ("Apple", 150, 78, 0, 21, 0),
        ],
        [
            ("Salmon fillet", 150, 280, 39, 0, 13),
            ("Quinoa", 100, 120, 4, 21, 2),
            ("Mixed vegetables", 150, 60, 3, 12, 0),
        ],
        
        # Dinner options
        [
            ("Grilled steak", 200, 542, 62, 0, 29),
            ("Baked potato", 150, 130, 3, 30, 0),
            ("Green beans", 100, 31, 2, 7, 0),
        ],
        [
            ("Spaghetti with meat sauce", 300, 420, 24, 55, 12),
            ("Garden salad", 100, 20, 1, 4, 0),
            ("Garlic bread", 50, 150, 4, 20, 6),
        ],
        [
            ("Grilled chicken thigh", 150, 280, 35, 0, 15),
            ("Sweet potato", 200, 180, 3, 41, 0),
            ("Asparagus", 100, 20, 2, 4, 0),
        ],
        
        # Snack options
        [
            ("Protein bar", 60, 200, 20, 22, 7),
        ],
        [
            ("String cheese", 30, 80, 6, 1, 6),
            ("Crackers", 30, 130, 3, 20, 5),
        ],
        [
            ("Peanut butter", 30, 190, 8, 7, 16),
            ("Celery", 100, 16, 1, 3, 0),
        ],
    ]
    
    meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
    
    # Generate meals for last 7 days (from 6 days ago to today)
    for day_offset in range(6, -1, -1):  # 6, 5, 4, 3, 2, 1, 0
        date = datetime.now() - timedelta(days=day_offset)
        
        # 3-4 meals per day
        num_meals = random.randint(3, 4)
        selected_meals = random.sample(meal_templates, num_meals)
        
        daily_totals = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0
        }
        
        for i, foods in enumerate(selected_meals):
            # Assign meal type
            if i == 0:
                meal_type = 'breakfast'
                meal_time = date.replace(hour=8, minute=random.randint(0, 59))
            elif i == 1:
                meal_type = 'lunch'
                meal_time = date.replace(hour=12, minute=random.randint(0, 59))
            elif i == 2:
                meal_type = 'dinner'
                meal_time = date.replace(hour=19, minute=random.randint(0, 59))
            else:
                meal_type = 'snack'
                meal_time = date.replace(hour=15, minute=random.randint(0, 59))
            
            # Calculate meal totals
            meal_calories = sum(f[2] for f in foods)
            meal_protein = sum(f[3] for f in foods)
            meal_carbs = sum(f[4] for f in foods)
            meal_fat = sum(f[5] for f in foods)
            
            # Create meal (without nutrition totals - calculated from food_items)
            meal = Meal(
                user_id=user.id,
                meal_type=meal_type,
                timestamp=meal_time,
                processing_status='completed'
            )
            db.session.add(meal)
            db.session.flush()  # Get meal.id
            
            # Add food items
            for food_name, grams, cal, protein, carbs, fat in foods:
                food_item = FoodItem(
                    meal_id=meal.id,
                    name=food_name,
                    portion_size_grams=grams,
                    confidence_score=0.95
                )
                db.session.add(food_item)
                db.session.flush()  # Get food_item.id
                
                # Add nutrients in separate table
                food_nutrient = FoodNutrient(
                    food_item_id=food_item.id,
                    calories=cal,
                    protein_g=protein,
                    carbs_g=carbs,
                    fat_g=fat,
                    fiber_g=2.0,
                    sugar_g=5.0,
                    sodium_mg=100.0
                )
                db.session.add(food_nutrient)
            
            # Update daily totals
            daily_totals['calories'] += meal_calories
            daily_totals['protein'] += meal_protein
            daily_totals['carbs'] += meal_carbs
            daily_totals['fat'] += meal_fat
        
        # Create daily summary
        summary = DailySummary(
            user_id=user.id,
            date=date.date(),
            total_calories=daily_totals['calories'],
            total_protein=daily_totals['protein'],
            total_carbs=daily_totals['carbs'],
            total_fat=daily_totals['fat'],
            meal_count=num_meals
        )
        db.session.add(summary)
        
        print(f"✅ Day {7 - day_offset}: {num_meals} meals, {daily_totals['calories']:.0f} cal")
    
    # Add goals
    calorie_goal = Goal(
        user_id=user.id,
        goal_type='calorie_target',
        target_value=2000,
        is_active=True
    )
    protein_goal = Goal(
        user_id=user.id,
        goal_type='protein_target',
        target_value=150,
        is_active=True
    )
    carb_goal = Goal(
        user_id=user.id,
        goal_type='carb_target',
        target_value=250,
        is_active=True
    )
    db.session.add(calorie_goal)
    db.session.add(protein_goal)
    db.session.add(carb_goal)
    
    db.session.commit()
    print("✅ Added goals: 2000 cal, 150g protein, 250g carbs")
    print("\n🎉 Test data seeded successfully!")
    print(f"📊 Total: {Meal.query.count()} meals, {FoodItem.query.count()} food items")

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        print("=" * 60)
        print("DATABASE RESET & SEED")
        print("=" * 60)
        seed_test_data()
        print("\n" + "=" * 60)
        print("✅ COMPLETE!")
        print("=" * 60)
