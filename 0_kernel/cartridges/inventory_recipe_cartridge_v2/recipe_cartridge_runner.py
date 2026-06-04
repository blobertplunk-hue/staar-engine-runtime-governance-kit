#!/usr/bin/env python3
"""Inventory Recipe Cartridge v2 runner.

Deterministic first-pass recipe candidate generator from normalized household inventory.
This is intentionally conservative: unknown allergen status becomes label-check.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

RECIPES: list[dict[str, Any]] = [
    {
        "title": "Pork Loin Black Bean Rice Bowls",
        "needs": ["pork loin", "black beans", "rice"],
        "uses_optional": ["spinach", "broccoli", "mushrooms", "lime", "onion"],
        "status": "shared_safe_if_pork_label_plain",
        "health_fit": "default",
        "sodium_risk": "low_if_no_salty_sauce",
        "added_sugar_risk": "low",
        "steps": [
            "Cook or slice pork loin.",
            "Warm rice and black beans/lentils.",
            "Saute mushrooms/spinach/onion or steam broccoli.",
            "Assemble: 1/2 cup rice, beans, vegetables, pork.",
            "Flavor with lime/salsa/spices, not salty sauce."
        ],
        "leftovers": "Pack pork, beans, and vegetables separately from rice."
    },
    {
        "title": "Rotisserie Chicken Vegetable Rice Bowls",
        "needs": ["rotisserie chicken", "rice"],
        "uses_optional": ["broccoli", "spinach", "peas", "carrots", "corn", "mushrooms"],
        "status": "shared_safe_if_chicken_label_ok",
        "health_fit": "limit_sodium",
        "sodium_risk": "medium_high",
        "added_sugar_risk": "low",
        "steps": [
            "Remove skin and shred chicken breast.",
            "Warm rice with vegetables.",
            "Add 4-6 oz chicken for adults; smaller chopped portions for kids.",
            "Add extra vegetables to reduce rice dominance."
        ],
        "leftovers": "Use remaining chicken in soup or bean bowls next day."
    },
    {
        "title": "Lentil Tomato GF Pasta",
        "needs": ["lentils", "tomato sauce", "gluten-free pasta"],
        "uses_optional": ["diced tomatoes", "tomato paste", "spinach", "mushrooms", "onion"],
        "status": "shared_safe_if_pasta_GF_and_sauce_label_ok",
        "health_fit": "default_control_pasta_portion",
        "sodium_risk": "medium_if_jarred_sauce",
        "added_sugar_risk": "label_check",
        "steps": [
            "Cook lentils until soft.",
            "Simmer tomato sauce/diced tomatoes/tomato paste.",
            "Add spinach/mushrooms/onion.",
            "Serve over GF pasta; make sauce heavier than pasta."
        ],
        "leftovers": "Sauce freezes well; use over potatoes or rice."
    },
    {
        "title": "White Bean Tuna Cucumber Bowls",
        "needs": ["tuna", "white beans"],
        "uses_optional": ["cucumber", "spinach", "lemon", "lime", "coleslaw"],
        "status": "shared_safe_if_tuna_label_ok",
        "health_fit": "default",
        "sodium_risk": "medium_if_canned_tuna_high_sodium",
        "added_sugar_risk": "low",
        "steps": [
            "Drain tuna and beans.",
            "Mix with cucumber, spinach or slaw.",
            "Add lemon/lime/vinegar and pepper.",
            "Serve as salad bowl or over small rice portion."
        ],
        "leftovers": "Best eaten same day once mixed."
    },
    {
        "title": "Flounder Broccoli Sweet Potato Plate",
        "needs": ["flounder", "broccoli", "sweet potatoes"],
        "uses_optional": ["spinach", "lemon"],
        "status": "needs_label_check_crusted_fish",
        "health_fit": "default_if_label_safe",
        "sodium_risk": "label_check",
        "added_sugar_risk": "label_check",
        "steps": [
            "Check crusted flounder label for wheat, egg, dairy, sesame, and nut cross-contact.",
            "Bake fish according to package.",
            "Steam broccoli and bake or microwave sweet potato.",
            "Serve with lemon; avoid creamy sauces."
        ],
        "leftovers": "Fish is best same day; use extra broccoli in bowls."
    }
]


def flatten_inventory(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for value in data.get("categories", {}).values():
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("item", "")))
            else:
                parts.append(str(item))
    return "\n".join(parts).lower()


def present(needle: str, inventory_text: str) -> bool:
    if needle == "gluten-free pasta":
        return bool(re.search(r"\b(gf|gluten-free).*\b(pasta|spaghetti|penne)\b", inventory_text))
    return bool(re.search(re.escape(needle), inventory_text))


def score_recipe(recipe: dict[str, Any], inventory_text: str) -> dict[str, Any]:
    found_needs = [n for n in recipe["needs"] if present(n, inventory_text)]
    found_optional = [n for n in recipe.get("uses_optional", []) if present(n, inventory_text)]
    score = len(found_needs) * 5 + len(found_optional)
    missing = [n for n in recipe["needs"] if n not in found_needs]
    return {
        "title": recipe["title"],
        "score": score,
        "missing_required": missing,
        "uses_required": found_needs,
        "uses_optional": found_optional,
        "status": recipe["status"],
        "health_fit": recipe["health_fit"],
        "sodium_risk": recipe["sodium_risk"],
        "added_sugar_risk": recipe["added_sugar_risk"],
        "steps": recipe["steps"],
        "leftovers": recipe["leftovers"]
    }


def run(inventory_path: Path, output_path: Path) -> int:
    data = json.loads(inventory_path.read_text())
    inventory_text = flatten_inventory(data)
    scored = [score_recipe(r, inventory_text) for r in RECIPES]
    scored = sorted(scored, key=lambda r: r["score"], reverse=True)
    output_path.write_text(json.dumps({"recipes": scored}, indent=2) + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    return run(Path(args.inventory), Path(args.output))


if __name__ == "__main__":
    raise SystemExit(main())
