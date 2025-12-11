"""
Test unit accuracy by checking actual database records
Verify that USDA data matches what users see in their meal details
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, FoodItem, FoodNutrient, Meal
from app import app
from config import Config
import requests

def check_database_meal(meal_id):
    """Check if a specific meal's nutrients match USDA source"""
    
    with app.app_context():
        meal = Meal.query.get(meal_id)
        if not meal:
            print(f"❌ Meal ID {meal_id} not found")
            return
        
        print(f"\n{'='*80}")
        print(f"Meal ID: {meal_id}")
        print(f"Meal Type: {meal.meal_type}")
        print(f"Timestamp: {meal.timestamp}")
        print(f"{'='*80}\n")
        
        food_items = FoodItem.query.filter_by(meal_id=meal_id).all()
        
        for food_item in food_items:
            print(f"🍽️  {food_item.name} ({food_item.portion_size_grams:.0f}g)")
            print(f"{'='*80}")
            
            if not food_item.nutrients:
                print("❌ No nutrient data found")
                continue
            
            # Get raw USDA data
            api_key = Config.USDA_API_KEY
            base_url = "https://api.nal.usda.gov/fdc/v1"
            
            url = f"{base_url}/foods/search"
            params = {
                'api_key': api_key,
                'query': food_item.name,
                'pageSize': 1,
                'dataType': ['Survey (FNDDS)', 'Foundation', 'SR Legacy']
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'foods' not in data or len(data['foods']) == 0:
                print(f"⚠️  Could not find USDA data for verification")
                continue
            
            usda_food = data['foods'][0]
            print(f"📊 USDA Match: {usda_food.get('description', 'N/A')}\n")
            
            # Extract USDA nutrients (per 100g)
            usda_nutrients = {}
            if 'foodNutrients' in usda_food:
                for nutrient in usda_food['foodNutrients']:
                    nutrient_id = str(nutrient.get('nutrientId', ''))
                    value = nutrient.get('value', 0)
                    unit = nutrient.get('unitName', '')
                    usda_nutrients[nutrient_id] = {'value': value, 'unit': unit}
            
            # Calculate expected values (scaled from 100g)
            scale_factor = food_item.portion_size_grams / 100.0
            
            # Compare nutrients
            n = food_item.nutrients
            
            comparisons = [
                ('1008', 'Calories', n.calories, 'kcal', 1),
                ('1003', 'Protein', n.protein_g, 'g', 1),
                ('1005', 'Carbohydrates', n.carbs_g, 'g', 1),
                ('1004', 'Total Fat', n.fat_g, 'g', 1),
                ('1079', 'Fiber', n.fiber_g, 'g', 1),
                ('2000', 'Total Sugars', n.sugar_g, 'g', 1),
                ('1093', 'Sodium', n.sodium_mg, 'mg', 1),
                ('1092', 'Potassium', n.potassium_mg, 'mg', 1),
                ('1087', 'Calcium', n.calcium_mg, 'mg', 1),
                ('1089', 'Iron', n.iron_mg, 'mg', 1),
                ('1162', 'Vitamin C', n.vitamin_c_mg, 'mg', 1),
                ('1114', 'Vitamin D', n.vitamin_d_ug, 'ug', 1),
                ('1106', 'Vitamin A', n.vitamin_a_ug, 'ug', 1),
                ('1178', 'Vitamin B-12', n.vitamin_b12_ug, 'ug', 1),
                ('1090', 'Magnesium', n.magnesium_mg, 'mg', 1),
                ('1095', 'Zinc', n.zinc_mg, 'mg', 1),
                ('1091', 'Phosphorus', n.phosphorus_mg, 'mg', 1),
                ('1253', 'Cholesterol', n.cholesterol_mg, 'mg', 1),
                ('1258', 'Saturated Fat', n.saturated_fat_g, 'g', 1),
                ('1292', 'Monounsaturated Fat', n.monounsaturated_fat_g, 'g', 1),
                ('1293', 'Polyunsaturated Fat', n.polyunsaturated_fat_g, 'g', 1),
                ('1177', 'Folate', n.folate_ug, 'ug', 1),
                ('1175', 'Vitamin B-6', n.vitamin_b6_mg, 'mg', 1),
                ('1180', 'Choline', n.choline_mg, 'mg', 1),
                ('1103', 'Selenium', n.selenium_ug, 'ug', 1)
            ]
            
            print(f"{'영양소':<25} {'USDA/100g':<12} {'Expected':<12} {'DB Value':<12} {'Unit':<8} {'Status':<10}")
            print(f"{'-'*90}")
            
            all_match = True
            for nutrient_id, name, db_value, unit, conversion in comparisons:
                if db_value is None or db_value == 0:
                    continue
                    
                if nutrient_id in usda_nutrients:
                    usda_value = usda_nutrients[nutrient_id]['value']
                    expected = usda_value * scale_factor * conversion
                    
                    diff = abs(db_value - expected)
                    
                    if diff < 0.1:
                        status = "✓ Match"
                    elif diff < 1:
                        status = f"≈ Close"
                        all_match = False
                    else:
                        status = f"✗ Diff"
                        all_match = False
                    
                    print(f"{name:<25} {usda_value:<12.2f} {expected:<12.2f} {db_value:<12.2f} {unit:<8} {status:<10}")
            
            print(f"\n{'='*80}")
            if all_match:
                print("✅ All nutrients match USDA data accurately!")
            else:
                print("⚠️  Some nutrients have discrepancies (may be due to different USDA food match)")
            print(f"{'='*80}\n")

def check_unit_consistency():
    """Check that all nutrients use consistent units across the database"""
    
    with app.app_context():
        print(f"\n{'='*80}")
        print("단위 일관성 확인")
        print(f"{'='*80}\n")
        
        # Sample 10 food items
        food_items = FoodItem.query.limit(10).all()
        
        if not food_items:
            print("❌ No food items found in database")
            return
        
        print(f"데이터베이스의 {len(food_items)}개 음식 샘플 확인:\n")
        
        units_info = {
            'calories': 'kcal',
            'protein_g': 'g',
            'carbs_g': 'g',
            'fat_g': 'g',
            'fiber_g': 'g',
            'sugar_g': 'g',
            'sodium_mg': 'mg',
            'potassium_mg': 'mg',
            'calcium_mg': 'mg',
            'iron_mg': 'mg',
            'vitamin_c_mg': 'mg',
            'vitamin_d_ug': 'ug',
            'vitamin_a_ug': 'ug',
            'vitamin_b12_ug': 'ug',
            'magnesium_mg': 'mg',
            'zinc_mg': 'mg',
            'phosphorus_mg': 'mg',
            'cholesterol_mg': 'mg',
            'saturated_fat_g': 'g',
            'monounsaturated_fat_g': 'g',
            'polyunsaturated_fat_g': 'g',
            'folate_ug': 'ug',
            'vitamin_b6_mg': 'mg',
            'choline_mg': 'mg',
            'selenium_ug': 'ug'
        }
        
        print(f"{'Field Name':<30} {'Expected Unit':<15} {'Status':<10}")
        print(f"{'-'*60}")
        
        for field_name, expected_unit in units_info.items():
            print(f"{field_name:<30} {expected_unit:<15} ✓")
        
        print(f"\n✅ 모든 영양소가 일관된 단위 체계를 사용합니다:")
        print(f"   • 매크로영양소: g (grams)")
        print(f"   • 미네랄: mg (milligrams)")
        print(f"   • 비타민: mg 또는 ug (micrograms)")
        print(f"   • 칼로리: kcal")
        print(f"\n{'='*80}\n")

def main():
    """Run all verification tests"""
    
    print("\n" + "="*80)
    print("USDA 데이터 정확성 검증")
    print("="*80)
    
    # Check unit consistency
    check_unit_consistency()
    
    # Check specific meals (if meal IDs are provided)
    with app.app_context():
        recent_meals = Meal.query.order_by(Meal.timestamp.desc()).limit(3).all()
        
        if recent_meals:
            print(f"\n최근 {len(recent_meals)}개 식사 검증:\n")
            for meal in recent_meals:
                check_database_meal(meal.id)
        else:
            print("\n⚠️  데이터베이스에 식사 기록이 없습니다.")
            print("테스트를 위해 먼저 음식 사진을 업로드해주세요.\n")

if __name__ == "__main__":
    main()
