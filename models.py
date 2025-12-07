"""
Database models for GlassBite AI Chatbot
Defines 5 tables: Users, Meals, FoodItems, DailySummaries, Goals
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User profiles and preferences"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100))
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    age = db.Column(db.Integer)
    dietary_restrictions = db.Column(db.Text)
    allergies = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    meals = db.relationship('Meal', back_populates='user', cascade='all, delete-orphan')
    daily_summaries = db.relationship('DailySummary', back_populates='user', cascade='all, delete-orphan')
    goals = db.relationship('Goal', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.phone_number}>'


class Meal(db.Model):
    """Log of meals with photos and voice notes"""
    __tablename__ = 'meals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    meal_type = db.Column(db.String(20))  # breakfast/lunch/dinner/snack
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    image_url = db.Column(db.String(500))
    voice_note_text = db.Column(db.Text)
    processing_status = db.Column(db.String(20), default='pending')  # pending/completed/failed
    
    # Relationships
    user = db.relationship('User', back_populates='meals')
    food_items = db.relationship('FoodItem', back_populates='meal', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Meal {self.id} - {self.meal_type} at {self.timestamp}>'


class FoodItem(db.Model):
    """Individual foods detected in each meal"""
    __tablename__ = 'food_items'
    
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    portion_size_grams = db.Column(db.Float)
    calories = db.Column(db.Float)
    protein_g = db.Column(db.Float)
    carbs_g = db.Column(db.Float)
    fat_g = db.Column(db.Float)
    fiber_g = db.Column(db.Float)
    sugar_g = db.Column(db.Float)
    sodium_mg = db.Column(db.Float)
    confidence_score = db.Column(db.Float)
    
    # Relationships
    meal = db.relationship('Meal', back_populates='food_items')
    
    def __repr__(self):
        return f'<FoodItem {self.name} - {self.portion_size_grams}g>'


class DailySummary(db.Model):
    """Cache daily nutrition totals for fast queries"""
    __tablename__ = 'daily_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    total_calories = db.Column(db.Float, default=0)
    total_protein = db.Column(db.Float, default=0)
    total_carbs = db.Column(db.Float, default=0)
    total_fat = db.Column(db.Float, default=0)
    total_fiber = db.Column(db.Float, default=0)
    total_sugar = db.Column(db.Float, default=0)
    total_sodium = db.Column(db.Float, default=0)
    meal_count = db.Column(db.Integer, default=0)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)
    
    # Relationships
    user = db.relationship('User', back_populates='daily_summaries')
    
    def __repr__(self):
        return f'<DailySummary {self.date} - {self.total_calories} cal>'


class Goal(db.Model):
    """Track user nutrition and weight goals"""
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    goal_type = db.Column(db.String(50))  # calorie_target, protein_target, weight_loss
    target_value = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Relationships
    user = db.relationship('User', back_populates='goals')
    
    def __repr__(self):
        return f'<Goal {self.goal_type} - {self.target_value}>'
