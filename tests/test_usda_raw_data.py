"""
Test to see raw USDA API response structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.usda_service import USDAService
import json

def test_raw_data():
    usda_service = USDAService()
    
    # Search for chicken breast
    print("Searching for: chicken breast")
    print("=" * 100)
    
    results = usda_service._search_food("chicken breast")
    
    if results and len(results) > 0:
        food = results[0]
        
        print(f"\nFood ID: {food.get('fdcId')}")
        print(f"Description: {food.get('description')}")
        print(f"Data Type: {food.get('dataType')}")
        print(f"\nAvailable nutrients:")
        print("-" * 100)
        
        if 'foodNutrients' in food:
            # Group nutrients by ID
            nutrient_dict = {}
            for nutrient in food['foodNutrients']:
                nutrient_id = nutrient.get('nutrientId')
                nutrient_number = nutrient.get('nutrientNumber')
                nutrient_name = nutrient.get('nutrientName')
                value = nutrient.get('value')
                unit = nutrient.get('unitName')
                
                if nutrient_id:
                    nutrient_dict[nutrient_id] = {
                        'number': nutrient_number,
                        'name': nutrient_name,
                        'value': value,
                        'unit': unit
                    }
            
            # Sort by nutrient ID
            for nid in sorted(nutrient_dict.keys()):
                n = nutrient_dict[nid]
                print(f"ID: {nid:4} | Number: {n['number']:3} | {n['name']:40} | {n['value']:8} {n['unit']}")
        
        print("\n" + "=" * 100)
        print("\nTarget nutrients mapping:")
        print("-" * 100)
        
        target_nutrients = {
            '1008': 'Energy (calories)',
            '1003': 'Protein',
            '1005': 'Carbohydrates',
            '1004': 'Total Fat',
            '1079': 'Fiber',
            '2000': 'Sugars, total',
            '1093': 'Sodium',
            '1092': 'Potassium',
            '1087': 'Calcium',
            '1089': 'Iron',
            '1162': 'Vitamin C',
            '1114': 'Vitamin D',
            '1106': 'Vitamin A, RAE',
            '1178': 'Vitamin B-12',
            '1090': 'Magnesium',
            '1095': 'Zinc',
            '1091': 'Phosphorus',
            '1253': 'Cholesterol',
            '1258': 'Saturated fatty acids',
            '1292': 'Monounsaturated fatty acids',
            '1293': 'Polyunsaturated fatty acids',
            '1177': 'Folate, total',
            '1175': 'Vitamin B-6',
            '1180': 'Choline, total',
            '1103': 'Selenium'
        }
        
        if 'foodNutrients' in food:
            for nutrient in food['foodNutrients']:
                nutrient_id = str(nutrient.get('nutrientId'))
                if nutrient_id in target_nutrients:
                    nutrient_name = nutrient.get('nutrientName')
                    value = nutrient.get('value')
                    unit = nutrient.get('unitName')
                    print(f"✓ Found: {target_nutrients[nutrient_id]:35} | ID: {nutrient_id:4} | {value} {unit}")
        
        # Check which are missing
        found_ids = set(str(n.get('nutrientId')) for n in food.get('foodNutrients', []))
        missing = set(target_nutrients.keys()) - found_ids
        if missing:
            print(f"\n✗ Missing ({len(missing)}):")
            for nid in missing:
                print(f"  - {target_nutrients[nid]} (ID: {nid})")
    
    else:
        print("No results found!")

if __name__ == "__main__":
    test_raw_data()
