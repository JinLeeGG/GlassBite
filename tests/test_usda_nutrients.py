"""
Test to see ALL nutrients available from USDA API
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.usda_service import USDAService

def test_all_nutrients():
    """Test multiple foods to see what nutrients USDA provides"""
    usda = USDAService()
    
    # Test different food types
    test_foods = [
        ("chicken breast", 100),
        ("banana", 100),
        ("broccoli", 100),
        ("salmon", 100),
        ("egg", 50),
        ("milk", 240),
        ("brown rice", 100),
        ("spinach", 100)
    ]
    
    all_nutrients = set()
    nutrient_frequency = {}
    
    print("=" * 80)
    print("🔬 USDA API Nutrient Analysis")
    print("=" * 80)
    
    for food_name, portion in test_foods:
        print(f"\n{'='*80}")
        print(f"📋 Testing: {food_name} ({portion}g)")
        print(f"{'='*80}")
        
        # Search
        search_results = usda._search_food(food_name)
        
        if not search_results:
            print(f"   ❌ No results found")
            continue
        
        food_data = search_results[0]
        
        print(f"\n   Description: {food_data.get('description')}")
        print(f"   FDC ID: {food_data.get('fdcId')}")
        print(f"   Data Type: {food_data.get('dataType')}")
        
        if 'foodNutrients' in food_data:
            print(f"\n   🧪 Available Nutrients ({len(food_data['foodNutrients'])} total):")
            print(f"   {'Nutrient Name':<50} {'Value':>10} {'Unit':>10}")
            print(f"   {'-'*72}")
            
            for nutrient in food_data['foodNutrients']:
                name = nutrient.get('nutrientName', 'N/A')
                value = nutrient.get('value', 0)
                unit = nutrient.get('unitName', 'N/A')
                
                # Track all unique nutrients
                all_nutrients.add(name)
                nutrient_frequency[name] = nutrient_frequency.get(name, 0) + 1
                
                # Print if value is not zero
                if value > 0:
                    print(f"   {name:<50} {value:>10.2f} {unit:>10}")
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"📊 NUTRIENT SUMMARY")
    print(f"{'='*80}")
    print(f"\nTotal unique nutrients found: {len(all_nutrients)}")
    print(f"\nNutrients by frequency (found in X out of {len(test_foods)} foods):")
    print(f"{'Nutrient Name':<50} {'Frequency':>10}")
    print(f"{'-'*62}")
    
    # Sort by frequency
    sorted_nutrients = sorted(nutrient_frequency.items(), key=lambda x: x[1], reverse=True)
    
    for nutrient, count in sorted_nutrients:
        print(f"{nutrient:<50} {count:>10}/{len(test_foods)}")
    
    # Categorize
    print(f"\n\n{'='*80}")
    print(f"📂 NUTRIENTS BY CATEGORY")
    print(f"{'='*80}")
    
    categories = {
        'Energy': [],
        'Protein': [],
        'Fat': [],
        'Carbohydrate': [],
        'Fiber': [],
        'Sugar': [],
        'Minerals': [],
        'Vitamins': [],
        'Amino Acids': [],
        'Other': []
    }
    
    for nutrient in all_nutrients:
        categorized = False
        
        if 'Energy' in nutrient:
            categories['Energy'].append(nutrient)
            categorized = True
        if 'Protein' in nutrient or 'Nitrogen' in nutrient:
            categories['Protein'].append(nutrient)
            categorized = True
        if 'lipid' in nutrient or 'Fat' in nutrient or 'fatty' in nutrient.lower() or 'Cholesterol' in nutrient:
            categories['Fat'].append(nutrient)
            categorized = True
        if 'Carbohydrate' in nutrient or 'Starch' in nutrient:
            categories['Carbohydrate'].append(nutrient)
            categorized = True
        if 'Fiber' in nutrient:
            categories['Fiber'].append(nutrient)
            categorized = True
        if 'Sugar' in nutrient or 'Fructose' in nutrient or 'Glucose' in nutrient or 'Lactose' in nutrient:
            categories['Sugar'].append(nutrient)
            categorized = True
        if any(mineral in nutrient for mineral in ['Calcium', 'Iron', 'Magnesium', 'Phosphorus', 'Potassium', 'Sodium', 'Zinc', 'Copper', 'Manganese', 'Selenium']):
            categories['Minerals'].append(nutrient)
            categorized = True
        if 'Vitamin' in nutrient or 'Retinol' in nutrient or 'Carotene' in nutrient or 'Thiamin' in nutrient or 'Riboflavin' in nutrient or 'Niacin' in nutrient or 'Folate' in nutrient or 'Choline' in nutrient:
            categories['Vitamins'].append(nutrient)
            categorized = True
        if any(aa in nutrient for aa in ['Tryptophan', 'Threonine', 'Isoleucine', 'Leucine', 'Lysine', 'Methionine', 'Cystine', 'Phenylalanine', 'Tyrosine', 'Valine', 'Arginine', 'Histidine', 'Alanine', 'Aspartic', 'Glutamic', 'Glycine', 'Proline', 'Serine']):
            categories['Amino Acids'].append(nutrient)
            categorized = True
        
        if not categorized:
            categories['Other'].append(nutrient)
    
    for category, nutrients in categories.items():
        if nutrients:
            print(f"\n{category} ({len(nutrients)}):")
            for nutrient in sorted(nutrients):
                freq = nutrient_frequency.get(nutrient, 0)
                print(f"  - {nutrient} ({freq}/{len(test_foods)})")
    
    print(f"\n{'='*80}")
    print(f"✅ Analysis Complete!")
    print(f"{'='*80}")

if __name__ == '__main__':
    test_all_nutrients()
