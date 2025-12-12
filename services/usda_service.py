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
        # Returns per 100g values - will be scaled later
        self.fallback_foods = {
            'coffee': {'calories': 2, 'protein_g': 0.3, 'carbs_g': 0, 'fat_g': 0},
            'black coffee': {'calories': 2, 'protein_g': 0.3, 'carbs_g': 0, 'fat_g': 0},
            'water': {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0},
            'tea': {'calories': 2, 'protein_g': 0, 'carbs_g': 0.7, 'fat_g': 0},
            'green tea': {'calories': 2, 'protein_g': 0.5, 'carbs_g': 0, 'fat_g': 0},
            'diet soda': {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0},
            'sparkling water': {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0},
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
            
            # Extract core food name (remove descriptors and cooking methods)
            core_name = self._extract_core_food_name(food_name)
            logger.info(f"Extracted core food name: '{core_name}' from '{food_name}'")
            
            # Search USDA database with core name
            search_results = self._search_food(core_name)
            
            if not search_results:
                logger.warning(f"No USDA data found for: {core_name}")
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
    
    def _extract_core_food_name(self, food_name):
        """
        Extract core food name by removing descriptors and cooking methods
        
        Examples:
            "Sliced Meatloaf with Ketchup Glaze" → "Meatloaf"
            "Steamed Green Beans" → "Green Beans"
            "Mashed Potatoes" → "Potatoes"
            "Grilled Chicken Breast" → "Chicken Breast"
        """
        # Words that signal end of core food name
        stop_words = ['with', 'in', 'on', 'topped', 'covered', 'drizzled', 'glazed']
        
        # Cooking methods and descriptors to remove
        descriptors = [
            'sliced', 'diced', 'chopped', 'minced', 'shredded', 'grated',
            'steamed', 'boiled', 'grilled', 'fried', 'baked', 'roasted', 'sauteed',
            'pan-fried', 'deep-fried', 'stir-fried', 'broiled', 'braised',
            'fresh', 'raw', 'cooked', 'prepared', 'homemade', 'frozen', 'canned'
        ]
        
        # Split and lowercase
        words = food_name.lower().split()
        core_words = []
        
        for word in words:
            # Stop at connector words
            if word in stop_words:
                break
            # Skip descriptors
            if word not in descriptors:
                core_words.append(word)
        
        # Join and return (limit to 3 words max for core food name)
        result = ' '.join(core_words[:3])
        return result if result else food_name
    
    def _search_food(self, food_name):
        """Search USDA FoodData Central with NFS priority"""
        try:
            url = f"{self.base_url}/foods/search"
            params = {
                'api_key': self.api_key,
                'query': food_name,
                'pageSize': 50,
                'dataType': ['Survey (FNDDS)', 'Foundation', 'SR Legacy']
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'foods' in data and len(data['foods']) > 0:
                foods = data['foods']
                
                # Complex dishes to avoid
                avoid_keywords = [
                    'sandwich', 'casserole', 'salad', 'soup', 'stew',
                    'frozen meal', 'dinner', 'entree', 'fast food',
                    'restaurant', 'chain', 'pizza', 'burger', 'wrap',
                    'burrito', 'taco', 'quesadilla', 'pie', 'cake'
                ]
                
                # Priority 1: Find NFS (Not Further Specified) items
                nfs_foods = []
                for food in foods:
                    desc = food.get('description', '').lower()
                    if ', nfs' in desc or ' nfs' in desc:
                        # Check if it's not a complex dish
                        if not any(keyword in desc for keyword in avoid_keywords):
                            nfs_foods.append(food)
                
                # Priority 2: Simple foods without avoid keywords
                simple_foods = []
                for food in foods:
                    desc = food.get('description', '').lower()
                    if not any(keyword in desc for keyword in avoid_keywords):
                        simple_foods.append(food)
                
                # Choose best match
                if nfs_foods:
                    selected_foods = nfs_foods
                    logger.info(f"✓ Found NFS item for '{food_name}'")
                elif simple_foods:
                    selected_foods = simple_foods
                    logger.info(f"Found simple food for '{food_name}'")
                else:
                    selected_foods = foods
                    logger.info(f"Using default results for '{food_name}'")
                
                # Log top 3 results
                logger.info(f"USDA search results for '{food_name}':")
                for i, food in enumerate(selected_foods[:3], 1):
                    desc = food.get('description', '')
                    logger.info(f"  {i}. {desc}")
                
                return selected_foods
            
            return None
            
        except Exception as e:
            logger.error(f"USDA API error: {e}")
            return None
    
    def _extract_nutrients(self, food_data, portion_grams):
        """Extract nutrients from USDA food data and scale to portion
        
        IMPORTANT: USDA FoodData Central nutrient values are ALWAYS per 100g,
        regardless of what servingSize says. We must always use 100g as the base.
        """
        
        nutrients = {
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fat_g': 0,
            'fiber_g': 0,
            'sugar_g': 0,
            'sodium_mg': 0
        }
        
        # Separate extra_nutrients from main nutrients
        # Map USDA nutrient IDs to keys (based on test_usda_raw_data.py findings)
        extra_nutrients = {}
        
        target_nutrient_ids = {
            # Already in main nutrients: 1008 (calories), 1003 (protein), 1005 (carbs), 1004 (fat)
            # Already in basic extra: 1079 (fiber), 2000 (sugar), 1093 (sodium)
            
            # Tier 1 additional (3 more)
            '1092': 'potassium_mg',      # Potassium
            '1087': 'calcium_mg',         # Calcium
            '1089': 'iron_mg',            # Iron
            
            # Tier 2 (8 nutrients)
            '1162': 'vitamin_c_mg',       # Vitamin C
            '1114': 'vitamin_d_ug',       # Vitamin D
            '1106': 'vitamin_a_ug',       # Vitamin A, RAE
            '1178': 'vitamin_b12_ug',     # Vitamin B-12
            '1090': 'magnesium_mg',       # Magnesium
            '1095': 'zinc_mg',            # Zinc
            '1091': 'phosphorus_mg',      # Phosphorus
            '1253': 'cholesterol_mg',     # Cholesterol
            
            # Tier 3 (7 nutrients)
            '1258': 'saturated_fat_g',    # Saturated fatty acids
            '1292': 'monounsaturated_fat_g',  # Monounsaturated fatty acids
            '1293': 'polyunsaturated_fat_g',  # Polyunsaturated fatty acids
            '1177': 'folate_ug',          # Folate, total
            '1175': 'vitamin_b6_mg',      # Vitamin B-6
            '1180': 'choline_mg',         # Choline, total
            '1103': 'selenium_ug'         # Selenium
        }
        
        # Extract nutrients (these are per 100g from USDA)
        if 'foodNutrients' in food_data:
            for nutrient in food_data['foodNutrients']:
                nutrient_id = str(nutrient.get('nutrientId', ''))
                nutrient_name = nutrient.get('nutrientName', '')
                value = nutrient.get('value', 0)
                unit = nutrient.get('unitName', '')
                
                # Check if it's one of our main nutrients
                if nutrient_id == '1008' and unit == 'KCAL':  # Energy (calories)
                    nutrients['calories'] = value
                elif nutrient_id == '1003':  # Protein
                    nutrients['protein_g'] = value
                elif nutrient_id == '1005':  # Carbs
                    nutrients['carbs_g'] = value
                elif nutrient_id == '1004':  # Total Fat
                    nutrients['fat_g'] = value
                elif nutrient_id == '1079':  # Fiber
                    nutrients['fiber_g'] = value
                elif nutrient_id == '2000':  # Total Sugars
                    nutrients['sugar_g'] = value
                elif nutrient_id == '1093':  # Sodium
                    nutrients['sodium_mg'] = value
                # Check if it's one of our extra nutrients
                elif nutrient_id in target_nutrient_ids:
                    extra_nutrients[target_nutrient_ids[nutrient_id]] = value
        
        # Scale from 100g base to actual portion size
        # USDA values are per 100g, so scale_factor = portion_grams / 100
        scale_factor = portion_grams / 100.0
        scaled_nutrients = {k: v * scale_factor for k, v in nutrients.items()}
        scaled_extra = {k: v * scale_factor for k, v in extra_nutrients.items()}
        
        # Add extra_nutrients to the result
        scaled_nutrients['extra_nutrients'] = scaled_extra
        
        return scaled_nutrients
    
    def _check_fallback(self, food_name, portion_grams):
        """Check if food is in fallback database"""
        food_lower = food_name.lower()
        
        if food_lower in self.fallback_foods:
            base_nutrition = self.fallback_foods[food_lower]
            # Fallback data is per 100g, scale it
            scale = portion_grams / 100
            scaled = {k: v * scale for k, v in base_nutrition.items()}
            # Add empty extra_nutrients for consistency
            scaled['extra_nutrients'] = {}
            return scaled
        
        return None
    
    def _estimate_nutrition(self, food_name, portion_grams):
        """
        Provide rough estimates when USDA lookup fails
        Based on common food categories
        """
        logger.warning(f"Using estimates for: {food_name}")
        
        food_lower = food_name.lower()
        
        # Basic estimates per 100g (main nutrients + extras)
        if any(word in food_lower for word in ['chicken', 'turkey', 'lean meat']):
            base = {'calories': 165, 'protein_g': 31, 'carbs_g': 0, 'fat_g': 3.6}
            extras = {'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 70}
        elif any(word in food_lower for word in ['beef', 'steak', 'pork']):
            base = {'calories': 250, 'protein_g': 26, 'carbs_g': 0, 'fat_g': 15}
            extras = {'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 60}
        elif any(word in food_lower for word in ['fish', 'salmon', 'tuna']):
            base = {'calories': 206, 'protein_g': 22, 'carbs_g': 0, 'fat_g': 12}
            extras = {'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 50}
        elif any(word in food_lower for word in ['rice', 'pasta', 'noodles']):
            base = {'calories': 130, 'protein_g': 2.7, 'carbs_g': 28, 'fat_g': 0.3}
            extras = {'fiber_g': 0.4, 'sugar_g': 0.1, 'sodium_mg': 1}
        elif any(word in food_lower for word in ['bread', 'toast']):
            base = {'calories': 265, 'protein_g': 9, 'carbs_g': 49, 'fat_g': 3.2}
            extras = {'fiber_g': 2.7, 'sugar_g': 5, 'sodium_mg': 491}
        elif any(word in food_lower for word in ['egg']):
            base = {'calories': 155, 'protein_g': 13, 'carbs_g': 1.1, 'fat_g': 11}
            extras = {'fiber_g': 0, 'sugar_g': 1.1, 'sodium_mg': 124}
        elif any(word in food_lower for word in ['vegetable', 'broccoli', 'carrot', 'lettuce', 'salad']):
            base = {'calories': 35, 'protein_g': 2.8, 'carbs_g': 7, 'fat_g': 0.4}
            extras = {'fiber_g': 2.6, 'sugar_g': 1.7, 'sodium_mg': 33}
        elif any(word in food_lower for word in ['fruit', 'apple', 'banana', 'orange']):
            base = {'calories': 52, 'protein_g': 0.3, 'carbs_g': 14, 'fat_g': 0.2}
            extras = {'fiber_g': 2.4, 'sugar_g': 10, 'sodium_mg': 1}
        else:
            # Generic food estimate
            base = {'calories': 150, 'protein_g': 5, 'carbs_g': 20, 'fat_g': 5}
            extras = {'fiber_g': 2, 'sugar_g': 3, 'sodium_mg': 100}
        
        # Scale to portion
        scale = portion_grams / 100
        scaled = {k: v * scale for k, v in base.items()}
        scaled['extra_nutrients'] = {k: v * scale for k, v in extras.items()}
        return scaled


# Singleton instance
usda_service = USDAService()

def get_nutrition_data(food_name, portion_grams):
    """Helper function for nutrition lookup"""
    return usda_service.get_nutrition_data(food_name, portion_grams)
