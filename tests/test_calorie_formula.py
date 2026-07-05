from odoo.tests.common import TransactionCase


class TestCalorieFormula(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.Profile = self.env["calorie.profile"]

    def test_known_values_and_goal_offsets(self):
        male = self.Profile._compute_calorie_budget("male", 30, 180, 80, "moderate", "maintain")
        female = self.Profile._compute_calorie_budget("female", 30, 180, 80, "moderate", "maintain")
        self.assertNotEqual(male, female)

        budgets = {}
        for level in ["sedentary", "light", "moderate", "active", "very_active"]:
            budget = self.Profile._compute_calorie_budget("male", 30, 180, 80, level, "maintain")
            budgets[level] = budget

        self.assertGreater(budgets["light"], budgets["sedentary"])
        self.assertGreater(budgets["moderate"], budgets["light"])
        self.assertGreater(budgets["active"], budgets["moderate"])
        self.assertGreater(budgets["very_active"], budgets["active"])

        maintain = self.Profile._compute_calorie_budget("male", 30, 180, 80, "moderate", "maintain")
        lose = self.Profile._compute_calorie_budget("male", 30, 180, 80, "moderate", "lose")
        gain = self.Profile._compute_calorie_budget("male", 30, 180, 80, "moderate", "gain")
        self.assertLess(lose, maintain)
        self.assertLess(maintain, gain)

    def test_zero_and_large_inputs(self):
        self.assertEqual(self.Profile._compute_calorie_budget("male", 0, 180, 80, "moderate", "maintain"), 0.0)
        self.assertEqual(self.Profile._compute_calorie_budget("male", 30, 0, 80, "moderate", "maintain"), 0.0)
        self.assertEqual(self.Profile._compute_calorie_budget("male", 30, 180, 0, "moderate", "maintain"), 0.0)
        budget = self.Profile._compute_calorie_budget("male", 30, 180, 8000, "moderate", "maintain")
        self.assertGreater(budget, 0.0)

    def test_realistic_inputs_are_positive(self):
        for sex in ["male", "female"]:
            for age in [20, 35, 50]:
                budget = self.Profile._compute_calorie_budget(sex, age, 170, 75, "moderate", "maintain")
                self.assertGreater(budget, 0.0)
