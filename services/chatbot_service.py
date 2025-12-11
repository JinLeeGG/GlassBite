"""
Chatbot Service - Natural language question handling
Classifies questions and routes to appropriate handlers
"""

import re
import logging
from datetime import datetime, timedelta, date
from models import db, User, Meal, FoodItem, DailySummary, Goal
from sqlalchemy import func
from services.recommendation_service import recommendation_engine
from services.allergen_service import allergen_service, parse_user_restrictions

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
        words = set(message.split())
        
        # ===== MEAL DETAILS REQUEST (check FIRST - very specific) =====
        if message.strip() in ['detail', 'details', 'list', 'breakdown', 'full']:
            return 'meal_details', {}
        
        # ===== GOAL SETTING (check FIRST - most specific) =====
        # Strict pattern: explicit goal setting with numbers
        if re.search(r'(my goal is|goal is|set.+goal).+\d+', message):
            return 'goal_setting', {}
        
        # Pattern: "goal" + number + unit (e.g., "goal 2000 calories")
        if re.search(r'\bgoal\b.{0,10}\d+', message):
            if any(word in message for word in ['calorie', 'protein', 'carb', 'fat']):
                return 'goal_setting', {}
        
        # Fuzzy: "I want" + number + (calories/protein)
        if re.search(r'\d+', message):
            if any(phrase in message for phrase in ['i want', 'target', 'aim for', 'trying to']):
                return 'goal_setting', {}
        
        # ===== GOAL PROGRESS (check before daily summary to avoid "how am i doing" conflict) =====
        # Strict patterns
        goal_progress_strict = [
            'what is my goal', "what's my goal", 'whats my goal',
            'my progress', 'goal progress', 'my goal',
            'am i meeting', 'meeting my goal',
            'what is my progress', "what's my progress"
        ]
        if any(phrase in message for phrase in goal_progress_strict):
            return 'goal_progress', {}
        
        # Single word commands
        if message.strip() in ['progress', 'goal', 'goals']:
            return 'goal_progress', {}
        
        # Fuzzy: question words + goal/progress words
        # But skip if it's clearly NOT a question (negative statements, uncertain statements)
        if 'goal' in words or 'progress' in words or 'target' in words:
            # Skip negative/uncertain statements
            if any(neg in message for neg in ["don't think", "not sure", "maybe", "crushing", "??"]):
                pass  # Continue to other checks
            else:
                question_words = {'what', 'show', 'check', 'tell', 'whats'}
                if words & question_words:
                    return 'goal_progress', {}
        
        # Natural variations for goal progress
        if any(phrase in message for phrase in ['on track', 'hit my goal', 'am i over', 'how\'s it going', "what's my status"]):
            return 'goal_progress', {}
        
        # ===== COMPARISON (check BEFORE timeframe queries) =====
        if any(word in message for word in ['compare', 'vs', 'versus', 'difference']):
            return 'comparison', {}
        
        # ===== MEAL HISTORY (check before daily summary) =====
        history_patterns = [
            'what did i eat', 'what did i have', 'what did i had',
            'show me what', 'what have i eaten', 'what i ate',
            'tell me what i ate', 'show me my meals', 'my meals',
            'food log', 'meal log', 'eating log'
        ]
        if any(phrase in message for phrase in history_patterns):
            timeframe = self.extract_timeframe(message)
            return 'history_query', {'timeframe': timeframe}
        
        # Timeframe keywords (yesterday, last week, this week)
        if any(word in message for word in ['yesterday', 'last week', 'last month', 'this week']):
            # But NOT if it's a nutrient query with explicit "intake" keyword
            if 'intake' not in message:
                timeframe = self.extract_timeframe(message)
                return 'history_query', {'timeframe': timeframe}
        
        # ===== DAILY SUMMARY (specific to today) =====
        if 'today' in message:
            # Priority: if has "how am i" but also "today", it's daily_summary
            if any(phrase in message for phrase in ['how am i doing today', "how's today", 'show me today', 'today so far']):
                return 'daily_summary', {'date': 'today'}
            # Other today + summary keywords
            if any(word in message for word in ['total', 'summary']):
                return 'daily_summary', {'date': 'today'}
        
        # Generic "how am i doing" without "today" -> goal_progress
        if 'how am i doing' in message and 'today' not in message:
            return 'goal_progress', {}
        
        # ===== NUTRIENT QUERY (check AFTER goal setting to avoid conflicts) =====
        # Support "cal" as shorthand for "calories"
        nutrient_keywords = ['protein', 'calories', 'calorie', 'cal', 'carbs', 'carb', 'fat']
        if any(word in message for word in nutrient_keywords):
            # Skip if already detected as goal_setting
            if not re.search(r'\d+', message) or 'intake' in message or 'how much' in message or 'how many' in message:
                nutrient = self.extract_nutrient(message)
                timeframe = self.extract_timeframe(message)
                return 'nutrient_query', {'nutrient': nutrient, 'timeframe': timeframe}
        
        # ===== PATTERN ANALYSIS =====
        if any(word in message for word in ['pattern', 'usually', 'tend to', 'eating habits']):
            return 'pattern_analysis', {}
        
        # ===== RECOMMENDATIONS =====
        if any(word in message for word in ['what should', 'recommend', 'suggest', 'should i eat']):
            # Check for specific meal type
            meal_type = None
            if 'breakfast' in message:
                meal_type = 'breakfast'
            elif 'lunch' in message:
                meal_type = 'lunch'
            elif 'dinner' in message:
                meal_type = 'dinner'
            elif 'snack' in message:
                meal_type = 'snack'
            return 'recommendation', {'meal_type': meal_type}
        
        # ===== DIETARY RESTRICTIONS MANAGEMENT =====
        if any(phrase in message for phrase in ['my restrictions', 'my allergies', 'set restrictions', 
                                                'set allergies', 'update restrictions', 'dietary restrictions',
                                                'i am allergic', "i'm allergic", 'i have allergies',
                                                'my restrictions are', 'my allergies are']):
            return 'restrictions_management', {}
        
        if any(phrase in message for phrase in ['what are my restrictions', 'show my restrictions',
                                                'what allergies', 'my dietary', 'show allergies',
                                                'what am i allergic to']):
            return 'view_restrictions', {}
        
        if 'add' in message and any(word in message for word in ['restriction', 'allergy', 'allergen']):
            return 'add_restriction', {}
        
        if 'remove' in message and any(word in message for word in ['restriction', 'allergy', 'allergen']):
            return 'remove_restriction', {}
        
        # ===== HELP =====
        if any(word in message for word in ['help', 'what can', 'how do', 'commands']):
            return 'help', {}
        
        # ===== DEFAULT =====
        return 'general', {}
    
    def extract_nutrient(self, message):
        """Extract which nutrient user is asking about"""
        if 'protein' in message:
            return 'protein'
        elif 'calorie' in message or 'cal' in message:
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
            if question_type == 'meal_details':
                # Get last meal ID from user object
                from models import User
                user = User.query.get(user_id)
                meal_id = user.last_meal_id if user else None
                return self.handle_meal_details(user_id, meal_id)
            
            elif question_type == 'goal_setting':
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
                meal_type = params.get('meal_type')
                return self.handle_recommendation(user_id, meal_type)
            
            elif question_type == 'history_query':
                return self.handle_history_query(user_id, params['timeframe'])
            
            elif question_type == 'restrictions_management':
                return self.handle_restrictions_setup(user_id, message_text)
            
            elif question_type == 'view_restrictions':
                return self.handle_view_restrictions(user_id)
            
            elif question_type == 'add_restriction':
                return self.handle_add_restriction(user_id, message_text)
            
            elif question_type == 'remove_restriction':
                return self.handle_remove_restriction(user_id, message_text)
            
            elif question_type == 'help':
                return self.handle_help()
            
            else:
                return self.handle_help()
        
        except Exception as e:
            logger.error(f"Error handling question: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def handle_meal_details(self, user_id, meal_id=None):
        """Handle request for detailed meal breakdown"""
        from services.meal_processor import meal_processor
        
        # If meal_id provided, use it; otherwise get most recent
        if meal_id:
            recent_meal = Meal.query.filter_by(
                id=meal_id,
                user_id=user_id,
                processing_status='completed'
            ).first()
        else:
            recent_meal = Meal.query.filter_by(
                user_id=user_id,
                processing_status='completed'
            ).order_by(Meal.timestamp.desc()).first()
        
        if not recent_meal:
            return "No recent meals found. Please log a meal first by sending a photo."
        
        # Get detailed messages
        detail_messages = meal_processor.get_meal_details(recent_meal.id, user_id)
        
        if not detail_messages:
            return "Could not retrieve meal details. Please try again."
        
        # Return as list (twilio_service will send multiple messages)
        return detail_messages
    
    def handle_goal_setting(self, user_id, message_text):
        """Parse and set goals from natural language"""
        
        # Extract number from message
        numbers = re.findall(r'\d+', message_text)
        
        if not numbers:
            return "Please specify a number (e.g., 'My goal is 2000 calories', 'My protein goal is 150g', or 'My carb goal is 250g')"
        
        target = int(numbers[0])
        
        # Determine goal type
        if 'protein' in message_text.lower():
            goal_type = 'protein_target'
            unit = 'g protein'
        elif 'carb' in message_text.lower():
            goal_type = 'carb_target'
            unit = 'g carbs'
        else:
            goal_type = 'calorie_target'
            unit = 'calories'
        
        # Deactivate old goals of this type
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
            is_active=True
        )
        db.session.add(goal)
        db.session.commit()
        
        response = f"Goal set! Targeting {target} {unit} per day."
        
        # Show all active goals
        all_goals = Goal.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        if len(all_goals) > 1:
            response += "\n\nYour active goals:"
            for g in all_goals:
                if g.goal_type == 'calorie_target':
                    response += f"\n• {g.target_value:.0f} calories"
                elif g.goal_type == 'protein_target':
                    response += f"\n• {g.target_value:.0f}g protein"
                elif g.goal_type == 'carb_target':
                    response += f"\n• {g.target_value:.0f}g carbs"
        
        return response
    
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
        """Show goal progress for all active goals"""
        
        # Get all three goals
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
        
        if not calorie_goal and not protein_goal and not carb_goal:
            return "You haven't set any goals yet. Send me 'My goal is 2000 calories' to get started!"
        
        summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=date.today()
        ).first()
        
        # If no summary, show goals without progress
        if not summary:
            response_parts = ["No meals logged today."]
            if calorie_goal:
                response_parts.append(f"Calorie goal: {calorie_goal.target_value:.0f} calories")
            if protein_goal:
                response_parts.append(f"Protein goal: {protein_goal.target_value:.0f}g")
            if carb_goal:
                response_parts.append(f"Carb goal: {carb_goal.target_value:.0f}g")
            return "\n".join(response_parts)
        
        response_parts = []
        
        # Show calorie progress if goal exists
        if calorie_goal:
            current_cal = summary.total_calories
            percentage_cal = (current_cal / calorie_goal.target_value * 100) if calorie_goal.target_value > 0 else 0
            remaining_cal = calorie_goal.target_value - current_cal
            
            cal_section = f"""Calorie Goal:
Target: {calorie_goal.target_value:.0f} calories
Current: {current_cal:.0f} calories
Progress: {percentage_cal:.0f}%"""
            
            if remaining_cal > 0:
                cal_section += f"\n{remaining_cal:.0f} calories remaining"
            else:
                cal_section += f"\n{abs(remaining_cal):.0f} calories over goal"
            
            response_parts.append(cal_section)
        
        # Show protein progress if goal exists
        if protein_goal:
            current_protein = summary.total_protein
            percentage_protein = (current_protein / protein_goal.target_value * 100) if protein_goal.target_value > 0 else 0
            remaining_protein = protein_goal.target_value - current_protein
            
            protein_section = f"""Protein Goal:
Target: {protein_goal.target_value:.0f}g
Current: {current_protein:.0f}g
Progress: {percentage_protein:.0f}%"""
            
            if remaining_protein > 0:
                protein_section += f"\n{remaining_protein:.0f}g remaining"
            else:
                protein_section += f"\n{abs(remaining_protein):.0f}g over goal"
            
            response_parts.append(protein_section)
        
        # Show carb progress if goal exists
        if carb_goal:
            current_carbs = summary.total_carbs
            percentage_carbs = (current_carbs / carb_goal.target_value * 100) if carb_goal.target_value > 0 else 0
            remaining_carbs = carb_goal.target_value - current_carbs
            
            carb_section = f"""Carb Goal:
Target: {carb_goal.target_value:.0f}g
Current: {current_carbs:.0f}g
Progress: {percentage_carbs:.0f}%"""
            
            if remaining_carbs > 0:
                carb_section += f"\n{remaining_carbs:.0f}g remaining"
            else:
                carb_section += f"\n{abs(remaining_carbs):.0f}g over goal"
            
            response_parts.append(carb_section)
        
        # Add encouragement based on overall progress
        if calorie_goal or protein_goal or carb_goal:
            avg_percentage = 0
            count = 0
            if calorie_goal and summary and calorie_goal.target_value > 0:
                avg_percentage += (summary.total_calories / calorie_goal.target_value * 100)
                count += 1
            if protein_goal and summary and protein_goal.target_value > 0:
                avg_percentage += (summary.total_protein / protein_goal.target_value * 100)
                count += 1
            if carb_goal and summary and carb_goal.target_value > 0:
                avg_percentage += (summary.total_carbs / carb_goal.target_value * 100)
                count += 1
            
            if count > 0:
                avg_percentage /= count
                if avg_percentage < 50:
                    response_parts.append("\nKeep going!")
                elif avg_percentage < 90:
                    response_parts.append("\nGreat progress!")
                else:
                    response_parts.append("\nAlmost there!")
        
        return "\n\n".join(response_parts)
    
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
    
    def handle_recommendation(self, user_id, meal_type=None):
        """Provide AI-powered personalized meal recommendations"""
        
        # If meal type specified, use it; otherwise determine from time
        if meal_type:
            context = meal_type
        else:
            current_hour = datetime.now().hour
            if 6 <= current_hour < 11:
                context = 'breakfast'
            elif 11 <= current_hour < 15:
                context = 'lunch'
            elif 15 <= current_hour < 18:
                context = 'snack'
            elif 18 <= current_hour < 22:
                context = 'dinner'
            else:
                context = 'general'
        
        # Use AI-powered recommendation engine with database insights
        return recommendation_engine.get_recommendations(user_id, context)
    
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
            total_cal = sum(f.nutrients.calories if f.nutrients else 0 for f in foods)
            
            response += f"{meal.meal_type.title() if meal.meal_type else 'Meal'} at {meal_time}\n"
            response += f"{total_cal:.0f} calories\n"
            
            if foods:
                food_names = [f.name for f in foods[:3]]
                response += f"{', '.join(food_names)}\n"
            
            response += "\n"
        
        return response.strip()
    
    def handle_restrictions_setup(self, user_id, message_text):
        """Set or update dietary restrictions"""
        
        # Extract restrictions from message
        restrictions_part = None
        
        # Try to find the restrictions after keywords
        for keyword in ['restrictions are', 'allergies are', 'allergic to', 'restrictions:', 
                       'allergies:', 'i have', 'i am', "i'm"]:
            if keyword in message_text.lower():
                restrictions_part = message_text.lower().split(keyword)[1].strip()
                break
        
        # Remove common trailing words
        if restrictions_part:
            for trailing in [' allergy', ' allergies', ' restriction', ' restrictions']:
                restrictions_part = restrictions_part.replace(trailing, '')
        
        if not restrictions_part:
            # Just show supported restrictions
            supported = allergen_service.get_supported_restrictions()
            return f"""Please specify your dietary restrictions or allergies.

{supported}

Examples:
• "My allergies are dairy, nuts"
• "Set restrictions: vegan"
• "I'm allergic to shellfish"
• "My restrictions are gluten, dairy, vegetarian"
"""
        
        # Parse and validate
        parsed = parse_user_restrictions(restrictions_part)
        
        if not parsed['allergens'] and not parsed['preferences']:
            supported = allergen_service.get_supported_restrictions()
            return f"""I didn't recognize those restrictions.

{supported}

Please try again with supported restrictions."""
        
        # Update user
        user = User.query.get(user_id)
        user.dietary_restrictions = restrictions_part
        db.session.commit()
        
        logger.info(f"Updated dietary restrictions for user {user_id}: {restrictions_part}")
        
        return f"""✅ Dietary restrictions updated!

Your restrictions: {parsed['display']}

I'll alert you immediately if any meal contains these ingredients.

• View anytime: "Show my restrictions"
• Add more: "Add gluten"
• Remove: "Remove dairy"
"""
    
    def handle_view_restrictions(self, user_id):
        """Show current dietary restrictions"""
        
        user = User.query.get(user_id)
        
        if not user.dietary_restrictions:
            supported = allergen_service.get_supported_restrictions()
            return f"""No dietary restrictions set.

{supported}

Set yours: "My allergies are dairy, nuts"
"""
        
        parsed = parse_user_restrictions(user.dietary_restrictions)
        
        message = f"🚨 Your dietary restrictions:\n\n{parsed['display']}\n\n"
        
        if parsed['allergens']:
            allergen_names = [allergen_service.allergen_database[a]['display_name'] 
                            for a in parsed['allergens']]
            message += f"Allergens: {', '.join(allergen_names)}\n"
        
        if parsed['preferences']:
            pref_names = [allergen_service.dietary_preferences[p]['display_name'] 
                         for p in parsed['preferences']]
            message += f"Dietary preferences: {', '.join(pref_names)}\n"
        
        message += "\nI'll warn you if meals contain these ingredients."
        message += "\n\nUpdate: 'My restrictions are dairy,nuts,vegan'"
        message += "\nAdd: 'Add gluten'"
        message += "\nRemove: 'Remove dairy'"
        
        return message
    
    def handle_add_restriction(self, user_id, message_text):
        """Add new dietary restriction"""
        
        user = User.query.get(user_id)
        
        # Extract restriction to add
        restriction_to_add = None
        for keyword in ['add ', 'add restriction ', 'add allergy ', 'add allergen ']:
            if keyword in message_text.lower():
                restriction_to_add = message_text.lower().split(keyword)[1].strip()
                # Remove trailing words
                for trailing in [' restriction', ' allergy', ' allergen']:
                    restriction_to_add = restriction_to_add.replace(trailing, '')
                break
        
        if not restriction_to_add:
            return """Please specify what to add.

Examples:
• "Add dairy"
• "Add vegan"
• "Add gluten allergy"
"""
        
        # Get current restrictions
        current = user.dietary_restrictions or ''
        current_list = [r.strip() for r in current.split(',') if r.strip()]
        
        # Add new restriction if not already present
        if restriction_to_add not in current_list:
            current_list.append(restriction_to_add)
        else:
            return f"'{restriction_to_add}' is already in your restrictions."
        
        new_restrictions = ','.join(current_list)
        parsed = parse_user_restrictions(new_restrictions)
        
        if not parsed['allergens'] and not parsed['preferences']:
            supported = allergen_service.get_supported_restrictions()
            return f"""'{restriction_to_add}' is not a recognized restriction.

{supported}

Try adding a supported restriction."""
        
        user.dietary_restrictions = new_restrictions
        db.session.commit()
        
        logger.info(f"Added restriction '{restriction_to_add}' for user {user_id}")
        
        return f"""✅ Added: {restriction_to_add}

Current restrictions: {parsed['display']}

I'll now warn you about {restriction_to_add} in your meals."""
    
    def handle_remove_restriction(self, user_id, message_text):
        """Remove dietary restriction"""
        
        user = User.query.get(user_id)
        
        if not user.dietary_restrictions:
            return "You have no dietary restrictions set."
        
        # Extract restriction to remove
        restriction_to_remove = None
        for keyword in ['remove ', 'remove restriction ', 'remove allergy ', 'remove allergen ']:
            if keyword in message_text.lower():
                restriction_to_remove = message_text.lower().split(keyword)[1].strip()
                # Remove trailing words
                for trailing in [' restriction', ' allergy', ' allergen']:
                    restriction_to_remove = restriction_to_remove.replace(trailing, '')
                break
        
        if not restriction_to_remove:
            return """Please specify what to remove.

Examples:
• "Remove dairy"
• "Remove vegan"
"""
        
        # Get current restrictions
        current_list = [r.strip() for r in user.dietary_restrictions.split(',') if r.strip()]
        
        # Remove restriction
        if restriction_to_remove in current_list:
            current_list.remove(restriction_to_remove)
        else:
            return f"'{restriction_to_remove}' is not in your restrictions.\n\nCurrent: {user.dietary_restrictions}"
        
        new_restrictions = ','.join(current_list)
        user.dietary_restrictions = new_restrictions
        db.session.commit()
        
        logger.info(f"Removed restriction '{restriction_to_remove}' for user {user_id}")
        
        if new_restrictions:
            parsed = parse_user_restrictions(new_restrictions)
            return f"""✅ Removed: {restriction_to_remove}

Current restrictions: {parsed['display']}"""
        else:
            return f"✅ Removed: {restriction_to_remove}\n\nAll restrictions cleared. You have no dietary restrictions set."
    
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

🚨 DIETARY RESTRICTIONS
"My allergies are dairy, nuts" - Set allergies
"I'm allergic to shellfish" - Set restrictions
"Show my restrictions" - View current
"Add gluten" - Add restriction
"Remove dairy" - Remove restriction

Just talk naturally! I understand questions in many ways."""


# Singleton instance
chatbot_service = ChatbotService()

def handle_chatbot_question(user_id, phone_number, message_text):
    """Helper function for handling questions"""
    return chatbot_service.handle_question(user_id, phone_number, message_text)
