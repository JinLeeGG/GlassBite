"""
USDA FoodData Central Service
Retrieves accurate nutrition information for foods
"""

import requests
import logging
from config import Config

logger = logging.getLogger(__name__)

class USDAService:
    """Service for retrieving nutrition data from USDA FoodData Central API"""
    
    def __init__(self):
        self.api_key = Config.USDA_API_KEY
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        
        # Fallback nutrition data for common foods not in USDA or hard to find
        self.fallback_foods = {
            'coffee': {'calories': 2, 'protein_g': 0.3, 'carbs_g': 0, 'fat_g': 0, 'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 5},
            'black coffee': {'calories': 2, 'protein_g': 0.3, 'carbs_g': 0, 'fat_g': 0, 'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 5},
            'water': {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0, 'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 0},
            'tea': {'calories': 2, 'protein_g': 0, 'carbs_g': 0.7, 'fat_g': 0, 'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 7},
            'green tea': {'calories': 2, 'protein_g': 0.5, 'carbs_g': 0, 'fat_g': 0, 'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 3},
            'diet soda': {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0, 'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 40},
            'sparkling water': {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0, 'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 0},
        }
    
    def get_nutrition_data(self, food_name, portion_grams):
        """
        Get nutrition data for a food item
        
        Args:
            food_name: Name of the food to look up
            portion_grams: Portion size in grams
        
        Returns:
            Dictionary with nutrition data:
            {
                "calories": 248,
                "protein_g": 31,
                "carbs_g": 0,
                "fat_g": 13.6,
                "fiber_g": 0,
                "sugar_g": 0,
                "sodium_mg": 70
            }
        """
        try:
            # Check fallback database first
            fallback = self._check_fallback(food_name, portion_grams)
            if fallback:
                logger.info(f"Using fallback data for: {food_name}")
                return fallback
            
            # Search USDA database
            logger.info(f"Searching USDA for: {food_name}")
            search_results = self._search_food(food_name)
            
            if not search_results:
                # Try generalized name
                generalized_name = self._generalize_food_name(food_name)
                logger.info(f"Trying generalized search: {generalized_name}")
                search_results = self._search_food(generalized_name)
            
            if not search_results:
                logger.warning(f"No USDA data found for: {food_name}")
                return self._estimate_nutrition(food_name, portion_grams)
            
            # Get the best match
            food_data = search_results[0]
            
            # Extract and scale nutrients
            nutrition = self._extract_nutrients(food_data, portion_grams)
            
            logger.info(f"Found nutrition for {food_name}: {nutrition['calories']} cal")
            return nutrition
            
        except Exception as e:
            logger.error(f"Error getting nutrition for {food_name}: {e}")
            return self._estimate_nutrition(food_name, portion_grams)
    
    def _search_food(self, food_name):
        """Search USDA FoodData Central with smart filtering"""
        try:
            url = f"{self.base_url}/foods/search"
            params = {
                'api_key': self.api_key,
                'query': food_name,
                'pageSize': 10,
                'dataType': ['Survey (FNDDS)', 'Foundation', 'SR Legacy']
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'foods' in data and len(data['foods']) > 0:
                foods = data['foods']
                
                # Exclude keywords (compound dishes, processed foods)
                exclude_keywords = [
                    'butter', 'oil', 'dressing', 'sauce', 'paste', 'powder',
                    'chips', 'tots', 'bread', 'cake', 'pie', 'nectar',
                    'with', 'and ', ' in ', 'salad', 'soup', 'stew',
                    'flavored', 'seasoned', 'marinated', 'breaded',
                    'lomi', 'candied', 'benedict', 'deviled', 'creamed',
                    'strawberry', 'blueberry', 'vanilla', 'chocolate',
                    'flour', 'cracker', 'pudding', 'split', 'burrito',
                    'casserole', 'mashed', 'roll', 'beans', 'baked',
                    'white', 'yolk', 'dehydrated', 'overripe',
                    'canned', 'juice', 'pickled', 'honey', 'roasted',
                    'fat free', 'nonfat', 'lowfat', 'reduced fat',
                    'dried', 'frozen', 'sweetened', 'imitation',
                    'yogurt', 'topping', 'fried', 'peel'
                ]
                
                # Priority keywords (cooking methods for real food)
                priority_keywords = ['raw', 'cooked', 'baked', 'roasted', 'grilled', 'steamed', 'boiled']
                
                # Bonus keywords (simple/plain foods)
                bonus_keywords = ['plain', 'nfs', 'unsalted', 'unflavored', 'whole', 'regular', 'peeled']
                
                # Filter and score
                scored_foods = []
                for food in foods:
                    description = food.get('description', '').lower()
                    score = 100  # Base score
                    
                    # Strong penalty for exclude keywords
                    has_exclude = False
                    for kw in exclude_keywords:
                        if kw in description:
                            score -= 50
                            has_exclude = True
                            break
                    
                    # Check if all words from food_name appear in description
                    food_words = set(food_name.lower().split())
                    desc_first_part = description.split(',')[0]
                    desc_words = set(desc_first_part.split())
                    
                    # All food name words in description
                    if food_words.issubset(desc_words):
                        score += 30
                    
                    # Description starts with food name
                    if description.startswith(food_name.lower()):
                        score += 20
                    
                    # Has cooking method keyword
                    has_priority = False
                    for kw in priority_keywords:
                        if kw in description:
                            score += 15
                            has_priority = True
                            break
                    
                    # Has bonus keywords (plain/simple foods)
                    for kw in bonus_keywords:
                        if kw in description:
                            score += 20
                            break
                    
                    # Prefer shorter descriptions (simpler foods)
                    word_count = len(desc_first_part.split())
                    if word_count <= 3:
                        score += 10
                    elif word_count <= 5:
                        score += 5
                    
                    # Prefer Foundation and SR Legacy types
                    data_type = food.get('dataType', '')
                    if data_type in ['Foundation', 'SR Legacy']:
                        score += 5
                    
                    scored_foods.append((score, food, description))
                
                # Sort by score
                scored_foods.sort(key=lambda x: x[0], reverse=True)
                
                # Log top 3 matches for debugging
                logger.info(f"Top 3 matches for '{food_name}':")
                for i, (score, food, desc) in enumerate(scored_foods[:3], 1):
                    logger.info(f"  {i}. [{score}] {desc}")
                
                # Filter out negative scores
                filtered = [food for score, food, desc in scored_foods if score > 0]
                
                return filtered if filtered else [scored_foods[0][1]]
            
            return None
            
        except Exception as e:
            logger.error(f"USDA API error: {e}")
            return None
    
    def _extract_nutrients(self, food_data, portion_grams):
        """Extract nutrients from USDA food data and scale to portion"""
        
        nutrients = {
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fat_g': 0,
            'fiber_g': 0,
            'sugar_g': 0,
            'sodium_mg': 0
        }
        
        # USDA provides nutrients per 100g
        serving_size = food_data.get('servingSize', 100)
        if serving_size == 0:
            serving_size = 100
        
        # Map USDA nutrient names to our keys
        nutrient_mapping = {
            'Energy': 'calories',
            'Protein': 'protein_g',
            'Carbohydrate, by difference': 'carbs_g',
            'Total lipid (fat)': 'fat_g',
            'Fiber, total dietary': 'fiber_g',
            'Sugars, total including NLEA': 'sugar_g',
            'Sodium, Na': 'sodium_mg'
        }
        
        # Extract nutrients
        if 'foodNutrients' in food_data:
            for nutrient in food_data['foodNutrients']:
                nutrient_name = nutrient.get('nutrientName', '')
                value = nutrient.get('value', 0)
                
                # Find matching nutrient
                for usda_name, our_key in nutrient_mapping.items():
                    if usda_name in nutrient_name:
                        nutrients[our_key] = value
                        break
        
        # Scale to actual portion size
        scale_factor = portion_grams / serving_size
        scaled_nutrients = {k: v * scale_factor for k, v in nutrients.items()}
        
        return scaled_nutrients
    
    def _check_fallback(self, food_name, portion_grams):
        """Check if food is in fallback database"""
        food_lower = food_name.lower()
        
        if food_lower in self.fallback_foods:
            base_nutrition = self.fallback_foods[food_lower]
            # Fallback data is per 100g, scale it
            scale = portion_grams / 100
            return {k: v * scale for k, v in base_nutrition.items()}
        
        return None
    
    def _generalize_food_name(self, food_name):
        """
        Simplify food name for better USDA matching
        Example: "grilled chicken breast" -> "chicken breast"
        """
        # Remove cooking methods
        cooking_methods = ['grilled', 'fried', 'baked', 'roasted', 'steamed', 
                          'boiled', 'sauteed', 'pan-fried', 'deep-fried']
        
        words = food_name.lower().split()
        filtered_words = [w for w in words if w not in cooking_methods]
        
        return ' '.join(filtered_words)
    
    def _estimate_nutrition(self, food_name, portion_grams):
        """
        Provide rough estimates when USDA lookup fails
        Based on common food categories
        """
        logger.warning(f"Using estimates for: {food_name}")
        
        food_lower = food_name.lower()
        
        # Basic estimates per 100g
        if any(word in food_lower for word in ['chicken', 'turkey', 'lean meat']):
            base = {'calories': 165, 'protein_g': 31, 'carbs_g': 0, 'fat_g': 3.6, 
                   'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 70}
        elif any(word in food_lower for word in ['beef', 'steak', 'pork']):
            base = {'calories': 250, 'protein_g': 26, 'carbs_g': 0, 'fat_g': 15, 
                   'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 60}
        elif any(word in food_lower for word in ['fish', 'salmon', 'tuna']):
            base = {'calories': 206, 'protein_g': 22, 'carbs_g': 0, 'fat_g': 12, 
                   'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 50}
        elif any(word in food_lower for word in ['rice', 'pasta', 'noodles']):
            base = {'calories': 130, 'protein_g': 2.7, 'carbs_g': 28, 'fat_g': 0.3, 
                   'fiber_g': 0.4, 'sugar_g': 0.1, 'sodium_mg': 1}
        elif any(word in food_lower for word in ['bread', 'toast']):
            base = {'calories': 265, 'protein_g': 9, 'carbs_g': 49, 'fat_g': 3.2, 
                   'fiber_g': 2.7, 'sugar_g': 5, 'sodium_mg': 491}
        elif any(word in food_lower for word in ['egg']):
            base = {'calories': 155, 'protein_g': 13, 'carbs_g': 1.1, 'fat_g': 11, 
                   'fiber_g': 0, 'sugar_g': 1.1, 'sodium_mg': 124}
        elif any(word in food_lower for word in ['vegetable', 'broccoli', 'carrot', 'lettuce', 'salad']):
            base = {'calories': 35, 'protein_g': 2.8, 'carbs_g': 7, 'fat_g': 0.4, 
                   'fiber_g': 2.6, 'sugar_g': 1.7, 'sodium_mg': 33}
        elif any(word in food_lower for word in ['fruit', 'apple', 'banana', 'orange']):
            base = {'calories': 52, 'protein_g': 0.3, 'carbs_g': 14, 'fat_g': 0.2, 
                   'fiber_g': 2.4, 'sugar_g': 10, 'sodium_mg': 1}
        else:
            # Generic food estimate
            base = {'calories': 150, 'protein_g': 5, 'carbs_g': 20, 'fat_g': 5, 
                   'fiber_g': 2, 'sugar_g': 3, 'sodium_mg': 100}
        
        # Scale to portion
        scale = portion_grams / 100
        return {k: v * scale for k, v in base.items()}


# Singleton instance
usda_service = USDAService()

def get_nutrition_data(food_name, portion_grams):
    """Helper function for nutrition lookup"""
    return usda_service.get_nutrition_data(food_name, portion_grams)
