# GlassBite Setup and Usage Guide

## Quick Start

This guide will help you set up and run the GlassBite AI Chatbot in under 30 minutes.

## Prerequisites

Before you begin, make sure you have:

- **Python 3.9+** installed
- **PostgreSQL** database installed and running
- **Git** for version control
- A **Twilio account** (free trial works!)
- A **Google AI Studio account** (free tier available)
- A **USDA FoodData Central account** (free API key)

## Step-by-Step Setup

### 1. Install Python Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL Database

```powershell
# Create the database
createdb glassbite_db

# Import the schema
psql glassbite_db -f schema.sql

# Verify tables were created
psql glassbite_db -c "\dt"
```

You should see 5 tables: users, meals, food_items, daily_summaries, goals

### 3. Get Your API Keys

#### Twilio (WhatsApp Integration)

1. Sign up at https://www.twilio.com/try-twilio
2. Go to **Console** → **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Join the Twilio Sandbox by sending the code to the provided number
4. Copy these values:
   - **Account SID** (starts with AC...)
   - **Auth Token**
   - **WhatsApp Number** (usually +1 415 523 8886)

#### Google Gemini (AI Vision)

1. Visit https://ai.google.dev/
2. Click **Get API key in Google AI Studio**
3. Create a new API key
4. Copy the key (starts with AIza...)

#### USDA FoodData Central (Nutrition Data)

1. Visit https://fdc.nal.usda.gov/api-key-signup.html
2. Fill out the simple form
3. Check your email for the API key
4. Copy the key

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```powershell
# Copy the example file
cp .env.example .env
```

Edit `.env` with your values:

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcd
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# API Keys
GEMINI_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz
USDA_API_KEY=your_usda_api_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/glassbite_db

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=change-this-to-a-random-string-in-production
```

**Important**: Never commit the `.env` file to git!

### 5. Test Database Connection

```powershell
python -c "from app import app, db; app.app_context().push(); print('Database connected!'); db.create_all(); print('Tables verified!')"
```

If successful, you'll see:

```
Database connected!
Tables verified!
```

### 6. Start the Flask Application

```powershell
python app.py
```

You should see:

```
Configuration validated successfully
Database tables created successfully
 * Running on http://0.0.0.0:5000
```

### 7. Set Up Ngrok (for WhatsApp Testing)

Open a **new terminal** window:

```powershell
# Download ngrok from https://ngrok.com/download
# Then run:
ngrok http 5000
```

You'll see output like:

```
Forwarding   https://abc123xyz.ngrok.io -> http://localhost:5000
```

**Copy the HTTPS URL** (e.g., `https://abc123xyz.ngrok.io`)

### 8. Configure Twilio Webhook

1. Go to https://console.twilio.com/
2. Navigate to **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Scroll to **Sandbox Settings**
4. Set **When a message comes in** to:
   ```
   https://abc123xyz.ngrok.io/webhook/whatsapp
   ```
5. Method: **HTTP POST**
6. Click **Save**

## Testing the Application

### Test 1: Health Check

```powershell
curl http://localhost:5000/
```

Expected response:

```json
{
  "status": "running",
  "app": "GlassBite AI Chatbot",
  "version": "1.0.0"
}
```

### Test 2: Send a WhatsApp Message

1. Open WhatsApp on your phone
2. Send a message to the Twilio sandbox number
3. Send: "How am I doing today?"

You should receive a response from the chatbot!

### Test 3: Log a Meal (Photo)

1. Take a photo of food with your phone
2. Send it to the Twilio WhatsApp number
3. Optionally add caption: "Having this for lunch"
4. Wait 5-10 seconds
5. You'll receive a detailed nutrition breakdown!

### Test 4: Ask Questions

Try these questions via WhatsApp:

- "What's my protein intake?"
- "Compare today to yesterday"
- "Show me patterns"
- "What should I eat next?"
- "My goal is 2000 calories"

### Test 5: Check Statistics

```powershell
curl http://localhost:5000/stats
```

Response:

```json
{
  "total_users": 1,
  "total_meals": 3,
  "total_foods": 8
}
```

## Common Issues and Solutions

### Issue: "Configuration error: Missing required environment variables"

**Solution**: Make sure all API keys are set in your `.env` file:

- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- GEMINI_API_KEY
- USDA_API_KEY

### Issue: "Could not connect to database"

**Solutions**:

1. Check PostgreSQL is running:

   ```powershell
   pg_ctl status
   ```

2. Verify database exists:

   ```powershell
   psql -l | findstr glassbite
   ```

3. Test connection manually:
   ```powershell
   psql postgresql://postgres:password@localhost:5432/glassbite_db
   ```

### Issue: "Twilio webhook not receiving messages"

**Solutions**:

1. Verify ngrok is running in a separate terminal
2. Check the ngrok URL hasn't expired (free tier resets every 2 hours)
3. Ensure webhook URL in Twilio console is correct
4. Test webhook manually:
   ```powershell
   curl -X POST http://localhost:5000/webhook/whatsapp -d "From=whatsapp:+1234567890" -d "Body=test"
   ```

### Issue: "AI returned invalid response format"

**Solutions**:

1. Check Gemini API key is valid
2. Verify you haven't exceeded free tier quota
3. Try with a different food image (better lighting)

### Issue: "No USDA data found"

**Solution**: The app automatically falls back to estimates. Check USDA API key is valid:

```powershell
curl "https://api.nal.usda.gov/fdc/v1/foods/search?api_key=YOUR_KEY&query=apple"
```

## Development Tips

### View Logs

```powershell
# View in real-time
Get-Content app.log -Wait

# View last 50 lines
Get-Content app.log -Tail 50
```

### Reset Database

```powershell
# Drop and recreate
dropdb glassbite_db
createdb glassbite_db
psql glassbite_db -f schema.sql
```

### Test Without WhatsApp

Use the test endpoints:

```powershell
# Test chatbot
curl -X POST http://localhost:5000/test/question `
  -H "Content-Type: application/json" `
  -d '{"phone_number": "whatsapp:+1234567890", "question": "How am I doing today?"}'

# Test meal logging (requires public image URL)
curl -X POST http://localhost:5000/test/meal `
  -H "Content-Type: application/json" `
  -d '{"phone_number": "whatsapp:+1234567890", "image_url": "https://example.com/food.jpg", "voice_note": "Lunch"}'
```

### Run in Debug Mode

The app is already in debug mode when `FLASK_ENV=development`. You'll see:

- Detailed error messages
- SQL queries logged
- Auto-reload on code changes

## Production Deployment

### Deploy to Heroku

```powershell
# Install Heroku CLI, then:
heroku login
heroku create glassbite-chatbot
heroku addons:create heroku-postgresql:mini

# Set all environment variables
heroku config:set GEMINI_API_KEY=your_key
heroku config:set USDA_API_KEY=your_key
heroku config:set TWILIO_ACCOUNT_SID=your_sid
heroku config:set TWILIO_AUTH_TOKEN=your_token
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Deploy
git push heroku main

# Initialize database
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Check it's running
heroku open
heroku logs --tail
```

Update Twilio webhook to: `https://glassbite-chatbot.herokuapp.com/webhook/whatsapp`

### Deploy to Railway

1. Go to https://railway.app/
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your GlassBite repository
4. Add **PostgreSQL** plugin
5. Add environment variables in settings
6. Deploy automatically happens
7. Copy the generated URL
8. Update Twilio webhook to the Railway URL

## Example Usage Scenarios

### Scenario 1: Daily Tracking

Morning:

```
User: [Sends photo of oatmeal with berries]
Bot: ✅ Meal logged! 287 calories, 8g protein
```

Lunch:

```
User: [Sends photo of chicken salad]
Bot: ✅ Meal logged! 425 calories, 35g protein
     Today's total: 712 calories, 43g protein
```

Afternoon:

```
User: "How am I doing today?"
Bot: 📊 Today's Summary:
     • 712 calories
     • 43g protein
     🎯 Goal: 2000 calories
     ████░░░░░░ 36%
     1,288 calories remaining
```

### Scenario 2: Goal Setting

```
User: "My goal is 2000 calories"
Bot: ✅ Goal set! Targeting 2000 calories per day.

User: "Am I meeting my goal?"
Bot: 🎯 Goal Progress:
     Target: 2000 calories
     Current: 1,523 calories
     ███████░░░ 76%
     477 calories remaining
     👍 Great progress!
```

### Scenario 3: Pattern Analysis

```
User: "Show me patterns"
Bot: 🔍 Pattern Analysis (Last 2 weeks):
     Weekday average: 1,845 cal/day
     Weekend average: 2,234 cal/day
     📈 You eat 21% more on weekends!
     ⚠️ You're skipping breakfast often (6/14 days).
```

### Scenario 4: Meal Recommendations

```
User: "What should I eat next?"
Bot: 🎯 You have 523 calories left today.
     Balanced meals:
     • Grilled salmon with quinoa (500 cal, 35g protein)
     • Chicken breast with sweet potato (450 cal, 40g protein)
     • Turkey wrap with veggies (400 cal, 30g protein)
```

## API Endpoints Reference

### Public Endpoints

- `GET /` - Health check
- `POST /webhook/whatsapp` - Twilio webhook (receives WhatsApp messages)
- `GET /stats` - Application statistics

### Development Endpoints (only in DEBUG mode)

- `POST /test/meal` - Test meal processing
- `POST /test/question` - Test chatbot questions

## Database Queries Examples

### Get user's total calories today

```sql
SELECT total_calories
FROM daily_summaries
WHERE user_id = 1 AND date = CURRENT_DATE;
```

### Find most logged foods

```sql
SELECT name, COUNT(*) as count, AVG(portion_size_grams) as avg_portion
FROM food_items
GROUP BY name
ORDER BY count DESC
LIMIT 10;
```

### Get weekly nutrition trends

```sql
SELECT
    date,
    total_calories,
    total_protein,
    meal_count
FROM daily_summaries
WHERE user_id = 1
  AND date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date;
```

### Find users over calorie goals

```sql
SELECT
    u.phone_number,
    ds.total_calories,
    g.target_value,
    (ds.total_calories - g.target_value) as over_by
FROM users u
JOIN daily_summaries ds ON u.id = ds.user_id
JOIN goals g ON u.id = g.user_id
WHERE ds.date = CURRENT_DATE
  AND g.is_active = TRUE
  AND g.goal_type = 'calorie_target'
  AND ds.total_calories > g.target_value;
```

## Performance Optimization Tips

1. **Database Indexes**: Already created in schema.sql
2. **Caching**: Daily summaries cache aggregated data
3. **Background Processing**: In production, use Celery for image processing
4. **API Rate Limiting**: Add rate limiting for production
5. **CDN**: Use CDN for static assets

## Security Best Practices

1. **Never commit .env file**
2. **Use strong SECRET_KEY in production**
3. **Enable HTTPS only (Twilio requires this)**
4. **Add authentication for API endpoints**
5. **Sanitize user inputs**
6. **Set up CORS properly**

## Next Steps

1. ✅ Complete setup and test locally
2. ✅ Log 5-10 test meals
3. ✅ Try all chatbot questions
4. ✅ Deploy to production (Heroku/Railway)
5. ✅ Update Twilio webhook to production URL
6. ✅ Test with real food photos
7. ✅ Share with friends for testing

## Support and Resources

- **Flask Docs**: https://flask.palletsprojects.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Twilio WhatsApp**: https://www.twilio.com/docs/whatsapp
- **Gemini API**: https://ai.google.dev/docs
- **USDA API**: https://fdc.nal.usda.gov/api-guide.html

## Contributing

This is an educational project. Feel free to:

- Fork the repository
- Submit bug reports
- Suggest new features
- Share your improvements

---

**Happy Tracking! 🍽️📊**

For questions, open an issue on GitHub or contact the maintainer.
