"""
Test allergen detection and dietary restriction integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.allergen_service import (
    detect_ingredients,
    validate_meal,
    parse_user_restrictions,
    allergen_service
)

def test_allergen_detection():
    """Test basic allergen detection"""
    print("\n=== TEST 1: Basic Allergen Detection ===")
    
    # Test dairy detection
    result = detect_ingredients("cheese pizza", ["wheat dough", "mozzarella cheese", "tomato sauce"])
    print(f"Cheese pizza allergens: {result['detected_allergens']}")
    assert 'dairy' in result['detected_allergens']
    assert 'gluten' in result['detected_allergens']
    print("✓ Cheese pizza correctly detected dairy and gluten")
    
    # Test multiple allergens
    result = detect_ingredients("chicken caesar salad", ["chicken", "parmesan cheese", "croutons", "caesar dressing"])
    print(f"Caesar salad allergens: {result['detected_allergens']}")
    assert 'dairy' in result['detected_allergens']
    assert 'gluten' in result['detected_allergens']
    print("✓ Caesar salad correctly detected dairy and gluten")
    
    # Test shellfish
    result = detect_ingredients("shrimp pasta", ["shrimp", "pasta", "garlic butter"])
    print(f"Shrimp pasta allergens: {result['detected_allergens']}")
    assert 'shellfish' in result['detected_allergens']
    assert 'gluten' in result['detected_allergens']
    assert 'dairy' in result['detected_allergens']
    print("✓ Shrimp pasta correctly detected shellfish, gluten, and dairy")

def test_parse_restrictions():
    """Test parsing user restrictions"""
    print("\n=== TEST 2: Parse User Restrictions ===")
    
    # Test simple allergens
    result = parse_user_restrictions("dairy, nuts")
    print(f"Parsed 'dairy, nuts': {result}")
    assert 'dairy' in result['allergens']
    assert 'nuts' in result['allergens']
    print("✓ Simple allergen parsing works")
    
    # Test dietary preferences
    result = parse_user_restrictions("vegan")
    print(f"Parsed 'vegan': {result}")
    assert 'vegan' in result['preferences']
    print("✓ Dietary preference parsing works")
    
    # Test mixed
    result = parse_user_restrictions("dairy, gluten, vegetarian")
    print(f"Parsed 'dairy, gluten, vegetarian': {result}")
    assert 'dairy' in result['allergens']
    assert 'gluten' in result['allergens']
    assert 'vegetarian' in result['preferences']
    print("✓ Mixed allergen and preference parsing works")

def test_meal_validation():
    """Test meal validation against restrictions"""
    print("\n=== TEST 3: Meal Validation ===")
    
    # Test meal with violations
    food_items = [
        {
            'name': 'cheese pizza',
            'detected_allergens': ['dairy', 'gluten'],
            'detected_ingredients': ['cheese', 'wheat dough']
        },
        {
            'name': 'garden salad',
            'detected_allergens': [],
            'detected_ingredients': ['lettuce', 'tomato']
        }
    ]
    
    user_restrictions = parse_user_restrictions("dairy")
    result = validate_meal(food_items, user_restrictions)
    
    print(f"Validation result: {result}")
    assert result['has_violations'] == True
    assert len(result['violations']) > 0
    assert 'cheese pizza' in result['flagged_foods']
    assert 'garden salad' in result['safe_foods']
    print("✓ Meal validation correctly identified violations")
    
    # Test meal without violations
    food_items = [
        {
            'name': 'grilled chicken',
            'detected_allergens': ['meat'],
            'detected_ingredients': ['chicken']
        },
        {
            'name': 'rice',
            'detected_allergens': [],
            'detected_ingredients': ['rice']
        }
    ]
    
    user_restrictions = parse_user_restrictions("dairy")
    result = validate_meal(food_items, user_restrictions)
    
    print(f"Validation result (safe meal): {result}")
    assert result['has_violations'] == False
    assert len(result['violations']) == 0
    print("✓ Safe meal correctly validated")

def test_vegan_validation():
    """Test vegan dietary preference validation"""
    print("\n=== TEST 4: Vegan Validation ===")
    
    # Vegan restrictions
    user_restrictions = parse_user_restrictions("vegan")
    print(f"Vegan restrictions: {user_restrictions}")
    
    # Test meat violation
    food_items = [
        {
            'name': 'grilled chicken',
            'detected_allergens': ['meat'],
            'detected_ingredients': ['chicken']
        }
    ]
    
    result = validate_meal(food_items, user_restrictions)
    print(f"Chicken validation: {result}")
    assert result['has_violations'] == True
    print("✓ Vegan correctly flags meat")
    
    # Test dairy violation
    food_items = [
        {
            'name': 'cheese pizza',
            'detected_allergens': ['dairy', 'gluten'],
            'detected_ingredients': ['cheese']
        }
    ]
    
    result = validate_meal(food_items, user_restrictions)
    print(f"Cheese validation: {result}")
    assert result['has_violations'] == True
    print("✓ Vegan correctly flags dairy")
    
    # Test vegan-safe food
    food_items = [
        {
            'name': 'quinoa bowl',
            'detected_allergens': [],
            'detected_ingredients': ['quinoa', 'vegetables']
        }
    ]
    
    result = validate_meal(food_items, user_restrictions)
    print(f"Quinoa validation: {result}")
    assert result['has_violations'] == False
    print("✓ Vegan correctly approves plant-based food")

def test_alert_formatting():
    """Test alert message formatting"""
    print("\n=== TEST 5: Alert Message Formatting ===")
    
    validation_result = {
        'has_violations': True,
        'violations': [
            {
                'food_name': 'cheese pizza',
                'allergen': 'dairy',
                'allergen_display': 'Dairy',
                'ingredient': 'cheese',
                'severity': 'allergen'
            },
            {
                'food_name': 'caesar salad',
                'allergen': 'gluten',
                'allergen_display': 'Gluten',
                'ingredient': 'croutons',
                'severity': 'allergen'
            }
        ],
        'safe_foods': ['apple', 'water'],
        'flagged_foods': ['cheese pizza', 'caesar salad'],
        'summary': '2 allergen violations detected'
    }
    
    message = allergen_service.format_alert_message(validation_result)
    print(f"Alert message:\n{message}")
    assert '🚨' in message
    assert 'cheese pizza' in message.lower()
    assert 'dairy' in message.lower()
    print("✓ Alert message correctly formatted")

def test_supported_restrictions():
    """Test getting supported restrictions"""
    print("\n=== TEST 6: Supported Restrictions ===")
    
    supported = allergen_service.get_supported_restrictions()
    print(f"Supported restrictions:\n{supported}")
    assert 'Dairy' in supported or 'dairy' in supported.lower()
    assert 'Vegetarian' in supported or 'vegetarian' in supported.lower()
    print("✓ Supported restrictions returned")

if __name__ == '__main__':
    print("=" * 60)
    print("ALLERGEN & DIETARY RESTRICTION INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_allergen_detection()
        test_parse_restrictions()
        test_meal_validation()
        test_vegan_validation()
        test_alert_formatting()
        test_supported_restrictions()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
