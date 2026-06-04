# Inventory Recipe Cartridge v2 — Dietary-Guideline-Gated

## Purpose

Given a household inventory list, produce practical recipes, meal plans, and shopping gaps that use available ingredients first while respecting the dietary rules determined in the health/food planning workflow.

This cartridge is for a family with overlapping constraints:

- Robert: weight loss, lower blood pressure, lower triglycerides, better HDL/non-HDL pattern, prediabetes prevention, lower sodium, lower added sugar, high fiber, high protein, and mostly minimally processed foods.
- Wife: PCOS-supportive, perimenopause-aware, thyroid-context-aware, breastfeeding, overweight; no aggressive dieting or breastfeeding supply-risk restriction.
- Children: one breastfeeding child with dairy allergy; one daughter with dairy, wheat, and egg allergies; one daughter with nut allergies except coconut.
- Default shared-meal rule: dairy-free, wheat-free/GF, egg-free, peanut-free, tree-nut-free; coconut is allowed by user rule.

## Evidence-locked dietary profile

The default recipe pattern is DASH/Mediterranean/flexitarian adapted for allergies:

- vegetables and fruit
- beans, lentils, and other legumes
- safe whole grains/starches such as rice, potatoes, quinoa, GF pasta, and certified GF oats when needed
- fish and lean/unprocessed proteins when label-safe
- limited sodium, added sugar, and saturated fat
- avoid crash dieting in breastfeeding mode

Evidence anchors:

- AHA dietary guidance: vegetables, fruits, whole grains, legumes, lean/fish proteins, liquid plant oils, less sodium, less added sugar, and fewer ultra-processed foods.
- CDC National DPP: calorie reduction, 5–7% weight loss, and at least 150 minutes/week activity as a diabetes-prevention pattern.
- 2023 International PCOS Guideline: lifestyle management, healthy eating, physical activity, and behavior strategies are core PCOS supports.
- CDC breastfeeding nutrition: breastfeeding mothers generally need additional calories, so recipe mode must not create crash-diet plans.
- FDA food allergen labeling: major allergen gates must include milk, eggs, fish, crustacean shellfish, tree nuts, peanuts, wheat, soybeans, and sesame; this household also requires practical dairy/wheat/egg/nut filtering.

## Hard safety rules

1. A recipe is **not shared-family-safe** unless dairy, wheat, egg, peanut, and tree-nut exposure are absent or explicitly replaced with safe forms.
2. Coconut is allowed by stated household rule, but labels still need normal review.
3. Packaged/crusted/sauced/seasoned foods default to `needs_label_check` unless label evidence is provided.
4. Greek yogurt is adult-only / not for dairy-allergy use.
5. Eggs are not for the egg-allergy child.
6. Flour tortillas are not wheat-safe unless a GF/wheat-free replacement is specified.
7. Crusted flounder requires label checking for wheat, egg, dairy, sesame, and nut cross-contact.
8. Canned chili, broth, sauces, baked beans, rotisserie chicken, sausage, deli meats, and ribs receive sodium-risk review.
9. No recipe may claim external web verification unless a web source is actually retrieved and cited.

## Recipe output requirements

Every recipe card should include:

- name
- mode
- uses-from-inventory list
- buy-gap list
- allergy status
- label checks
- Robert fit: `default`, `limit`, or `treat`
- wife fit: `compatible`, `needs_addon`, or `not_ideal`
- toddler fit: `safe`, `prep_required`, `not_safe`, or `label_check`
- sodium/added sugar risk
- protein/fiber estimate tier
- steps
- leftovers/use-first note

## Supported modes

- `use_perishables_first`
- `quick_dinner_30_min`
- `cheap_week_plan`
- `robert_weight_loss`
- `wife_pcos_breastfeeding`
- `toddler_safe`
- `family_shared_safe`
- `adult_only_variant`
- `leftover_builder`
- `shopping_gap_builder`
- `web_recipe_search` — requires citations and reject/adapt gates.

## Current v2 limitations

v2 is a useful first cartridge but intentionally incomplete. Required v3 improvements are tracked in `governance/improvement_log/INVENTORY_RECIPE_CARTRIDGE_V3_NEEDED_IMPROVEMENTS_20260604.md`:

- structured nutrition scoring
- stronger shopping-gap engine
- web recipe retrieval with citations
- mode/type diversity controller
- adversarial fixtures
- CLI receipts and fail-closed test gates
