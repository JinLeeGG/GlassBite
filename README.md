# 🥗 GlassBite: AI-Powered Hands-Free Nutrition Tracker

<div align="center">

![GlassBite](https://img.shields.io/badge/Status-Production%20Ready-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Enabled-25D366)
![AI](https://img.shields.io/badge/AI-Gemini-orange)
![Nutrients](https://img.shields.io/badge/Nutrients-25%20Tracked-brightgreen)

**Snap a photo with your smart glasses. AI tracks everything. Zero manual entry.**

A voice-optimized nutrition tracking system designed for Ray-Ban Meta smart glasses, powered by Google Gemini AI and USDA nutrition data.

</div>

---

## 🎯 Overview

Hands-free nutrition tracking for Ray-Ban Meta smart glasses. Take a photo, AI identifies foods and portions, logs nutrition data, and responds via voice.

**Key Differentiators:**
- **Voice-First**: TTS-optimized responses (no emojis/markdown)
- **25 Nutrients**: Complete tracking beyond macros
- **Natural Language**: "How much protein?" instead of menus
- **Two-Step Workflow**: AI detects → You confirm

---

## 🏗️ Architecture

### System Flow

```
📸 Ray-Ban Meta Glasses
    ↓ (Photo via WhatsApp)
📱 Twilio WhatsApp API
    ↓
🔄 Flask Webhook Server
    ↓
🤖 Google Gemini Vision AI
    ├─ Identifies food names
    ├─ Estimates portions (grams)
    └─ Returns structured data
    ↓
🗄️ USDA FoodData Central API
    ├─ Smart matching algorithm (99%+ accuracy)
    ├─ 300K+ food database
    └─ Returns nutrition data
    ↓
💾 PostgreSQL Database
    ├─ Meals & food items
    ├─ Daily summaries
    └─ User goals
    ↓
💬 WhatsApp Response (Voice-Optimized)
```

### Tech Stack

- **Backend**: Python 3.10, Flask, SQLAlchemy, PostgreSQL (5 tables, 25 nutrients)
- **AI**: Google Gemini (`gemini-pro-latest`), USDA FoodData Central (300K+ foods)
- **Integration**: Twilio WhatsApp API, Ngrok
- **Voice**: TTS-optimized (no emojis/markdown, expanded units)

---

## ✨ Key Features

### 1. **AI Food Recognition**

Google Gemini analyzes meal photos and:

- Identifies multiple foods in a single image
- Estimates portion sizes in grams
- Returns confidence scores
- Handles complex multi-food meals
- Detects non-food images (prevents accidental logging)

### 2. **25-Nutrient Comprehensive Tracking**

Three-tier nutrition system captures everything:

**Tier 1: Essential Macronutrients (10 nutrients)**

- Calories, Protein, Carbs, Fat
- Fiber, Sugar, Sodium, Potassium
- Calcium, Iron

**Tier 2: Important Micronutrients (8 nutrients)**

- Vitamins: C, D, A, B12
- Minerals: Magnesium, Zinc, Phosphorus, Cholesterol

**Tier 3: Supplementary Nutrients (7 nutrients)**

- Fat types: Saturated, Monounsaturated, Polyunsaturated
- B-Vitamins: Folate, B6
- Other: Choline, Selenium

All 25 nutrients extracted from USDA FoodData Central and stored in dedicated `food_nutrients` table with 1:1 relationship to food items.

### 3. **Smart USDA Matching**

Custom algorithm achieves 99%+ accuracy (100/100 test foods):
- Excludes processed foods (powder, sauce, canned)
- Prioritizes cooking methods (grilled, steamed, baked)
- Scores: Base 100, exact +30, cooking +15, processed -50

### 4. **Voice-Optimized Responses**

TTS-friendly design for smart glasses:
- No emojis ("check mark" vs silence)
- No progress bars or markdown
- Full words: "grams" not "g", "calories" not "cal"
- Example: "Meal logged successfully. 520 calories, 45 grams protein."

---

### 5. **Natural Language Chatbot**

Supports queries in plain English:

**Daily Tracking**: "How am I doing today?", "What's my protein intake?", "Am I meeting my goal?"

**Analysis**: "Compare today vs yesterday", "Show me patterns"

**History**: "What did I eat yesterday?"

**Recommendations**: "What should I eat next?"

**Goals**: "My goal is 2000 calories", "My protein goal is 150g", "My carb goal is 250g"

**Dietary Restrictions**: "My allergies are dairy, nuts", "Add gluten", "Remove dairy", "Show my restrictions"
- Supports: Dairy, Gluten, Nuts, Shellfish, Fish, Eggs, Soy, Meat, Pork, Alcohol
- Diets: Vegetarian, Vegan, Pescatarian, Halal, Kosher

**Nutrients**: "Nutrition status", "Nutrition week", "Show nutrients" (all 25 tracked)

---

### 6. **Two-Step Confirmation**

1. AI analyzes photo → Shows detected foods
2. User confirms meal type (breakfast/lunch/dinner/snack)
3. System logs with timestamp + voice confirmation

**Benefits**: Accurate timestamps, error correction, clear intent

---

### 7. **Goal Tracking**

Set daily targets for calories, protein, carbs with real-time progress.

---

### 8. **AI Meal Recommendations**

Personalized suggestions based on: remaining nutrients, eating history, meal context, variety.  
**Fallback**: AI → Rule-based → Static defaults

---

### 9. **Dietary Restriction Alerts**

Real-time allergen detection with **meal blocking**:

- Detects 10 allergen categories in ingredients
- Validates against 5 dietary preferences
- **Immediately blocks meals** with violations
- Lists safe vs. unsafe foods
- Prevents accidental logging of restricted items

**Example Flow:**
```
1. User sends photo of cheese pizza
2. AI detects ingredients: cheese, wheat dough
3. System checks user restrictions: dairy, gluten
4. 🚨 ALERT: Contains Dairy (cheese), Gluten (wheat)
5. 🚫 MEAL NOT LOGGED
6. Processing stops - no meal type prompt
```

---

## 🚀 Installation

### Prerequisites

Ensure you have the following before installation:

| Requirement | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Core runtime |
| PostgreSQL | 12+ | Database |
| Twilio Account | - | WhatsApp integration |
| Google AI Studio | - | Gemini API access |
| USDA API Key | - | Nutrition data |

### Account Setup

1. **Twilio** - [Sign up](https://www.twilio.com/try-twilio) for WhatsApp Business API
2. **Google Gemini** - [Get API key](https://ai.google.dev/)
3. **USDA FoodData** - [Request key](https://fdc.nal.usda.gov/api-key-signup.html)

### Step 1: Clone Repository

```bash
git clone https://github.com/JinLeeGG/GlassBite.git
cd GlassBite
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

Create `.env` file:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/glassbite_db
GEMINI_API_KEY=your_key          # ai.google.dev
USDA_API_KEY=your_key             # fdc.nal.usda.gov
TWILIO_ACCOUNT_SID=your_sid       # twilio.com/console
TWILIO_AUTH_TOKEN=your_token      
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
FLASK_SECRET_KEY=your_secret      # Generate: python -c "import secrets; print(secrets.token_hex(32))"
FLASK_ENV=development
```

### Step 5: Initialize Database

```bash
createdb glassbite_db
psql -d glassbite_db -f schema.sql
```

### Step 6: Run Application

```bash
python app.py           # Terminal 1
ngrok http 5000         # Terminal 2
```

### Step 7: Configure Twilio Webhook

1. Copy Ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`)
2. Go to [console.twilio.com](https://console.twilio.com/) → **Messaging** → **WhatsApp Sandbox**
3. Set webhook: `https://your-url.ngrok.io/webhook/whatsapp` (POST)

### Step 8: Test the System

Send a WhatsApp message to your Twilio sandbox number:

```
You: "How am I doing today?"
Bot: "You have not logged any meals yet today. Send a food photo to get started!"
```

✅ **Installation Complete!**

---

**GitHub**: [@JinLeeGG](https://github.com/JinLeeGG) • **MIT License** • Made for hands-free nutrition tracking
