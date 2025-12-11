"""
Test USDA unit conversion and user display accuracy
USDA API returns nutrients in various units (g, mg, ug)
This test verifies:
1. Raw USDA data units
2. Conversion to user display units
3. Accuracy of displayed values
"""

import requests
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.usda_service import USDAService

def get_raw_usda_data(food_name):
    """Get raw USDA data without any processing"""
    api_key = Config.USDA_API_KEY
    base_url = "https://api.nal.usda.gov/fdc/v1"
    
    print(f"\n{'='*80}")
    print(f"검색어: {food_name}")
    print(f"{'='*80}\n")
    
    # Search for food
    url = f"{base_url}/foods/search"
    params = {
        'api_key': api_key,
        'query': food_name,
        'pageSize': 1,
        'dataType': ['Survey (FNDDS)', 'Foundation', 'SR Legacy']
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    if 'foods' not in data or len(data['foods']) == 0:
        print(f"❌ '{food_name}' 검색 결과 없음")
        return None
    
    food = data['foods'][0]
    print(f"🔍 검색 결과: {food.get('description', 'N/A')}")
    print(f"   FDC ID: {food.get('fdcId', 'N/A')}")
    print(f"   Data Type: {food.get('dataType', 'N/A')}\n")
    
    return food

def print_nutrient_comparison(food_name, portion_grams):
    """Compare raw USDA data with processed user display values"""
    
    # 1. Get raw USDA data
    raw_food = get_raw_usda_data(food_name)
    if not raw_food:
        return
    
    print(f"📊 USDA 원본 데이터 (per 100g):")
    print(f"{'='*80}")
    
    # Extract raw nutrients
    raw_nutrients = {}
    if 'foodNutrients' in raw_food:
        for nutrient in raw_food['foodNutrients']:
            nutrient_id = str(nutrient.get('nutrientId', ''))
            nutrient_name = nutrient.get('nutrientName', '')
            value = nutrient.get('value', 0)
            unit = nutrient.get('unitName', '')
            
            # Store all nutrients
            raw_nutrients[nutrient_id] = {
                'name': nutrient_name,
                'value': value,
                'unit': unit
            }
    
    # Define nutrient mapping
    nutrient_map = {
        '1008': ('Calories', 'KCAL'),
        '1003': ('Protein', 'G'),
        '1005': ('Carbohydrates', 'G'),
        '1004': ('Total Fat', 'G'),
        '1079': ('Fiber', 'G'),
        '2000': ('Total Sugars', 'G'),
        '1093': ('Sodium', 'MG'),
        '1092': ('Potassium', 'MG'),
        '1087': ('Calcium', 'MG'),
        '1089': ('Iron', 'MG'),
        '1162': ('Vitamin C', 'MG'),
        '1114': ('Vitamin D', 'UG'),
        '1106': ('Vitamin A', 'UG'),
        '1178': ('Vitamin B-12', 'UG'),
        '1090': ('Magnesium', 'MG'),
        '1095': ('Zinc', 'MG'),
        '1091': ('Phosphorus', 'MG'),
        '1253': ('Cholesterol', 'MG'),
        '1258': ('Saturated Fat', 'G'),
        '1292': ('Monounsaturated Fat', 'G'),
        '1293': ('Polyunsaturated Fat', 'G'),
        '1177': ('Folate', 'UG'),
        '1175': ('Vitamin B-6', 'MG'),
        '1180': ('Choline', 'MG'),
        '1103': ('Selenium', 'UG')
    }
    
    print(f"{'영양소':<25} {'USDA 값':<15} {'단위':<10}")
    print(f"{'-'*50}")
    
    for nutrient_id, (name, expected_unit) in nutrient_map.items():
        if nutrient_id in raw_nutrients:
            n = raw_nutrients[nutrient_id]
            value = n['value']
            unit = n['unit']
            
            # Check unit match
            unit_status = "✓" if unit == expected_unit else f"⚠️ ({unit})"
            print(f"{name:<25} {value:<15.2f} {expected_unit:<10} {unit_status}")
    
    # 2. Get processed data from USDAService
    print(f"\n{'='*80}")
    print(f"🍽️  처리된 데이터 (portion: {portion_grams}g):")
    print(f"{'='*80}")
    
    usda_service = USDAService()
    processed_data = usda_service.get_nutrition_data(food_name, portion_grams)
    
    if not processed_data:
        print("❌ 처리된 데이터를 가져올 수 없음")
        return
    
    # Calculate scale factor
    scale_factor = portion_grams / 100.0
    
    print(f"\n{'영양소':<25} {'USDA/100g':<12} {'Scale':<10} {'User Display':<15} {'단위':<10} {'검증':<10}")
    print(f"{'-'*85}")
    
    # Main nutrients
    main_nutrients = [
        ('1008', 'Calories', processed_data.get('calories', 0), 'kcal'),
        ('1003', 'Protein', processed_data.get('protein_g', 0), 'g'),
        ('1005', 'Carbohydrates', processed_data.get('carbs_g', 0), 'g'),
        ('1004', 'Total Fat', processed_data.get('fat_g', 0), 'g'),
        ('1079', 'Fiber', processed_data.get('fiber_g', 0), 'g'),
        ('2000', 'Total Sugars', processed_data.get('sugar_g', 0), 'g'),
        ('1093', 'Sodium', processed_data.get('sodium_mg', 0), 'mg')
    ]
    
    for nutrient_id, name, user_value, display_unit in main_nutrients:
        if nutrient_id in raw_nutrients:
            raw_value = raw_nutrients[nutrient_id]['value']
            raw_unit = raw_nutrients[nutrient_id]['unit']
            expected_value = raw_value * scale_factor
            
            # Check accuracy
            diff = abs(user_value - expected_value)
            accuracy = "✓" if diff < 0.1 else f"⚠️ ({diff:.2f})"
            
            print(f"{name:<25} {raw_value:<12.2f} x{scale_factor:<9.2f} = {user_value:<12.2f} {display_unit:<10} {accuracy}")
    
    # Extra nutrients
    extra_nutrients = processed_data.get('extra_nutrients', {})
    
    if extra_nutrients:
        print(f"\n추가 영양소 (Extra Nutrients):")
        print(f"{'-'*85}")
        
        extra_map = [
            ('1092', 'Potassium', extra_nutrients.get('potassium_mg', 0), 'mg'),
            ('1087', 'Calcium', extra_nutrients.get('calcium_mg', 0), 'mg'),
            ('1089', 'Iron', extra_nutrients.get('iron_mg', 0), 'mg'),
            ('1162', 'Vitamin C', extra_nutrients.get('vitamin_c_mg', 0), 'mg'),
            ('1114', 'Vitamin D', extra_nutrients.get('vitamin_d_ug', 0), 'ug'),
            ('1106', 'Vitamin A', extra_nutrients.get('vitamin_a_ug', 0), 'ug'),
            ('1178', 'Vitamin B-12', extra_nutrients.get('vitamin_b12_ug', 0), 'ug'),
            ('1090', 'Magnesium', extra_nutrients.get('magnesium_mg', 0), 'mg'),
            ('1095', 'Zinc', extra_nutrients.get('zinc_mg', 0), 'mg'),
            ('1091', 'Phosphorus', extra_nutrients.get('phosphorus_mg', 0), 'mg'),
            ('1253', 'Cholesterol', extra_nutrients.get('cholesterol_mg', 0), 'mg'),
            ('1258', 'Saturated Fat', extra_nutrients.get('saturated_fat_g', 0), 'g'),
            ('1292', 'Monounsaturated Fat', extra_nutrients.get('monounsaturated_fat_g', 0), 'g'),
            ('1293', 'Polyunsaturated Fat', extra_nutrients.get('polyunsaturated_fat_g', 0), 'g'),
            ('1177', 'Folate', extra_nutrients.get('folate_ug', 0), 'ug'),
            ('1175', 'Vitamin B-6', extra_nutrients.get('vitamin_b6_mg', 0), 'mg'),
            ('1180', 'Choline', extra_nutrients.get('choline_mg', 0), 'mg'),
            ('1103', 'Selenium', extra_nutrients.get('selenium_ug', 0), 'ug')
        ]
        
        for nutrient_id, name, user_value, display_unit in extra_map:
            if nutrient_id in raw_nutrients and user_value > 0:
                raw_value = raw_nutrients[nutrient_id]['value']
                raw_unit = raw_nutrients[nutrient_id]['unit']
                expected_value = raw_value * scale_factor
                
                # Check unit conversion
                if raw_unit == 'UG' and display_unit == 'ug':
                    # Correct: ug to ug (no conversion)
                    unit_conversion = "✓"
                elif raw_unit == 'MG' and display_unit == 'mg':
                    # Correct: mg to mg (no conversion)
                    unit_conversion = "✓"
                elif raw_unit == 'G' and display_unit == 'g':
                    # Correct: g to g (no conversion)
                    unit_conversion = "✓"
                elif raw_unit == 'MG' and display_unit == 'g':
                    # Need conversion: mg to g
                    expected_value = expected_value / 1000
                    unit_conversion = "🔄 (mg→g)"
                elif raw_unit == 'UG' and display_unit == 'g':
                    # Need conversion: ug to g
                    expected_value = expected_value / 1000000
                    unit_conversion = "🔄 (ug→g)"
                else:
                    unit_conversion = f"⚠️ ({raw_unit}→{display_unit})"
                
                # Check accuracy
                diff = abs(user_value - expected_value)
                accuracy = "✓" if diff < 0.1 else f"⚠️ Diff: {diff:.2f}"
                
                print(f"{name:<25} {raw_value:<12.2f} x{scale_factor:<9.2f} = {user_value:<12.2f} {display_unit:<10} {unit_conversion} {accuracy}")

def main():
    """Run tests with different foods and portions"""
    
    test_cases = [
        ("chicken breast", 200),  # Protein-rich food
        ("salmon", 150),           # Fish with omega-3
        ("brown rice", 180),       # Carb-rich food
        ("broccoli", 100),         # Vegetable with vitamins
        ("egg", 50)                # Small portion test
    ]
    
    for food_name, portion_grams in test_cases:
        print_nutrient_comparison(food_name, portion_grams)
        print("\n" + "="*80 + "\n")
    
    # Summary
    print("\n" + "🔍 단위 변환 규칙 요약:")
    print("="*80)
    print("USDA API는 모든 값을 per 100g로 제공합니다.")
    print("\n단위 변환:")
    print("  • Calories (KCAL) → kcal (변환 없음)")
    print("  • Macronutrients (G) → g (변환 없음)")
    print("  • Minerals (MG) → mg (변환 없음)")
    print("  • Vitamins (UG/MG) → ug/mg (변환 없음)")
    print("\n⚠️ 만약 g로 통일하려면:")
    print("  • MG → G: 값 / 1000")
    print("  • UG → G: 값 / 1000000")
    print("\n현재 시스템은 원본 단위를 유지하여 표시합니다.")
    print("="*80)

if __name__ == "__main__":
    main()
