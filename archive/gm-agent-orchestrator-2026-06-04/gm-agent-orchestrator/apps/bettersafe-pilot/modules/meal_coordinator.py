#!/usr/bin/env python3
"""BetterSafe Meal Coordinator — Recipe matching + shopping lists (local only)"""

import logging
import json

logger = logging.getLogger('BetterSafe.Meals')


class MealCoordinator:
    """Match meals to available ingredients."""

    def __init__(self, db):
        self.db = db
        logger.info("Meal Coordinator initialized")

    def add_meal_plan(self, date, meal_type, recipe_name, ingredients, prep_time=0, cook_time=0):
        """Add a meal to the plan."""
        data = {
            'date': date,
            'meal_type': meal_type,
            'recipe_name': recipe_name,
            'ingredients': json.dumps(ingredients),
            'prep_time_min': prep_time,
            'cooking_time_min': cook_time
        }
        meal_id = self.db.insert('meal_plans', data)
        logger.info(f"Added meal {meal_id}: {recipe_name} on {date}")
        return meal_id

    def check_ingredients_available(self, ingredients):
        """Check if ingredients are in fridge."""
        fridge_items = self.db.get_all('fridge_inventory')
        available = []
        missing = []

        for ingredient in ingredients:
            found = any(f[1].lower() == ingredient['name'].lower() for f in fridge_items)
            if found:
                available.append(ingredient)
            else:
                missing.append(ingredient)

        return {'available': available, 'missing': missing}

    def get_meal_for_date(self, date):
        """Get meals planned for a specific date."""
        self.db.cursor.execute(
            'SELECT * FROM meal_plans WHERE date = ?',
            (date,)
        )
        return self.db.cursor.fetchall()

    def suggest_recipe_for_expiring_items(self):
        """Suggest recipes using soon-to-expire ingredients."""
        # Placeholder: would query recipes that use expiring items
        return []

    def get_status(self):
        """Get meal planning status."""
        meals = self.db.get_all('meal_plans')
        return {
            'total_meals_planned': len(meals),
            'upcoming_meals': 0  # TODO: count meals in next 7 days
        }
