import logging

import requests

from odoo import _

_logger = logging.getLogger(__name__)


def fetch_nutrition_data(food_name):
    if not food_name:
        _logger.warning("Nutrition lookup skipped because no food name was provided.")
        return {
            "state": "error",
            "message": _("Please enter a food name to look up."),
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
        }

    request_headers = {
        "User-Agent": "calories_test_odoo/1.0 (+https://example.com)",
        "Accept": "application/json",
    }
    request_params = {
        "search_terms": food_name,
        "search_simple": 1,
        "fields": "product_name,nutriments",
        "page_size": 1,
    }

    try:
        response = requests.get(
            "https://world.openfoodfacts.org/api/v2/search",
            params=request_params,
            headers=request_headers,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        _logger.warning("Nutrition lookup failed for %s using v2 search: %s", food_name, exc)
        try:
            response = requests.get(
                "https://world.openfoodfacts.org/cgi/search.pl",
                params={
                    **request_params,
                    "json": 1,
                },
                headers=request_headers,
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as fallback_exc:
            _logger.exception(
                "Nutrition lookup failed for %s using fallback endpoint: %s",
                food_name,
                fallback_exc,
            )
            return {
                "state": "error",
                "message": _(
                    "Unable to reach the nutrition service right now. Please try again later."
                ),
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            }

    try:
        payload = response.json()
    except ValueError as exc:
        _logger.exception("Nutrition service returned invalid JSON for %s: %s", food_name, exc)
        return {
            "state": "error",
            "message": _("The nutrition service returned invalid data."),
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
        }

    products = payload.get("products") or []
    if not products:
        _logger.info("Nutrition lookup returned no products for %s", food_name)
        return {
            "state": "not_found",
            "message": _("No nutrition information was found for this food."),
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
        }

    product = products[0]
    nutriments = product.get("nutriments") or {}
    calories = (
        nutriments.get("energy-kcal_serving")
        or nutriments.get("energy-kcal_100g")
        or nutriments.get("energy-kcal")
        or 0.0
    )
    protein_g = (
        nutriments.get("proteins_serving")
        or nutriments.get("proteins_100g")
        or 0.0
    )
    carbs_g = (
        nutriments.get("carbohydrates_serving")
        or nutriments.get("carbohydrates_100g")
        or 0.0
    )
    fat_g = nutriments.get("fat_serving") or nutriments.get("fat_100g") or 0.0

    return {
        "state": "fetched",
        "message": False,
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
    }
