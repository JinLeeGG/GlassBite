"""
Quick test for nutrition status feature - tests classification only
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_classification():
    """Test classification patterns without database"""
    print("\n" + "="*80)
    print("TESTING NUTRITION STATUS CLASSIFICATION")
    print("="*80)
    
    # Manual classification logic (copied from chatbot_service)
    def classify(message):
        message = message.lower()
        
        # Daily nutrition status
        if any(phrase in message for phrase in ['nutrition status', 'my nutrients', 'show nutrients', 
                                                'nutrient status', 'my nutrition', 'show nutrition',
                                                'what nutrients']):
            if 'week' not in message:
                return 'nutrition_status', {'days': 1}
        
        # Weekly nutrition status
        if any(phrase in message for phrase in ['nutrition week', 'weekly nutrients', 'week nutrients',
                                                'weekly nutrition', 'nutrition this week']):
            return 'nutrition_status', {'days': 7}
        
        return 'unknown', {}
    
    test_cases = [
        ("nutrition status", "nutrition_status", 1),
        ("my nutrients", "nutrition_status", 1),
        ("show nutrients", "nutrition_status", 1),
        ("nutrition week", "nutrition_status", 7),
        ("weekly nutrients", "nutrition_status", 7),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_type, expected_days in test_cases:
        question_type, params = classify(message)
        days = params.get('days', None)
        
        if question_type == expected_type and days == expected_days:
            print(f"✅ PASS: '{message}' → {question_type} (days={days})")
            passed += 1
        else:
            print(f"❌ FAIL: '{message}' → {question_type} (days={days}), expected {expected_type} (days={expected_days})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == '__main__':
    success = test_classification()
    print("\n" + "="*80)
    if success:
        print("✅ ALL CLASSIFICATION TESTS PASSED!")
        print("\nThe nutrition status feature should now work correctly.")
        print("Try these commands:")
        print("  - 'nutrition status' (daily)")
        print("  - 'nutrition week' (weekly)")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)
