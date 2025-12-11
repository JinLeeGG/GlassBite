"""
Test Edge Cases for Dietary Restriction / Allergen Detection System
Tests various edge cases and boundary conditions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.allergen_service import allergen_service

def print_test_header(test_name):
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")

def print_result(validation_result):
    print(f"\nHas Violations: {validation_result['has_violations']}")
    print(f"Violations: {len(validation_result['violations'])}")
    if validation_result['violations']:
        for v in validation_result['violations']:
            print(f"  - {v['food_name']}: {v['allergen_display']} ({v['ingredient']}) [{v['severity']}]")
    print(f"Safe Foods: {validation_result['safe_foods']}")
    print(f"Summary: {validation_result['summary']}")

# =============================================================================
# EDGE CASE 1: Empty/Null Inputs
# =============================================================================
print_test_header("Edge Case 1: Empty User Restrictions")
user_restrictions = allergen_service.parse_user_restrictions("")
print(f"Parsed: {user_restrictions}")

foods = [
    {'name': 'cheese pizza', 'detected_allergens': ['dairy', 'gluten'], 'detected_ingredients': ['mozzarella', 'wheat dough']},
    {'name': 'peanut butter', 'detected_allergens': ['nuts'], 'detected_ingredients': ['peanuts']}
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == False, "Should have no violations with empty restrictions"

# =============================================================================
# EDGE CASE 2: Multiple Allergens in Single Food
# =============================================================================
print_test_header("Edge Case 2: Multiple Allergens in Single Food")
user_restrictions = allergen_service.parse_user_restrictions("dairy,nuts,gluten")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {
        'name': 'almond milk cheese pizza',
        'detected_allergens': ['dairy', 'nuts', 'gluten'],
        'detected_ingredients': ['mozzarella cheese', 'almond', 'wheat flour']
    }
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Should detect multiple allergens"
assert len(result['violations']) == 3, "Should have 3 violations"

# =============================================================================
# EDGE CASE 3: Hidden Ingredients (Cross-contamination)
# =============================================================================
print_test_header("Edge Case 3: Hidden Ingredients in 'Plain' Foods")
user_restrictions = allergen_service.parse_user_restrictions("dairy")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'fried rice with butter', 'detected_allergens': ['dairy'], 'detected_ingredients': ['butter']},
    {'name': 'salad with cheese crumbles', 'detected_allergens': ['dairy'], 'detected_ingredients': ['cheese']},
    {'name': 'bread with milk', 'detected_allergens': ['dairy', 'gluten'], 'detected_ingredients': ['milk', 'wheat']}
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Should detect hidden dairy"
assert len(result['violations']) == 3, "All items contain dairy"

# =============================================================================
# EDGE CASE 4: Vegan vs Vegetarian Conflicts
# =============================================================================
print_test_header("Edge Case 4: Vegan Restrictions (stricter than Vegetarian)")
user_restrictions = allergen_service.parse_user_restrictions("vegan")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'chicken breast', 'detected_allergens': ['meat'], 'detected_ingredients': ['chicken']},
    {'name': 'cheese omelette', 'detected_allergens': ['dairy', 'eggs'], 'detected_ingredients': ['cheese', 'eggs']},
    {'name': 'salmon sushi', 'detected_allergens': ['fish'], 'detected_ingredients': ['salmon']},
    {'name': 'tofu salad', 'detected_allergens': ['soy'], 'detected_ingredients': ['tofu']}  # Soy is vegan-safe
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Vegan should block meat, dairy, eggs, fish"
assert len(result['violations']) >= 3, "Should have at least 3 violations"
assert 'tofu salad' in result['safe_foods'], "Tofu should be safe for vegans"

# =============================================================================
# EDGE CASE 5: Halal Restrictions (Pork + Alcohol)
# =============================================================================
print_test_header("Edge Case 5: Halal Restrictions")
user_restrictions = allergen_service.parse_user_restrictions("halal")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'bacon', 'detected_allergens': ['pork', 'meat'], 'detected_ingredients': ['pork']},
    {'name': 'beef steak', 'detected_allergens': ['meat'], 'detected_ingredients': ['beef']},
    {'name': 'wine', 'detected_allergens': ['alcohol'], 'detected_ingredients': ['wine']},
    {'name': 'chicken breast', 'detected_allergens': ['meat'], 'detected_ingredients': ['chicken']}
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Should block pork and alcohol"
# Note: beef/chicken might also be blocked if not halal-certified, but our system only checks ingredients

# =============================================================================
# EDGE CASE 6: Kosher Restrictions (Pork + Shellfish)
# =============================================================================
print_test_header("Edge Case 6: Kosher Restrictions")
user_restrictions = allergen_service.parse_user_restrictions("kosher")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'shrimp scampi', 'detected_allergens': ['shellfish'], 'detected_ingredients': ['shrimp']},
    {'name': 'bacon', 'detected_allergens': ['pork'], 'detected_ingredients': ['pork']},
    {'name': 'salmon', 'detected_allergens': ['fish'], 'detected_ingredients': ['salmon']},  # Kosher fish is OK
    {'name': 'chicken', 'detected_allergens': ['meat'], 'detected_ingredients': ['chicken']}
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Should block shellfish and pork"

# =============================================================================
# EDGE CASE 7: Overlapping Restrictions (Allergen + Preference)
# =============================================================================
print_test_header("Edge Case 7: Overlapping Allergen + Dietary Preference")
user_restrictions = allergen_service.parse_user_restrictions("dairy,vegetarian")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'cheese pizza', 'detected_allergens': ['dairy', 'gluten'], 'detected_ingredients': ['cheese']},
    {'name': 'beef steak', 'detected_allergens': ['meat'], 'detected_ingredients': ['beef']},
    {'name': 'plain pasta', 'detected_allergens': ['gluten'], 'detected_ingredients': ['wheat']}
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Should block dairy (allergen) and meat (preference)"
assert len(result['violations']) == 2, "Cheese pizza (dairy) and beef (meat)"

# =============================================================================
# EDGE CASE 8: Case Sensitivity and Variations
# =============================================================================
print_test_header("Edge Case 8: Case Sensitivity and Name Variations")
user_restrictions = allergen_service.parse_user_restrictions("Dairy,NUTS,gLuTeN")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'CHEESE BURGER', 'detected_allergens': ['dairy', 'meat', 'gluten'], 'detected_ingredients': ['Cheese', 'wheat bun']},
    {'name': 'Almond Milk', 'detected_allergens': ['nuts'], 'detected_ingredients': ['almond']},
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Should be case-insensitive"

# =============================================================================
# EDGE CASE 9: No Allergens Detected but Food Name Suggests Risk
# =============================================================================
print_test_header("Edge Case 9: Food Name Contains Allergen but Not Detected")
user_restrictions = allergen_service.parse_user_restrictions("shellfish")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'shrimp pasta', 'detected_allergens': [], 'detected_ingredients': []},  # AI missed it!
]

# Allergen detection should catch this in the food name
allergen_info = allergen_service.detect_ingredients('shrimp pasta', [])
print(f"Detected from name: {allergen_info}")
foods[0]['detected_allergens'] = allergen_info['detected_allergens']
foods[0]['detected_ingredients'] = allergen_info['detected_ingredients']

result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Should detect 'shrimp' in food name"

# =============================================================================
# EDGE CASE 10: All Foods Safe
# =============================================================================
print_test_header("Edge Case 10: All Foods Are Safe")
user_restrictions = allergen_service.parse_user_restrictions("shellfish,nuts")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'grilled chicken', 'detected_allergens': ['meat'], 'detected_ingredients': ['chicken']},
    {'name': 'white rice', 'detected_allergens': [], 'detected_ingredients': ['rice']},
    {'name': 'steamed broccoli', 'detected_allergens': [], 'detected_ingredients': ['broccoli']}
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == False, "Should have no violations"
assert len(result['safe_foods']) == 3, "All foods should be safe"

# =============================================================================
# EDGE CASE 11: Severity Levels (Allergen vs Preference)
# =============================================================================
print_test_header("Edge Case 11: Severity Differentiation")
user_restrictions = allergen_service.parse_user_restrictions("dairy,vegetarian")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'milk chocolate', 'detected_allergens': ['dairy'], 'detected_ingredients': ['milk']},
    {'name': 'chicken nuggets', 'detected_allergens': ['meat'], 'detected_ingredients': ['chicken']}
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)

# Check severity levels
dairy_violation = next(v for v in result['violations'] if v['allergen'] == 'dairy')
meat_violation = next(v for v in result['violations'] if v['allergen'] == 'meat')
print(f"\nDairy severity: {dairy_violation['severity']}")
print(f"Meat severity: {meat_violation['severity']}")
assert dairy_violation['severity'] == 'allergen', "Dairy should be 'allergen'"
assert meat_violation['severity'] == 'preference', "Meat should be 'preference'"

# =============================================================================
# EDGE CASE 12: Complex Multi-Ingredient Dish
# =============================================================================
print_test_header("Edge Case 12: Complex Dish with Many Ingredients")
user_restrictions = allergen_service.parse_user_restrictions("dairy,gluten,soy")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {
        'name': 'bibimbap with fried egg and cheese',
        'detected_allergens': ['dairy', 'eggs', 'soy', 'gluten'],
        'detected_ingredients': ['cheese', 'egg', 'soy sauce', 'wheat rice bowl']
    }
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Should detect multiple restricted allergens"

# =============================================================================
# EDGE CASE 13: Similar Food Names
# =============================================================================
print_test_header("Edge Case 13: Similar Food Names (Almond Milk vs Regular Milk)")
user_restrictions = allergen_service.parse_user_restrictions("dairy")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'almond milk', 'detected_allergens': ['nuts'], 'detected_ingredients': ['almond']},  # Not dairy!
    {'name': 'regular milk', 'detected_allergens': ['dairy'], 'detected_ingredients': ['milk']}
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert 'almond milk' in result['safe_foods'], "Almond milk should be safe (not dairy)"
assert 'regular milk' not in result['safe_foods'], "Regular milk should be blocked"

# =============================================================================
# EDGE CASE 14: Cross-Category Foods (e.g., Fish Sauce)
# =============================================================================
print_test_header("Edge Case 14: Cross-Category Foods")
user_restrictions = allergen_service.parse_user_restrictions("fish")
print(f"User Restrictions: {user_restrictions['display']}")

foods = [
    {'name': 'pad thai with fish sauce', 'detected_allergens': ['fish'], 'detected_ingredients': ['fish sauce']},
]
result = allergen_service.validate_meal(foods, user_restrictions)
print_result(result)
assert result['has_violations'] == True, "Fish sauce should trigger fish allergy"

# =============================================================================
# SUMMARY
# =============================================================================
print(f"\n{'='*80}")
print("ALL EDGE CASE TESTS PASSED!")
print(f"{'='*80}")
print("\nTested Edge Cases:")
print("1. ✓ Empty/Null user restrictions")
print("2. ✓ Multiple allergens in single food")
print("3. ✓ Hidden ingredients in 'plain' foods")
print("4. ✓ Vegan vs Vegetarian conflicts")
print("5. ✓ Halal restrictions (pork + alcohol)")
print("6. ✓ Kosher restrictions (pork + shellfish)")
print("7. ✓ Overlapping allergen + dietary preference")
print("8. ✓ Case sensitivity and name variations")
print("9. ✓ Food name contains allergen but not detected")
print("10. ✓ All foods are safe")
print("11. ✓ Severity differentiation (allergen vs preference)")
print("12. ✓ Complex multi-ingredient dishes")
print("13. ✓ Similar food names (almond milk vs regular milk)")
print("14. ✓ Cross-category foods (fish sauce)")
print("\n✅ Allergen detection system is robust!")
