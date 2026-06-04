# Inventory Recipe Cartridge v3 — Stage 0–2 Implementation Plan

## Scope

This stage upgrades the v2 cartridge into a more machine-enforced v3 cartridge foundation.

Stage coverage:

- Stage 0: harden the cartridge contract and rulebooks.
- Stage 1: normalize inventory into a structured schema with source confidence, label-check flags, perishable ranking, and recipe roles.
- Stage 2: add first-pass nutrition scoring with deterministic category/risk rules.

Out of scope for this stage:

- full web recipe search and adaptation
- live USDA FoodData Central API calls
- complete macro calculation from exact package labels
- full meal calendar generation

## Evidence basis

The v3 contract preserves the evidence anchors recorded in the v2 improvement log:

- AHA dietary guidance: vegetables, fruits, whole grains, legumes, fish/lean proteins, liquid plant oils, lower sodium, lower added sugar, and fewer ultra-processed foods.
- CDC National DPP: calorie reduction, 5–7% weight loss, and at least 150 minutes/week activity as the default prevention pattern.
- 2023 International PCOS guideline: healthy eating, physical activity, and lifestyle management as core supports.
- CDC breastfeeding nutrition: breastfeeding mode must not generate crash-diet outputs.
- FDA food allergen labeling: milk, eggs, fish, crustacean shellfish, tree nuts, peanuts, wheat, soybeans, and sesame remain label-gated.
- USDA FoodData Central: planned authoritative source for later exact nutrition lookup; this stage creates a local first-pass scoring map.

## Machine gates

A recipe candidate must not pass v3 Stage 0–2 validation unless:

1. It has allergy status fields.
2. Unknown packaged-food allergen status is marked `needs_label_check`.
3. It has protein, fiber, sodium, added sugar, saturated fat, vegetable-volume, and calorie-density scores.
4. It has Robert, wife/breastfeeding, and toddler fit fields.
5. It records which inventory items were used and which label checks remain.
6. It does not mark dairy, wheat, egg, peanut, or tree-nut containing foods as shared-family-safe.

## Deliverables

- `cartridge_contract_v3.json`
- `dietary_rulebook_v3.json`
- `allergen_rulebook_v3.json`
- `nutrition_scoring_rules_v3.json`
- `normalized_inventory_schema_v3.json`
- `current_inventory_normalized_20260604_v3.json`
- `recipe_cartridge_runner_v3.py`
- `examples/stage0_2_sample_output.json`
- `receipts/STAGE0_2_RECEIPT.json`
