"""
Simple test for nutrition status classification patterns
Tests only the classification logic without database dependencies
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_classification_patterns():
    """Test that nutrition status commands are classified correctly"""
    print("\n" + "="*80)
    print("TESTING NUTRITION STATUS CLASSIFICATION PATTERNS")
    print("="*80)
    
    # Import the classification method
    from services.chatbot_service import ChatbotService
    chatbot = ChatbotService()
    
    test_cases = [
        # Daily patterns
        ("nutrition status", "nutrition_status", 1),
        ("show my nutrition status", "nutrition_status", 1),
        ("my nutrients", "nutrition_status", 1),
        ("show nutrients", "nutrition_status", 1),
        ("nutrient status", "nutrition_status", 1),
        ("my nutrition", "nutrition_status", 1),
        ("what nutrients have i consumed", "nutrition_status", 1),
        
        # Weekly patterns
        ("nutrition week", "nutrition_status", 7),
        ("weekly nutrients", "nutrition_status", 7),
        ("week nutrients", "nutrition_status", 7),
        ("weekly nutrition", "nutrition_status", 7),
        ("nutrition this week", "nutrition_status", 7),
        
        # Edge cases - should NOT match nutrition status
        ("what should i eat for breakfast", "recommendation", None),
        ("show my restrictions", "view_restrictions", None),
        ("help", "help", None),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_type, expected_days in test_cases:
        question_type, params = chatbot.classify_question(message)
        days = params.get('days', None)
        
        if expected_days is None:
            # Just check question type
            if question_type == expected_type:
                print(f"✅ PASS: '{message}' → {question_type}")
                passed += 1
            else:
                print(f"❌ FAIL: '{message}' → {question_type}, expected {expected_type}")
                failed += 1
        else:
            # Check both question type and days parameter
            if question_type == expected_type and days == expected_days:
                print(f"✅ PASS: '{message}' → {question_type} (days={days})")
                passed += 1
            else:
                print(f"❌ FAIL: '{message}' → {question_type} (days={days}), expected {expected_type} (days={expected_days})")
                failed += 1
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*80}")
    
    return failed == 0


if __name__ == '__main__':
    try:
        success = test_classification_patterns()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
