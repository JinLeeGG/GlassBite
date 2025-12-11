"""
AI-Powered Recommendation Service
Provides personalized meal suggestions based on user history, goals, and preferences
"""

import logging
from datetime import datetime, date, timedelta
from models import db, User, Meal, FoodItem, FoodNutrient, DailySummary, Goal
from services.gemini_service import GeminiService
import json

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Intelligent meal recommendation engine"""
    
    def __init__(self):
        self.gemini = GeminiService()
        
        # Cuisine database with popular dishes
        self.cuisine_database = {
            'korean': {
                'name': 'Korean',
                'popular_dishes': ['Bibimbap', 'Bulgogi', 'Kimchi Jjigae', 'Japchae', 'Galbi', 'Tteokbokki', 'Samgyeopsal', 'Sundubu Jjigae'],
                'characteristics': 'fermented foods, rice-based, balanced vegetables, spicy flavors, banchan side dishes'
            },
            'vietnamese': {
                'name': 'Vietnamese',
                'popular_dishes': ['Pho', 'Banh Mi', 'Bun Cha', 'Goi Cuon', 'Com Tam', 'Bun Bo Hue', 'Cao Lau', 'Banh Xeo'],
                'characteristics': 'fresh herbs, rice noodles, light and healthy, fish sauce, balanced flavors'
            },
            'japanese': {
                'name': 'Japanese',
                'popular_dishes': ['Sushi', 'Ramen', 'Teriyaki Chicken', 'Tempura', 'Udon', 'Donburi', 'Miso Soup', 'Yakitori'],
                'characteristics': 'seafood-focused, umami flavors, rice-based, minimal oil, presentation-focused'
            },
            'chinese': {
                'name': 'Chinese',
                'popular_dishes': ['Kung Pao Chicken', 'Mapo Tofu', 'Peking Duck', 'Dim Sum', 'Fried Rice', 'Sweet and Sour Pork', 'Hot Pot'],
                'characteristics': 'wok cooking, diverse regional styles, balanced flavors, rice or noodle base'
            },
            'thai': {
                'name': 'Thai',
                'popular_dishes': ['Pad Thai', 'Green Curry', 'Tom Yum', 'Massaman Curry', 'Som Tam', 'Pad See Ew', 'Larb'],
                'characteristics': 'spicy, sweet, sour, and salty balance, coconut milk, fresh herbs, aromatic'
            },
            'indian': {
                'name': 'Indian',
                'popular_dishes': ['Chicken Tikka Masala', 'Palak Paneer', 'Biryani', 'Dal Tadka', 'Butter Chicken', 'Samosa', 'Naan'],
                'characteristics': 'rich spices, curry-based, lentils, rice, tandoor cooking, vegetarian-friendly'
            },
            'mexican': {
                'name': 'Mexican',
                'popular_dishes': ['Tacos', 'Burrito Bowl', 'Enchiladas', 'Quesadilla', 'Fajitas', 'Guacamole', 'Pozole'],
                'characteristics': 'corn and beans, fresh vegetables, spicy peppers, lime, cilantro'
            },
            'mediterranean': {
                'name': 'Mediterranean',
                'popular_dishes': ['Greek Salad', 'Hummus', 'Falafel', 'Shawarma', 'Moussaka', 'Tabbouleh', 'Souvlaki'],
                'characteristics': 'olive oil, fresh vegetables, legumes, whole grains, lean proteins, heart-healthy'
            },
            'italian': {
                'name': 'Italian',
                'popular_dishes': ['Pasta Primavera', 'Chicken Parmigiana', 'Minestrone', 'Caprese Salad', 'Risotto', 'Osso Buco'],
                'characteristics': 'pasta, olive oil, tomatoes, cheese, herbs, regional diversity'
            }
        }
    
    def get_cuisine_recommendation(self, user_id, cuisine_type, meal_type=None):
        """
        Generate cuisine-specific recommendations
        
        Args:
            user_id: User ID
            cuisine_type: Type of cuisine (korean, vietnamese, japanese, etc.)
            meal_type: Optional meal type (breakfast, lunch, dinner, snack)
        
        Returns:
            str: Formatted recommendation message
        """
        try:
            # Build user profile
            user_profile = self._build_user_profile(user_id)
            
            # Get cuisine info
            cuisine_info = self.cuisine_database.get(cuisine_type.lower())
            
            if not cuisine_info:
                return f"I don't have detailed information about {cuisine_type} cuisine yet. Try Korean, Vietnamese, Japanese, Chinese, Thai, Indian, Mexican, Mediterranean, or Italian."
            
            # Generate AI-powered recommendations
            recommendations = self._generate_cuisine_recommendations(
                user_profile, 
                cuisine_info, 
                meal_type
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating cuisine recommendations: {e}")
            return "Unable to generate recommendations at this time."
    
    def get_daily_meal_plan(self, user_id):
        """
        Generate a complete day's meal plan using Gemini AI
        
        Args:
            user_id: User ID
        
        Returns:
            str: Formatted daily meal plan
        """
        try:
            # Gather comprehensive user data
            user_profile = self._build_comprehensive_profile(user_id)
            
            if not user_profile:
                return "I need at least 3 days of meal data to create a personalized meal plan. Keep logging your meals!"
            
            # Generate AI-powered daily meal plan
            daily_plan = self._generate_daily_meal_plan(user_profile)
            
            return daily_plan
            
        except Exception as e:
            logger.error(f"Error generating daily meal plan: {e}")
            return "Unable to generate meal plan at this time. Please try again later."
    
    def _build_user_profile(self, user_id):
        """Build basic user profile for cuisine recommendations"""
        
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Get recent meal history (last 7 days)
        seven_days_ago = date.today() - timedelta(days=7)
        recent_meals = Meal.query.filter(
            Meal.user_id == user_id,
            Meal.timestamp >= seven_days_ago,
            Meal.processing_status == 'completed'
        ).order_by(Meal.timestamp.desc()).limit(21).all()
        
        # Get current goals
        goals = Goal.query.filter_by(user_id=user_id, is_active=True).all()
        
        # Get today's progress
        today_summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today()
        ).first()
        
        profile = {
            'user_id': user_id,
            'dietary_restrictions': user.dietary_restrictions or "None",
            'goals': self._format_goals(goals),
            'today_progress': self._format_today_progress(today_summary, goals),
            'recent_foods': self._get_recent_foods(recent_meals)
        }
        
        return profile
    
    def _get_recent_foods(self, meals):
        """Get recently eaten foods"""
        foods = []
        for meal in meals[:10]:  # Last 10 meals
            meal_foods = FoodItem.query.filter_by(meal_id=meal.id).all()
            foods.extend([f.name for f in meal_foods])
        return list(set(foods))[:15]  # Unique foods, max 15
    
    def _build_comprehensive_profile(self, user_id):
        """Build comprehensive user profile with detailed eating history"""
        
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Get last 14 days of meal history
        two_weeks_ago = date.today() - timedelta(days=14)
        recent_meals = Meal.query.filter(
            Meal.user_id == user_id,
            Meal.timestamp >= two_weeks_ago,
            Meal.processing_status == 'completed'
        ).order_by(Meal.timestamp.desc()).all()
        
        if len(recent_meals) < 3:
            return None
        
        # Build detailed meal history
        meal_history = self._format_meal_history(recent_meals)
        
        # Get nutritional patterns
        nutrition_patterns = self._analyze_nutrition_patterns(recent_meals)
        
        # Get current goals
        goals = Goal.query.filter_by(user_id=user_id, is_active=True).all()
        
        # Get today's progress
        today_summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today()
        ).first()
        
        # Get recent daily summaries
        recent_summaries = DailySummary.query.filter(
            DailySummary.user_id == user_id,
            DailySummary.date >= two_weeks_ago
        ).order_by(DailySummary.date.desc()).all()
        
        profile = {
            'user_id': user_id,
            'dietary_restrictions': user.dietary_restrictions or "None specified",
            'meal_history': meal_history,
            'nutrition_patterns': nutrition_patterns,
            'goals': self._format_goals(goals),
            'today_progress': self._format_today_progress(today_summary, goals),
            'recent_averages': self._calculate_recent_averages(recent_summaries),
            'nutrient_gaps': self._identify_nutrient_gaps_detailed(recent_meals, goals)
        }
        
        return profile
    
    def _format_meal_history(self, meals):
        """Format recent meals for AI analysis"""
        
        history = []
        
        for meal in meals[:21]:  # Last 21 meals (about 7 days)
            meal_data = {
                'date': meal.timestamp.strftime('%A, %B %d'),
                'time': meal.timestamp.strftime('%I:%M %p'),
                'meal_type': meal.meal_type,
                'foods': []
            }
            
            foods = FoodItem.query.filter_by(meal_id=meal.id).all()
            
            for food in foods:
                food_info = {
                    'name': food.name,
                    'portion_grams': food.portion_size_grams
                }
                
                if food.nutrients:
                    food_info.update({
                        'calories': round(food.nutrients.calories, 0),
                        'protein_g': round(food.nutrients.protein_g, 1),
                        'carbs_g': round(food.nutrients.carbs_g, 1),
                        'fat_g': round(food.nutrients.fat_g, 1)
                    })
                
                meal_data['foods'].append(food_info)
            
            if meal_data['foods']:  # Only include meals with food data
                history.append(meal_data)
        
        return history
    
    def _analyze_nutrition_patterns(self, meals):
        """Analyze detailed nutrition patterns"""
        
        patterns = {
            'most_common_foods': {},
            'meal_type_distribution': {},
            'average_meal_size': 0,
            'protein_per_meal': 0,
            'carbs_per_meal': 0,
            'fat_per_meal': 0
        }
        
        total_meals = len(meals)
        if total_meals == 0:
            return patterns
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for meal in meals:
            meal_type = meal.meal_type or 'unknown'
            patterns['meal_type_distribution'][meal_type] = \
                patterns['meal_type_distribution'].get(meal_type, 0) + 1
            
            foods = FoodItem.query.filter_by(meal_id=meal.id).all()
            
            for food in foods:
                patterns['most_common_foods'][food.name] = \
                    patterns['most_common_foods'].get(food.name, 0) + 1
                
                if food.nutrients:
                    total_calories += food.nutrients.calories or 0
                    total_protein += food.nutrients.protein_g or 0
                    total_carbs += food.nutrients.carbs_g or 0
                    total_fat += food.nutrients.fat_g or 0
        
        patterns['average_meal_size'] = round(total_calories / total_meals, 0)
        patterns['protein_per_meal'] = round(total_protein / total_meals, 1)
        patterns['carbs_per_meal'] = round(total_carbs / total_meals, 1)
        patterns['fat_per_meal'] = round(total_fat / total_meals, 1)
        
        # Get top 10 most common foods
        patterns['top_foods'] = sorted(
            patterns['most_common_foods'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return patterns
    
    def _format_goals(self, goals):
        """Format goals for AI analysis"""
        goal_dict = {}
        for goal in goals:
            goal_dict[goal.goal_type] = goal.target_value
        return goal_dict if goal_dict else {'calorie_target': 2000, 'protein_target': 100}
    
    def _format_today_progress(self, summary, goals):
        """Format today's progress"""
        if not summary:
            return {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        
        return {
            'calories': round(summary.total_calories, 0),
            'protein': round(summary.total_protein, 1),
            'carbs': round(summary.total_carbs, 1),
            'fat': round(summary.total_fat, 1)
        }
    
    def _calculate_recent_averages(self, summaries):
        """Calculate average daily nutrition from recent days"""
        
        if not summaries:
            return {}
        
        total_days = len(summaries)
        
        return {
            'avg_daily_calories': round(sum(s.total_calories for s in summaries) / total_days, 0),
            'avg_daily_protein': round(sum(s.total_protein for s in summaries) / total_days, 1),
            'avg_daily_carbs': round(sum(s.total_carbs for s in summaries) / total_days, 1),
            'avg_daily_fat': round(sum(s.total_fat for s in summaries) / total_days, 1)
        }
    
    def _identify_nutrient_gaps_detailed(self, meals, goals):
        """Identify specific nutrient deficiencies with details"""
        
        nutrient_totals = {
            'protein': 0,
            'fiber': 0,
            'calcium': 0,
            'iron': 0,
            'vitamin_c': 0,
            'vitamin_d': 0
        }
        
        days = set()
        
        for meal in meals:
            days.add(meal.timestamp.date())
            foods = FoodItem.query.filter_by(meal_id=meal.id).all()
            
            for food in foods:
                if food.nutrients:
                    nutrient_totals['protein'] += food.nutrients.protein_g or 0
                    nutrient_totals['fiber'] += food.nutrients.fiber_g or 0
                    nutrient_totals['calcium'] += food.nutrients.calcium_mg or 0
                    nutrient_totals['iron'] += food.nutrients.iron_mg or 0
                    nutrient_totals['vitamin_c'] += food.nutrients.vitamin_c_mg or 0
                    nutrient_totals['vitamin_d'] += food.nutrients.vitamin_d_ug or 0
        
        num_days = len(days) if days else 1
        avg_nutrients = {k: round(v / num_days, 1) for k, v in nutrient_totals.items()}
        
        gaps = []
        if avg_nutrients['protein'] < 50:
            gaps.append(f"protein (averaging {avg_nutrients['protein']}g, need 50g+)")
        if avg_nutrients['fiber'] < 25:
            gaps.append(f"fiber (averaging {avg_nutrients['fiber']}g, need 25g+)")
        if avg_nutrients['calcium'] < 1000:
            gaps.append(f"calcium (averaging {avg_nutrients['calcium']}mg, need 1000mg+)")
        if avg_nutrients['iron'] < 18:
            gaps.append(f"iron (averaging {avg_nutrients['iron']}mg, need 18mg+)")
        if avg_nutrients['vitamin_c'] < 75:
            gaps.append(f"vitamin C (averaging {avg_nutrients['vitamin_c']}mg, need 75mg+)")
        if avg_nutrients['vitamin_d'] < 15:
            gaps.append(f"vitamin D (averaging {avg_nutrients['vitamin_d']}mcg, need 15mcg+)")
        
        return gaps
    
    def _generate_daily_meal_plan(self, profile):
        """Generate complete daily meal plan using Gemini AI"""
        
        prompt = f"""You are a professional nutritionist creating a personalized daily meal plan.

USER DIETARY PROFILE:
Dietary Restrictions: {profile['dietary_restrictions']}

RECENT EATING HISTORY (Last 7 Days):
{json.dumps(profile['meal_history'][:15], indent=2)}

NUTRITION PATTERNS:
- Average meal size: {profile['nutrition_patterns']['average_meal_size']} calories
- Average protein per meal: {profile['nutrition_patterns']['protein_per_meal']}g
- Average carbs per meal: {profile['nutrition_patterns']['carbs_per_meal']}g
- Average fat per meal: {profile['nutrition_patterns']['fat_per_meal']}g

FAVORITE FOODS (Most Frequently Eaten):
{', '.join([food for food, count in profile['nutrition_patterns']['top_foods'][:5]])}

DAILY GOALS:
{json.dumps(profile['goals'], indent=2)}

RECENT AVERAGES (Last 14 Days):
{json.dumps(profile['recent_averages'], indent=2)}

NUTRIENT GAPS TO ADDRESS:
{', '.join(profile['nutrient_gaps']) if profile['nutrient_gaps'] else 'None identified'}

TODAY'S PROGRESS SO FAR:
{json.dumps(profile['today_progress'], indent=2)}

TASK:
Create a DIVERSE meal plan for the REST OF TODAY featuring dishes from DIFFERENT countries/cuisines.

REQUIREMENTS:
1. Include dishes from at least 2-3 different international cuisines (Korean, Vietnamese, Japanese, Thai, Indian, Mediterranean, etc.)
2. Each meal should be from a DIFFERENT cuisine to maximize variety
3. Use authentic dish names (e.g., "Bibimbap" not "Korean rice bowl")
4. Specify exact portion sizes
5. Provide detailed nutrition breakdown
6. Fits the user's eating patterns and preferences
7. Meets daily nutrition goals
8. Addresses identified nutrient gaps
9. NO emojis - voice-optimized text only

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

Here's your personalized international meal plan for today:

BREAKFAST (Cuisine: [Country/Region])
[Dish name in native language]
[Ingredient 1], [portion]
[Ingredient 2], [portion]
[Ingredient 3], [portion]
Total: [calories] calories, [protein]g protein, [carbs]g carbs, [fat]g fat

LUNCH (Cuisine: [Different Country/Region])
[Dish name]
[Ingredient 1], [portion]
[Ingredient 2], [portion]
[Ingredient 3], [portion]
Total: [calories] calories, [protein]g protein, [carbs]g carbs, [fat]g fat

DINNER (Cuisine: [Another Different Country/Region])
[Dish name]
[Ingredient 1], [portion]
[Ingredient 2], [portion]
[Ingredient 3], [portion]
Total: [calories] calories, [protein]g protein, [carbs]g carbs, [fat]g fat

SNACKS
[Snack 1], [portion]
[Snack 2], [portion]
Total: [calories] calories, [protein]g protein

DAILY TOTALS
Calories: [total]
Protein: [total]g
Carbs: [total]g
Fat: [total]g

WHY THIS DIVERSE PLAN WORKS FOR YOU
[2-3 sentences explaining the cultural variety and how it addresses their patterns and goals]

Be specific with dish names. Use real international dishes."""

        try:
            logger.info("Requesting diverse international meal plan from Gemini...")
            response = self.gemini.model.generate_content(prompt)
            
            if response and response.text:
                return response.text
            else:
                return self._fallback_daily_plan(profile)
                
        except Exception as e:
            logger.error(f"Gemini API error in daily meal plan: {e}")
            return self._fallback_daily_plan(profile)
    
    def _fallback_daily_plan(self, profile):
        """Fallback meal plan if AI fails"""
        
        calorie_target = profile['goals'].get('calorie_target', 2000)
        protein_target = profile['goals'].get('protein_target', 100)
        
        return f"""Here's a diverse international meal plan for today:

BREAKFAST (Cuisine: Japanese)
Miso soup with tofu, 1 bowl
Grilled salmon, 100g
Steamed rice, 150g
Nori seaweed, 5g
Total: 400 calories, 28g protein, 45g carbs, 12g fat

LUNCH (Cuisine: Vietnamese)
Pho Bo, beef noodle soup, 1 large bowl
Rice noodles, 200g
Beef slices, 100g
Fresh herbs (basil, cilantro, mint), 30g
Total: 450 calories, 30g protein, 60g carbs, 8g fat

DINNER (Cuisine: Korean)
Bibimbap with bulgogi
Mixed vegetables, 150g
Bulgogi beef, 120g
Brown rice, 200g
Gochujang sauce, 2 tablespoons
Total: 650 calories, 35g protein, 75g carbs, 18g fat

SNACKS
Greek yogurt with honey, 150g
Almonds, 30g
Total: 300 calories, 12g protein, 25g carbs, 12g fat

DAILY TOTALS
Calories: 1800
Protein: 105g
Carbs: 205g
Fat: 50g

WHY THIS DIVERSE PLAN WORKS FOR YOU
This plan features authentic dishes from three different Asian cuisines, providing variety in flavors and nutrients while meeting your protein goals and staying within your calorie target."""


    def _generate_cuisine_recommendations(self, profile, cuisine_info, meal_type):
        """Generate cuisine-specific recommendations using Gemini AI"""
        
        remaining_cal = profile['today_progress'].get('calories', 0)
        calorie_goal = profile['goals'].get('calorie_target', 2000)
        remaining = calorie_goal - remaining_cal
        
        prompt = f"""You are an expert in {cuisine_info['name']} cuisine and nutrition.

USER PROFILE:
- Dietary restrictions: {profile['dietary_restrictions']}
- Daily calorie goal: {calorie_goal}
- Calories consumed today: {remaining_cal}
- Calories remaining: {remaining}
- Recent foods eaten: {', '.join(profile.get('recent_foods', [])[:10])}

CUISINE INFORMATION:
- Cuisine: {cuisine_info['name']}
- Popular dishes: {', '.join(cuisine_info['popular_dishes'])}
- Characteristics: {cuisine_info['characteristics']}

TASK:
Recommend 3 authentic {cuisine_info['name']} dishes for {meal_type or 'the next meal'}.

REQUIREMENTS:
1. Each dish should be a real, authentic {cuisine_info['name']} dish
2. Include specific ingredients and typical portion sizes
3. Provide estimated calories, protein, carbs, and fat
4. Ensure dishes fit within remaining calorie budget ({remaining} calories)
5. Consider dietary restrictions: {profile['dietary_restrictions']}
6. Explain what makes each dish healthy or balanced
7. NO emojis - voice-optimized text only

FORMAT:
Option 1: [Dish Name in native language if applicable]
Description: [Brief description of the dish]
Main ingredients: [ingredient 1], [ingredient 2], [ingredient 3]
Typical serving: [portion description]
Nutrition: [calories] calories, [protein]g protein, [carbs]g carbs, [fat]g fat
Why it works: [Brief health benefit]

Option 2: [similar format]

Option 3: [similar format]

Be specific and culturally authentic. Use real dish names."""

        try:
            logger.info(f"Requesting {cuisine_info['name']} recommendations from Gemini...")
            response = self.gemini.model.generate_content(prompt)
            
            if response and response.text:
                header = f"Here are {cuisine_info['name']} meal suggestions for {meal_type or 'you'}:\n\n"
                return header + response.text
            else:
                return self._fallback_cuisine_recommendations(cuisine_info, meal_type, remaining)
                
        except Exception as e:
            logger.error(f"Gemini API error in cuisine recommendations: {e}")
            return self._fallback_cuisine_recommendations(cuisine_info, meal_type, remaining)
    
    def _fallback_cuisine_recommendations(self, cuisine_info, meal_type, remaining_cal):
        """Fallback recommendations if AI fails"""
        
        dishes = cuisine_info['popular_dishes'][:3]
        
        response = f"Here are some popular {cuisine_info['name']} dishes:\n\n"
        
        for i, dish in enumerate(dishes, 1):
            response += f"Option {i}: {dish}\n"
            response += f"A traditional {cuisine_info['name']} dish\n"
            response += f"Estimated 400-600 calories per serving\n\n"
        
        return response


# Singleton instance
recommendation_engine = RecommendationEngine()

def get_daily_meal_plan(user_id):
    """Helper function to get daily meal plan"""
    return recommendation_engine.get_daily_meal_plan(user_id)

def get_cuisine_recommendation(user_id, cuisine_type, meal_type=None):
    """Helper function to get cuisine-specific recommendations"""
    return recommendation_engine.get_cuisine_recommendation(user_id, cuisine_type, meal_type)
