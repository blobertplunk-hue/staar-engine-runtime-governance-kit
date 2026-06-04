#!/usr/bin/env python3
"""Inventory Recipe Cartridge v3 Stage 0-3 runner.

Consumes normalized inventory and emits recipe candidates with fail-closed allergy
status and first-pass nutrition scoring. Stage 3 adds validation helpers used by
adversarial fixtures. No web retrieval is performed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HIGH_SODIUM_FLAGS = {"sodium_medium_high", "sodium_high"}
LABEL_SODIUM_FLAGS = {"sodium_label_check", "label_check_sodium"}
HIGH_SUGAR_FLAGS = {"added_sugar_high"}
LABEL_SUGAR_FLAGS = {"added_sugar_label_check", "label_check_added_sugar"}
HIGH_SAT_FLAGS = {"saturated_fat_medium_high", "saturated_fat_high"}
PROTEIN_FLAGS = {"protein", "lean_protein"}
FIBER_FLAGS = {"fiber"}
VEG_FLAGS = {"vegetable", "high_volume", "low_calorie"}
STARCH_FLAGS = {"starch", "controlled_starch"}
REQUIRED_SHARED_CLEARANCE = ["milk", "wheat", "egg", "peanut", "tree_nut"]
REQUIRED_NUTRITION_SCORE_FIELDS = [
    "protein_score",
    "fiber_score",
    "sodium_risk",
    "added_sugar_risk",
    "saturated_fat_risk",
    "vegetable_volume",
    "calorie_density",
]
REQUIRED_RECIPE_FIELDS = [
    "title",
    "mode",
    "recipe_type",
    "uses_from_inventory",
    "missing_required",
    "need_to_buy",
    "steps",
    "allergy_status",
    "nutrition_score",
    "robert_fit",
    "wife_fit",
    "toddler_fit",
    "leftovers",
]

RECIPES: list[dict[str, Any]] = [
    {
        "title": "Pork Loin Black Bean Rice Bowls",
        "mode": "robert_weight_loss",
        "recipe_type": "bowl",
        "needs": ["pork_loin", "dried_black_beans", "white_rice"],
        "optional": ["spinach", "fresh_broccoli", "mushrooms"],
        "steps": [
            "Cook pork loin plainly.",
            "Cook or warm black beans and rice.",
            "Add spinach, broccoli, and mushrooms.",
            "Serve adult portion with 1/2 cup rice and extra vegetables.",
        ],
        "leftovers": "Use pork and beans in next-day bowls or soup.",
    },
    {
        "title": "Lentil Tomato GF Pasta with Spinach and Mushrooms",
        "mode": "family_shared_safe",
        "recipe_type": "pasta",
        "needs": ["lentils", "gf_penne", "tomato_sauce"],
        "optional": ["spinach", "mushrooms"],
        "steps": [
            "Cook lentils until soft.",
            "Simmer tomato sauce with lentils and vegetables.",
            "Serve sauce-heavy over GF pasta.",
        ],
        "leftovers": "Freeze extra lentil sauce.",
    },
    {
        "title": "Rotisserie Chicken Broccoli Rice Bowls",
        "mode": "use_perishables_first",
        "recipe_type": "bowl",
        "needs": ["rotisserie_chicken", "white_rice", "fresh_broccoli"],
        "optional": ["spinach", "mushrooms"],
        "steps": [
            "Remove chicken skin and shred breast meat.",
            "Steam broccoli and add spinach or mushrooms.",
            "Serve over a controlled rice portion.",
        ],
        "leftovers": "Use remaining chicken in soup.",
    },
    {
        "title": "White Bean Tuna Cucumber Salad Bowl",
        "mode": "quick_dinner_30_min",
        "recipe_type": "salad",
        "needs": ["canned_tuna", "great_northern_beans", "cucumbers"],
        "optional": ["spinach"],
        "steps": [
            "Drain tuna and beans.",
            "Combine with cucumber and greens/slaw.",
            "Dress with lemon/lime or vinegar.",
        ],
        "leftovers": "Best eaten same day.",
    },
    {
        "title": "Crusted Flounder Broccoli Sweet Potato Plate",
        "mode": "label_check",
        "recipe_type": "sheet_pan",
        "needs": ["crusted_flounder", "fresh_broccoli", "sweet_potatoes"],
        "optional": [],
        "steps": [
            "Check fish label for wheat, egg, dairy, sesame, and nut cross-contact.",
            "Bake fish according to package.",
            "Serve with broccoli and sweet potato.",
        ],
        "leftovers": "Fish is best same day.",
    },
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_items(inv: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {i["item_id"]: i for i in inv.get("items", [])}


def aggregate_flags(items: list[dict[str, Any]]) -> set[str]:
    flags: set[str] = set()
    for item in items:
        flags.update(item.get("nutrition_flags", []))
    return flags


def allergen_gate(items: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[str] = []
    blocked: list[dict[str, str]] = []
    for item in items:
        status = item.get("allergen_status", {})
        if item.get("label_check_required"):
            checks.append(item["display_name"])
        for allergen in REQUIRED_SHARED_CLEARANCE:
            if status.get(allergen) == "contains":
                blocked.append({"item": item["display_name"], "allergen": allergen})
            elif status.get(allergen) == "needs_label_check":
                checks.append(item["display_name"])
    return {
        "shared_family_safe": not blocked and not checks,
        "blocked_allergens": blocked,
        "label_checks": sorted(set(checks)),
    }


def score_nutrition(items: list[dict[str, Any]]) -> dict[str, str]:
    flags = aggregate_flags(items)
    protein = "high" if flags & PROTEIN_FLAGS else "medium" if "breakfast" in flags else "low"
    fiber = "high" if flags & FIBER_FLAGS and flags & VEG_FLAGS else "medium" if flags & FIBER_FLAGS else "low"
    sodium = "high" if flags & HIGH_SODIUM_FLAGS else "label_check" if flags & LABEL_SODIUM_FLAGS else "low"
    sugar = "high" if flags & HIGH_SUGAR_FLAGS else "label_check" if flags & LABEL_SUGAR_FLAGS else "low"
    sat = "high" if "saturated_fat_high" in flags else "medium" if flags & HIGH_SAT_FLAGS else "low"
    veg_count = sum(1 for item in items if set(item.get("nutrition_flags", [])) & VEG_FLAGS)
    veg = "high" if veg_count >= 2 else "medium" if flags & VEG_FLAGS else "low"
    cal = "high" if flags & HIGH_SAT_FLAGS and flags & STARCH_FLAGS else "moderate" if flags & STARCH_FLAGS else "low"
    return {
        "protein_score": protein,
        "fiber_score": fiber,
        "sodium_risk": sodium,
        "added_sugar_risk": sugar,
        "saturated_fat_risk": sat,
        "vegetable_volume": veg,
        "calorie_density": cal,
    }


def classify_fits(nutrition: dict[str, str], allergy: dict[str, Any], recipe: dict[str, Any]) -> dict[str, str]:
    robert = "default"
    if (
        nutrition["sodium_risk"] in {"high", "label_check"}
        or nutrition["added_sugar_risk"] == "high"
        or nutrition["saturated_fat_risk"] == "high"
    ):
        robert = "limit"
    wife = "compatible" if nutrition["protein_score"] in {"high", "medium"} and nutrition["fiber_score"] in {"high", "medium"} else "needs_addon"
    toddler_prep = bool(recipe.get("toddler_prep_required")) or recipe["recipe_type"] in {"salad", "bowl", "snack", "raw_fruit"}
    toddler = "label_check" if allergy["label_checks"] else "prep_required" if toddler_prep else "safe"
    return {"robert_fit": robert, "wife_fit": wife, "toddler_fit": toddler}


def validate_recipe_card(recipe: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_RECIPE_FIELDS:
        if field not in recipe:
            errors.append(f"missing_required_field:{field}")
    nutrition = recipe.get("nutrition_score", {})
    for field in REQUIRED_NUTRITION_SCORE_FIELDS:
        if field not in nutrition:
            errors.append(f"missing_nutrition_score_field:{field}")
    allergy = recipe.get("allergy_status", {})
    if allergy.get("shared_family_safe") and (allergy.get("blocked_allergens") or allergy.get("label_checks")):
        errors.append("unsafe_shared_family_safe_claim")
    if recipe.get("robert_fit") == "default":
        if nutrition.get("sodium_risk") in {"high", "label_check"}:
            errors.append("robert_default_with_sodium_risk")
        if nutrition.get("added_sugar_risk") == "high":
            errors.append("robert_default_with_high_added_sugar")
        if nutrition.get("saturated_fat_risk") == "high":
            errors.append("robert_default_with_high_saturated_fat")
    return errors


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    for idx, recipe in enumerate(payload.get("recipes", [])):
        recipe_errors = validate_recipe_card(recipe)
        if recipe_errors:
            errors.append({"index": idx, "title": recipe.get("title"), "errors": recipe_errors})
    return {"valid": not errors, "errors": errors, "recipe_count": len(payload.get("recipes", []))}


def build_recipes(inv: dict[str, Any]) -> list[dict[str, Any]]:
    idx = index_items(inv)
    out: list[dict[str, Any]] = []
    for recipe in RECIPES:
        used = [idx[item_id] for item_id in recipe["needs"] if item_id in idx]
        used.extend(idx[item_id] for item_id in recipe.get("optional", []) if item_id in idx)
        missing = [item_id for item_id in recipe["needs"] if item_id not in idx]
        allergy = allergen_gate(used)
        nutrition = score_nutrition(used)
        fits = classify_fits(nutrition, allergy, recipe)
        out.append({
            "title": recipe["title"],
            "mode": recipe["mode"],
            "recipe_type": recipe["recipe_type"],
            "uses_from_inventory": [item["display_name"] for item in used],
            "missing_required": missing,
            "need_to_buy": [],
            "steps": recipe["steps"],
            "allergy_status": allergy,
            "nutrition_score": nutrition,
            **fits,
            "leftovers": recipe["leftovers"],
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt")
    parser.add_argument("--strict", action="store_true", help="exit nonzero if generated recipe cards fail validation")
    args = parser.parse_args()
    inventory_path = Path(args.inventory)
    output_path = Path(args.output)
    inventory = json.loads(inventory_path.read_text())
    payload = {
        "schema": "metablooms.inventory_recipe_cartridge.stage3_output.v3",
        "recipes": build_recipes(inventory),
    }
    validation = validate_payload(payload)
    payload["validation"] = validation
    output_path.write_text(json.dumps(payload, indent=2) + "\n")
    if args.receipt:
        receipt = {
            "schema": "metablooms.inventory_recipe_cartridge.stage3_receipt.v3",
            "inventory_sha256": sha(inventory_path),
            "output_sha256": sha(output_path),
            "recipe_count": len(payload["recipes"]),
            "gates": {
                "required_scores_present": all("nutrition_score" in recipe for recipe in payload["recipes"]),
                "allergy_status_present": all("allergy_status" in recipe for recipe in payload["recipes"]),
                "label_checks_fail_closed": validation["valid"],
            },
            "validation": validation,
        }
        Path(args.receipt).write_text(json.dumps(receipt, indent=2) + "\n")
    return 0 if validation["valid"] or not args.strict else 2


if __name__ == "__main__":
    raise SystemExit(main())
