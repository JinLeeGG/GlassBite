"""
Database models for GlassBite AI Chatbot
Final optimized 5-table design
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User profiles"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dietary_restrictions = db.Column(db.Text)
    last_meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=True)
    
    # Relationships
    meals = db.relationship('Meal', back_populates='user', cascade='all, delete-orphan', foreign_keys='Meal.user_id')
    last_meal = db.relationship('Meal', foreign_keys=[last_meal_id], post_update=True)
    daily_summaries = db.relationship('DailySummary', back_populates='user', cascade='all, delete-orphan')
    goals = db.relationship('Goal', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.phone_number}>'


class Meal(db.Model):
    """Meal log with photos and voice notes"""
    __tablename__ = 'meals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    meal_type = db.Column(db.String(20))  # breakfast/lunch/dinner/snack
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    image_url = db.Column(db.String(500))
    voice_note_text = db.Column(db.Text)
    processing_status = db.Column(db.String(20), default='pending')  # pending/analyzed/completed/failed
    
    # Relationships
    user = db.relationship('User', back_populates='meals', foreign_keys=[user_id])
    food_items = db.relationship('FoodItem', back_populates='meal', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Meal {self.id} - {self.meal_type} at {self.timestamp}>'


class FoodItem(db.Model):
    """Individual foods with flexible nutrition storage"""
    __tablename__ = 'food_items'
    
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    portion_size_grams = db.Column(db.Float)
    confidence_score = db.Column(db.Float)
    
    # Relationships
    meal = db.relationship('Meal', back_populates='food_items')
    nutrients = db.relationship('FoodNutrient', back_populates='food_item', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<FoodItem {self.name} - {self.portion_size_grams}g>'


class FoodNutrient(db.Model):
    """Detailed nutrition data for food items (25 nutrients)"""
    __tablename__ = 'food_nutrients'
    
    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Tier 1: Essential Macronutrients (10 nutrients)
    calories = db.Column(db.Float)
    protein_g = db.Column(db.Float)
    carbs_g = db.Column(db.Float)
    fat_g = db.Column(db.Float)
    fiber_g = db.Column(db.Float)
    sugar_g = db.Column(db.Float)
    sodium_mg = db.Column(db.Float)
    potassium_mg = db.Column(db.Float)
    calcium_mg = db.Column(db.Float)
    iron_mg = db.Column(db.Float)
    
    # Tier 2: Important Micronutrients (8 nutrients)
    vitamin_c_mg = db.Column(db.Float)
    vitamin_d_ug = db.Column(db.Float)
    vitamin_a_ug = db.Column(db.Float)
    vitamin_b12_ug = db.Column(db.Float)
    magnesium_mg = db.Column(db.Float)
    zinc_mg = db.Column(db.Float)
    phosphorus_mg = db.Column(db.Float)
    cholesterol_mg = db.Column(db.Float)
    
    # Tier 3: Supplementary Nutrients (7 nutrients)
    saturated_fat_g = db.Column(db.Float)
    monounsaturated_fat_g = db.Column(db.Float)
    polyunsaturated_fat_g = db.Column(db.Float)
    folate_ug = db.Column(db.Float)
    vitamin_b6_mg = db.Column(db.Float)
    choline_mg = db.Column(db.Float)
    selenium_ug = db.Column(db.Float)
    
    # Relationships
    food_item = db.relationship('FoodItem', back_populates='nutrients')
    
    def __repr__(self):
        return f'<FoodNutrient for FoodItem {self.food_item_id}>'


class DailySummary(db.Model):
    """Daily nutrition totals"""
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
    """User nutrition goals"""
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    goal_type = db.Column(db.String(50))  # calorie_target, protein_target, carb_target
    target_value = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Relationships
    user = db.relationship('User', back_populates='goals')
    
    def __repr__(self):
        return f'<Goal {self.goal_type} - {self.target_value}>'
