"""
Test script for AI-powered recommendation engine
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from services.recommendation_service import recommendation_engine

def test_recommendations():
    """Test recommendation engine with different contexts"""
    
    with app.app_context():
        print("=" * 60)
        print("AI-POWERED RECOMMENDATION ENGINE TEST")
        print("=" * 60)
        
        # Test user ID (use an existing user or test with ID 1)
        test_user_id = 1
        
        # Test 1: General recommendations
        print("\n📋 TEST 1: General Recommendations")
        print("-" * 60)
        try:
            result = recommendation_engine.get_recommendations(test_user_id, 'general')
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Breakfast recommendations
        print("\n\n🍳 TEST 2: Breakfast Recommendations")
        print("-" * 60)
        try:
            result = recommendation_engine.get_recommendations(test_user_id, 'breakfast')
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Dinner recommendations
        print("\n\n🍽️ TEST 3: Dinner Recommendations")
        print("-" * 60)
        try:
            result = recommendation_engine.get_recommendations(test_user_id, 'dinner')
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Check user insights gathering
        print("\n\n📊 TEST 4: User Insights Analysis")
        print("-" * 60)
        try:
            insights = recommendation_engine._gather_user_insights(test_user_id)
            print(f"Total meals logged: {insights['total_meals']}")
            print(f"Average meal calories: {insights['avg_meal_calories']:.0f}")
            print(f"Average protein per meal: {insights['avg_protein_per_meal']:.0f}g")
            print(f"Favorite foods: {', '.join(insights['favorite_foods'][:5])}")
            print(f"Recent foods: {', '.join(insights['recent_foods'][:5])}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: Check nutrient gaps
        print("\n\n📈 TEST 5: Nutrient Gaps Calculation")
        print("-" * 60)
        try:
            gaps = recommendation_engine._calculate_nutrient_gaps(test_user_id)
            print(f"Calories consumed: {gaps['calories_consumed']:.0f}")
            print(f"Calories remaining: {gaps['calories_remaining']:.0f}")
            print(f"Protein consumed: {gaps['protein_consumed']:.0f}g")
            print(f"Protein remaining: {gaps['protein_remaining']:.0f}g")
            print(f"Over budget: {gaps['over_budget']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 6: Community insights
        print("\n\n👥 TEST 6: Community Insights")
        print("-" * 60)
        try:
            community = recommendation_engine._get_community_insights()
            popular = community.get('popular_foods', [])
            print(f"Top community foods:")
            for i, food in enumerate(popular[:5], 1):
                print(f"  {i}. {food['name']} (logged {food['popularity_count']} times)")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ TESTS COMPLETE")
        print("=" * 60)


if __name__ == '__main__':
    test_recommendations()
