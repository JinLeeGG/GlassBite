"""
Seed user with comprehensive meal history for testing AI recommendations
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from models import db, User, Meal, FoodItem, FoodNutrient, DailySummary, Goal
from app import app
import random

def get_test_phone_number():
    """Get WhatsApp test number from environment"""
    return os.getenv('TEST_WHATSAPP_NUMBER', 'whatsapp:+12232690603')

def seed_meal_history():
    """Add 7+ days of realistic meal history for the test user"""
    with app.app_context():
        print("🌱 Seeding meal history for AI recommendation testing...")
        
        # Get the test user
        test_phone = get_test_phone_number()
        user = User.query.filter_by(phone_number=test_phone).first()
        
        if not user:
            print(f"❌ No user found with phone: {test_phone}")
            return
        
        print(f"✅ Found user: {user.phone_number} (ID: {user.id})")
        
        # Meal templates with realistic patterns
        breakfast_options = [
            {
                "name": "Protein Breakfast",
                "foods": [
                    ("Scrambled eggs", 100, 155, 13, 1, 11, 2, 0, 140),
                    ("Whole wheat toast", 60, 160, 6, 28, 3, 1, 0, 180),
                    ("Avocado", 50, 80, 1, 4, 7, 3, 0, 4),
                ]
            },
            {
                "name": "Greek Yogurt Bowl",
                "foods": [
                    ("Greek yogurt", 200, 130, 20, 8, 0, 0, 0, 75),
                    ("Granola", 50, 220, 5, 38, 8, 4, 12, 15),
                    ("Blueberries", 100, 57, 1, 15, 0, 2, 10, 1),
                    ("Honey", 20, 64, 0, 17, 0, 0, 17, 1),
                ]
            },
            {
                "name": "Oatmeal Power Bowl",
                "foods": [
                    ("Oatmeal", 200, 150, 5, 27, 3, 4, 1, 5),
                    ("Almond butter", 30, 185, 7, 6, 16, 3, 1, 5),
                    ("Banana", 120, 105, 1, 27, 0, 3, 14, 1),
                ]
            },
        ]
        
        lunch_options = [
            {
                "name": "Chicken Rice Bowl",
                "foods": [
                    ("Grilled chicken breast", 150, 248, 47, 0, 5, 0, 0, 125),
                    ("Brown rice", 150, 170, 4, 35, 1, 2, 1, 5),
                    ("Steamed broccoli", 100, 35, 3, 7, 0, 3, 2, 30),
                    ("Olive oil", 10, 90, 0, 0, 10, 0, 0, 0),
                ]
            },
            {
                "name": "Salmon Quinoa Bowl",
                "foods": [
                    ("Grilled salmon", 150, 280, 39, 0, 13, 0, 0, 75),
                    ("Quinoa", 150, 180, 6, 32, 3, 4, 2, 10),
                    ("Mixed vegetables", 150, 60, 3, 12, 0, 4, 5, 35),
                    ("Lemon dressing", 20, 40, 0, 1, 4, 0, 1, 120),
                ]
            },
            {
                "name": "Turkey Wrap",
                "foods": [
                    ("Whole wheat tortilla", 80, 180, 6, 32, 3, 4, 2, 320),
                    ("Turkey breast", 100, 135, 30, 0, 1, 0, 0, 1050),
                    ("Lettuce & tomato", 80, 15, 1, 3, 0, 1, 2, 5),
                    ("Hummus", 40, 70, 2, 8, 3, 2, 0, 115),
                ]
            },
        ]
        
        dinner_options = [
            {
                "name": "Steak Dinner",
                "foods": [
                    ("Grilled sirloin steak", 200, 380, 50, 0, 18, 0, 0, 140),
                    ("Sweet potato", 200, 180, 4, 41, 0, 6, 13, 70),
                    ("Asparagus", 100, 20, 2, 4, 0, 2, 2, 2),
                    ("Butter", 10, 72, 0, 0, 8, 0, 0, 82),
                ]
            },
            {
                "name": "Pasta Night",
                "foods": [
                    ("Whole wheat pasta", 200, 310, 13, 62, 2, 10, 2, 8),
                    ("Turkey meatballs", 150, 295, 35, 8, 13, 0, 3, 520),
                    ("Marinara sauce", 150, 70, 2, 14, 1, 4, 10, 480),
                    ("Parmesan cheese", 20, 86, 8, 1, 6, 0, 0, 336),
                ]
            },
            {
                "name": "Fish Tacos",
                "foods": [
                    ("Grilled tilapia", 150, 145, 30, 0, 3, 0, 0, 75),
                    ("Corn tortillas", 100, 210, 5, 44, 3, 6, 2, 15),
                    ("Cabbage slaw", 80, 20, 1, 5, 0, 2, 3, 15),
                    ("Avocado", 60, 96, 1, 5, 9, 4, 0, 4),
                    ("Lime & cilantro", 10, 3, 0, 1, 0, 0, 0, 1),
                ]
            },
        ]
        
        snack_options = [
            [("Apple", 150, 78, 0, 21, 0, 3, 16, 2)],
            [("Almonds", 30, 170, 6, 6, 15, 4, 1, 0)],
            [("Protein bar", 60, 200, 20, 22, 7, 3, 12, 200)],
            [("Greek yogurt", 150, 100, 15, 6, 0, 0, 5, 60)],
        ]
        
        # Create meals for the last 10 days
        meals_created = 0
        start_date = datetime.now() - timedelta(days=10)
        
        for day in range(10):
            current_date = start_date + timedelta(days=day)
            
            # Breakfast
            breakfast = random.choice(breakfast_options)
            meal = Meal(
                user_id=user.id,
                meal_type='breakfast',
                timestamp=current_date.replace(hour=8, minute=random.randint(0, 59)),
                processing_status='completed'
            )
            db.session.add(meal)
            db.session.flush()
            
            for food_data in breakfast["foods"]:
                name, grams, cal, prot, carb, fat, fib, sug, sod = food_data
                food_item = FoodItem(
                    meal_id=meal.id,
                    name=name,
                    portion_size_grams=grams,
                    confidence_score=0.95
                )
                db.session.add(food_item)
                db.session.flush()
                
                nutrients = FoodNutrient(
                    food_item_id=food_item.id,
                    calories=cal,
                    protein_g=prot,
                    carbs_g=carb,
                    fat_g=fat,
                    fiber_g=fib,
                    sugar_g=sug,
                    sodium_mg=sod,
                    calcium_mg=30,
                    iron_mg=1.5,
                    potassium_mg=200
                )
                db.session.add(nutrients)
            
            meals_created += 1
            
            # Lunch
            lunch = random.choice(lunch_options)
            meal = Meal(
                user_id=user.id,
                meal_type='lunch',
                timestamp=current_date.replace(hour=13, minute=random.randint(0, 59)),
                processing_status='completed'
            )
            db.session.add(meal)
            db.session.flush()
            
            for food_data in lunch["foods"]:
                name, grams, cal, prot, carb, fat, fib, sug, sod = food_data
                food_item = FoodItem(
                    meal_id=meal.id,
                    name=name,
                    portion_size_grams=grams,
                    confidence_score=0.95
                )
                db.session.add(food_item)
                db.session.flush()
                
                nutrients = FoodNutrient(
                    food_item_id=food_item.id,
                    calories=cal,
                    protein_g=prot,
                    carbs_g=carb,
                    fat_g=fat,
                    fiber_g=fib,
                    sugar_g=sug,
                    sodium_mg=sod,
                    calcium_mg=25,
                    iron_mg=2.0,
                    potassium_mg=300
                )
                db.session.add(nutrients)
            
            meals_created += 1
            
            # Dinner
            dinner = random.choice(dinner_options)
            meal = Meal(
                user_id=user.id,
                meal_type='dinner',
                timestamp=current_date.replace(hour=19, minute=random.randint(0, 59)),
                processing_status='completed'
            )
            db.session.add(meal)
            db.session.flush()
            
            for food_data in dinner["foods"]:
                name, grams, cal, prot, carb, fat, fib, sug, sod = food_data
                food_item = FoodItem(
                    meal_id=meal.id,
                    name=name,
                    portion_size_grams=grams,
                    confidence_score=0.95
                )
                db.session.add(food_item)
                db.session.flush()
                
                nutrients = FoodNutrient(
                    food_item_id=food_item.id,
                    calories=cal,
                    protein_g=prot,
                    carbs_g=carb,
                    fat_g=fat,
                    fiber_g=fib,
                    sugar_g=sug,
                    sodium_mg=sod,
                    calcium_mg=35,
                    iron_mg=3.5,
                    potassium_mg=400
                )
                db.session.add(nutrients)
            
            meals_created += 1
            
            # Add 1-2 snacks randomly
            if random.random() > 0.3:
                snack = random.choice(snack_options)
                meal = Meal(
                    user_id=user.id,
                    meal_type='snack',
                    timestamp=current_date.replace(hour=random.choice([11, 16]), minute=random.randint(0, 59)),
                    processing_status='completed'
                )
                db.session.add(meal)
                db.session.flush()
                
                for food_data in snack:
                    name, grams, cal, prot, carb, fat, fib, sug, sod = food_data
                    food_item = FoodItem(
                        meal_id=meal.id,
                        name=name,
                        portion_size_grams=grams,
                        confidence_score=0.95
                    )
                    db.session.add(food_item)
                    db.session.flush()
                    
                    nutrients = FoodNutrient(
                        food_item_id=food_item.id,
                        calories=cal,
                        protein_g=prot,
                        carbs_g=carb,
                        fat_g=fat,
                        fiber_g=fib,
                        sugar_g=sug,
                        sodium_mg=sod,
                        calcium_mg=20,
                        iron_mg=1.0,
                        potassium_mg=150
                    )
                    db.session.add(nutrients)
                
                meals_created += 1
        
        # Add user goals
        goals_to_add = [
            Goal(user_id=user.id, goal_type='calorie_target', target_value=2000, is_active=True),
            Goal(user_id=user.id, goal_type='protein_target', target_value=150, is_active=True),
        ]
        
        for goal in goals_to_add:
            db.session.add(goal)
        
        db.session.commit()
        
        print(f"✅ Created {meals_created} meals across 10 days")
        print(f"✅ Added 2 nutrition goals")
        print("\n🎉 Database seeded successfully!")
        print("\n📱 Now test via WhatsApp by sending:")
        print("   - 'Create a meal plan for today'")
        print("   - 'What should I eat today'")
        print("   - 'Plan my meals'")

if __name__ == '__main__':
    seed_meal_history()
