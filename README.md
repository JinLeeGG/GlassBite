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

## 🎯 What is GlassBite?

GlassBite makes nutrition tracking completely hands-free. Take a photo of your meal with Ray-Ban Meta smart glasses, send it via WhatsApp, and AI automatically:

- Identifies all foods in the image
- Estimates portion sizes
- Looks up accurate nutrition data
- Logs everything to your profile
- Responds with voice-friendly audio through your glasses

No typing. No menus. No apps to open. Just take a photo and listen.

---

## 🏗️ System Architecture

### Data Flow

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

**Backend**

- Python 3.10 + Flask
- SQLAlchemy ORM
- PostgreSQL database (5 tables, 25-nutrient schema)

**AI & Data**

- Google Gemini API (`gemini-pro-latest`)
- USDA FoodData Central API (300K+ foods)
- Custom smart food matching algorithm
- 25-nutrient tracking system (3 tiers)

**Integrations**

- Twilio WhatsApp Business API
- Ngrok for local development

**Voice Optimization**

- Zero emojis (TTS-friendly)
- No progress bars or markdown
- Expanded units (g → grams, cal → calories)
- Simple sentence structure

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

Custom scoring algorithm filters 300K+ foods with 99%+ accuracy:

- **Excludes** processed/compound foods (butter, sauce, powder, canned, juice)
- **Prioritizes** cooking methods (raw, cooked, grilled, steamed)
- **Favors** simple foods (plain, NFS, unsalted, whole)
- **Scoring system**: Base 100, exact match +30, exclude keywords -50, cooking methods +15, bonus keywords +20

Test results: 100/100 common foods matched correctly

### 4. **Voice-Optimized Responses**

Every response designed for Ray-Ban Meta glasses audio:

- No emojis (TTS reads them incorrectly: "체크마크 Meal logged")
- No progress bars (visual only: "████░░░░")
- No markdown formatting (ignored in audio)
- Full words instead of abbreviations (grams not g)
- Clean, simple sentence structure

### 5. **Natural Language Queries**

Ask questions in plain English:

- "How much protein did I eat today?"
- "What's my progress toward my calorie goal?"
- "Compare today to yesterday"
- "What should I eat for dinner?"
- "Show me my eating patterns"

### 6. **Two-Step Meal Workflow**

Accurate logging with user confirmation:

1. AI analyzes photo and shows detected foods
2. User confirms meal type (breakfast/lunch/dinner/snack)
3. System logs with proper timestamp
4. Voice-friendly confirmation sent

### 7. **Goal Tracking**

Set and monitor nutritional targets:

- Daily calorie goals
- Protein intake targets
- Macronutrient ratios
- Real-time progress tracking

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Google Gemini API key ([Get one free](https://ai.google.dev/))
- USDA FoodData Central API key ([Get one free](https://fdc.nal.usda.gov/api-key-signup.html))
- Twilio account with WhatsApp enabled

### Installation

```bash
# Clone repository
git clone https://github.com/JinLeeGG/GlassBite.git
cd GlassBite

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/glassbite_db

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# USDA
USDA_API_KEY=your_usda_api_key

# Flask
FLASK_SECRET_KEY=your_secret_key
```

### Database Initialization

```bash
# Create database
createdb glassbite_db

# Apply schema (recommended - includes all 25 nutrient columns)
psql -d glassbite_db -f schema.sql

# OR initialize with Python (alternative method)
python database_utils.py
```

### Run Application

```bash
# Terminal 1: Start Flask server
python app.py

# Terminal 2: Start Ngrok tunnel
ngrok http 5000

# Update Twilio webhook URL:
# Twilio Console → WhatsApp Sandbox → Webhook URL
# Set to: https://your-ngrok-url.ngrok.io/webhook/whatsapp
```

---

## 📱 Usage Examples

### Basic Meal Logging

**Step 1: Take photo with Ray-Ban Meta glasses**

**Step 2: Send via WhatsApp**

**Step 3: AI analyzes (2-3 seconds)**

```
Bot: "Analyzing your meal..."
```

**Step 4: Review detected foods**

```
Bot: "Got it! I detected:
     Grilled salmon, 150 grams
     Steamed broccoli, 100 grams
     Brown rice, 200 grams

     Total: 520 calories, 45 grams protein

     Is this breakfast, lunch, dinner, or snack?"
```

**Step 5: Confirm meal type**

```
You: "dinner"

Bot: "Meal logged as Dinner.
     Grilled salmon (150 grams): 270 calories, 39 grams protein, 0 grams carbs, 12 grams fat
     Steamed broccoli (100 grams): 35 calories, 2 grams protein, 7 grams carbs, 0 grams fat
     Brown rice (200 grams): 215 calories, 4 grams protein, 43 grams carbs, 3 grams fat

     Total: 520 calories, 45 grams protein, 50 grams carbs, 15 grams fat

     Today: 1520 calories, 85 grams protein (76 percent of 2000 calorie goal)"
```

### Natural Language Queries

```
You: "How much protein did I eat today?"
Bot: "Today you have eaten 85 grams of protein so far."

You: "What's my calorie progress?"
Bot: "You have consumed 1450 out of 2000 calories.
     73 percent of your daily goal. 550 calories remaining."

You: "Compare today to yesterday"
Bot: "Today: 1450 calories, 85 grams protein
     Yesterday: 1680 calories, 92 grams protein
     Difference: 230 fewer calories, 7 fewer grams protein today."
```

### Change Meal Type

```
You: "change to lunch"
Bot: "Changed your last meal to Lunch."
```

### Set Goals

```
You: "set calorie goal 2000"
Bot: "Goal set. Targeting 2000 calories per day."
```

---

## 🔌 API Endpoints

### `GET /`

Health check endpoint

```json
{
  "status": "running",
  "app": "GlassBite AI Chatbot",
  "version": "1.0.0"
}
```

### `POST /webhook/whatsapp`

Main webhook for Twilio WhatsApp integration

**Handles:**

- Photos with voice notes → Meal logging workflow
- Text messages → Chatbot queries or meal type confirmation

**Request (from Twilio):**

- `From`: User's WhatsApp number (e.g., `whatsapp:+12233392848`)
- `Body`: Message text
- `NumMedia`: Number of media attachments
- `MediaUrl0`: URL of first media attachment

**Response:** Empty 200 OK (Twilio requirement)

---

## 🧪 Testing

### USDA Food Matching Test

```bash
python tests/test_usda.py
```

Runs 100 common foods through the smart matching algorithm:

```
🔍 Testing: chicken breast (150g)
----------------------------------------------------------------------
📋 Found 10 results:
   1. Chicken breast, rotisserie, skin not eaten
   2. Chicken breast, rotisserie, skin eaten
   3. Chicken breast, sauteed, skin not eaten

✅ Using: Chicken breast, rotisserie, skin not eaten
   Calories: 216.0 cal
   Protein:  42.1g
   Carbs:    0.0g
   Fat:      5.4g

======================================================================
Result Summary
======================================================================
✅ Success: 100/100
❌ Failed: 0/100
Success rate: 100%
======================================================================
```

**Test Categories:**

- 15 Poultry & Meat items
- 10 Seafood items
- 15 Grains & Carbs
- 20 Vegetables
- 15 Fruits
- 10 Dairy & Eggs
- 10 Nuts & Seeds
- 5 Other items

All 100 foods matched correctly with smart filtering.

---

## 🗂️ Project Structure

```
GlassBite/
├── app.py                      # Flask webhook server
├── config.py                   # Configuration management
├── models.py                   # SQLAlchemy database models (5 tables)
├── database_utils.py           # Database initialization
├── schema.sql                  # PostgreSQL schema with 25-nutrient structure
├── services/
│   ├── gemini_service.py      # Google Gemini AI integration
│   ├── usda_service.py        # USDA nutrition data + smart matching
│   ├── meal_processor.py      # Meal logging workflow + 25-nutrient extraction
│   ├── chatbot_service.py     # Natural language query handler
│   └── twilio_service.py      # WhatsApp messaging
├── tests/
│   ├── test_usda.py           # USDA matching test suite (100 foods)
│   ├── test_usda_raw_data.py  # Raw USDA API response testing
│   └── reset_and_seed.py      # Database reset and seeding
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── SETUP_GUIDE.md             # Detailed setup instructions
```

### Key Components

**`services/gemini_service.py`**

- Analyzes food images with Google Gemini Vision
- Extracts food names and portion estimates
- Returns structured JSON data

**`services/usda_service.py`**

- Searches USDA FoodData Central (300K+ foods)
- **Smart matching algorithm** with custom scoring
- Scales nutrition data to actual portion size

**`services/meal_processor.py`**

- Orchestrates meal logging workflow
- Two-step confirmation (analysis → meal type)
- **Extracts all 25 nutrients from USDA API**
- Saves to FoodItem + FoodNutrient tables (1:1 relationship)
- Voice-optimized response formatting

**`services/chatbot_service.py`**

- Handles natural language queries
- Intent detection with keyword matching
- Generates voice-friendly responses
- Supports 9+ query types

---

## 🎯 Design Decisions

### Why Voice-First?

Ray-Ban Meta glasses are worn all day - users listen, not read:

- Removed markdown (formatting ignored by TTS)
- Expanded abbreviations (grams not g, calories not cal)

### Why Two-Step Confirmation?

AI analyzes first, user confirms meal type after:

- More accurate timestamps (user specifies breakfast vs lunch)
- Better error correction (review before saving)
- Clearer user intent

### Why Custom USDA Matching?

First search result is often wrong (60% error rate):

- "salmon" → "Lomi salmon" (Hawaiian dish)
- "banana" → "Banana powder"
- "broccoli" → "Fried broccoli"

Smart scoring algorithm improves to 99%+ accuracy:

- Excludes processed foods (powder, sauce, chips)
- Prioritizes cooking methods (raw, cooked, grilled)
- Favors simple descriptions (plain, NFS, whole)

### Why 25 Nutrients Instead of 4?

Comprehensive health tracking requires more than just macros:

- **Micronutrient deficiencies** are common (Vitamin D, Iron, B12)
- **Fat quality matters** (saturated vs. unsaturated)
- **B-vitamins** affect energy and metabolism
- **Minerals** support bone health, immunity, and more

The system extracts all 25 nutrients from USDA without performance impact, stored in a dedicated `food_nutrients` table with 1:1 relationship to `food_items`.

### Why Separate FoodItem and FoodNutrient Tables?

Separation of concerns and flexibility:

- **FoodItem**: Basic food info (name, portion, confidence)
- **FoodNutrient**: All 25 nutrient values (calories, protein, vitamins, minerals, etc.)
- **1:1 Relationship**: Each food item has exactly one nutrient record
- **Null Safety**: Code checks `if item.nutrients` before accessing values
- **Future-Proof**: Easy to add more nutrients without touching FoodItem table

### Why Timezone-Aware?

Using `datetime.now()` instead of `date.today()`:

- Accurate daily progress tracking
- Proper meal-to-day association
- Handles midnight edge cases

---

## 📊 Database Schema

### Tables

**users**

- id, phone_number, created_at

**meals**

- id, user_id, meal_type, timestamp
- image_url, voice_note_text, processing_status

**food_items**

- id, meal_id, name
- portion_size_grams, confidence_score

**food_nutrients** (25 nutrients per food item)

- id, food_item_id (1:1 relationship)
- **Tier 1 (10)**: calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg, potassium_mg, calcium_mg, iron_mg
- **Tier 2 (8)**: vitamin_c_mg, vitamin_d_ug, vitamin_a_ug, vitamin_b12_ug, magnesium_mg, zinc_mg, phosphorus_mg, cholesterol_mg
- **Tier 3 (7)**: saturated_fat_g, monounsaturated_fat_g, polyunsaturated_fat_g, folate_ug, vitamin_b6_mg, choline_mg, selenium_ug

**daily_summaries**

- id, user_id, date
- total_calories, total_protein, total_carbs, total_fat
- meal_count

**goals**

- id, user_id, goal_type, target_value
- start_date, end_date, status

---

## 🔧 Configuration

### API Rate Limits

- **Gemini**: 60 requests/minute (free tier)
- **USDA**: 1000 requests/hour (free tier)
- **Twilio**: Depends on plan (tested on paid tier)

### Supported Meal Types

- breakfast
- lunch
- dinner
- snack

### Chatbot Query Types

- Daily summary ("how am I doing today")
- Nutrient queries ("how much protein")
- Goal progress ("am I meeting my goal")
- Comparisons ("compare today to yesterday")
- Pattern analysis ("show me my patterns")
- Recommendations ("what should I eat")
- History queries ("what did I eat yesterday")
- Help ("help")

---

## 🐛 Troubleshooting

### Gemini 404 Error

- Solution: Use `gemini-pro-latest` model name
- Check API key is valid at ai.google.dev

### USDA Returns Wrong Foods

- Smart matching should handle this (99%+ accuracy)
- Run `python test_usda.py` to verify
- Check specific food in test output

### Timezone Issues

- Ensure using `datetime.now()` not `date.today()`
- Check database timezone configuration
- Daily progress should update at midnight

### WhatsApp Not Responding

- Verify Ngrok tunnel is running (`ngrok http 5000`)
- Check Twilio webhook URL matches Ngrok URL
- Confirm phone number added to Twilio sandbox

### TTS Reads Symbols

- All responses are voice-optimized
- Report any remaining emojis/symbols as bugs

---

## 🚀 Future Enhancements

- [ ] Web dashboard with 25-nutrient visualizations
- [ ] Micronutrient deficiency alerts (Vitamin D, Iron, B12, etc.)
- [ ] Comprehensive nutrient reports (all 25 nutrients tracked)
- [ ] Weekly/monthly nutrition reports
- [ ] Recipe suggestions based on nutrient gaps
- [ ] Barcode scanning for packaged foods
- [ ] Restaurant menu integration
- [ ] Meal prep planning
- [ ] Multi-language support
- [ ] Fitness tracker integration (Apple Health, Fitbit)
- [ ] Export nutrition data (CSV, PDF)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini** - AI vision and food recognition
- **USDA FoodData Central** - Comprehensive nutrition database (300K+ foods)
- **Twilio** - WhatsApp Business API integration
- **Ray-Ban Meta** - Smart glasses platform

---

## 📧 Contact

**JinLee**  
GitHub: [@JinLeeGG](https://github.com/JinLeeGG)

---

<div align="center">

**Made with ❤️ for hands-free nutrition tracking**

[⬆ Back to Top](#-glassbite-ai-powered-hands-free-nutrition-tracker)

</div>
