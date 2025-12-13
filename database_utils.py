"""
Database utility functions and helper queries
"""

from models import db, User, Meal, FoodItem, FoodNutrient, DailySummary, Goal
from datetime import datetime, timedelta, date
from sqlalchemy import func

def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    
    total_meals = Meal.query.filter_by(
        user_id=user_id,
        processing_status='completed'
    ).count()
    
    total_foods = db.session.query(func.count(FoodItem.id)).join(
        Meal
    ).filter(Meal.user_id == user_id).scalar()
    
    # Get 30-day summary
    thirty_days_ago = date.today() - timedelta(days=30)
    summaries = DailySummary.query.filter(
        DailySummary.user_id == user_id,
        DailySummary.date >= thirty_days_ago
    ).all()
    
    if summaries:
        avg_calories = sum(s.total_calories for s in summaries) / len(summaries)
        avg_protein = sum(s.total_protein for s in summaries) / len(summaries)
    else:
        avg_calories = 0
        avg_protein = 0
    
    # Most logged foods
    top_foods = db.session.query(
        FoodItem.name,
        func.count(FoodItem.id).label('count')
    ).join(Meal).filter(
        Meal.user_id == user_id
    ).group_by(FoodItem.name).order_by(
        func.count(FoodItem.id).desc()
    ).limit(5).all()
    
    return {
        'total_meals': total_meals,
        'total_foods': total_foods,
        'avg_daily_calories': avg_calories,
        'avg_daily_protein': avg_protein,
        'top_foods': [{'name': f[0], 'count': f[1]} for f in top_foods]
    }


def get_leaderboard():
    """Get top users by meal count"""
    
    top_users = db.session.query(
        User.phone_number,
        func.count(Meal.id).label('meal_count')
    ).join(Meal).group_by(
        User.id, User.phone_number
    ).order_by(
        func.count(Meal.id).desc()
    ).limit(10).all()
    
    return [{'phone': u[0], 'meals': u[1]} for u in top_users]


def get_popular_foods(limit=20):
    """Get most frequently logged foods"""
    
    popular = db.session.query(
        FoodItem.name,
        func.count(FoodItem.id).label('count'),
        func.avg(FoodItem.portion_size_grams).label('avg_portion'),
        func.avg(FoodNutrient.calories).label('avg_calories')
    ).join(
        FoodNutrient, FoodItem.id == FoodNutrient.food_item_id, isouter=True
    ).group_by(
        FoodItem.name
    ).order_by(
        func.count(FoodItem.id).desc()
    ).limit(limit).all()
    
    return [{
        'name': f[0],
        'count': f[1],
        'avg_portion': f[2],
        'avg_calories': f[3]
    } for f in popular]


def cleanup_old_data(days=90):
    """Archive or delete data older than specified days"""
    
    cutoff_date = date.today() - timedelta(days=days)
    
    # Delete old meals and their food items (cascade)
    old_meals = Meal.query.filter(
        Meal.timestamp < datetime.combine(cutoff_date, datetime.min.time())
    ).all()
    
    count = len(old_meals)
    
    for meal in old_meals:
        db.session.delete(meal)
    
    # Delete old daily summaries
    old_summaries = DailySummary.query.filter(
        DailySummary.date < cutoff_date
    ).all()
    
    for summary in old_summaries:
        db.session.delete(summary)
    
    db.session.commit()
    
    return {
        'meals_deleted': count,
        'summaries_deleted': len(old_summaries)
    }


def export_user_data(user_id, format='json'):
    """Export all user data for GDPR compliance"""
    
    user = User.query.get(user_id)
    if not user:
        return None
    
    meals = Meal.query.filter_by(user_id=user_id).all()
    summaries = DailySummary.query.filter_by(user_id=user_id).all()
    goals = Goal.query.filter_by(user_id=user_id).all()
    
    data = {
        'user': {
            'phone_number': user.phone_number,
            'created_at': user.created_at.isoformat() if user.created_at else None
        },
        'meals': [],
        'daily_summaries': [],
        'goals': []
    }
    
    for meal in meals:
        foods = FoodItem.query.filter_by(meal_id=meal.id).all()
        data['meals'].append({
            'timestamp': meal.timestamp.isoformat(),
            'meal_type': meal.meal_type,
            'foods': [
                {
                    'name': f.name,
                    'portion_grams': f.portion_size_grams,
                    'calories': f.nutrients.calories if f.nutrients else None,
                    'protein_g': f.nutrients.protein_g if f.nutrients else None
                } for f in foods
            ]
        })
    
    for summary in summaries:
        data['daily_summaries'].append({
            'date': summary.date.isoformat(),
            'total_calories': summary.total_calories,
            'total_protein': summary.total_protein,
            'meal_count': summary.meal_count
        })
    
    for goal in goals:
        data['goals'].append({
            'goal_type': goal.goal_type,
            'target_value': goal.target_value,
            'is_active': goal.is_active
        })
    
    if format == 'json':
        import json
        return json.dumps(data, indent=2)
    else:
        return data


def cancel_pending_meal(user_id):
    """Cancel pending meal (before completion)
    
    Args:
        user_id: User ID
    
    Returns:
        dict with success, message, and meal_info
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Find pending or analyzed meal
    pending_meal = Meal.query.filter_by(
        user_id=user_id
    ).filter(
        Meal.processing_status.in_(['pending', 'analyzed'])
    ).order_by(Meal.timestamp.desc()).first()
    
    if not pending_meal:
        return {
            'success': False,
            'message': 'No pending meal to cancel',
            'meal_info': None
        }
    
    # Get meal info before deletion
    meal_info = {
        'meal_type': pending_meal.meal_type,
        'status': pending_meal.processing_status,
        'timestamp': pending_meal.timestamp
    }
    
    try:
        # Delete meal (cascade will delete food_items and nutrients)
        db.session.delete(pending_meal)
        db.session.commit()
        
        logger.info(f"Cancelled pending meal {pending_meal.id} for user {user_id}")
        
        return {
            'success': True,
            'message': 'Meal logging cancelled',
            'meal_info': meal_info
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling meal: {e}")
        return {
            'success': False,
            'message': 'Error cancelling meal',
            'meal_info': None
        }


def delete_last_meal(user_id):
    """Delete user's last completed meal and update daily summary
    
    Args:
        user_id: User ID
    
    Returns:
        dict with success, message, meal_info, and updated_totals
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Find last completed meal
    last_meal = Meal.query.filter_by(
        user_id=user_id,
        processing_status='completed'
    ).order_by(Meal.timestamp.desc()).first()
    
    if not last_meal:
        return {
            'success': False,
            'message': 'No meals to delete',
            'meal_info': None,
            'updated_totals': None
        }
    
    # Get meal info before deletion
    meal_date = last_meal.timestamp.date()
    food_items = FoodItem.query.filter_by(meal_id=last_meal.id).all()
    
    # Calculate meal totals
    meal_calories = 0
    meal_protein = 0
    meal_carbs = 0
    meal_fat = 0
    food_items_details = []
    
    for item in food_items:
        # Store name and portion size
        food_detail = {
            'name': item.name,
            'portion_grams': item.portion_size_grams
        }
        food_items_details.append(food_detail)
        
        if item.nutrients:
            meal_calories += item.nutrients.calories or 0
            meal_protein += item.nutrients.protein_g or 0
            meal_carbs += item.nutrients.carbs_g or 0
            meal_fat += item.nutrients.fat_g or 0
    
    meal_info = {
        'meal_type': last_meal.meal_type,
        'timestamp': last_meal.timestamp,
        'food_count': len(food_items),
        'food_items': food_items_details,
        'calories': meal_calories,
        'protein': meal_protein,
        'carbs': meal_carbs,
        'fat': meal_fat
    }
    
    try:
        # Update daily summary (subtract meal totals)
        daily_summary = DailySummary.query.filter_by(
            user_id=user_id,
            date=meal_date
        ).first()
        
        if daily_summary:
            daily_summary.total_calories = max(0, daily_summary.total_calories - meal_calories)
            daily_summary.total_protein = max(0, daily_summary.total_protein - meal_protein)
            daily_summary.total_carbs = max(0, daily_summary.total_carbs - meal_carbs)
            daily_summary.total_fat = max(0, daily_summary.total_fat - meal_fat)
            daily_summary.meal_count = max(0, daily_summary.meal_count - 1)
        
        # Update user's last_meal_id if this was the last meal
        user = User.query.get(user_id)
        if user and user.last_meal_id == last_meal.id:
            # Find previous meal
            prev_meal = Meal.query.filter_by(
                user_id=user_id,
                processing_status='completed'
            ).filter(
                Meal.id != last_meal.id
            ).order_by(Meal.timestamp.desc()).first()
            
            user.last_meal_id = prev_meal.id if prev_meal else None
        
        # Delete meal (cascade will delete food_items and nutrients)
        db.session.delete(last_meal)
        db.session.commit()
        
        logger.info(f"Deleted meal {last_meal.id} for user {user_id}")
        
        updated_totals = {
            'calories': daily_summary.total_calories if daily_summary else 0,
            'protein': daily_summary.total_protein if daily_summary else 0,
            'carbs': daily_summary.total_carbs if daily_summary else 0,
            'fat': daily_summary.total_fat if daily_summary else 0
        }
        
        return {
            'success': True,
            'message': 'Meal deleted successfully',
            'meal_info': meal_info,
            'updated_totals': updated_totals
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting meal: {e}", exc_info=True)
        return {
            'success': False,
            'message': 'Error deleting meal',
            'meal_info': None,
            'updated_totals': None
        }


def get_or_create_user(phone_number):
    """Get existing user or create new one
    
    Args:
        phone_number: Phone number (with or without whatsapp: prefix)
    
    Returns:
        User object
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Ensure phone number has whatsapp: prefix
    if not phone_number.startswith('whatsapp:'):
        phone_number = f'whatsapp:{phone_number}'
    
    user = User.query.filter_by(phone_number=phone_number).first()
    
    if not user:
        user = User(phone_number=phone_number)
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created new user: {phone_number}")
    
    return user


if __name__ == '__main__':
    # Example usage
    from app import app
    
    with app.app_context():
        # Get stats for user 1
        stats = get_user_stats(1)
        print("User Stats:", stats)
        
        # Get leaderboard
        leaderboard = get_leaderboard()
        print("\nLeaderboard:", leaderboard)
        
        # Get popular foods
        popular = get_popular_foods(10)
        print("\nPopular Foods:", popular)
