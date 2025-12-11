# Quick Reference: Dietary Restrictions & Allergen Alerts

## 📱 User Commands

### Set Dietary Restrictions
```
"My allergies are dairy, nuts"
"Set restrictions: vegan"
"I'm allergic to shellfish"
"My restrictions are gluten, dairy, vegetarian"
```

### View Current Restrictions
```
"Show my restrictions"
"What are my restrictions?"
"What am I allergic to?"
"My dietary"
```

### Add a Restriction
```
"Add dairy"
"Add vegan"
"Add gluten allergy"
```

### Remove a Restriction
```
"Remove dairy"
"Remove vegan"
```

## 🍽️ Supported Restrictions

### Allergens (10 categories):
- **Dairy** - milk, cheese, butter, yogurt, cream, whey, casein
- **Gluten** - wheat, bread, pasta, flour, barley, rye
- **Nuts** - almond, walnut, cashew, peanut, pecan
- **Shellfish** - shrimp, crab, lobster, clam, oyster
- **Fish** - salmon, tuna, cod, tilapia, anchovy
- **Eggs** - egg, omelet, mayonnaise, meringue
- **Soy** - tofu, edamame, tempeh, miso
- **Meat** - beef, pork, chicken, turkey, lamb
- **Pork** - bacon, ham, sausage, prosciutto
- **Alcohol** - wine, beer, vodka, rum, whiskey

### Dietary Preferences (5 types):
- **Vegetarian** - excludes meat, pork, fish, shellfish
- **Vegan** - excludes dairy, eggs, meat, pork, fish, shellfish
- **Pescatarian** - excludes meat, pork
- **Halal** - excludes pork, alcohol
- **Kosher** - excludes pork, shellfish

## 🔔 Alert Examples

### Immediate Alert (sent after image analysis):
```
🚨 DIETARY ALERT

⚠️ ALLERGEN WARNING:
• cheese pizza: Contains Dairy (cheese)
• caesar salad: Contains Gluten (croutons)

✓ Safe items: apple
```

### Meal Type Prompt (with warnings):
```
Got it! I detected:
• cheese pizza, 300g ⚠️ Dairy
• caesar salad, 150g ⚠️ Gluten
• apple, 100g

Total: 650 calories, 28g protein

⚠️ Contains restricted ingredients

Is this breakfast, lunch, dinner, or snack?
```

### Final Confirmation (with summary):
```
✓ Lunch logged (3 items)

🚨 WARNING: Contains Dairy (cheese), Gluten (croutons)

Nutrition: 650 cal, 28g protein, 75g carbs, 25g fat

Today: 1450/2000 cal (73%), 92/150g protein (61%)
```

## 💻 Developer API Reference

### AllergenService Methods

```python
from services.allergen_service import allergen_service, detect_ingredients, validate_meal, parse_user_restrictions

# Detect allergens in a food
result = detect_ingredients(
    food_name="cheese pizza",
    ingredients_list=["wheat dough", "mozzarella cheese", "tomato sauce"]
)
# Returns: {
#   'detected_allergens': ['dairy', 'gluten'],
#   'detected_ingredients': ['cheese', 'wheat dough']
# }

# Parse user restrictions
restrictions = parse_user_restrictions("dairy, nuts, vegan")
# Returns: {
#   'allergens': ['dairy', 'nuts'],
#   'preferences': ['vegan'],
#   'display': 'Dairy, Nuts, Vegan'
# }

# Validate meal
food_items = [
    {
        'name': 'cheese pizza',
        'detected_allergens': ['dairy', 'gluten'],
        'detected_ingredients': ['cheese', 'wheat dough']
    },
    {
        'name': 'salad',
        'detected_allergens': [],
        'detected_ingredients': ['lettuce', 'tomato']
    }
]
result = validate_meal(food_items, restrictions)
# Returns: {
#   'has_violations': True,
#   'violations': [...],
#   'safe_foods': ['salad'],
#   'summary': 'WARNING: Contains Dairy (cheese)'
# }

# Format alert message
alert = allergen_service.format_alert_message(result)
# Returns formatted WhatsApp message string

# Get supported restrictions
supported = allergen_service.get_supported_restrictions()
# Returns formatted list of all supported restrictions
```

## 🔄 Integration Flow

### 1. User Updates Restrictions
```python
# In chatbot_service.py
user.dietary_restrictions = "dairy,nuts,vegan"
db.session.commit()
```

### 2. Meal Processing with Allergen Check
```python
# In meal_processor.py

# 1. Get Gemini analysis (includes ingredients)
detected_foods = analyze_food_image(image_url, voice_note, twilio_auth)

# 2. Parse user restrictions
user_restrictions = parse_user_restrictions(user.dietary_restrictions or '')

# 3. Detect allergens
for food in detected_foods:
    ingredients = food.get('ingredients', [])
    allergen_info = detect_ingredients(food['name'], ingredients)
    food['detected_allergens'] = allergen_info['detected_allergens']
    food['detected_ingredients'] = allergen_info['detected_ingredients']

# 4. Validate meal
validation_result = validate_meal(detected_foods, user_restrictions)

# 5. Send immediate alert if violations
if validation_result['has_violations']:
    alert_message = allergen_service.format_alert_message(validation_result)
    send_whatsapp_message(phone_number, alert_message)

# 6. Continue with meal processing...
```

## 🧪 Testing

### Run Allergen Tests
```bash
cd /Users/sonnguyen/GlassBite
PYTHONPATH=/Users/sonnguyen/GlassBite python tests/test_allergen_integration.py
```

### Quick Test in Python
```python
from services.allergen_service import detect_ingredients, parse_user_restrictions, validate_meal

# Test detection
result = detect_ingredients("cheese pizza", ["cheese", "wheat"])
print(result)  # {'detected_allergens': ['dairy', 'gluten'], ...}

# Test parsing
restrictions = parse_user_restrictions("dairy,vegan")
print(restrictions)  # {'allergens': ['dairy'], 'preferences': ['vegan'], ...}

# Test validation
foods = [{'name': 'pizza', 'detected_allergens': ['dairy'], 'detected_ingredients': ['cheese']}]
result = validate_meal(foods, restrictions)
print(result['has_violations'])  # True
```

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number TEXT UNIQUE NOT NULL,
    dietary_restrictions TEXT,  -- Comma-separated: "dairy,nuts,vegan"
    created_at TIMESTAMP,
    last_meal_id INTEGER REFERENCES meals(id)
);
```

### Example Data
```sql
UPDATE users 
SET dietary_restrictions = 'dairy,nuts,vegan'
WHERE phone_number = 'whatsapp:+1234567890';
```

## 🐛 Troubleshooting

### No Alert Sent
- Check user.dietary_restrictions is set
- Verify allergen detection: `detect_ingredients()` returns allergens
- Confirm meal validation: `validate_meal()` finds violations
- Check Twilio service logs for delivery issues

### Wrong Allergen Detected
- Review keyword list in allergen_database
- Check ingredients list from Gemini response
- Verify food name contains allergen keywords

### Restriction Not Recognized
- Ensure restriction name is exact match (case-insensitive)
- Check supported restrictions: `allergen_service.get_supported_restrictions()`
- Verify parsing: `parse_user_restrictions(user_input)`

## 📚 Related Documentation

- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Complete implementation details
- [DIETARY_ALERTS.md](./DIETARY_ALERTS.md) - System architecture
- [AI_RECOMMENDATION_SYSTEM.md](./AI_RECOMMENDATION_SYSTEM.md) - Recommendation engine

---
**Last Updated:** December 11, 2025  
**Version:** 1.0.0
