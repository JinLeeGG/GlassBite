"""
Test if the proposed 25 nutrients are available across diverse food items.
Tests 30 different foods representing various categories.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.usda_service import USDAService

def test_25_nutrients():
    usda_service = USDAService()
    
    # 25 nutrients we want to store (mapped to our keys in extra_nutrients)
    target_nutrients = {
        # Tier 1 (10 essential) - using our internal keys
        'calories': 'Energy (calories)',
        'protein_g': 'Protein',
        'carbs_g': 'Carbohydrates',
        'fat_g': 'Total Fat',
        'fiber_g': 'Fiber',
        'sugar_g': 'Sugars, total',
        'sodium_mg': 'Sodium',
        'potassium_mg': 'Potassium',
        'calcium_mg': 'Calcium',
        'iron_mg': 'Iron',
        
        # Tier 2 (8 important)
        'vitamin_c_mg': 'Vitamin C',
        'vitamin_d_ug': 'Vitamin D',
        'vitamin_a_ug': 'Vitamin A, RAE',
        'vitamin_b12_ug': 'Vitamin B-12',
        'magnesium_mg': 'Magnesium',
        'zinc_mg': 'Zinc',
        'phosphorus_mg': 'Phosphorus',
        'cholesterol_mg': 'Cholesterol',
        
        # Tier 3 (7 supplementary)
        'saturated_fat_g': 'Saturated fatty acids',
        'monounsaturated_fat_g': 'Monounsaturated fatty acids',
        'polyunsaturated_fat_g': 'Polyunsaturated fatty acids',
        'folate_ug': 'Folate, total',
        'vitamin_b6_mg': 'Vitamin B-6',
        'choline_mg': 'Choline, total',
        'selenium_ug': 'Selenium'
    }
    
    # 30 diverse foods to test
    test_foods = [
        # Proteins
        "chicken breast",
        "salmon",
        "egg",
        "tofu",
        "beef steak",
        "pork chop",
        "shrimp",
        "turkey",
        
        # Dairy
        "milk",
        "yogurt",
        "cheddar cheese",
        
        # Grains
        "brown rice",
        "white rice",
        "oatmeal",
        "whole wheat bread",
        "pasta",
        
        # Vegetables
        "broccoli",
        "spinach",
        "carrot",
        "tomato",
        "sweet potato",
        "bell pepper",
        
        # Fruits
        "banana",
        "apple",
        "orange",
        "strawberry",
        
        # Legumes & Nuts
        "black beans",
        "peanut butter",
        "almonds",
        
        # Other
        "avocado"
    ]
    
    print(f"Testing 25 proposed nutrients across {len(test_foods)} diverse foods\n")
    print("=" * 100)
    
    # Track nutrient availability
    nutrient_counts = {nid: 0 for nid in target_nutrients.keys()}
    total_foods = len(test_foods)
    food_results = []
    
    for food_name in test_foods:
        print(f"\nTesting: {food_name}")
        result = usda_service.get_nutrition_data(food_name, 100)
        
        if result:
            found_nutrients = []
            missing_nutrients = []
            
            # Check each target nutrient
            for nutrient_key, nutrient_name in target_nutrients.items():
                found = False
                value = None
                
                # Check in main nutrition dict first
                if nutrient_key in result:
                    value = result[nutrient_key]
                    if value is not None:
                        found = True
                # If not in main, check in extra_nutrients
                elif 'extra_nutrients' in result and nutrient_key in result['extra_nutrients']:
                    value = result['extra_nutrients'][nutrient_key]
                    if value is not None:
                        found = True
                
                if found:
                    nutrient_counts[nutrient_key] += 1
                    found_nutrients.append(f"{nutrient_name}: {value}")
                else:
                    missing_nutrients.append(nutrient_name)
            
            found_count = len(found_nutrients)
            missing_count = len(missing_nutrients)
            coverage = (found_count / 25) * 100
            
            print(f"  ✓ Found: {found_count}/25 nutrients ({coverage:.1f}%)")
            
            if missing_count > 0 and missing_count <= 5:
                print(f"  ✗ Missing ({missing_count}): {', '.join(missing_nutrients)}")
            elif missing_count > 5:
                print(f"  ✗ Missing {missing_count} nutrients")
            
            food_results.append({
                'name': food_name,
                'found': found_count,
                'missing': missing_count,
                'coverage': coverage,
                'missing_list': missing_nutrients
            })
        else:
            print(f"  ✗ Failed to get nutrition data")
            food_results.append({
                'name': food_name,
                'found': 0,
                'missing': 25,
                'coverage': 0,
                'missing_list': list(target_nutrients.values())
            })
    
    # Summary statistics
    print("\n" + "=" * 100)
    print("\nSUMMARY: Nutrient Availability Analysis")
    print("=" * 100)
    
    print("\n1. BY NUTRIENT (sorted by availability):")
    print("-" * 100)
    
    nutrient_availability = []
    for nutrient_id, nutrient_name in target_nutrients.items():
        count = nutrient_counts[nutrient_id]
        percentage = (count / total_foods) * 100
        nutrient_availability.append((nutrient_name, count, percentage))
    
    # Sort by availability (descending)
    nutrient_availability.sort(key=lambda x: x[1], reverse=True)
    
    tier1_nutrients = set(['Energy (calories)', 'Protein', 'Carbohydrates', 'Total Fat', 
                          'Fiber', 'Sugars, total', 'Sodium', 'Potassium', 'Calcium', 'Iron'])
    tier2_nutrients = set(['Vitamin C', 'Vitamin D', 'Vitamin A, RAE', 'Vitamin B-12', 
                          'Magnesium', 'Zinc', 'Phosphorus', 'Cholesterol'])
    tier3_nutrients = set(['Saturated fatty acids', 'Monounsaturated fatty acids', 
                          'Polyunsaturated fatty acids', 'Folate, total', 'Vitamin B-6', 
                          'Choline, total', 'Selenium'])
    
    for nutrient_name, count, percentage in nutrient_availability:
        tier = ""
        if nutrient_name in tier1_nutrients:
            tier = "[Tier 1]"
        elif nutrient_name in tier2_nutrients:
            tier = "[Tier 2]"
        elif nutrient_name in tier3_nutrients:
            tier = "[Tier 3]"
        
        bar_length = int(percentage / 2)  # Scale to 50 chars max
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{tier:10} {nutrient_name:35} {bar} {count:2}/{total_foods} ({percentage:5.1f}%)")
    
    print("\n2. BY FOOD (sorted by coverage):")
    print("-" * 100)
    
    # Sort foods by coverage
    food_results.sort(key=lambda x: x['coverage'], reverse=True)
    
    for food in food_results:
        bar_length = int(food['coverage'] / 2)  # Scale to 50 chars max
        bar = "█" * bar_length + "░" * (50 - bar_length)
        status = "✓" if food['coverage'] >= 80 else "⚠" if food['coverage'] >= 60 else "✗"
        print(f"{status} {food['name']:20} {bar} {food['found']:2}/25 ({food['coverage']:5.1f}%)")
        
        # Show missing nutrients for foods with low coverage
        if food['coverage'] < 60 and len(food['missing_list']) > 0:
            print(f"   Missing: {', '.join(food['missing_list'][:5])}" + 
                  (f" +{len(food['missing_list'])-5} more" if len(food['missing_list']) > 5 else ""))
    
    print("\n3. TIER ANALYSIS:")
    print("-" * 100)
    
    tier1_count = sum(1 for n, c, p in nutrient_availability if n in tier1_nutrients and p >= 80)
    tier2_count = sum(1 for n, c, p in nutrient_availability if n in tier2_nutrients and p >= 80)
    tier3_count = sum(1 for n, c, p in nutrient_availability if n in tier3_nutrients and p >= 80)
    
    print(f"Tier 1 (Essential):     {tier1_count}/10 nutrients available in ≥80% of foods")
    print(f"Tier 2 (Important):     {tier2_count}/8 nutrients available in ≥80% of foods")
    print(f"Tier 3 (Supplementary): {tier3_count}/7 nutrients available in ≥80% of foods")
    
    avg_coverage = sum(f['coverage'] for f in food_results) / len(food_results)
    print(f"\nAverage coverage across all foods: {avg_coverage:.1f}%")
    
    foods_with_good_coverage = sum(1 for f in food_results if f['coverage'] >= 80)
    print(f"Foods with ≥80% coverage: {foods_with_good_coverage}/{total_foods} ({foods_with_good_coverage/total_foods*100:.1f}%)")
    
    print("\n4. RECOMMENDATIONS:")
    print("-" * 100)
    
    # Find nutrients with low availability
    low_availability = [(n, c, p) for n, c, p in nutrient_availability if p < 60]
    
    if low_availability:
        print("⚠ The following nutrients are available in <60% of foods:")
        for nutrient_name, count, percentage in low_availability:
            tier = ""
            if nutrient_name in tier1_nutrients:
                tier = "[Tier 1 - CRITICAL]"
            elif nutrient_name in tier2_nutrients:
                tier = "[Tier 2]"
            elif nutrient_name in tier3_nutrients:
                tier = "[Tier 3]"
            print(f"  {tier:20} {nutrient_name:35} {count}/{total_foods} ({percentage:.1f}%)")
        
        print("\n💡 Consider:")
        print("  - Remove nutrients with <60% availability from required fields")
        print("  - Make Tier 3 nutrients optional (allow NULL values)")
        print("  - Focus on Tier 1 & 2 for AI recommendations")
    else:
        print("✓ All 25 nutrients have good availability (≥60% of foods)")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    test_25_nutrients()
