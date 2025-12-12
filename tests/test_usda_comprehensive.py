"""
Comprehensive USDA search test with 100+ common foods
Tests search accuracy across diverse food categories
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.usda_service import USDAService

# 100+ common foods across different categories
TEST_FOODS = [
    # Meat & Poultry (20)
    "chicken breast", "chicken thigh", "chicken wings", "ground beef", "steak",
    "pork chops", "bacon", "sausage", "turkey breast", "ground turkey",
    "lamb chops", "beef brisket", "ribeye steak", "sirloin steak", "meatloaf",
    "chicken drumstick", "pork tenderloin", "ham", "roast beef", "veal",
    
    # Seafood (15)
    "salmon", "tuna", "shrimp", "cod", "tilapia",
    "halibut", "mahi mahi", "trout", "catfish", "crab",
    "lobster", "scallops", "sardines", "mackerel", "anchovy",
    
    # Vegetables (20)
    "broccoli", "carrots", "spinach", "kale", "lettuce",
    "tomatoes", "cucumber", "bell peppers", "onions", "garlic",
    "green beans", "peas", "corn", "asparagus", "zucchini",
    "cauliflower", "brussels sprouts", "cabbage", "celery", "mushrooms",
    
    # Fruits (15)
    "apple", "banana", "orange", "grapes", "strawberries",
    "blueberries", "watermelon", "pineapple", "mango", "peach",
    "pear", "kiwi", "avocado", "lemon", "lime",
    
    # Grains & Starches (15)
    "white rice", "brown rice", "quinoa", "oatmeal", "pasta",
    "spaghetti", "bread", "whole wheat bread", "bagel", "tortilla",
    "potatoes", "sweet potato", "couscous", "barley", "farro",
    
    # Dairy & Eggs (10)
    "milk", "cheese", "cheddar cheese", "yogurt", "greek yogurt",
    "eggs", "butter", "cream cheese", "sour cream", "cottage cheese",
    
    # Legumes & Nuts (10)
    "black beans", "kidney beans", "chickpeas", "lentils", "peanuts",
    "almonds", "walnuts", "cashews", "peanut butter", "hummus",
    
    # Prepared Foods (10)
    "pizza", "hamburger", "hot dog", "taco", "burrito",
    "fried rice", "mashed potatoes", "french fries", "mac and cheese", "lasagna",
]

def test_search_success_rate():
    """Test what percentage of foods return valid results"""
    print("=" * 80)
    print("🧪 TEST: Search Success Rate (100+ Foods)")
    print("=" * 80)
    
    usda = USDAService()
    
    successful = 0
    failed = 0
    nfs_found = 0
    no_results = 0
    
    results_by_category = {
        "✅ NFS Found": [],
        "✅ Simple Food": [],
        "⚠️ Complex Food": [],
        "❌ No Results": []
    }
    
    print(f"\nTesting {len(TEST_FOODS)} foods...\n")
    
    for i, food_name in enumerate(TEST_FOODS, 1):
        try:
            # Extract core name
            core_name = usda._extract_core_food_name(food_name)
            
            # Search
            search_results = usda._search_food(core_name)
            
            if search_results and len(search_results) > 0:
                first_result = search_results[0].get('description', '')
                first_result_lower = first_result.lower()
                
                # Check if NFS
                has_nfs = ', nfs' in first_result_lower or ' nfs' in first_result_lower
                
                # Check for complex keywords
                complex_keywords = ['sandwich', 'casserole', 'salad', 'soup', 'frozen meal']
                is_complex = any(kw in first_result_lower for kw in complex_keywords)
                
                if has_nfs:
                    results_by_category["✅ NFS Found"].append((food_name, first_result))
                    nfs_found += 1
                    successful += 1
                elif not is_complex:
                    results_by_category["✅ Simple Food"].append((food_name, first_result))
                    successful += 1
                else:
                    results_by_category["⚠️ Complex Food"].append((food_name, first_result))
                    successful += 1
                
                # Progress indicator
                if i % 10 == 0:
                    print(f"Progress: {i}/{len(TEST_FOODS)} foods tested...")
            else:
                results_by_category["❌ No Results"].append((food_name, "No results"))
                no_results += 1
                failed += 1
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            results_by_category["❌ No Results"].append((food_name, f"Error: {e}"))
            failed += 1
    
    # Print results by category
    print("\n" + "=" * 80)
    print("📊 DETAILED RESULTS BY CATEGORY")
    print("=" * 80)
    
    for category, items in results_by_category.items():
        if items:
            print(f"\n{category} ({len(items)} items):")
            for food, result in items[:5]:  # Show first 5 of each category
                print(f"  • {food:25} → {result}")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
    
    # Statistics
    print("\n" + "=" * 80)
    print("📊 STATISTICS")
    print("=" * 80)
    
    total = len(TEST_FOODS)
    success_rate = (successful / total) * 100
    nfs_rate = (nfs_found / total) * 100
    
    print(f"Total Foods Tested:     {total}")
    print(f"Successful Searches:    {successful} ({success_rate:.1f}%)")
    print(f"  - NFS Found:          {nfs_found} ({nfs_rate:.1f}%)")
    print(f"  - Simple Foods:       {len(results_by_category['✅ Simple Food'])}")
    print(f"  - Complex Foods:      {len(results_by_category['⚠️ Complex Food'])}")
    print(f"Failed Searches:        {failed} ({(failed/total)*100:.1f}%)")
    
    print("\n" + "=" * 80)
    
    # Pass if > 90% successful
    passed = success_rate >= 90
    
    if passed:
        print("✅ TEST PASSED: Search success rate is excellent!")
    else:
        print("⚠️ TEST FAILED: Search success rate is below 90%")
    
    print("=" * 80 + "\n")
    
    return passed


def test_nutrition_retrieval():
    """Test that nutrition data can be retrieved for common foods"""
    print("=" * 80)
    print("🧪 TEST: Nutrition Data Retrieval")
    print("=" * 80)
    
    usda = USDAService()
    
    # Test 20 diverse foods
    sample_foods = [
        "chicken breast", "salmon", "broccoli", "apple", "white rice",
        "eggs", "almonds", "yogurt", "sweet potato", "ground beef",
        "shrimp", "spinach", "banana", "oatmeal", "cheese",
        "black beans", "tuna", "carrots", "pasta", "milk"
    ]
    
    successful = 0
    failed = 0
    
    print(f"\nTesting nutrition retrieval for {len(sample_foods)} foods...\n")
    
    for food in sample_foods:
        try:
            nutrition = usda.get_nutrition_data(food, 100)
            
            if nutrition and nutrition.get('calories', 0) > 0:
                print(f"✅ {food:20} → {nutrition['calories']:.0f} cal, "
                      f"{nutrition['protein_g']:.1f}g protein, "
                      f"{nutrition['carbs_g']:.1f}g carbs, "
                      f"{nutrition['fat_g']:.1f}g fat")
                successful += 1
            else:
                print(f"❌ {food:20} → Invalid nutrition data")
                failed += 1
        except Exception as e:
            print(f"❌ {food:20} → Error: {e}")
            failed += 1
    
    print(f"\n📊 Results: {successful}/{len(sample_foods)} successful ({(successful/len(sample_foods))*100:.1f}%)")
    
    passed = successful >= len(sample_foods) * 0.9  # 90% success rate
    
    if passed:
        print("✅ TEST PASSED\n")
    else:
        print("⚠️ TEST FAILED\n")
    
    return passed


def test_category_accuracy():
    """Test search accuracy by food category"""
    print("=" * 80)
    print("🧪 TEST: Category-Specific Accuracy")
    print("=" * 80)
    
    usda = USDAService()
    
    categories = {
        "Meat & Poultry": ["chicken breast", "ground beef", "pork chops", "turkey", "bacon"],
        "Seafood": ["salmon", "tuna", "shrimp", "cod", "tilapia"],
        "Vegetables": ["broccoli", "carrots", "spinach", "tomatoes", "green beans"],
        "Fruits": ["apple", "banana", "orange", "strawberries", "grapes"],
        "Grains": ["white rice", "brown rice", "pasta", "bread", "oatmeal"],
        "Dairy": ["milk", "cheese", "yogurt", "eggs", "butter"],
    }
    
    category_results = {}
    
    for category, foods in categories.items():
        print(f"\n{category}:")
        successful = 0
        
        for food in foods:
            try:
                core_name = usda._extract_core_food_name(food)
                results = usda._search_food(core_name)
                
                if results and len(results) > 0:
                    desc = results[0].get('description', '')
                    has_nfs = ', nfs' in desc.lower() or ' nfs' in desc.lower()
                    status = "NFS" if has_nfs else "OK"
                    print(f"  ✅ {food:20} → {desc[:50]}... [{status}]")
                    successful += 1
                else:
                    print(f"  ❌ {food:20} → No results")
            except Exception as e:
                print(f"  ❌ {food:20} → Error")
        
        success_rate = (successful / len(foods)) * 100
        category_results[category] = success_rate
        print(f"  Category Success Rate: {success_rate:.1f}%")
    
    print("\n" + "=" * 80)
    print("📊 CATEGORY SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for category, rate in category_results.items():
        status = "✅" if rate >= 80 else "⚠️"
        print(f"{status} {category:20} {rate:.1f}%")
        if rate < 80:
            all_passed = False
    
    avg_rate = sum(category_results.values()) / len(category_results)
    print(f"\n📊 Average Success Rate: {avg_rate:.1f}%")
    
    if all_passed and avg_rate >= 85:
        print("✅ TEST PASSED\n")
        return True
    else:
        print("⚠️ TEST FAILED\n")
        return False


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("\n" + "=" * 80)
    print("🚀 COMPREHENSIVE USDA SEARCH TEST (100+ Foods)")
    print("=" * 80 + "\n")
    
    start_time = time.time()
    
    results = []
    
    results.append(("Search Success Rate", test_search_success_rate()))
    results.append(("Nutrition Retrieval", test_nutrition_retrieval()))
    results.append(("Category Accuracy", test_category_accuracy()))
    
    elapsed_time = time.time() - start_time
    
    # Final Summary
    print("=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} test suites passed")
    print(f"⏱️  Time: {elapsed_time:.1f} seconds")
    
    if passed == total:
        print("🎉 All comprehensive tests passed! Production ready!")
    else:
        print("⚠️  Some tests failed. Please review.")
    
    print("=" * 80 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = run_comprehensive_tests()
    exit(0 if success else 1)
