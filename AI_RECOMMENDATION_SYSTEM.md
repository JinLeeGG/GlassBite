# AI-Powered Recommendation Engine 🤖

## Overview

The AI-Powered Recommendation Engine uses **Gemini AI** combined with **database analytics** to provide intelligent, personalized meal suggestions based on:

- **User's eating history** (30-day analysis)
- **Current nutritional goals and gaps**
- **Learned preferences** (favorite foods, meal patterns)
- **Community insights** (popular foods across all users)
- **Context awareness** (time of day, meal type)

## Features

### 1. Database Intelligence 📊

The system analyzes your actual eating data:

```python
# Tracks from your history:
- Total meals logged (30 days)
- Average meal calories & protein
- Top 10 favorite foods (frequency-based)
- Recent foods (last 7 days)
- Meal timing patterns
- Meal type preferences
```

### 2. Nutrient Gap Analysis 🎯

Calculates what you need today:

```python
# Real-time calculations:
- Calories consumed vs. remaining
- Protein consumed vs. remaining
- Over/under budget detection
- Carbs and fat tracking
```

### 3. Community Wisdom 👥

Learns from all users:

```python
# Cross-user insights:
- Top 20 most logged foods
- Average portion sizes
- Popular meal combinations
```

### 4. AI-Generated Suggestions 🧠

**Gemini receives:**
- Your eating profile
- Today's nutrition status
- Popular community foods
- Meal context (breakfast/lunch/dinner/snack)

**Gemini generates:**
- 3 personalized meal options
- Accurate calorie/protein/carb/fat estimates
- Personalization insights ("Why this fits you")
- Variety (avoids recent foods)

### 5. Smart Fallback System 🔄

**Three-tier approach:**
1. **AI-powered** (preferred) - Gemini generates custom recommendations
2. **Rule-based with user data** - Uses favorite foods if AI fails
3. **Static recommendations** - Generic options as last resort

## Usage

### Via Text Messages

```
User: "What should I eat?"
→ Context-based recommendation (time-aware)

User: "What should I eat for breakfast?"
→ Breakfast-specific suggestions

User: "Recommend a meal"
→ AI analyzes and suggests

User: "Suggest something for dinner"
→ Dinner recommendations with personalization
```

### Example Output

```
You have 520 calories remaining.

1. Grilled chicken thighs with roasted sweet potato
   520 calories, 45g protein, 48g carbs, 18g fat
   → Matches your favorite protein, different from recent meals

2. Baked cod with quinoa and asparagus
   480 calories, 42g protein, 45g carbs, 12g fat
   → Light fish option, community favorite

3. Turkey meatballs with zucchini noodles
   450 calories, 40g protein, 25g carbs, 20g fat
   → Lower carb option, similar to your usual style

💪 Focus on protein - you need 45g more today
```

## Architecture

### File Structure

```
services/
├── recommendation_service.py  # Main AI engine
├── chatbot_service.py         # Integration layer
└── gemini_service.py           # Gemini API utilities
```

### Key Components

#### RecommendationEngine Class

```python
class RecommendationEngine:
    def get_recommendations(user_id, context)
        # Main entry point
    
    def _gather_user_insights(user_id)
        # Analyze 30-day eating history
    
    def _calculate_nutrient_gaps(user_id)
        # Calculate today's gaps
    
    def _get_community_insights()
        # Query popular foods
    
    def _generate_ai_recommendations(...)
        # Call Gemini AI
    
    def _rule_based_recommendations(...)
        # Fallback using user data
```

### Database Queries

**User History:**
```sql
SELECT * FROM meals 
WHERE user_id = ? 
  AND timestamp >= (CURRENT_DATE - INTERVAL '30 days')
  AND processing_status = 'completed'
```

**Community Insights:**
```sql
SELECT food_items.name, COUNT(*), AVG(portion_size_grams)
FROM food_items
JOIN food_nutrients ON food_items.id = food_nutrients.food_item_id
GROUP BY food_items.name
ORDER BY COUNT(*) DESC
LIMIT 20
```

**Today's Summary:**
```sql
SELECT * FROM daily_summaries
WHERE user_id = ? AND date = CURRENT_DATE
```

**Active Goals:**
```sql
SELECT * FROM goals
WHERE user_id = ? 
  AND goal_type IN ('calorie_target', 'protein_target', 'carb_target')
  AND is_active = TRUE
```

## AI Prompt Engineering

### Prompt Structure

```python
"""
You are a nutrition expert AI. Generate 3 personalized meal recommendations.

USER EATING PROFILE:
- Total meals logged: {count}
- Average meal: {calories} cal, {protein}g protein
- Favorite foods: {list}
- Recently ate: {recent_list}

TODAY'S NUTRITION STATUS:
- Calories consumed: {consumed}
- Calories remaining: {remaining}
- Protein remaining: {protein_gap}
- Over budget: {yes/no}

POPULAR COMMUNITY FOODS:
{community_favorites}

REQUIREMENTS:
1. Fit remaining calories/protein
2. Consider eating history
3. Avoid recent foods
4. Use realistic portions
5. Include: name, calories, protein, carbs, fat
6. Add personalization insight

OUTPUT FORMAT:
[Plain text, no JSON, concise]
"""
```

### Why This Works

✅ **Specific constraints** - AI knows exact calorie/protein targets
✅ **Context-rich** - Full eating history provided
✅ **Realistic** - Community data grounds suggestions in reality
✅ **Actionable** - Clear format requirements
✅ **Personalized** - Unique to each user

## Performance

### Response Times
- Database queries: ~50-100ms
- AI generation: ~1-3 seconds
- Total response: ~1-3.5 seconds

### Caching Opportunities
```python
# Future optimization:
- Cache community insights (5 min TTL)
- Cache user insights (1 hour TTL)
- Pre-compute nutrient gaps
```

## Testing

Run the test suite:

```bash
cd /Users/sonnguyen/GlassBite
python tests/test_recommendation_engine.py
```

Tests include:
1. General recommendations
2. Context-specific (breakfast/lunch/dinner)
3. User insights analysis
4. Nutrient gap calculation
5. Community insights query
6. Fallback mechanisms

## Error Handling

**Three-tier fallback:**
```python
try:
    # Tier 1: AI-powered
    return gemini_recommendations()
except GeminiError:
    try:
        # Tier 2: Rule-based with user data
        return rule_based_with_favorites()
    except Exception:
        # Tier 3: Static generic
        return static_recommendations()
```

**Logged errors:**
- Gemini API failures
- Database query errors
- Parsing errors
- Missing user data

## Configuration

### Environment Variables

```bash
# .env file
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://...
```

### Gemini Model

Currently using: `gemini-2.0-flash-exp`

**Why this model:**
- Fast response times (~1-2 sec)
- Good nutrition knowledge
- Reliable structured output
- Cost-effective

## Future Enhancements

### Planned Features

1. **Dietary Restrictions**
   - Vegetarian/vegan filtering
   - Allergen avoidance
   - Religious dietary laws

2. **Recipe Integration**
   - Step-by-step cooking instructions
   - Ingredient shopping lists
   - Prep time estimates

3. **Seasonal Awareness**
   - Seasonal produce suggestions
   - Holiday-appropriate meals
   - Weather-based recommendations

4. **Budget Optimization**
   - Cost-per-meal estimates
   - Budget-friendly alternatives
   - Bulk cooking suggestions

5. **Advanced ML**
   - Collaborative filtering
   - Deep learning meal embeddings
   - Taste profile modeling

6. **Social Features**
   - Share favorite meals
   - Friend recommendations
   - Group meal planning

## API Reference

### get_recommendations()

```python
def get_recommendations(user_id: int, context: str = 'general') -> str:
    """
    Generate personalized meal recommendations.
    
    Args:
        user_id: User database ID
        context: 'general', 'breakfast', 'lunch', 'dinner', 'snack'
    
    Returns:
        Formatted recommendation text with 3 meal suggestions
    
    Raises:
        Exception: Falls back to static recommendations on error
    """
```

### Example Integration

```python
from services.recommendation_service import recommendation_engine

# Get recommendations
result = recommendation_engine.get_recommendations(
    user_id=123,
    context='dinner'
)

print(result)
# Output: AI-generated personalized suggestions
```

## Monitoring

### Key Metrics to Track

- **Usage**: Recommendations requested per day
- **Success Rate**: AI vs. fallback ratio
- **Response Time**: P50, P95, P99 latencies
- **User Engagement**: Recommendations followed (if tracked)
- **Data Quality**: Users with sufficient history

### Logging

```python
logger.info(f"Recommendations requested: user={user_id}, context={context}")
logger.error(f"Gemini API error: {error}")
logger.warning(f"Insufficient user data: user={user_id}")
```

## Dependencies

```txt
google-generativeai==0.3.1  # Gemini AI
flask-sqlalchemy==3.1.1      # Database ORM
psycopg2-binary==2.9.9       # PostgreSQL driver
```

## Credits

- **AI Model**: Google Gemini 2.0 Flash
- **Database**: PostgreSQL with SQLAlchemy
- **Architecture**: Flask microservice pattern
- **Data Source**: USDA FoodData Central

---

## Support

For issues or questions:
1. Check the test suite: `tests/test_recommendation_engine.py`
2. Review logs in `app.log`
3. Verify Gemini API key is configured
4. Ensure database connection is active

**Last Updated**: December 11, 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready
