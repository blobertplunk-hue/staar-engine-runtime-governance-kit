#!/usr/bin/env python3
"""Stage 3 adversarial fail-closed tests for Inventory Recipe Cartridge v3."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "recipe_cartridge_runner_v3.py"
spec = importlib.util.spec_from_file_location("recipe_cartridge_runner_v3", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(runner)


def item(name: str, *, allergens: dict[str, str] | None = None, flags: list[str] | None = None, label: bool = False) -> dict:
    base = {k: "clear" for k in ["milk", "wheat", "egg", "peanut", "tree_nut"]}
    if allergens:
        base.update(allergens)
    return {
        "display_name": name,
        "allergen_status": base,
        "nutrition_flags": flags or [],
        "label_check_required": label,
    }


def classify(items: list[dict], recipe_type: str = "bowl", toddler_prep_required: bool = False):
    allergy = runner.allergen_gate(items)
    nutrition = runner.score_nutrition(items)
    fits = runner.classify_fits(nutrition, allergy, {"recipe_type": recipe_type, "toddler_prep_required": toddler_prep_required})
    return allergy, nutrition, fits


def test_greek_yogurt_shared_family_fails_closed():
    allergy, _, _ = classify([item("Greek yogurt", allergens={"milk": "contains"}, flags=["protein"])])
    assert allergy["shared_family_safe"] is False
    assert {"item": "Greek yogurt", "allergen": "milk"} in allergy["blocked_allergens"]


def test_egg_breakfast_shared_family_fails_closed():
    allergy, _, _ = classify([item("Eggs", allergens={"egg": "contains"}, flags=["protein"])])
    assert allergy["shared_family_safe"] is False
    assert {"item": "Eggs", "allergen": "egg"} in allergy["blocked_allergens"]


def test_flour_tortilla_tacos_fail_closed_for_wheat():
    allergy, _, _ = classify([item("Flour tortillas", allergens={"wheat": "contains"}, flags=["controlled_starch"])])
    assert allergy["shared_family_safe"] is False
    assert {"item": "Flour tortillas", "allergen": "wheat"} in allergy["blocked_allergens"]


def test_crusted_flounder_needs_label_check():
    allergy, nutrition, fits = classify([item("Crusted flounder", allergens={"milk":"needs_label_check","wheat":"needs_label_check","egg":"needs_label_check"}, flags=["protein", "label_check_sodium"], label=True)])
    assert allergy["shared_family_safe"] is False
    assert "Crusted flounder" in allergy["label_checks"]
    assert nutrition["sodium_risk"] == "label_check"
    assert fits["toddler_fit"] == "label_check"


def test_bbq_ribs_with_sugary_sauce_robert_limit():
    _, nutrition, fits = classify([item("BBQ ribs", flags=["protein", "saturated_fat_medium_high", "added_sugar_high"])])
    assert nutrition["added_sugar_risk"] == "high"
    assert nutrition["saturated_fat_risk"] == "medium"
    assert fits["robert_fit"] == "limit"


def test_canned_chili_high_sodium_robert_limit():
    _, nutrition, fits = classify([item("Canned chili", flags=["protein", "sodium_high"])])
    assert nutrition["sodium_risk"] == "high"
    assert fits["robert_fit"] == "limit"


def test_rotisserie_chicken_label_and_sodium_limit():
    allergy, nutrition, fits = classify([item("Rotisserie chicken", allergens={"milk":"needs_label_check","wheat":"needs_label_check"}, flags=["protein", "sodium_medium_high"], label=True)])
    assert allergy["shared_family_safe"] is False
    assert nutrition["sodium_risk"] == "high"
    assert fits["robert_fit"] == "limit"


def test_lentil_tomato_gf_pasta_clear_labels_can_be_default():
    items = [
        item("Lentils", flags=["protein", "fiber"]),
        item("GF pasta", flags=["controlled_starch"]),
        item("Tomato sauce clear label", flags=[]),
        item("Spinach", flags=["vegetable", "fiber"]),
        item("Mushrooms", flags=["vegetable"]),
    ]
    allergy, nutrition, fits = classify(items, recipe_type="pasta")
    assert allergy["shared_family_safe"] is True
    assert nutrition["protein_score"] == "high"
    assert nutrition["fiber_score"] == "high"
    assert nutrition["sodium_risk"] == "low"
    assert fits["robert_fit"] == "default"


def test_pork_loin_bean_bowl_default():
    items = [
        item("Pork loin", flags=["lean_protein"]),
        item("Black beans", flags=["protein", "fiber"]),
        item("Broccoli", flags=["vegetable", "fiber"]),
        item("Rice", flags=["controlled_starch"]),
    ]
    allergy, nutrition, fits = classify(items, recipe_type="bowl")
    assert allergy["shared_family_safe"] is True
    assert nutrition["sodium_risk"] == "low"
    assert fits["robert_fit"] == "default"
    assert fits["toddler_fit"] == "prep_required"


def test_toddler_grape_snack_requires_prep():
    allergy, nutrition, fits = classify([item("Grapes", flags=["fruit", "fiber"])], recipe_type="snack", toddler_prep_required=True)
    assert allergy["shared_family_safe"] is True
    assert fits["toddler_fit"] == "prep_required"


def test_generated_payload_validates():
    inv_path = ROOT / "current_inventory_normalized_20260604_v3.json"
    payload = {"recipes": runner.build_recipes(__import__("json").loads(inv_path.read_text()))}
    validation = runner.validate_payload(payload)
    assert validation["valid"] is True, validation
    assert validation["recipe_count"] == 5


if __name__ == "__main__":
    tests = [name for name in globals() if name.startswith("test_")]
    failures = []
    for name in tests:
        try:
            globals()[name]()
        except Exception as exc:
            failures.append((name, repr(exc)))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        raise SystemExit(1)
    print(f"PASS {len(tests)} tests")
