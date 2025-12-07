-- GlassBite Database Schema
-- PostgreSQL implementation of 5-table design

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS food_items CASCADE;
DROP TABLE IF EXISTS meals CASCADE;
DROP TABLE IF EXISTS daily_summaries CASCADE;
DROP TABLE IF EXISTS goals CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    height_cm FLOAT,
    weight_kg FLOAT,
    age INTEGER,
    dietary_restrictions TEXT,
    allergies TEXT,
    created_at TIMESTAMP DEFAULT NOW()
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
    calories FLOAT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT,
    fiber_g FLOAT,
    sugar_g FLOAT,
    sodium_mg FLOAT,
    confidence_score FLOAT
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
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_type VARCHAR(50),
    target_value FLOAT NOT NULL,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create Indexes for Performance
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_meals_user_timestamp ON meals(user_id, timestamp);
CREATE INDEX idx_meals_user_date ON meals(user_id, CAST(timestamp AS DATE));
CREATE INDEX idx_food_items_meal ON food_items(meal_id);
CREATE INDEX idx_daily_summaries_user_date ON daily_summaries(user_id, date);
CREATE INDEX idx_goals_user_active ON goals(user_id, is_active);

-- Insert Sample Data for Testing
INSERT INTO users (phone_number, name, height_cm, weight_kg, age) 
VALUES ('whatsapp:+1234567890', 'Test User', 175.0, 70.0, 25);

-- Insert sample goal
INSERT INTO goals (user_id, goal_type, target_value, start_date, is_active)
VALUES (1, 'calorie_target', 2000, CURRENT_DATE, TRUE);

-- Verify tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
