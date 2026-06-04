# INVENTORY_RECIPE_CARTRIDGE_V3_NEEDED_IMPROVEMENTS — 2026-06-04

## Status

Inventory Recipe Cartridge v2 has been added as a first-generation cartridge. It is useful for deterministic inventory-based recipe candidates and conservative allergy/health gating, but it is not yet complete enough to be treated as a world-class recipe-decision engine.

## Evidence anchors

The v3 upgrade should remain aligned to these evidence bases:

- American Heart Association dietary guidance: prioritize vegetables, fruits, whole grains, legumes, fish/lean proteins, liquid plant oils, lower sodium, lower added sugar, and fewer ultra-processed foods.
  - https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/nutrition-basics/aha-diet-and-lifestyle-recommendations
- CDC National Diabetes Prevention Program: calorie reduction, 5–7% weight loss, and at least 150 minutes/week activity are core diabetes-prevention pattern elements.
  - https://www.cdc.gov/diabetes-prevention/programs/what-is-the-national-dpp.html
- 2023 International Evidence-Based PCOS Guideline: lifestyle management, healthy eating, physical activity, and behavior strategies are core PCOS supports.
  - https://www.asrm.org/practice-guidance/practice-committee-documents/recommendations-from-the-2023-international-evidence-based-guideline-for-the-assessment-and-management-of-polycystic-ovary-syndrome/
- CDC breastfeeding nutrition: breastfeeding mothers generally require additional calories, so wife/breastfeeding mode must avoid crash-diet outputs.
  - https://www.cdc.gov/breastfeeding-special-circumstances/hcp/diet-micronutrients/maternal-diet.html
- FDA food allergen labeling: milk, egg, fish, crustacean shellfish, tree nuts, peanuts, wheat, soybeans, and sesame are major allergen categories; unknown packaged-food status must remain label-check, not safe.
  - https://www.fda.gov/food/nutrition-food-labeling-and-critical-foods/food-allergies
- USDA FoodData Central API: default authoritative source for generic nutrient lookup in nutrition scoring.
  - https://fdc.nal.usda.gov/api-guide.html

## Required v3 improvements

### 1. Nutrition scoring engine

Implement recipe-level scoring fields:

- protein_score: high / medium / low
- fiber_score: high / medium / low
- sodium_risk: low / medium / high / label_check
- added_sugar_risk: low / medium / high / label_check
- saturated_fat_risk: low / medium / high / label_check
- vegetable_volume: high / medium / low
- calorie_density: low / moderate / high
- Robert fit: default / limit / treat
- wife fit: compatible / needs_addon / not_ideal
- toddler fit: safe / prep_required / not_safe / label_check

Machine gate: every recipe must have all fields populated before delivery.

### 2. USDA-compatible ingredient map

Add a local generic nutrient map with optional USDA FoodData Central lookup support. Packaged foods remain approximate or `needs_label_check` unless label data is provided.

Machine gate: no recipe may claim precise nutrition unless ingredient source and quantity basis are recorded.

### 3. Shopping-gap engine

For any inventory, output:

- can-cook-now recipes
- use-first perishables
- limiting ingredients
- buy-next items that unlock the most meals
- do-not-prioritize items already abundant

Machine gate: buy-next recommendations must cite the recipes unlocked by each item.

### 4. Recipe diversity controller

Support at least these recipe types:

- bowl
- soup/stew
- pasta
- sheet-pan meal
- oven/slow-cooker meal
- salad/slaw plate
- tacos/tostadas
- breakfast
- toddler soft meal
- leftover conversion

Machine gate: no batch should be more than 40% bowls/stews unless user explicitly requests that.

### 5. Web recipe retrieval with citations

Add a web mode that searches external recipes, extracts title/source/ingredients, rejects or adapts unsafe recipes, and cites each accepted external source.

Machine gate: no external-recipe claim without an actual retrieved URL/source.

### 6. Allergy adversarial fixtures

Add test fixtures requiring fail-closed behavior:

- Greek yogurt recipe for shared family -> adult-only / reject shared-safe
- egg breakfast for egg-allergy child -> reject shared-safe
- flour tortilla tacos -> not wheat-free unless replacement specified
- crusted flounder -> needs label check
- BBQ ribs with sugary sauce -> Robert limit/treat
- canned chili meal -> sodium risk high
- rotisserie chicken meal -> sodium risk medium/high
- lentil tomato GF pasta -> Robert default if GF and low sodium
- pork loin bean bowl -> Robert default
- toddler grape snack -> prep required

Machine gate: all unsafe shared cases must fail closed.

### 7. CLI receipts and run audit

Every cartridge runner execution must produce:

- stdout log
- stderr log
- run receipt JSON
- input inventory SHA
- output recipe SHA
- mode requested
- gates passed/failed

Machine gate: missing receipt or missing output is a failure.

## Acceptance criteria for v3

The v3 upgrade is not complete until:

1. Nutrition scoring is present for every recipe.
2. Allergy gates fail closed on all adversarial fixtures.
3. Shopping-gap logic produces use-first/can-cook-now/buy-next/do-not-prioritize sections.
4. External recipe mode requires citations and rejects unsafe recipes.
5. Recipe diversity controller is enforced.
6. Runtime receipts are written for every run.
7. A cartridge packet and tests are committed together.
