"""
Debug USDA API response to understand the data structure
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.usda_service import USDAService

def debug_single_food():
    usda = USDAService()
    
    # Test with egg (known to be wrong)
    food_name = "egg"
    portion_grams = 50
    
    print("="*70)
    print(f"🔍 Debugging: {food_name} ({portion_grams}g)")
    print("="*70)
    
    # Search
    search_results = usda._search_food(food_name)
    
    if search_results:
        food_data = search_results[0]
        
        print(f"\n📋 Food Item:")
        print(f"   Description: {food_data.get('description')}")
        print(f"   FDC ID: {food_data.get('fdcId')}")
        print(f"   Data Type: {food_data.get('dataType')}")
        print(f"   Serving Size: {food_data.get('servingSize', 'N/A')}")
        print(f"   Serving Size Unit: {food_data.get('servingSizeUnit', 'N/A')}")
        
        # Print raw nutrient data
        print(f"\n🧪 Raw Nutrient Data (from USDA):")
        if 'foodNutrients' in food_data:
            for nutrient in food_data['foodNutrients'][:10]:  # First 10
                name = nutrient.get('nutrientName', 'N/A')
                value = nutrient.get('value', 0)
                unit = nutrient.get('unitName', 'N/A')
                print(f"   {name}: {value} {unit}")
        
        # Extract and scale
        nutrition = usda._extract_nutrients(food_data, portion_grams)
        
        print(f"\n✅ Scaled to {portion_grams}g:")
        print(f"   Calories: {nutrition['calories']:.1f} cal")
        print(f"   Protein:  {nutrition['protein_g']:.1f}g")
        print(f"   Carbs:    {nutrition['carbs_g']:.1f}g")
        print(f"   Fat:      {nutrition['fat_g']:.1f}g")
        
        # Manual calculation check
        print(f"\n🧮 Manual Check:")
        print(f"   If USDA value is per 100g and we want {portion_grams}g:")
        print(f"   Scale factor should be: {portion_grams}/100 = {portion_grams/100}")
        
        # Find Energy nutrient
        for nutrient in food_data['foodNutrients']:
            if 'Energy' in nutrient.get('nutrientName', ''):
                energy_per_100g = nutrient.get('value', 0)
                print(f"   Energy from USDA: {energy_per_100g} kcal (per 100g)")
                print(f"   Expected for {portion_grams}g: {energy_per_100g * (portion_grams/100):.1f} kcal")
                print(f"   Actual result: {nutrition['calories']:.1f} kcal")
                if abs(nutrition['calories'] - energy_per_100g * (portion_grams/100)) > 1:
                    print(f"   ⚠️  MISMATCH! Calculation is wrong!")
                else:
                    print(f"   ✅ Calculation is correct!")
                break

if __name__ == '__main__':
    debug_single_food()
