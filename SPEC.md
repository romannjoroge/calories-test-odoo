
## Background

The test module you build does nothing.
Please build a working Odoo 19 module called calorie_advisor that helps users
track their daily calorie intake. The module must be installable, useful
to a real user, and meet Odoo coding standards.

Reference:
  https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html

---

## Requirements

The module must:

1. Calculate a personalised daily calorie budget for each user based on
   their body data and lifestyle. Use a medically recognised formula.
   The result must be physiologically realistic for a real adult.

2. Allow users to log meals throughout the day and track how many
   calories they have consumed vs their budget.

3. Fetch real nutritional data for foods from a free external API
   (no API key required). The API call must be triggered by a button
   on the meal log entry.

4. Show the user how many calories remain for the day, updated
   automatically as meals are logged.

---

## Acceptance Criteria

Module
- [ ] Module installs on Odoo 19 with zero errors and zero warnings
- [ ] Module name and folder name follow Odoo naming rules
- [ ] Module is listed in Apps and can be installed from the UI

Formula
- [ ] A male and female with identical inputs produce different
      daily calorie budgets
- [ ] All lifestyle activity levels produce strictly different budgets
      (more active = more calories)
- [ ] Changing any body data field immediately recalculates the budget
      without saving
- [ ] A weight loss goal produces a lower budget than maintaining weight
- [ ] Daily budget is always a positive number for any realistic input

Meal Logging
- [ ] A user can log multiple meals per day
- [ ] Each meal entry shows the calories it contributes
- [ ] Total calories consumed today is visible on the profile
- [ ] Calories remaining today is visible on the profile
- [ ] Yesterday's meals are not included in today's totals
- [ ] Consuming more than the budget shows a negative remaining value

External API
- [ ] Clicking the fetch button on a meal entry populates calorie and
      nutritional data from a real external source
- [ ] If the food is not found, the user sees a clear readable message
- [ ] If the API is unreachable, the user sees a clear readable message
- [ ] The application never crashes silently on API failure

Code Quality
- [ ] No deprecated Odoo API decorators
- [ ] All field names, method names, XML IDs, and file names follow
      Odoo coding guidelines
- [ ] Every model has _name and _description
- [ ] Error messages use the Odoo translation method correctly
- [ ] No bare except blocks

Tests
- [ ] Unit tests cover the formula with known expected values
- [ ] Unit tests cover edge cases (zero inputs, very large inputs,
      overeating)
- [ ] API tests mock the HTTP call — no real network calls in tests
- [ ] All error paths have a corresponding test
- [ ] All tests pass with --test-enable