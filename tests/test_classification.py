"""
Chatbot Classification Test Suite
Tests the accuracy of natural language question classification
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.chatbot_service import chatbot_service


# ============================================================================
# PRODUCTION-GRADE TEST CASES
# Comprehensive test suite covering voice input, edge cases, and real usage
# ============================================================================

# Test cases: (message, expected_classification)
test_cases = [
    # ===== GOAL SETTING (Basic) =====
    ("My goal is 2000 calories", "goal_setting"),
    ("I want to eat 150g protein", "goal_setting"),
    ("Set my calorie target to 1800", "goal_setting"),
    ("Goal is 2500 calories", "goal_setting"),
    ("My protein goal is 120", "goal_setting"),
    ("Set goal to 2000", "goal_setting"),
    ("I want 2000 calories a day", "goal_setting"),
    ("My target is 1500 calories", "goal_setting"),
    
    # ===== GOAL SETTING (Voice input variations) =====
    ("I want 2000 cal", "goal_setting"),
    ("Set my goal 3000 calories", "goal_setting"),
    ("Goal 2200 calories", "goal_setting"),
    ("I want to aim for 180 grams of protein", "goal_setting"),
    ("Trying to hit 2500 calories", "goal_setting"),
    
    # ===== GOAL PROGRESS (Basic) =====
    ("What is my goal?", "goal_progress"),
    ("What's my goal?", "goal_progress"),
    ("Am I meeting my goal?", "goal_progress"),
    ("Show my progress", "goal_progress"),
    ("How am I doing?", "goal_progress"),
    ("My progress", "goal_progress"),
    ("What's my progress?", "goal_progress"),
    ("Goal progress", "goal_progress"),
    ("Check my progress", "goal_progress"),
    ("Am I on track?", "goal_progress"),
    
    # ===== GOAL PROGRESS (Natural variations) =====
    ("How's it going?", "goal_progress"),
    ("What's my status?", "goal_progress"),
    ("Hit my goal yet?", "goal_progress"),
    ("Am I over?", "goal_progress"),
    ("Did I hit my goal?", "goal_progress"),
    ("Am I meeting my target?", "goal_progress"),
    ("Check my goal", "goal_progress"),
    ("Show goal", "goal_progress"),
    
    # ===== GOAL PROGRESS (Voice input - no apostrophes) =====
    ("Whats my goal", "goal_progress"),
    ("Hows my progress", "goal_progress"),
    ("Show my goal", "goal_progress"),
    ("Tell me my goal", "goal_progress"),
    
    # ===== COMPARISON (Basic) =====
    ("Compare today vs yesterday", "comparison"),
    ("Today versus yesterday", "comparison"),
    ("Difference between today and yesterday", "comparison"),
    ("Compare today and yesterday", "comparison"),
    ("Today vs yesterday", "comparison"),
    ("Compare with yesterday", "comparison"),
    ("Show difference", "comparison"),
    
    # ===== COMPARISON (Natural variations) =====
    ("Compare my protein today vs yesterday", "comparison"),
    ("How does today compare to yesterday", "comparison"),
    ("Today compared to yesterday", "comparison"),
    ("Difference from yesterday", "comparison"),
    
    # ===== HISTORY QUERY (Basic) =====
    ("What did I eat yesterday?", "history_query"),
    ("What did I have yesterday?", "history_query"),
    ("Show me what I ate today", "history_query"),
    ("What did I eat last week?", "history_query"),
    ("My meals from yesterday", "history_query"),
    ("What have I eaten today?", "history_query"),
    ("Show me my meals", "history_query"),
    ("What did I have last month?", "history_query"),
    
    # ===== HISTORY QUERY (Natural variations) =====
    ("Tell me what I ate", "history_query"),
    ("I ate protein yesterday", "history_query"),
    ("What I ate yesterday", "history_query"),
    ("Show my meals yesterday", "history_query"),
    ("My food log", "history_query"),
    ("What did I eat and how am I doing?", "history_query"),  # First intent wins
    
    # ===== DAILY SUMMARY (Basic) =====
    ("How am I doing today?", "daily_summary"),
    ("Today's summary", "daily_summary"),
    ("What's my total for today?", "daily_summary"),
    ("Show me today", "daily_summary"),
    ("How's today so far?", "daily_summary"),
    
    # ===== DAILY SUMMARY (Natural variations) =====
    ("Today so far", "daily_summary"),
    ("Todays total", "daily_summary"),
    ("Summary for today", "daily_summary"),
    ("Total for today", "daily_summary"),
    
    # ===== NUTRIENT QUERY (Basic) =====
    ("How much protein did I have?", "nutrient_query"),
    ("My calorie intake today", "nutrient_query"),
    ("Show me my carbs", "nutrient_query"),
    ("How many calories today?", "nutrient_query"),
    ("Protein intake", "nutrient_query"),
    ("My fat intake", "nutrient_query"),
    ("Carbs for the week", "nutrient_query"),
    
    # ===== NUTRIENT QUERY (Natural variations) =====
    ("How much protein?", "nutrient_query"),
    ("Calories so far?", "nutrient_query"),
    ("My protein today", "nutrient_query"),
    ("Fat intake yesterday", "nutrient_query"),
    ("Carbs this week", "nutrient_query"),
    
    # ===== PATTERN ANALYSIS =====
    ("Show me patterns", "pattern_analysis"),
    ("My eating habits", "pattern_analysis"),
    ("What are my patterns?", "pattern_analysis"),
    ("Do I have eating patterns?", "pattern_analysis"),
    ("Analyze my patterns", "pattern_analysis"),
    
    # ===== RECOMMENDATIONS =====
    ("What should I eat next?", "recommendation"),
    ("Recommend a meal", "recommendation"),
    ("Suggest something", "recommendation"),
    ("What should I have?", "recommendation"),
    ("Meal suggestions", "recommendation"),
    
    # ===== HELP =====
    ("Help", "help"),
    ("What can you do?", "help"),
    ("How do I use this?", "help"),
    ("Commands", "help"),
]


edge_cases = [
    # ===== EXTREMELY SHORT / AMBIGUOUS INPUT =====
    ("goal", "general"),
    ("check", "general"),
    ("2000", "general"),
    ("show", "general"),
    ("today", "general"),
    ("progress", "general"),
    
    # ===== VOICE RECOGNITION ERRORS (Common mishearings) =====
    ("coal progress", "general"),  # "goal" misheard as "coal"
    ("Show my girl", "general"),  # "goal" misheard as "girl"
    ("Set my gold to 2000", "general"),  # "goal" misheard as "gold"
    
    # ===== MULTIPLE INTENTS (Priority testing) =====
    ("Set my goal to 2000 and show progress", "goal_setting"),  # goal_setting wins
    ("Compare and show my goal", "comparison"),  # comparison wins
    ("What did I eat yesterday and today", "history_query"),  # history wins
    
    # ===== TIMEFRAME-ONLY QUERIES =====
    ("yesterday", "history_query"),
    ("last week", "history_query"),
    ("last month", "history_query"),
    ("this week", "history_query"),
    
    # ===== CASUAL / SLANG EXPRESSIONS =====
    ("Did I smash it today?", "general"),
    ("Crushing my goals?", "general"),
    ("What's the damage?", "general"),  # Too slangy
    
    # ===== NEGATIVE / QUESTIONING TONE =====
    ("I don't think I'm hitting my goal", "general"),
    ("Maybe I should check my progress", "general"),
    ("Not sure about my calories", "general"),
    
    # ===== COMPOUND QUESTIONS =====
    ("How am I doing and what should I eat?", "goal_progress"),  # First intent
    ("Show progress and recommend meal", "goal_progress"),  # First intent
    
    # ===== PUNCTUATION / FORMATTING VARIATIONS =====
    ("What's my goal???", "goal_progress"),
    ("SHOW MY PROGRESS", "goal_progress"),
    ("what is my goal", "goal_progress"),
    ("my goal is 2000!!!", "goal_setting"),
    
    # ===== INCOMPLETE SENTENCES (Voice cut-off) =====
    ("Show my", "general"),
    ("What did I", "general"),
    ("How am I", "general"),
    ("I want", "general"),
    
    # ===== CONTEXT-DEPENDENT (Should work standalone) =====
    ("Show it", "general"),
    ("Tell me", "general"),
    ("How much?", "general"),
    
    # ===== SIMILAR SOUNDING WORDS =====
    ("Show my girls", "general"),  # "goals" misheard
    ("Check my propose", "general"),  # "progress" misheard
    ("What's my coal", "general"),  # "goal" misheard
    
    # ===== FILLER WORDS (Common in voice input) =====
    ("Um show my progress", "goal_progress"),
    ("Hey what's my goal", "goal_progress"),
    ("So how am I doing today", "daily_summary"),
    ("Okay compare today vs yesterday", "comparison"),
    
    # ===== GREETINGS MIXED WITH COMMANDS =====
    ("Hey how am I doing", "goal_progress"),
    ("Hi what's my progress", "goal_progress"),
    ("Hello show my goal", "goal_progress"),
    
    # ===== NUMBERS WITHOUT CONTEXT =====
    ("150", "general"),
    ("2000", "general"),
    ("3000 calories", "general"),  # No intent verb
    
    # ===== PARTIAL NUTRIENT NAMES =====
    ("How much pro?", "general"),  # "protein" shortened too much
    ("My cal intake", "nutrient_query"),  # "calories" shortened acceptably
    ("Show carb", "nutrient_query"),  # "carbs" singular form
]


# ============================================================================
# STRESS TEST CASES - Extreme edge cases
# ============================================================================
stress_test_cases = [
    # ===== EXTREMELY LONG QUERIES =====
    ("I want to know what my goal is and also how much progress I've made today and whether I'm on track to meet it", "goal_progress"),
    ("Can you please tell me what I ate yesterday and also compare it to what I ate today", "history_query"),
    
    # ===== MIXED LANGUAGE (Common with voice assistants) =====
    ("What's my goal por favor", "goal_progress"),  # Spanish mixed in
    ("Show my progress s'il vous plaît", "goal_progress"),  # French mixed in
    
    # ===== BACKGROUND NOISE ARTIFACTS =====
    ("Show my progress [background noise]", "goal_progress"),
    ("What's my goal uh uh", "goal_progress"),
    ("Um uh what did I eat yesterday", "history_query"),
    
    # ===== REPEATED WORDS (Voice stutter) =====
    ("Show show my progress", "goal_progress"),
    ("What what's my goal", "goal_progress"),
    ("I I want 2000 calories", "goal_setting"),
    
    # ===== MISSING SPACES (Voice recognition error) =====
    ("Whatsmygoal", "general"),  # Too corrupted
    ("showprogress", "general"),  # Too corrupted
    
    # ===== EXTRA WORDS =====
    ("Please show me my progress thank you", "goal_progress"),
    ("Could you tell me what my goal is", "goal_progress"),
    ("I'd like to see what I ate yesterday", "history_query"),
    
    # ===== QUESTIONS ABOUT THE BOT ITSELF =====
    ("Are you working?", "general"),
    ("Can you hear me?", "general"),
    ("Hello?", "general"),
]


def run_tests(include_stress_tests=False):
    """Run all classification tests and report results"""
    
    print("=" * 80)
    print("🧪 CHATBOT CLASSIFICATION TEST SUITE - PRODUCTION GRADE")
    print("=" * 80)
    print()
    
    # Combine test cases
    all_tests = test_cases + edge_cases
    if include_stress_tests:
        all_tests += stress_test_cases
        print("⚠️  STRESS TEST MODE ENABLED")
    
    print(f"📋 Running {len(all_tests)} test cases...")
    print()
    
    correct = 0
    total = len(all_tests)
    failures = []
    
    # Group results by category
    category_results = {}
    
    for message, expected_type in all_tests:
        try:
            actual_type, _ = chatbot_service.classify_question(message)
            
            # Handle None return
            if actual_type is None:
                actual_type = "general"
            
            is_correct = actual_type == expected_type
            
            if is_correct:
                correct += 1
                status = "✅"
            else:
                failures.append((message, expected_type, actual_type))
                status = "❌"
            
            # Track by category
            if expected_type not in category_results:
                category_results[expected_type] = {'correct': 0, 'total': 0}
            
            category_results[expected_type]['total'] += 1
            if is_correct:
                category_results[expected_type]['correct'] += 1
            
            # Print result
            status_symbol = "✅" if is_correct else "❌"
            print(f"{status_symbol} '{message[:60]}{'...' if len(message) > 60 else ''}'")
            if not is_correct:
                print(f"   Expected: {expected_type}, Got: {actual_type}")
        
        except Exception as e:
            failures.append((message, expected_type, f"ERROR: {str(e)}"))
            print(f"❌ '{message}' → ERROR: {e}")
            category_results.setdefault('ERROR', {'correct': 0, 'total': 0})
            category_results['ERROR']['total'] += 1
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 RESULTS SUMMARY")
    print("=" * 80)
    
    accuracy = (correct / total) * 100
    
    # Color coding for accuracy
    if accuracy >= 95:
        emoji = "🟢"
        status = "EXCELLENT"
    elif accuracy >= 90:
        emoji = "🟡"
        status = "GOOD"
    elif accuracy >= 80:
        emoji = "🟠"
        status = "ACCEPTABLE"
    else:
        emoji = "🔴"
        status = "NEEDS IMPROVEMENT"
    
    print(f"\n{emoji} Overall Accuracy: {accuracy:.1f}% ({correct}/{total}) - {status}")
    
    # Category breakdown
    print("\n📈 Accuracy by Category:")
    print("-" * 60)
    for category, results in sorted(category_results.items()):
        cat_accuracy = (results['correct'] / results['total']) * 100
        cat_emoji = "✅" if cat_accuracy == 100 else "⚠️" if cat_accuracy >= 90 else "❌"
        print(f"  {cat_emoji} {category:20s}: {cat_accuracy:5.1f}% ({results['correct']}/{results['total']})")
    
    # Failed cases with categorization
    if failures:
        print(f"\n❌ Failed Cases ({len(failures)}):")
        print("-" * 60)
        
        # Group failures by type
        failure_types = {}
        for msg, expected, actual in failures:
            key = f"{expected} → {actual}"
            if key not in failure_types:
                failure_types[key] = []
            failure_types[key].append(msg)
        
        for failure_type, messages in failure_types.items():
            print(f"\n  📍 {failure_type} ({len(messages)} cases):")
            for msg in messages[:3]:  # Show first 3 examples
                print(f"     - '{msg}'")
            if len(messages) > 3:
                print(f"     ... and {len(messages) - 3} more")
    else:
        print("\n🎉 All tests passed!")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    if accuracy >= 95:
        print("✅ Classification system is production-ready!")
        print("✅ All major use cases are covered.")
        print("💡 Consider monitoring real user queries for new patterns.")
    elif accuracy >= 90:
        print("🟡 Classification system is mostly ready.")
        print("💡 Review failed cases and add missing patterns.")
        print("💡 Consider edge case handling for failed categories.")
    elif accuracy >= 80:
        print("🟠 Classification system needs improvement.")
        print("⚠️  Multiple categories have issues.")
        print("💡 Focus on top failing categories first.")
    else:
        print("🔴 Classification system needs significant work.")
        print("⚠️  Not ready for production use.")
        print("💡 Review core classification logic.")
    
    print("=" * 80)
    
    return accuracy, failures


if __name__ == "__main__":
    import sys
    
    # Check for stress test flag
    run_stress = "--stress" in sys.argv or "-s" in sys.argv
    
    accuracy, failures = run_tests(include_stress_tests=run_stress)
    
    # Exit with error code if accuracy is below threshold
    threshold = 90 if run_stress else 95  # Lower threshold for stress tests
    
    if accuracy < threshold:
        print(f"\n⚠️  Warning: Accuracy below {threshold}% threshold!")
        sys.exit(1)
    else:
        print(f"\n✅ Success: Accuracy meets {threshold}% threshold!")
        sys.exit(0)
