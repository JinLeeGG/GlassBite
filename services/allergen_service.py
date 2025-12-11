"""
Allergen and Dietary Restriction Service
Detects allergens and validates meals against user dietary restrictions
"""

import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

class AllergenService:
    """Service for allergen detection and dietary restriction validation"""
    
    def __init__(self):
        # Common allergen categories
        self.allergen_database = {
            'dairy': {
                'keywords': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 
                           'lactose', 'ghee', 'paneer', 'mozzarella', 'cheddar', 'parmesan'],
                'display_name': 'Dairy'
            },
            'gluten': {
                'keywords': ['wheat', 'bread', 'pasta', 'flour', 'barley', 'rye', 'couscous',
                           'seitan', 'semolina', 'spelt', 'noodle', 'tortilla', 'pita'],
                'display_name': 'Gluten'
            },
            'nuts': {
                'keywords': ['almond', 'walnut', 'cashew', 'pecan', 'pistachio', 'hazelnut',
                           'macadamia', 'peanut', 'nut'],
                'display_name': 'Nuts'
            },
            'shellfish': {
                'keywords': ['shrimp', 'crab', 'lobster', 'prawn', 'crawfish', 'clam', 
                           'mussel', 'oyster', 'scallop'],
                'display_name': 'Shellfish'
            },
            'fish': {
                'keywords': ['salmon', 'tuna', 'cod', 'tilapia', 'fish', 'anchovy', 'sardine',
                           'halibut', 'trout', 'bass', 'mackerel'],
                'display_name': 'Fish'
            },
            'eggs': {
                'keywords': ['egg', 'omelet', 'omelette', 'scrambled', 'mayonnaise', 'meringue'],
                'display_name': 'Eggs'
            },
            'soy': {
                'keywords': ['soy', 'tofu', 'edamame', 'tempeh', 'miso', 'soy sauce'],
                'display_name': 'Soy'
            },
            'meat': {
                'keywords': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'veal', 'bacon',
                           'ham', 'sausage', 'steak', 'meatball', 'burger'],
                'display_name': 'Meat'
            },
            'pork': {
                'keywords': ['pork', 'bacon', 'ham', 'sausage', 'prosciutto', 'pepperoni'],
                'display_name': 'Pork'
            },
            'alcohol': {
                'keywords': ['wine', 'beer', 'vodka', 'rum', 'whiskey', 'sake', 'champagne'],
                'display_name': 'Alcohol'
            }
        }
        
        # Dietary preference categories
        self.dietary_preferences = {
            'vegetarian': {
                'excludes': ['meat', 'fish', 'shellfish'],
                'display_name': 'Vegetarian'
            },
            'vegan': {
                'excludes': ['meat', 'fish', 'shellfish', 'dairy', 'eggs'],
                'display_name': 'Vegan'
            },
            'pescatarian': {
                'excludes': ['meat'],
                'display_name': 'Pescatarian'
            },
            'halal': {
                'excludes': ['pork', 'alcohol'],
                'display_name': 'Halal'
            },
            'kosher': {
                'excludes': ['pork', 'shellfish'],
                'display_name': 'Kosher'
            }
        }
    
    def parse_user_restrictions(self, restrictions_string: str) -> Dict:
        """
        Parse user dietary restrictions from string to structured format
        
        Args:
            restrictions_string: Comma-separated restrictions (e.g., "dairy,nuts,vegan")
        
        Returns:
            {
                'allergens': ['dairy', 'nuts'],
                'preferences': ['vegan'],
                'display': 'Dairy, Nuts, Vegan'
            }
        """
        if not restrictions_string:
            return {'allergens': [], 'preferences': [], 'display': 'None'}
        
        restrictions = [r.strip().lower() for r in restrictions_string.split(',')]
        
        allergens = []
        preferences = []
        
        for restriction in restrictions:
            if restriction in self.allergen_database:
                allergens.append(restriction)
            elif restriction in self.dietary_preferences:
                preferences.append(restriction)
        
        # Generate display names
        display_names = []
        for allergen in allergens:
            display_names.append(self.allergen_database[allergen]['display_name'])
        for pref in preferences:
            display_names.append(self.dietary_preferences[pref]['display_name'])
        
        return {
            'allergens': allergens,
            'preferences': preferences,
            'display': ', '.join(display_names) if display_names else 'None'
        }
    
    def detect_ingredients(self, food_name: str, ingredients_list: List[str] = None) -> Dict:
        """
        Detect allergens and ingredients in a food item
        
        Args:
            food_name: Name of the food
            ingredients_list: Optional list of specific ingredients detected by AI
        
        Returns:
            {
                'detected_allergens': ['dairy', 'gluten'],
                'detected_ingredients': ['cheese', 'wheat bread'],
                'confidence': 0.85
            }
        """
        detected_allergens = set()
        detected_ingredients = []
        
        # Check food name
        food_lower = food_name.lower()
        
        # Check against allergen database
        for allergen, data in self.allergen_database.items():
            for keyword in data['keywords']:
                if keyword in food_lower:
                    detected_allergens.add(allergen)
                    detected_ingredients.append(keyword)
        
        # Check ingredients list if provided
        if ingredients_list:
            for ingredient in ingredients_list:
                ingredient_lower = ingredient.lower()
                for allergen, data in self.allergen_database.items():
                    for keyword in data['keywords']:
                        if keyword in ingredient_lower:
                            detected_allergens.add(allergen)
                            if ingredient not in detected_ingredients:
                                detected_ingredients.append(ingredient)
        
        # Calculate confidence based on detection method
        confidence = 0.9 if ingredients_list else 0.75
        
        return {
            'detected_allergens': list(detected_allergens),
            'detected_ingredients': detected_ingredients,
            'confidence': confidence
        }
    
    def validate_meal(self, food_items: List[Dict], user_restrictions: Dict) -> Dict:
        """
        Validate entire meal against user dietary restrictions
        
        Args:
            food_items: List of food items with detected ingredients
            user_restrictions: Parsed user restrictions
        
        Returns:
            {
                'has_violations': bool,
                'violations': [...],
                'safe_foods': ['Green salad', 'Apple'],
                'summary': 'WARNING: Contains dairy (cheese)'
            }
        """
        violations = []
        safe_foods = []
        
        # Get all restricted allergens
        restricted_allergens = set(user_restrictions.get('allergens', []))
        
        # Add allergens from dietary preferences
        for preference in user_restrictions.get('preferences', []):
            if preference in self.dietary_preferences:
                excluded = self.dietary_preferences[preference]['excludes']
                restricted_allergens.update(excluded)
        
        # Check each food item
        for food in food_items:
            food_name = food.get('name', '')
            detected = food.get('detected_allergens', [])
            ingredients = food.get('detected_ingredients', [])
            
            # Check for violations
            food_violations = []
            for allergen in detected:
                if allergen in restricted_allergens:
                    # Determine severity
                    severity = 'allergen' if allergen in user_restrictions.get('allergens', []) else 'preference'
                    
                    # Find specific ingredient
                    ingredient = next((ing for ing in ingredients 
                                     if any(keyword in ing.lower() 
                                           for keyword in self.allergen_database[allergen]['keywords'])),
                                    allergen)
                    
                    food_violations.append({
                        'food_name': food_name,
                        'allergen': allergen,
                        'allergen_display': self.allergen_database[allergen]['display_name'],
                        'ingredient': ingredient,
                        'severity': severity
                    })
            
            if food_violations:
                violations.extend(food_violations)
            else:
                safe_foods.append(food_name)
        
        # Generate summary
        summary = self._generate_violation_summary(violations)
        
        return {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'safe_foods': safe_foods,
            'summary': summary
        }
    
    def _generate_violation_summary(self, violations: List[Dict]) -> str:
        """Generate human-readable summary of violations"""
        if not violations:
            return 'All foods are safe'
        
        # Group by allergen
        allergen_groups = {}
        for v in violations:
            allergen_display = v['allergen_display']
            if allergen_display not in allergen_groups:
                allergen_groups[allergen_display] = []
            allergen_groups[allergen_display].append(v['ingredient'])
        
        # Build summary
        parts = []
        for allergen, ingredients in allergen_groups.items():
            unique_ingredients = list(set(ingredients))
            parts.append(f"{allergen} ({', '.join(unique_ingredients[:2])})")
        
        return 'WARNING: Contains ' + ', '.join(parts)
    
    def format_alert_message(self, validation_result: Dict) -> str:
        """
        Format dietary restriction violations into alert message
        
        Returns:
            User-friendly alert message
        """
        if not validation_result['has_violations']:
            return None
        
        violations = validation_result['violations']
        
        # Separate by severity
        allergen_violations = [v for v in violations if v['severity'] == 'allergen']
        preference_violations = [v for v in violations if v['severity'] == 'preference']
        
        message = "🚨 DIETARY ALERT\n\n"
        
        if allergen_violations:
            message += "⚠️ ALLERGEN WARNING:\n"
            for v in allergen_violations:
                message += f"• {v['food_name']}: Contains {v['allergen_display']} ({v['ingredient']})\n"
            message += "\n"
        
        if preference_violations:
            message += "ℹ️ DIETARY PREFERENCE:\n"
            for v in preference_violations:
                message += f"• {v['food_name']}: Contains {v['allergen_display']} ({v['ingredient']})\n"
            message += "\n"
        
        if validation_result['safe_foods']:
            message += f"✓ Safe items: {', '.join(validation_result['safe_foods'][:3])}"
            if len(validation_result['safe_foods']) > 3:
                message += f" +{len(validation_result['safe_foods']) - 3} more"
        
        return message.strip()
    
    def get_supported_restrictions(self) -> str:
        """Get formatted list of supported restrictions"""
        allergens = [data['display_name'] for data in self.allergen_database.values()]
        preferences = [data['display_name'] for data in self.dietary_preferences.values()]
        
        return f"""Supported allergens: {', '.join(allergens[:5])}...

Dietary preferences: {', '.join(preferences)}

Example: "dairy,nuts,vegan" or "gluten,shellfish" or "vegetarian" """


# Singleton instance
allergen_service = AllergenService()

def detect_ingredients(food_name: str, ingredients_list: List[str] = None) -> Dict:
    """Helper function for ingredient detection"""
    return allergen_service.detect_ingredients(food_name, ingredients_list)

def validate_meal(food_items: List[Dict], user_restrictions: Dict) -> Dict:
    """Helper function for meal validation"""
    return allergen_service.validate_meal(food_items, user_restrictions)

def parse_user_restrictions(restrictions_string: str) -> Dict:
    """Helper function for parsing restrictions"""
    return allergen_service.parse_user_restrictions(restrictions_string)
