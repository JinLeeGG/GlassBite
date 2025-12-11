-- GlassBite Database Schema
-- PostgreSQL implementation of 5-table design

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS food_nutrients CASCADE;
DROP TABLE IF EXISTS food_items CASCADE;
DROP TABLE IF EXISTS meals CASCADE;
DROP TABLE IF EXISTS daily_summaries CASCADE;
DROP TABLE IF EXISTS goals CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(50) UNIQUE NOT NULL,
    dietary_restrictions TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_meal_id INTEGER
);

-- 2. Meals Table
CREATE TABLE meals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_type VARCHAR(20),
    timestamp TIMESTAMP DEFAULT NOW(),
    image_url VARCHAR(500),
    voice_note_text TEXT,
    processing_status VARCHAR(20) DEFAULT 'pending'
);

-- 3. Food Items Table
CREATE TABLE food_items (
    id SERIAL PRIMARY KEY,
    meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    portion_size_grams FLOAT,
    confidence_score FLOAT
);

-- 3b. Food Nutrients Table (Detailed nutrition data for each food item)
CREATE TABLE food_nutrients (
    id SERIAL PRIMARY KEY,
    food_item_id INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE UNIQUE,
    
    -- Tier 1: Essential Macronutrients (10 nutrients)
    calories FLOAT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT,
    fiber_g FLOAT,
    sugar_g FLOAT,
    sodium_mg FLOAT,
    potassium_mg FLOAT,
    calcium_mg FLOAT,
    iron_mg FLOAT,
    
    -- Tier 2: Important Micronutrients (8 nutrients)
    vitamin_c_mg FLOAT,
    vitamin_d_ug FLOAT,
    vitamin_a_ug FLOAT,
    vitamin_b12_ug FLOAT,
    magnesium_mg FLOAT,
    zinc_mg FLOAT,
    phosphorus_mg FLOAT,
    cholesterol_mg FLOAT,
    
    -- Tier 3: Supplementary Nutrients (7 nutrients)
    saturated_fat_g FLOAT,
    monounsaturated_fat_g FLOAT,
    polyunsaturated_fat_g FLOAT,
    folate_ug FLOAT,
    vitamin_b6_mg FLOAT,
    choline_mg FLOAT,
    selenium_ug FLOAT
);

-- 4. Daily Summaries Table
CREATE TABLE daily_summaries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_calories FLOAT DEFAULT 0,
    total_protein FLOAT DEFAULT 0,
    total_carbs FLOAT DEFAULT 0,
    total_fat FLOAT DEFAULT 0,
    total_fiber FLOAT DEFAULT 0,
    total_sugar FLOAT DEFAULT 0,
    total_sodium FLOAT DEFAULT 0,
    meal_count INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);

-- 5. Goals Table
-- Supports: calorie_target, protein_target, carb_target
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_type VARCHAR(50),
    target_value FLOAT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Add foreign key constraint for last_meal_id (after meals table exists)
ALTER TABLE users ADD CONSTRAINT fk_users_last_meal 
    FOREIGN KEY (last_meal_id) REFERENCES meals(id) ON DELETE SET NULL;

-- Create Indexes for Performance
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_meals_user_timestamp ON meals(user_id, timestamp);
CREATE INDEX idx_meals_user_date ON meals(user_id, CAST(timestamp AS DATE));
CREATE INDEX idx_food_items_meal ON food_items(meal_id);
CREATE INDEX idx_food_nutrients_food_item ON food_nutrients(food_item_id);
CREATE INDEX idx_daily_summaries_user_date ON daily_summaries(user_id, date);
CREATE INDEX idx_goals_user_active ON goals(user_id, is_active);

-- Insert Sample Data for Testing
INSERT INTO users (phone_number) 
VALUES ('whatsapp:+1234567890');

-- Insert sample goal
INSERT INTO goals (user_id, goal_type, target_value, is_active)
VALUES (1, 'calorie_target', 2000, TRUE);

-- Verify tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
