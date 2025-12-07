"""
Database utility functions and helper queries
"""

from models import db, User, Meal, FoodItem, DailySummary, Goal
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
        func.avg(FoodItem.calories).label('avg_calories')
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
            'name': user.name,
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
                    'calories': f.calories,
                    'protein_g': f.protein_g
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
            'start_date': goal.start_date.isoformat() if goal.start_date else None,
            'is_active': goal.is_active
        })
    
    if format == 'json':
        import json
        return json.dumps(data, indent=2)
    else:
        return data


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
