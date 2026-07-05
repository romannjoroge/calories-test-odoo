from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.tests.common import TransactionCase

from calories_test_odoo.models.calorie_meal_log import CalorieMealLog


class TestMealLogging(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.Profile = self.env["calorie.profile"]
        self.MealLog = self.env["calorie.meal.log"]

    def test_multiple_meals_and_yesterday_exclusion(self):
        profile = self.Profile.create({
            "user_id": self.env.user.id,
            "sex": "male",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        })

        self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "Apple",
            "datetime_consumed": datetime.now(),
            "calories": 95.0,
        })
        self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "Banana",
            "datetime_consumed": datetime.now(),
            "calories": 105.0,
        })
        self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "Old meal",
            "datetime_consumed": datetime.now() - timedelta(days=1),
            "calories": 999.0,
        })

        profile._compute_today_totals()
        self.assertEqual(profile.calories_consumed_today, 200.0)
        self.assertEqual(profile.calories_remaining_today, profile.daily_calorie_budget - 200.0)

    def test_remaining_goes_negative_when_over_budget(self):
        profile = self.Profile.create({
            "user_id": self.env.user.id,
            "sex": "male",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "sedentary",
            "goal": "maintain",
        })
        self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "Big lunch",
            "datetime_consumed": datetime.now(),
            "calories": 5000.0,
        })
        profile._compute_today_totals()
        self.assertLess(profile.calories_remaining_today, 0.0)

    def test_ingredients_are_aggregated_into_meal_totals(self):
        profile = self.Profile.create({
            "user_id": self.env.user.id,
            "sex": "male",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        })
        meal = self.MealLog.create({
            "profile_id": profile.id,
            "food_name": "Spaghetti meal",
            "datetime_consumed": datetime.now(),
            "ingredient_ids": [(0, 0, {"name": "spaghetti"}), (0, 0, {"name": "meatballs"})],
        })
        with patch.object(
            CalorieMealLog,
            "_fetch_nutrition_data",
            side_effect=[
                {"state": "fetched", "message": False, "calories": 120.0, "protein_g": 4.0, "carbs_g": 20.0, "fat_g": 3.0},
                {"state": "fetched", "message": False, "calories": 180.0, "protein_g": 12.0, "carbs_g": 10.0, "fat_g": 9.0},
            ],
        ) as mocked_fetch:
            meal.action_fetch_nutrition_data()

        self.assertEqual(meal.calories, 300.0)
        self.assertEqual(meal.protein_g, 16.0)
        self.assertEqual(meal.carbs_g, 30.0)
        self.assertEqual(meal.fat_g, 12.0)
        self.assertEqual(mocked_fetch.call_count, 2)
        self.assertEqual(profile.calories_consumed_today, 300.0)
