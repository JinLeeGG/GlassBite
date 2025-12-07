"""
Chatbot Service - Natural language question handling
Classifies questions and routes to appropriate handlers
"""

import re
import logging
from datetime import datetime, timedelta, date
from models import db, User, Meal, FoodItem, DailySummary, Goal
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Simple in-memory conversation context
conversation_context = {}

class ChatbotService:
    """Service for handling natural language questions"""
    
    def classify_question(self, message_text):
        """
        Determine what type of question the user is asking
        
        Returns:
            Tuple of (question_type, params)
        """
        message = message_text.lower()
        
        # Goal setting (check FIRST - more specific patterns with numbers)
        if re.search(r'(my goal is|goal is|set.+goal).+\d+', message):
            return 'goal_setting', {}
        
        # Goal progress (questions about goals - check before general nutrient queries)
        if any(word in message for word in ['what is my goal', "what's my goal", 'my progress', 'goal progress', 'am i meeting', 'meeting my goal', 'what is my progress', "what's my progress", 'how am i doing']):
            return 'goal_progress', {}
        
        # Meal history queries (check first before daily summary)
        if any(word in message for word in ['what did i eat', 'what did i have', 'what did i had', 'show me what', 'what have i eaten']):
            timeframe = self.extract_timeframe(message)
            return 'history_query', {'timeframe': timeframe}
        
        if any(word in message for word in ['yesterday', 'last week', 'last month']):
            timeframe = self.extract_timeframe(message)
            return 'history_query', {'timeframe': timeframe}
        
        # Today's summary
        if any(word in message for word in ['today', 'so far']):
            if any(word in message for word in ['total', 'doing', 'summary', 'how am i', 'how\'s my']):
                return 'daily_summary', {'date': 'today'}
        
        # Specific nutrient query
        if any(word in message for word in ['protein', 'calories', 'calorie', 'carbs', 'carb', 'fat']):
            nutrient = self.extract_nutrient(message)
            timeframe = self.extract_timeframe(message)
            return 'nutrient_query', {'nutrient': nutrient, 'timeframe': timeframe}
        
        # Comparison queries
        if any(word in message for word in ['compare', 'vs', 'versus', 'difference']):
            return 'comparison', {}
        
        # Pattern analysis
        if any(word in message for word in ['pattern', 'usually', 'tend to', 'eating habits']):
            return 'pattern_analysis', {}
        
        # Recommendations
        if any(word in message for word in ['what should', 'recommend', 'suggest', 'should i eat']):
            return 'recommendation', {}
        
        # Help/General
        if any(word in message for word in ['help', 'what can', 'how do', 'commands']):
            return 'help', {}
        
        # Default
        return 'general', {}
    
    def extract_nutrient(self, message):
        """Extract which nutrient user is asking about"""
        if 'protein' in message:
            return 'protein'
        elif 'calorie' in message:
            return 'calories'
        elif 'carb' in message:
            return 'carbs'
        elif 'fat' in message:
            return 'fat'
        elif 'fiber' in message:
            return 'fiber'
        elif 'sugar' in message:
            return 'sugar'
        elif 'sodium' in message:
            return 'sodium'
        return 'calories'
    
    def extract_timeframe(self, message):
        """Extract time period from message"""
        if 'today' in message:
            return 'today'
        elif 'yesterday' in message:
            return 'yesterday'
        elif 'week' in message:
            return 'this_week'
        elif 'month' in message:
            return 'this_month'
        return 'today'
    
    def handle_question(self, user_id, phone_number, message_text):
        """
        Main entry point for handling questions
        
        Args:
            user_id: User ID
            phone_number: Phone number for context storage
            message_text: User's question
        
        Returns:
            Response message string
        """
        # Check if this is a follow-up question
        context = conversation_context.get(phone_number, {})
        
        if self.is_followup_question(message_text) and context:
            response = self.handle_followup(user_id, message_text, context)
        else:
            # Classify and route
            question_type, params = self.classify_question(message_text)
            response = self.route_to_handler(user_id, question_type, params, message_text)
            
            # Save context
            conversation_context[phone_number] = {
                'last_question_type': question_type,
                'last_params': params,
                'timestamp': datetime.now()
            }
        
        return response
    
    def is_followup_question(self, message):
        """Detect follow-up questions"""
        followup_phrases = ['what about', 'how about', 'what if']
        message_lower = message.lower()
        
        # Check for followup phrases
        if any(phrase in message_lower for phrase in followup_phrases):
            return True
        
        # Check for standalone followup words (with word boundaries)
        words = message_lower.split()
        standalone_words = ['and', 'also', 'or']
        if any(word in standalone_words for word in words) and len(words) < 6:
            return True
        
        return False
    
    def handle_followup(self, user_id, message, context):
        """Handle context-aware follow-ups"""
        if context['last_question_type'] == 'daily_summary':
            # User might be asking about specific nutrients
            message_lower = message.lower()
            if 'protein' in message_lower:
                return self.handle_nutrient_query(user_id, 'protein', 'today')
            elif 'carb' in message_lower:
                return self.handle_nutrient_query(user_id, 'carbs', 'today')
            elif 'fat' in message_lower:
                return self.handle_nutrient_query(user_id, 'fat', 'today')
        
        # Default: treat as new question
        return "I didn't quite understand. Can you rephrase?"
    
    def route_to_handler(self, user_id, question_type, params, message_text=''):
        """Route to appropriate question handler"""
        
        try:
            if question_type == 'goal_setting':
                return self.handle_goal_setting(user_id, message_text)
            
            elif question_type == 'daily_summary':
                return self.handle_daily_summary(user_id, params.get('date', 'today'))
            
            elif question_type == 'nutrient_query':
                return self.handle_nutrient_query(
                    user_id,
                    params['nutrient'],
                    params['timeframe']
                )
            
            elif question_type == 'goal_progress':
                return self.handle_goal_progress(user_id)
            
            elif question_type == 'comparison':
                return self.handle_comparison(user_id)
            
            elif question_type == 'pattern_analysis':
                return self.handle_pattern_analysis(user_id)
            
            elif question_type == 'recommendation':
                return self.handle_recommendation(user_id)
            
            elif question_type == 'history_query':
                return self.handle_history_query(user_id, params['timeframe'])
            
            elif question_type == 'help':
                return self.handle_help()
            
            else:
                return self.handle_help()
        
        except Exception as e:
            logger.error(f"Error handling question: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def handle_goal_setting(self, user_id, message_text):
        """Parse and set goals from natural language"""
        
        # Extract number from message
        numbers = re.findall(r'\d+', message_text)
        
        if not numbers:
            return "Please specify a number (e.g., 'My goal is 2000 calories' or 'My protein goal is 150g')"
        
        target = int(numbers[0])
        
        # Determine goal type
        if 'protein' in message_text.lower():
            goal_type = 'protein_target'
            unit = 'g'
        else:
            goal_type = 'calorie_target'
            unit = 'calories'
        
        # Deactivate old goals
        old_goals = Goal.query.filter_by(
            user_id=user_id,
            goal_type=goal_type,
            is_active=True
        ).all()
        
        for g in old_goals:
            g.is_active = False
        
        # Create new goal
        goal = Goal(
            user_id=user_id,
            goal_type=goal_type,
            target_value=target,
            start_date=date.today(),
            is_active=True
        )
        db.session.add(goal)
        db.session.commit()
        
        return f"Goal set! Targeting {target} {unit} per day."
    
    def handle_daily_summary(self, user_id, date_str='today'):
        """Get today's nutrition totals"""
        
        if date_str == 'today':
            target_date = date.today()
        elif date_str == 'yesterday':
            target_date = date.today() - timedelta(days=1)
        else:
            target_date = date.today()
        
        summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=target_date
        ).first()
        
        if not summary or summary.meal_count == 0:
            return f"You haven't logged any meals yet {'today' if date_str == 'today' else date_str}."
        
        # Get active calorie goal
        goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type='calorie_target',
            is_active=True
        ).first()
        
        response = f"""{'Today' if date_str == 'today' else 'Yesterday'}'s Summary:

{summary.total_calories:.0f} calories
{summary.total_protein:.0f}g protein
{summary.total_carbs:.0f}g carbs
{summary.total_fat:.0f}g fat

Meals logged: {summary.meal_count}"""
        
        if goal:
            remaining = goal.target_value - summary.total_calories
            percentage = (summary.total_calories / goal.target_value) * 100
            
            response += f"\n\nGoal: {goal.target_value:.0f} calories"
            response += f"\nProgress: {percentage:.0f}%"
            
            if remaining > 0:
                response += f"\n{remaining:.0f} calories remaining"
            else:
                response += f"\n{abs(remaining):.0f} calories over goal"
        
        return response
    
    def handle_nutrient_query(self, user_id, nutrient, timeframe):
        """Answer specific nutrient questions"""
        
        if timeframe == 'today':
            summary = DailySummary.query.filter_by(
                user_id=user_id,
                date=date.today()
            ).first()
            
            if not summary:
                return f"You haven't logged any meals yet today."
            
            value = getattr(summary, f'total_{nutrient}', 0)
            unit = 'g' if nutrient != 'sodium' else 'mg'
            
            return f"You've had {value:.0f}{unit} {nutrient} today."
        
        elif timeframe == 'this_week':
            start_date = date.today() - timedelta(days=7)
            summaries = DailySummary.query.filter(
                DailySummary.user_id == user_id,
                DailySummary.date >= start_date
            ).all()
            
            if not summaries:
                return "No meal data for the past week."
            
            total = sum(getattr(s, f'total_{nutrient}', 0) for s in summaries)
            avg = total / 7
            unit = 'g' if nutrient != 'sodium' else 'mg'
            
            return f"This week: {total:.0f}{unit} {nutrient} total, {avg:.0f}{unit} per day average."
        
        return "I can check today or this week."
    
    def handle_goal_progress(self, user_id):
        """Show goal progress"""
        
        # Get calorie goal first (most common query)
        goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type='calorie_target',
            is_active=True
        ).first()
        
        # If no calorie goal, check for protein goal
        if not goal:
            goal = Goal.query.filter_by(
                user_id=user_id,
                goal_type='protein_target',
                is_active=True
            ).first()
        
        if not goal:
            return "You haven't set a goal yet. Send me 'My goal is 2000 calories' to get started!"
        
        summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today()
        ).first()
        
        if not summary:
            goal_type_clean = goal.goal_type.replace('_target', '').replace('calorie', 'calories')
            return f"No meals logged today. Your goal is {goal.target_value:.0f} {goal_type_clean}."
        
        if goal.goal_type in ['calorie_target', 'calories']:
            current = summary.total_calories
            unit = 'calories'
        elif goal.goal_type in ['protein_target', 'protein']:
            current = summary.total_protein
            unit = 'g protein'
        else:
            current = 0
            unit = ''
        
        percentage = (current / goal.target_value * 100) if goal.target_value > 0 else 0
        remaining = goal.target_value - current
        
        response = f"""Goal Progress:

Target: {goal.target_value:.0f} {unit}
Current: {current:.0f} {unit}
Progress: {percentage:.0f}%"""
        
        if remaining > 0:
            response += f"\n\n{remaining:.0f} {unit} remaining"
            if percentage < 50:
                response += "\nKeep going!"
            elif percentage < 90:
                response += "\nGreat progress!"
        else:
            response += f"\n\n{abs(remaining):.0f} {unit} over goal"
        
        return response
    
    def handle_comparison(self, user_id):
        """Compare today vs yesterday"""
        
        today_summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today()
        ).first()
        
        yesterday_summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today() - timedelta(days=1)
        ).first()
        
        if not today_summary:
            return "You haven't logged any meals today yet."
        
        if not yesterday_summary:
            return "No data from yesterday to compare."
        
        cal_diff = today_summary.total_calories - yesterday_summary.total_calories
        protein_diff = today_summary.total_protein - yesterday_summary.total_protein
        
        response = f"""Today vs Yesterday:

Calories: {today_summary.total_calories:.0f} ({cal_diff:+.0f})
Protein: {today_summary.total_protein:.0f}g ({protein_diff:+.0f}g)
Carbs: {today_summary.total_carbs:.0f}g
Fat: {today_summary.total_fat:.0f}g"""
        
        if abs(cal_diff) > 200:
            if cal_diff > 0:
                response += f"\n\nYou're eating {abs(cal_diff):.0f} more calories today."
            else:
                response += f"\n\nYou're eating {abs(cal_diff):.0f} fewer calories today."
        
        return response
    
    def handle_pattern_analysis(self, user_id):
        """Analyze eating patterns"""
        
        # Get last 14 days
        start_date = date.today() - timedelta(days=14)
        summaries = DailySummary.query.filter(
            DailySummary.user_id == user_id,
            DailySummary.date >= start_date
        ).all()
        
        if len(summaries) < 5:
            return "Not enough data yet. Log meals for at least 5 days to see patterns."
        
        # Separate weekday vs weekend
        weekday_cals = []
        weekend_cals = []
        
        for summary in summaries:
            if summary.date.weekday() < 5:  # Monday = 0, Friday = 4
                weekday_cals.append(summary.total_calories)
            else:
                weekend_cals.append(summary.total_calories)
        
        weekday_avg = sum(weekday_cals) / len(weekday_cals) if weekday_cals else 0
        weekend_avg = sum(weekend_cals) / len(weekend_cals) if weekend_cals else 0
        
        response = f"""Pattern Analysis (Last 2 weeks):

Weekday average: {weekday_avg:.0f} cal/day
Weekend average: {weekend_avg:.0f} cal/day"""
        
        if weekday_avg > 0 and weekend_avg > 0:
            diff_pct = ((weekend_avg - weekday_avg) / weekday_avg * 100)
            
            if abs(diff_pct) > 20:
                if diff_pct > 0:
                    response += f"\n\nYou eat {diff_pct:.0f}% more on weekends!"
                else:
                    response += f"\n\nYou eat {abs(diff_pct):.0f}% less on weekends."
        
        # Check breakfast frequency
        meals = Meal.query.filter(
            Meal.user_id == user_id,
            Meal.timestamp >= datetime.now() - timedelta(days=14)
        ).all()
        
        breakfast_count = sum(1 for m in meals if m.meal_type == 'breakfast')
        
        if breakfast_count < 10:
            response += f"\n\nYou're skipping breakfast often ({breakfast_count} out of 14 days)."
        
        return response
    
    def handle_recommendation(self, user_id):
        """Provide personalized meal recommendations"""
        
        today = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today()
        ).first()
        
        goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type='calorie_target',
            is_active=True
        ).first()
        
        if not goal:
            return "Set a calorie goal first! Send me 'My goal is 2000 calories'"
        
        if not today:
            return f"""You have your full {goal.target_value:.0f} calorie budget today!

Start with a balanced breakfast to fuel your day."""
        
        remaining_cal = goal.target_value - today.total_calories
        protein_goal = 100  # Assume 100g protein goal
        remaining_protein = protein_goal - today.total_protein
        
        if remaining_cal < 0:
            return f"""You're {abs(remaining_cal):.0f} calories over your goal today.

Consider:
Light walk or exercise
Smaller portions for remaining meals
More vegetables, low calorie and filling"""
        
        elif remaining_cal < 300:
            return f"""You have {remaining_cal:.0f} calories left today.

Light options:
Greek yogurt with berries, 150 calories, 15 grams protein
Small salad with grilled chicken, 250 calories, 25 grams protein
Protein shake, 200 calories, 20 grams protein"""
        
        elif remaining_cal < 600:
            return f"""You have {remaining_cal:.0f} calories left today.

Balanced meals:
Grilled salmon with quinoa, 500 calories, 35 grams protein
Chicken breast with sweet potato, 450 calories, 40 grams protein
Turkey wrap with veggies, 400 calories, 30 grams protein"""
        
        else:
            protein_msg = f"\nAim for {remaining_protein:.0f} grams more protein" if remaining_protein > 20 else ""
            return f"""You have {remaining_cal:.0f} calories left today.

You have plenty of room! Consider:
Full dinner with protein, carbs, and veggies{protein_msg}
Stay hydrated
Don't skip meals"""
    
    def handle_history_query(self, user_id, timeframe):
        """Show meal history"""
        
        if timeframe == 'today':
            target_date = date.today()
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
        elif timeframe == 'yesterday':
            target_date = date.today() - timedelta(days=1)
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
        elif timeframe == 'this_week':
            target_date = date.today() - timedelta(days=7)
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.now()
        else:
            target_date = date.today()
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
        
        meals = Meal.query.filter(
            Meal.user_id == user_id,
            Meal.timestamp >= start_datetime,
            Meal.timestamp <= end_datetime,
            Meal.processing_status == 'completed'
        ).order_by(Meal.timestamp).all()
        
        if not meals:
            return f"No meals logged for {timeframe}."
        
        response = f"Meals from {timeframe}:\n\n"
        
        for meal in meals[:5]:  # Limit to 5 meals
            meal_time = meal.timestamp.strftime('%I:%M %p')
            foods = FoodItem.query.filter_by(meal_id=meal.id).all()
            total_cal = sum(f.calories for f in foods)
            
            response += f"{meal.meal_type.title() if meal.meal_type else 'Meal'} at {meal_time}\n"
            response += f"{total_cal:.0f} calories\n"
            
            if foods:
                food_names = [f.name for f in foods[:3]]
                response += f"{', '.join(food_names)}\n"
            
            response += "\n"
        
        return response.strip()
    
    def handle_help(self):
        """Show help message"""
        return """Hey I'm GlassBite! Here's what I can do:

MEAL TRACKING
Send food photos - I'll log everything automatically

DAILY CHECK-INS
"How am I doing today?" - Today's summary 
"What's my protein intake?" - Specific nutrients
"Am I meeting my goal?" - Goal progress

COMPARE & ANALYZE
"Compare today vs yesterday" - Daily comparison
"Show me patterns" - Week trends

HISTORY
"What did I eat yesterday?" - Past meals

PLANNING
"What should I eat next?" - Smart recommendations

GOALS
"My goal is 2000 calories" - Set calorie target
"My protein goal is 150g" - Set protein target

Just talk naturally! I understand questions in many ways."""


# Singleton instance
chatbot_service = ChatbotService()

def handle_chatbot_question(user_id, phone_number, message_text):
    """Helper function for handling questions"""
    return chatbot_service.handle_question(user_id, phone_number, message_text)
