"""
Test cancel and delete meal functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Meal, FoodItem, FoodNutrient, DailySummary
from database_utils import cancel_pending_meal, delete_last_meal
from datetime import datetime, date

def setup_test_data():
    """Create test user and meals"""
    with app.app_context():
        # Create test user
        test_phone = "whatsapp:+1234567890"
        user = User.query.filter_by(phone_number=test_phone).first()
        
        if not user:
            user = User(phone_number=test_phone)
            db.session.add(user)
            db.session.commit()
        
        print(f"✓ Test user created: {user.id}")
        return user.id

def test_1_cancel_pending_meal():
    """Test cancelling a pending meal"""
    print("\n" + "="*70)
    print("TEST 1: Cancel Pending Meal")
    print("="*70)
    
    with app.app_context():
        user_id = setup_test_data()
        
        # Create a pending meal
        pending_meal = Meal(
            user_id=user_id,
            meal_type='pending',
            processing_status='analyzed',
            timestamp=datetime.now()
        )
        db.session.add(pending_meal)
        db.session.commit()
        
        meal_id = pending_meal.id
        print(f"✓ Created pending meal ID: {meal_id}")
        
        # Add some food items
        food = FoodItem(
            meal_id=meal_id,
            name="Test Food",
            portion_size_grams=100
        )
        db.session.add(food)
        db.session.commit()
        print(f"✓ Added food item to meal")
        
        # Cancel the meal
        result = cancel_pending_meal(user_id)
        
        print(f"\nResult: {result['success']}")
        print(f"Message: {result['message']}")
        
        # Verify meal is deleted
        deleted_meal = Meal.query.get(meal_id)
        if deleted_meal is None:
            print("✅ PASS: Meal successfully deleted")
        else:
            print("❌ FAIL: Meal still exists")
        
        # Verify food items are cascade deleted
        deleted_food = FoodItem.query.filter_by(meal_id=meal_id).first()
        if deleted_food is None:
            print("✅ PASS: Food items cascade deleted")
        else:
            print("❌ FAIL: Food items still exist")

def test_2_cancel_no_pending_meal():
    """Test cancelling when no pending meal exists"""
    print("\n" + "="*70)
    print("TEST 2: Cancel When No Pending Meal")
    print("="*70)
    
    with app.app_context():
        user_id = setup_test_data()
        
        # Try to cancel without pending meal
        result = cancel_pending_meal(user_id)
        
        print(f"Result: {result['success']}")
        print(f"Message: {result['message']}")
        
        if not result['success'] and result['message'] == 'No pending meal to cancel':
            print("✅ PASS: Correctly handles no pending meal")
        else:
            print("❌ FAIL: Should fail when no pending meal")

def test_3_delete_completed_meal():
    """Test deleting a completed meal"""
    print("\n" + "="*70)
    print("TEST 3: Delete Completed Meal")
    print("="*70)
    
    with app.app_context():
        user_id = setup_test_data()
        
        # Create a completed meal
        meal = Meal(
            user_id=user_id,
            meal_type='lunch',
            processing_status='completed',
            timestamp=datetime.now()
        )
        db.session.add(meal)
        db.session.commit()
        meal_id = meal.id
        
        print(f"✓ Created completed meal ID: {meal_id}")
        
        # Add food items with nutrients
        food = FoodItem(
            meal_id=meal_id,
            name="Chicken Breast",
            portion_size_grams=150
        )
        db.session.add(food)
        db.session.commit()
        
        nutrients = FoodNutrient(
            food_item_id=food.id,
            calories=250,
            protein_g=50,
            carbs_g=0,
            fat_g=5
        )
        db.session.add(nutrients)
        db.session.commit()
        
        print(f"✓ Added food with nutrients: 250 cal, 50g protein")
        
        # Create daily summary
        summary = DailySummary(
            user_id=user_id,
            date=date.today(),
            total_calories=1500,
            total_protein=100,
            total_carbs=150,
            total_fat=50,
            meal_count=3
        )
        db.session.add(summary)
        db.session.commit()
        
        print(f"✓ Created daily summary: 1500 cal, 100g protein, 3 meals")
        
        # Delete the meal
        result = delete_last_meal(user_id)
        
        print(f"\nResult: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Meal info: {result['meal_info']}")
        print(f"Updated totals: {result['updated_totals']}")
        
        # Verify meal is deleted
        deleted_meal = Meal.query.get(meal_id)
        if deleted_meal is None:
            print("✅ PASS: Meal successfully deleted")
        else:
            print("❌ FAIL: Meal still exists")
        
        # Verify daily summary updated
        updated_summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today()
        ).first()
        
        if updated_summary:
            expected_cal = 1500 - 250  # 1250
            expected_protein = 100 - 50  # 50
            expected_meals = 3 - 1  # 2
            
            print(f"\nDaily Summary After Delete:")
            print(f"  Calories: {updated_summary.total_calories} (expected: {expected_cal})")
            print(f"  Protein: {updated_summary.total_protein}g (expected: {expected_protein}g)")
            print(f"  Meals: {updated_summary.meal_count} (expected: {expected_meals})")
            
            if (updated_summary.total_calories == expected_cal and 
                updated_summary.total_protein == expected_protein and
                updated_summary.meal_count == expected_meals):
                print("✅ PASS: Daily summary correctly updated")
            else:
                print("❌ FAIL: Daily summary not correctly updated")

def test_4_delete_no_meals():
    """Test deleting when no meals exist"""
    print("\n" + "="*70)
    print("TEST 4: Delete When No Meals")
    print("="*70)
    
    with app.app_context():
        user_id = setup_test_data()
        
        # Delete all meals first
        Meal.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        # Try to delete
        result = delete_last_meal(user_id)
        
        print(f"Result: {result['success']}")
        print(f"Message: {result['message']}")
        
        if not result['success'] and result['message'] == 'No meals to delete':
            print("✅ PASS: Correctly handles no meals")
        else:
            print("❌ FAIL: Should fail when no meals")

def test_5_delete_updates_last_meal_id():
    """Test that user.last_meal_id is updated after deletion"""
    print("\n" + "="*70)
    print("TEST 5: Delete Updates User.last_meal_id")
    print("="*70)
    
    with app.app_context():
        user_id = setup_test_data()
        user = User.query.get(user_id)
        
        # Create two completed meals
        meal1 = Meal(
            user_id=user_id,
            meal_type='breakfast',
            processing_status='completed',
            timestamp=datetime(2025, 12, 12, 8, 0, 0)
        )
        db.session.add(meal1)
        db.session.commit()
        
        meal2 = Meal(
            user_id=user_id,
            meal_type='lunch',
            processing_status='completed',
            timestamp=datetime(2025, 12, 12, 12, 0, 0)
        )
        db.session.add(meal2)
        db.session.commit()
        
        print(f"✓ Created meal 1 (breakfast) ID: {meal1.id}")
        print(f"✓ Created meal 2 (lunch) ID: {meal2.id}")
        
        # Set user's last_meal_id to meal2
        user.last_meal_id = meal2.id
        db.session.commit()
        
        print(f"✓ Set user.last_meal_id = {meal2.id}")
        
        # Add food to meal2
        food = FoodItem(
            meal_id=meal2.id,
            name="Salad",
            portion_size_grams=200
        )
        db.session.add(food)
        db.session.commit()
        
        # Delete last meal (meal2)
        result = delete_last_meal(user_id)
        
        print(f"\nResult: {result['success']}")
        
        # Check user.last_meal_id
        db.session.refresh(user)
        
        print(f"User.last_meal_id after delete: {user.last_meal_id}")
        
        if user.last_meal_id == meal1.id:
            print("✅ PASS: User.last_meal_id correctly updated to previous meal")
        else:
            print(f"❌ FAIL: User.last_meal_id should be {meal1.id}, got {user.last_meal_id}")

def cleanup():
    """Clean up test data"""
    print("\n" + "="*70)
    print("CLEANUP")
    print("="*70)
    
    with app.app_context():
        test_phone = "whatsapp:+1234567890"
        user = User.query.filter_by(phone_number=test_phone).first()
        
        if user:
            # Delete all related data (cascade will handle meals, food_items, etc.)
            db.session.delete(user)
            db.session.commit()
            print("✓ Cleaned up test user and related data")

def run_all_tests():
    """Run all test cases"""
    print("\n" + "🧪 " + "="*68)
    print("CANCEL & DELETE MEAL FUNCTIONALITY TESTS")
    print("="*70)
    
    try:
        test_1_cancel_pending_meal()
        test_2_cancel_no_pending_meal()
        test_3_delete_completed_meal()
        test_4_delete_no_meals()
        test_5_delete_updates_last_meal_id()
    finally:
        cleanup()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)

if __name__ == '__main__':
    run_all_tests()
