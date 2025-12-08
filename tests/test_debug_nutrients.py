"""
Debug test to check what's actually in extra_nutrients
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.usda_service import USDAService
import json

usda_service = USDAService()

# Test one food
food_name = "chicken breast"
result = usda_service.get_nutrition_data(food_name, 100)

print(f"Testing: {food_name}")
print("=" * 100)
print("\nMain nutrients:")
for key, value in result.items():
    if key != 'extra_nutrients':
        print(f"  {key}: {value}")

print("\nExtra nutrients:")
if 'extra_nutrients' in result:
    extra = result['extra_nutrients']
    print(f"  Type: {type(extra)}")
    print(f"  Keys: {list(extra.keys()) if extra else 'empty'}")
    for key, value in extra.items():
        print(f"  {key}: {value}")
else:
    print("  NO extra_nutrients key found!")

print("\n" + "=" * 100)
print("\nFull JSON:")
print(json.dumps(result, indent=2))
