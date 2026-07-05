# agents.md — calories_test_odoo (Odoo 19 module)

This file tells any coding agent (Claude Code, etc.) how to build, verify, and
extend this module. Read this fully before writing code. When in doubt,
prefer the Odoo 19 coding guidelines over habits from older Odoo versions.

Reference: https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html

## 1. Mission

Build a real, installable Odoo 19 module, `calories_test_odoo`, that:
1. Computes a personalized daily calorie budget from body data + lifestyle.
2. Lets a user log meals and see calories consumed vs. budget, live.
3. Fetches real nutrition data from a free, no-key external API on a button click.
4. Never crashes on bad input or API failure — always a translated, readable message.

The module is judged against the acceptance criteria in `SPEC.md`. Treat every checkbox as a test you must
be able to point to.

## 2. Non-negotiable technical decisions

Lock these in before writing models, so the agent doesn't reinvent them mid-task.

### 2.1 Calorie formula
Use the **Mifflin-St Jeor equation** (medically recognized, more accurate than
Harris-Benedict for modern populations):

- Male:   `BMR = 10*weight_kg + 6.25*height_cm - 5*age - 5`
- Female: `BMR = 10*weight_kg + 6.25*height_cm - 5*age + 161`

Then `TDEE = BMR * activity_multiplier`, with strictly increasing multipliers, e.g.:

| Activity level     | Multiplier |
|---------------------|-----------|
| sedentary            | 1.2  |
| light (1-3x/week)    | 1.375|
| moderate (3-5x/week) | 1.55 |
| active (6-7x/week)   | 1.725|
| very_active          | 1.9  |

Goal adjustment (applied after TDEE):
- `maintain` → TDEE
- `lose` → TDEE - 500 (never below a safe floor, e.g. clamp at 1200 kcal)
- `gain` → TDEE + 500

Implement this as a **pure Python method** (`_compute_calorie_budget` or similar)
that is trivially unit-testable without a DB, plus an `@api.depends` compute
field that calls it. This satisfies both the "recompute without saving"
criterion (onchange/compute in the UI) and the "unit test with known values"
criterion (call the pure function directly in tests).

### 2.2 External nutrition API
Use **Open Food Facts** (`https://world.openfoodfacts.org/`) — free, no API
key, no auth. Example: `GET https://world.openfoodfacts.org/api/v2/search?fields=product_name,nutriments&search_terms=<food>`.

Wrap every call in a thin client method (e.g. `_fetch_nutrition_data(food_name)`)
that:
- Uses Python's `requests` with an explicit timeout.
- Returns a clear result object/dict, never raises raw exceptions upward.
- Distinguishes "not found" from "unreachable" so the two required user-facing
  messages are actually different messages.
- Is the *only* place that does I/O, so tests can mock this one method/call
  site instead of monkeypatching `requests` everywhere.

Never let this call happen implicitly (on save, on create, on cron). It must
only run from an explicit button (`type="object"` button calling an
`ondelete=False`-safe method — see §4).

### 2.3 Odoo/Python API conventions (do / don't)

Do:
- `@api.depends`, `@api.onchange`, `@api.constrains`, `@api.model_create_multi`
- `self.env['ir.model...']`, `self.env.user`, `fields.Datetime.now()`
- `_("...")` (or `self.env._(...)` per 19.x translation helper — confirm
  current convention in the linked guidelines) for every user-facing string
- `UserError` / `ValidationError` from `odoo.exceptions` for expected failures
- Explicit `except requests.RequestException as e:` (or similarly specific)
  — never a bare `except:`
- snake_case for fields/methods, `CamelCase` for Python classes,
  `module_name.model_name` style for `_name` (e.g. `calorie.meal.log`)
- XML IDs: `calories_test_odoo.view_calorie_meal_log_form`,
  `calories_test_odoo.action_calorie_profile`, etc. — always namespaced by module

Don't:
- `@api.one`, `@api.multi`, `@api.returns` (removed/deprecated)
- Bare `except:` anywhere, including around the HTTP call
- Business logic in XML (no complex `eval` domains that should be Python)
- Direct SQL unless there's no ORM-safe way to do it

## 3. Data model sketch

Agents should feel free to refine this, but it should land close to:

- `calorie.profile` (or fields directly on `res.users`/`res.partner` via
  inheritance — pick one and be consistent): body data (age, sex, height_cm,
  weight_kg, activity_level selection, goal selection), computed
  `daily_calorie_budget`, computed `calories_consumed_today`,
  computed `calories_remaining_today`.
- `calorie.meal.log`: `partner_id`/`user_id`, `food_name`, `datetime_consumed`
  (defaults to now, editable), `quantity`, `calories` (fetched or manual),
  `protein_g`/`carbs_g`/`fat_g` (optional, from API), `fetch_state`
  (draft/fetched/not_found/error), button method `action_fetch_nutrition_data`.

"Today" filtering must be done in Python/domain using `fields.Date.context_today(self)`
or equivalent — not string-matching — so the "yesterday's meals excluded"
criterion is robust across timezones.

## 4. UI requirements mapped to criteria

- Profile form: body-data fields visible, budget field with `readonly=1` and
  `force_save` off, so it updates live via onchange — no save required.
- Meal log form: "Fetch nutrition data" button (`type="object"`), calories
  field, and a state/message field that shows not-found/unreachable errors
  inline (not just as a system traceback) — e.g. via `ValidationError` caught
  and re-shown, or a stored `error_message` field displayed in the view.
- Profile/kanban or form should show consumed vs. remaining, ideally with a
  progress bar widget, and remaining should render as a signed number
  (negative when over budget) not clamped to zero.

## 5. Testing requirements

Place tests under `calories_test_odoo/tests/`, imported via `tests/__init__.py`,
using `odoo.tests.common.TransactionCase` (or `HttpCase` only if you add
controller/JS-heavy behavior).

Must include:
- `test_calorie_formula.py`: known-value assertions for at least one male and
  one female case, each activity level (assert strictly increasing budgets),
  `lose` < `maintain` < `gain`, zero/degenerate input handling, very large
  input handling (no overflow/negative result), and a positivity assertion
  across a spread of realistic inputs.
- `test_meal_logging.py`: multiple meals same day sum correctly, "today" vs
  "yesterday" exclusion (create a log with a backdated datetime and assert
  it's excluded), remaining goes negative when over budget.
- `test_nutrition_api.py`: mock `requests.get` (e.g. `unittest.mock.patch`)
  to simulate (a) success, (b) not-found response, (c) connection
  error/timeout — assert the correct message/state results for each, and
  assert no real network call occurs (mock must be asserted as called).

Run with:
```
cd "C:\Program Files\Odoo 19.0e.20260702\server\"
"..\python\python.exe" odoo-bin -c odoo.conf --addons-path="odoo\addons,C:\Odoo\custom" -d <test_db> -i calories_test_odoo --test-enable --stop-after-init --log-level=test
```
All tests must pass with zero errors before considering a task complete.

## 6. File layout

```
calories_test_odoo/
  __init__.py
  __manifest__.py
  models/
    __init__.py
    calorie_profile.py
    calorie_meal_log.py
  views/
    calorie_profile_views.xml
    calorie_meal_log_views.xml
    calories_test_odoo_menus.xml
  security/
    ir.model.access.csv
  tests/
    __init__.py
    test_calorie_formula.py
    test_meal_logging.py
    test_nutrition_api.py
  static/description/icon.png   (optional but recommended for Apps listing)
```

`__manifest__.py` must include `name`, `version` (e.g. `19.0.1.0.0`),
`category`, `summary`, `depends` (at least `base`; add `mail` only if you use
chatter/activities), `data` listing security + views, and `license` must be
`OEEL-1`. Set `application: True` so it shows in Apps.

## 7. Definition of done (self-check before declaring finished)

Agents should verify, not assume:
- [ ] Module installs cleanly: `-i calories_test_odoo --stop-after-init`, no
      errors/warnings in log
- [ ] `--test-enable` run is green
- [ ] Manually trace each acceptance-criteria bullet in the original spec to
      a specific field/method/test — if you can't point to one, it's not done
- [ ] Grep the codebase for `api.one`, `api.multi`, bare `except:`, and
      un-translated string literals in raised errors — should be zero hits
- [ ] Confirm the external API is only ever called from the button's
      controller method, never from `create`/`write`/`compute`

## 8. Workflow notes for the agent

- Work model-by-model: profile + formula first (fully unit-tested) before
  wiring up meal logging, then the API client last — each stage should be
  independently runnable/testable.
- Prefer small, verifiable commits/tool-calls: write a model, write its test,
  run it, then move on, rather than generating the whole module and testing
  once at the end.
- If a requirement is ambiguous (e.g., store profile on `res.users` vs. a new
  model), state the assumption in a comment at the top of the file rather
  than silently picking one.