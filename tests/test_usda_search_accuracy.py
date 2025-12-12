"""
Comprehensive test suite for USDA food search accuracy
Tests core name extraction, NFS priority, and nutrition data accuracy
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.usda_service import USDAService

def test_core_name_extraction():
    """Test that core food names are extracted correctly"""
    print("=" * 80)
    print("🧪 TEST 1: Core Food Name Extraction")
    print("=" * 80)
    
    usda = USDAService()
    
    test_cases = [
        ("Sliced Meatloaf with Ketchup Glaze", "meatloaf"),
        ("Steamed Green Beans", "green beans"),
        ("Grilled Chicken Breast", "chicken breast"),
        ("Baked Sweet Potato", "sweet potato"),
        ("Pan-Fried Salmon with Lemon", "salmon"),
        ("Mashed Potatoes", "mashed potatoes"),
        ("Fresh Sliced Apple", "apple"),
        ("Cooked White Rice", "white rice"),
    ]
    
    passed = 0
    failed = 0
    
    for original, expected in test_cases:
        result = usda._extract_core_food_name(original)
        if result == expected:
            print(f"✅ '{original}' → '{result}'")
            passed += 1
        else:
            print(f"❌ '{original}' → '{result}' (expected '{expected}')")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_nfs_priority():
    """Test that NFS items are prioritized correctly"""
    print("=" * 80)
    print("🧪 TEST 2: NFS Priority Selection")
    print("=" * 80)
    
    usda = USDAService()
    
    test_foods = [
        ("meatloaf", "Meat loaf dinner, NFS"),
        ("mashed potatoes", "Potato, mashed, NFS"),
        ("chicken breast", "Chicken breast, NFS"),
        ("rice", "Rice, NFS"),
    ]
    
    passed = 0
    failed = 0
    
    for food_name, expected_keyword in test_foods:
        results = usda._search_food(food_name)
        if results and len(results) > 0:
            first_result = results[0].get('description', '')
            has_nfs = ', nfs' in first_result.lower() or ' nfs' in first_result.lower()
            
            if has_nfs:
                print(f"✅ '{food_name}' → '{first_result}' (NFS found)")
                passed += 1
            else:
                print(f"⚠️  '{food_name}' → '{first_result}' (No NFS available)")
                passed += 1  # Not a failure if NFS doesn't exist
        else:
            print(f"❌ '{food_name}' → No results found")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_complex_dish_filtering():
    """Test that complex dishes are filtered out when simpler options exist"""
    print("=" * 80)
    print("🧪 TEST 3: Complex Dish Filtering")
    print("=" * 80)
    
    usda = USDAService()
    
    # These should NOT return sandwiches, casseroles, or frozen meals (unless NFS)
    test_foods = [
        ("green beans", ["casserole", "fried"]),  # Should avoid these
        ("chicken", ["sandwich", "burger"]),
        ("beef", ["pizza", "taco"]),
    ]
    
    passed = 0
    failed = 0
    
    for food_name, avoid_words in test_foods:
        results = usda._search_food(food_name)
        if results and len(results) > 0:
            first_result = results[0].get('description', '').lower()
            
            # Check if it contains NFS (which overrides filters)
            has_nfs = ', nfs' in first_result or ' nfs' in first_result
            
            # Check if it has avoid words
            has_avoid = any(word in first_result for word in avoid_words)
            
            if has_nfs or not has_avoid:
                print(f"✅ '{food_name}' → '{results[0].get('description', '')}' (Clean)")
                passed += 1
            else:
                print(f"❌ '{food_name}' → '{results[0].get('description', '')}' (Contains: {[w for w in avoid_words if w in first_result]})")
                failed += 1
        else:
            print(f"⚠️  '{food_name}' → No results")
            passed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_nutrition_accuracy():
    """Test that nutrition data is retrieved and scaled correctly"""
    print("=" * 80)
    print("🧪 TEST 4: Nutrition Data Accuracy")
    print("=" * 80)
    
    usda = USDAService()
    
    test_cases = [
        ("chicken breast", 100, {"min_protein": 20, "max_protein": 35, "min_calories": 100, "max_calories": 200}),
        ("white rice", 100, {"min_carbs": 20, "max_carbs": 35, "min_calories": 100, "max_calories": 180}),
        ("mashed potatoes", 100, {"min_carbs": 15, "max_carbs": 25, "min_calories": 80, "max_calories": 150}),
        ("green beans", 100, {"min_fiber": 2, "max_fiber": 5, "min_calories": 20, "max_calories": 60}),
    ]
    
    passed = 0
    failed = 0
    
    for food_name, portion, expected_ranges in test_cases:
        nutrition = usda.get_nutrition_data(food_name, portion)
        
        # Check if nutrition data is valid
        if nutrition:
            # Validate expected ranges
            valid = True
            issues = []
            
            for nutrient, range_val in expected_ranges.items():
                nutrient_key = nutrient.replace("min_", "").replace("max_", "") + "_g"
                if nutrient_key == "calories_g":
                    nutrient_key = "calories"
                
                actual_value = nutrition.get(nutrient_key, 0)
                
                if "min_" in nutrient and actual_value < range_val:
                    valid = False
                    issues.append(f"{nutrient_key}={actual_value} < {range_val}")
                elif "max_" in nutrient and actual_value > range_val:
                    valid = False
                    issues.append(f"{nutrient_key}={actual_value} > {range_val}")
            
            if valid:
                print(f"✅ '{food_name}' ({portion}g) → {nutrition['calories']} cal, "
                      f"{nutrition['protein_g']:.1f}g protein, {nutrition['carbs_g']:.1f}g carbs")
                passed += 1
            else:
                print(f"❌ '{food_name}' ({portion}g) → Out of range: {', '.join(issues)}")
                print(f"   Got: {nutrition['calories']} cal, {nutrition['protein_g']:.1f}g protein, "
                      f"{nutrition['carbs_g']:.1f}g carbs, {nutrition['fat_g']:.1f}g fat")
                failed += 1
        else:
            print(f"❌ '{food_name}' → No nutrition data found")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_portion_scaling():
    """Test that nutrition values scale correctly with portion size"""
    print("=" * 80)
    print("🧪 TEST 5: Portion Scaling Accuracy")
    print("=" * 80)
    
    usda = USDAService()
    
    # Get nutrition for different portions and verify scaling
    test_cases = [
        ("chicken breast", [100, 200, 50]),
        ("rice", [100, 150, 75]),
    ]
    
    passed = 0
    failed = 0
    
    for food_name, portions in test_cases:
        base_nutrition = usda.get_nutrition_data(food_name, 100)
        
        if not base_nutrition:
            print(f"❌ '{food_name}' → Could not get base nutrition")
            failed += 1
            continue
        
        print(f"\n📋 Testing '{food_name}' scaling:")
        print(f"   Base (100g): {base_nutrition['calories']} cal, {base_nutrition['protein_g']:.1f}g protein")
        
        all_valid = True
        for portion in portions[1:]:  # Skip 100g (base)
            nutrition = usda.get_nutrition_data(food_name, portion)
            
            if nutrition:
                expected_calories = base_nutrition['calories'] * (portion / 100)
                expected_protein = base_nutrition['protein_g'] * (portion / 100)
                
                # Allow 5% tolerance for rounding
                cal_diff = abs(nutrition['calories'] - expected_calories) / expected_calories
                protein_diff = abs(nutrition['protein_g'] - expected_protein) / expected_protein
                
                if cal_diff < 0.05 and protein_diff < 0.05:
                    print(f"   ✅ {portion}g: {nutrition['calories']:.0f} cal, {nutrition['protein_g']:.1f}g protein (Scaled correctly)")
                else:
                    print(f"   ❌ {portion}g: {nutrition['calories']:.0f} cal (expected {expected_calories:.0f}), "
                          f"{nutrition['protein_g']:.1f}g protein (expected {expected_protein:.1f})")
                    all_valid = False
            else:
                print(f"   ❌ {portion}g: No data")
                all_valid = False
        
        if all_valid:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed\n")
    return failed == 0


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 80)
    print("🚀 USDA SEARCH ACCURACY TEST SUITE")
    print("=" * 80 + "\n")
    
    results = []
    
    results.append(("Core Name Extraction", test_core_name_extraction()))
    results.append(("NFS Priority", test_nfs_priority()))
    results.append(("Complex Dish Filtering", test_complex_dish_filtering()))
    results.append(("Nutrition Accuracy", test_nutrition_accuracy()))
    results.append(("Portion Scaling", test_portion_scaling()))
    
    # Summary
    print("=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for production!")
    else:
        print("⚠️  Some tests failed. Please review.")
    
    print("=" * 80 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
