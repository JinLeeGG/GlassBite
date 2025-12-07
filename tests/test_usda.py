"""
test_usda.py - USDA API test with detailed matching info
"""

from services.usda_service import USDAService

def test_usda_foods_detailed():
    
    usda = USDAService()
    
    # List of food - 100 common foods across all categories
    test_foods = [
        # Poultry & Meat (15)
        ('chicken breast', 150),
        ('chicken thigh', 150),
        ('ground beef', 100),
        ('beef steak', 150),
        ('pork chop', 150),
        ('bacon', 30),
        ('turkey breast', 100),
        ('lamb chop', 100),
        ('ground pork', 100),
        ('ribeye steak', 150),
        ('chicken wing', 100),
        ('pork tenderloin', 150),
        ('beef brisket', 150),
        ('sausage', 50),
        ('ham', 100),
        
        # Seafood (10)
        ('salmon', 150),
        ('tuna', 150),
        ('shrimp', 100),
        ('cod', 150),
        ('tilapia', 150),
        ('crab', 100),
        ('lobster', 100),
        ('mackerel', 150),
        ('sardines', 100),
        ('trout', 150),
        
        # Grains & Carbs (15)
        ('white rice', 150),
        ('brown rice', 150),
        ('pasta', 100),
        ('quinoa', 100),
        ('oatmeal', 50),
        ('whole wheat bread', 60),
        ('white bread', 60),
        ('bagel', 80),
        ('tortilla', 50),
        ('couscous', 100),
        ('barley', 100),
        ('cornmeal', 50),
        ('rye bread', 60),
        ('rice noodles', 100),
        ('soba noodles', 100),
        
        # Vegetables (20)
        ('broccoli', 100),
        ('spinach', 100),
        ('carrot', 100),
        ('tomato', 150),
        ('cucumber', 100),
        ('bell pepper', 100),
        ('onion', 100),
        ('garlic', 10),
        ('kale', 100),
        ('lettuce', 100),
        ('cauliflower', 100),
        ('zucchini', 100),
        ('eggplant', 100),
        ('celery', 100),
        ('mushroom', 100),
        ('asparagus', 100),
        ('green beans', 100),
        ('cabbage', 100),
        ('brussels sprouts', 100),
        ('peas', 100),
        
        # Fruits (15)
        ('banana', 120),
        ('apple', 150),
        ('orange', 150),
        ('strawberry', 100),
        ('blueberry', 100),
        ('mango', 150),
        ('pineapple', 150),
        ('watermelon', 200),
        ('grapes', 100),
        ('peach', 150),
        ('pear', 150),
        ('kiwi', 100),
        ('cherry', 100),
        ('plum', 100),
        ('grapefruit', 150),
        
        # Dairy & Eggs (10)
        ('egg', 50),
        ('milk', 240),
        ('cheddar cheese', 30),
        ('mozzarella cheese', 30),
        ('greek yogurt', 150),
        ('cottage cheese', 100),
        ('butter', 10),
        ('cream cheese', 30),
        ('parmesan cheese', 20),
        ('sour cream', 30),
        
        # Nuts & Seeds (10)
        ('almonds', 30),
        ('peanuts', 30),
        ('walnuts', 30),
        ('cashews', 30),
        ('pistachios', 30),
        ('sunflower seeds', 30),
        ('chia seeds', 20),
        ('flax seeds', 20),
        ('pumpkin seeds', 30),
        ('pecans', 30),
        
        # Other (5)
        ('avocado', 100),
        ('sweet potato', 150),
        ('potato', 150),
        ('tofu', 100),
        ('beans', 100),
    ]
    
    print("="*70)
    print("USDA API Test - Detailed Matching")
    print("="*70)
    
    success_count = 0
    fail_count = 0
    
    for food_name, grams in test_foods:
        print(f"\n🔍 Testing: {food_name} ({grams}g)")
        print("-" * 70)
        
        try:
            # Search USDA to see what options are available
            search_results = usda._search_food(food_name)
            
            if search_results:
                print(f"📋 Found {len(search_results)} results:")
                for i, food in enumerate(search_results[:5], 1):
                    desc = food.get('description', 'N/A')
                    data_type = food.get('dataType', 'N/A')
                    print(f"   {i}. {desc}")
                    print(f"      Type: {data_type}")
                
                # Get actual nutrition using the first match
                food_data = search_results[0]
                nutrition = usda._extract_nutrients(food_data, grams)
                
                print(f"\n✅ Using: {food_data.get('description', 'N/A')}")
                print(f"   Calories: {nutrition['calories']:.1f} cal")
                print(f"   Protein:  {nutrition['protein_g']:.1f}g")
                print(f"   Carbs:    {nutrition['carbs_g']:.1f}g")
                print(f"   Fat:      {nutrition['fat_g']:.1f}g")
                
                success_count += 1
            else:
                print(f"❌ No results found")
                fail_count += 1
                
        except Exception as e:
            print(f"❌ Error: {e}")
            fail_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("Result Summary")
    print("="*70)
    print(f"✅ Success: {success_count}/{len(test_foods)}")
    print(f"❌ Failed: {fail_count}/{len(test_foods)}")
    print(f"Success rate: {(success_count/len(test_foods)*100):.0f}%")
    print("="*70)

if __name__ == '__main__':
    test_usda_foods_detailed()