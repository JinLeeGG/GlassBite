"""
AI-Powered Recommendation Engine
Uses Gemini AI + Database Analysis for personalized meal suggestions
"""

import logging
import google.generativeai as genai
from datetime import datetime, timedelta, date
from collections import Counter, defaultdict
from models import db, User, Meal, FoodItem, FoodNutrient, DailySummary, Goal
from sqlalchemy import func
from config import Config

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """AI-powered meal recommendation system using database insights"""
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def get_recommendations(self, user_id, context='general'):
        """
        Generate AI-powered personalized meal recommendations
        
        Args:
            user_id: User ID
            context: 'general', 'breakfast', 'lunch', 'dinner', 'snack'
        
        Returns:
            Personalized recommendation message
        """
        try:
            # 1. Gather intelligence from database
            user_insights = self._gather_user_insights(user_id)
            nutrient_gaps = self._calculate_nutrient_gaps(user_id)
            community_insights = self._get_community_insights()
            
            # 2. Use Gemini to generate personalized recommendations
            recommendations = self._generate_ai_recommendations(
                user_insights,
                nutrient_gaps,
                community_insights,
                context
            )
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}")
            return self._fallback_recommendations(user_id)
    
    def _gather_user_insights(self, user_id):
        """Extract deep insights from user's eating history"""
        # Get last 30 days of meals
        start_date = date.today() - timedelta(days=30)
        
        meals = Meal.query.filter(
            Meal.user_id == user_id,
            Meal.timestamp >= datetime.combine(start_date, datetime.min.time()),
            Meal.processing_status == 'completed'
        ).all()
        
        insights = {
            'total_meals': len(meals),
            'favorite_foods': [],
            'avg_meal_calories': 0,
            'avg_protein_per_meal': 0,
            'meal_times': defaultdict(int),
            'meal_type_frequency': defaultdict(int),
            'recent_foods': [],
            'food_frequency': Counter()
        }
        
        if not meals:
            return insights
        
        total_calories = 0
        total_protein = 0
        recent_foods_list = []
        
        for meal in meals:
            # Track meal types
            if meal.meal_type:
                insights['meal_type_frequency'][meal.meal_type] += 1
            
            # Track meal times
            hour = meal.timestamp.hour
            insights['meal_times'][hour] += 1
            
            # Get foods and nutrients
            foods = FoodItem.query.filter_by(meal_id=meal.id).all()
            for food in foods:
                food_name = food.name.lower()
                insights['food_frequency'][food_name] += 1
                
                # Track recent foods (last 7 days)
                if meal.timestamp >= datetime.now() - timedelta(days=7):
                    recent_foods_list.append(food_name)
                
                if food.nutrients:
                    total_calories += food.nutrients.calories or 0
                    total_protein += food.nutrients.protein_g or 0
        
        # Calculate averages
        if len(meals) > 0:
            insights['avg_meal_calories'] = total_calories / len(meals)
            insights['avg_protein_per_meal'] = total_protein / len(meals)
        
        # Get top 10 favorite foods
        insights['favorite_foods'] = [food for food, count in insights['food_frequency'].most_common(10)]
        insights['recent_foods'] = list(set(recent_foods_list[-15:]))  # Last 15 unique foods
        
        return insights
    
    def _calculate_nutrient_gaps(self, user_id):
        """Calculate current nutrient gaps and goals"""
        # Get today's summary
        today = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today()
        ).first()
        
        # Get active goals
        calorie_goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type='calorie_target',
            is_active=True
        ).first()
        
        protein_goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type='protein_target',
            is_active=True
        ).first()
        
        carb_goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type='carb_target',
            is_active=True
        ).first()
        
        gaps = {
            'calories_remaining': 0,
            'protein_remaining': 0,
            'carbs_remaining': 0,
            'fat_remaining': 0,
            'calories_consumed': 0,
            'protein_consumed': 0,
            'carbs_consumed': 0,
            'over_budget': False,
            'has_goals': False
        }
        
        if calorie_goal:
            gaps['has_goals'] = True
            if today:
                gaps['calories_consumed'] = today.total_calories
                gaps['protein_consumed'] = today.total_protein
                gaps['carbs_consumed'] = today.total_carbs
                gaps['calories_remaining'] = max(0, calorie_goal.target_value - today.total_calories)
                if today.total_calories > calorie_goal.target_value:
                    gaps['over_budget'] = True
            else:
                gaps['calories_remaining'] = calorie_goal.target_value
        
        if protein_goal:
            if today:
                gaps['protein_remaining'] = max(0, protein_goal.target_value - today.total_protein)
            else:
                gaps['protein_remaining'] = protein_goal.target_value
        
        if carb_goal:
            if today:
                gaps['carbs_remaining'] = max(0, carb_goal.target_value - today.total_carbs)
            else:
                gaps['carbs_remaining'] = carb_goal.target_value
        
        return gaps
    
    def _get_community_insights(self):
        """Get popular foods from all users (community wisdom)"""
        try:
            # Get top 20 most logged foods across all users
            popular_foods = db.session.query(
                FoodItem.name,
                func.count(FoodItem.id).label('count'),
                func.avg(FoodItem.portion_size_grams).label('avg_portion')
            ).join(
                FoodNutrient, FoodItem.id == FoodNutrient.food_item_id
            ).group_by(
                FoodItem.name
            ).order_by(
                func.count(FoodItem.id).desc()
            ).limit(20).all()
            
            community_favorites = []
            for food in popular_foods:
                community_favorites.append({
                    'name': food[0],
                    'popularity_count': food[1],
                    'avg_portion': food[2] or 100
                })
            
            return {
                'popular_foods': community_favorites
            }
        except Exception as e:
            logger.error(f"Error getting community insights: {e}")
            return {'popular_foods': []}
    
    def _generate_ai_recommendations(self, user_insights, nutrient_gaps, community_insights, context):
        """Use Gemini AI to generate personalized recommendations"""
        
        # Build context-rich prompt
        prompt = self._build_ai_prompt(user_insights, nutrient_gaps, community_insights, context)
        
        try:
            # Call Gemini
            response = self.model.generate_content(prompt)
            
            # Parse and format response
            recommendations = self._parse_ai_response(response.text, nutrient_gaps)
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Fallback to rule-based
            return self._rule_based_recommendations(user_insights, nutrient_gaps, context)
    
    def _build_ai_prompt(self, user_insights, nutrient_gaps, community_insights, context):
        """Build intelligent prompt for Gemini"""
        
        # Context header
        time_context = {
            'breakfast': 'breakfast time (morning meal)',
            'lunch': 'lunch time (midday meal)',
            'dinner': 'dinner time (evening meal)',
            'snack': 'snack time (light meal)',
            'general': 'any time of day'
        }.get(context, 'general')
        
        prompt = f"""You are a nutrition expert AI. Generate 3 personalized meal recommendations for {time_context}.

USER EATING PROFILE:
- Total meals logged: {user_insights['total_meals']}
- Average meal: {user_insights['avg_meal_calories']:.0f} calories, {user_insights['avg_protein_per_meal']:.0f}g protein
- Favorite foods: {', '.join(user_insights['favorite_foods'][:8]) if user_insights['favorite_foods'] else 'None yet'}
- Recently ate: {', '.join(user_insights['recent_foods'][-5:]) if user_insights['recent_foods'] else 'None'}

TODAY'S NUTRITION STATUS:
- Calories consumed: {nutrient_gaps['calories_consumed']:.0f}
- Protein consumed: {nutrient_gaps['protein_consumed']:.0f}g
- Carbs consumed: {nutrient_gaps['carbs_consumed']:.0f}g
- Calories remaining: {nutrient_gaps['calories_remaining']:.0f}
- Protein remaining: {nutrient_gaps['protein_remaining']:.0f}g
- Over budget: {'YES - need light meals' if nutrient_gaps['over_budget'] else 'No'}

POPULAR COMMUNITY FOODS (what others eat):
{', '.join([f['name'] for f in community_insights['popular_foods'][:10]]) if community_insights['popular_foods'] else 'Various healthy options'}

REQUIREMENTS:
1. Suggest 3 realistic meals that fit their remaining calories/protein
2. Consider their eating history (what they actually like)
3. Avoid foods they just ate (provide variety)
4. Use realistic portion sizes
5. Each meal should include: name, calories, protein, carbs, fat
6. Add one personalization insight per meal (why it's good for them)

OUTPUT FORMAT (plain text, no JSON):
1. [Meal name]
   [Calories] calories, [protein]g protein, [carbs]g carbs, [fat]g fat
   → [Why this meal fits them]

2. [Meal name]
   [Calories] calories, [protein]g protein, [carbs]g carbs, [fat]g fat
   → [Why this meal fits them]

3. [Meal name]
   [Calories] calories, [protein]g protein, [carbs]g carbs, [fat]g fat
   → [Why this meal fits them]

IMPORTANT: Be concise. Use simple language. No emojis. Focus on practical meals they can actually make or buy.
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_text, nutrient_gaps):
        """Parse and format Gemini's response"""
        
        try:
            # Add header based on situation
            if nutrient_gaps['over_budget']:
                header = f"You're over budget. Light options:\n\n"
            elif nutrient_gaps['calories_remaining'] > 800:
                header = f"You have {nutrient_gaps['calories_remaining']:.0f} calories remaining.\n\n"
            elif nutrient_gaps['calories_remaining'] > 0:
                header = f"You have {nutrient_gaps['calories_remaining']:.0f} calories left.\n\n"
            else:
                header = "Personalized meal ideas:\n\n"
            
            # Clean up AI response
            cleaned = ai_text.strip()
            
            # Remove any markdown formatting
            cleaned = cleaned.replace('**', '').replace('*', '')
            
            # Combine header + AI recommendations
            final_response = header + cleaned
            
            # Add protein reminder if needed
            if nutrient_gaps['protein_remaining'] > 40:
                final_response += f"\n\n💪 Focus on protein - you need {nutrient_gaps['protein_remaining']:.0f}g more today"
            
            return final_response
        
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return ai_text  # Return raw if parsing fails
    
    def _rule_based_recommendations(self, user_insights, nutrient_gaps, context):
        """Fallback rule-based recommendations using user data"""
        
        # Get favorite foods as inspiration
        favorite_proteins = []
        favorite_carbs = []
        
        for food in user_insights['favorite_foods'][:5]:
            if any(protein in food for protein in ['chicken', 'salmon', 'egg', 'beef', 'turkey', 'tuna']):
                favorite_proteins.append(food)
            elif any(carb in food for carb in ['rice', 'bread', 'pasta', 'potato', 'oat']):
                favorite_carbs.append(food)
        
        protein_base = favorite_proteins[0] if favorite_proteins else "grilled chicken"
        carb_base = favorite_carbs[0] if favorite_carbs else "brown rice"
        
        remaining_cal = nutrient_gaps['calories_remaining']
        
        if remaining_cal < 300:
            return f"""You have {remaining_cal:.0f} calories left.

Light options:
1. Greek yogurt with berries
   180 calories, 15g protein
   → Low calorie, high protein

2. Small salad with {protein_base}
   250 calories, 25g protein
   → Based on your favorites

3. Protein shake
   200 calories, 20g protein
   → Quick and easy"""
        
        elif remaining_cal < 600:
            return f"""You have {remaining_cal:.0f} calories left.

Balanced meals:
1. {protein_base.title()} with {carb_base}
   480 calories, 40g protein
   → Your go-to meal

2. Grilled salmon with quinoa
   520 calories, 38g protein
   → Omega-3 rich

3. Turkey wrap with vegetables
   420 calories, 30g protein
   → Light but filling"""
        
        else:
            return f"""You have {remaining_cal:.0f} calories left.

Full meals:
1. {protein_base.title()} with {carb_base} and vegetables
   650 calories, 50g protein
   → Your usual favorite

2. Steak with sweet potato
   680 calories, 52g protein
   → Hearty and satisfying

3. Chicken burrito bowl
   580 calories, 40g protein
   → Balanced macros"""
    
    def _fallback_recommendations(self, user_id):
        """Simple fallback if everything fails"""
        gaps = self._calculate_nutrient_gaps(user_id)
        
        if gaps['calories_remaining'] < 300:
            return """Light options:
1. Greek yogurt with berries - 180 cal, 15g protein
2. Small salad with chicken - 250 cal, 25g protein
3. Protein shake - 200 cal, 20g protein"""
        elif gaps['calories_remaining'] < 600:
            return """Balanced meals:
1. Grilled salmon with quinoa - 520 cal, 38g protein
2. Chicken with brown rice - 480 cal, 40g protein
3. Turkey wrap - 420 cal, 30g protein"""
        else:
            return """Full meals:
1. Steak with sweet potato - 680 cal, 52g protein
2. Chicken burrito bowl - 580 cal, 40g protein
3. Pasta with lean beef - 620 cal, 42g protein"""


# Singleton instance
recommendation_engine = RecommendationEngine()

def get_meal_recommendations(user_id, context='general'):
    """Helper function for getting AI-powered recommendations"""
    return recommendation_engine.get_recommendations(user_id, context)
