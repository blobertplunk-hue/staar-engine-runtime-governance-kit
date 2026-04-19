# STAAR ADAPTIVE ENGINE — STANDARD OPERATING PROCEDURE
## Invariants, Architecture, and Ground-Up Build Guide for Any TEKS

**Version:** v32 | **Author:** Reverse-engineered from staar_engine_v32_chooser_fixed.html  
**Purpose:** Any LLM can follow this document to build a correct, complete, STAAR-aligned adaptive practice engine for any TEKS standard from scratch.

---

## PART 1 — WHAT THIS IS

A STAAR Engine is a single self-contained HTML file that:
- Generates unlimited practice questions covering every item format STAAR has ever used for one TEKS
- Adapts question selection based on the student's error patterns
- Matches the exact visual and interaction conventions of the Cambium STAAR platform
- Runs on any device with no server, no login, no external dependencies

---

## PART 2 — NON-NEGOTIABLE INVARIANTS

These rules apply to every STAAR Engine regardless of TEKS. Violating any of them produces a broken or misleading engine.

### INVARIANT 1 — STAAR FORMAT PARITY
Every item format that has appeared on released STAAR tests for the target TEKS MUST be represented in the engine. You must read all released items before writing any generator code. Do not guess what STAAR asks. Read the items.

**How to find released items:** Search "STAAR released test [grade] [subject] [year]" on tea.texas.gov or use a lead4ward IQ Analysis document. Collect every item for the target TEKS going back to 2015.

### INVARIANT 2 — CAMBIUM UI CONVENTION
- **Single-answer questions** (MC): choices show a **circle (○)** before each option
- **Two-answer questions** (multiselect): choices show a **square (□)** before each option
- There is **no "Next Question" / "Skip" button**. Students cannot skip. Auto-advance fires after correct answer only.
- The directions line must say "Select one answer." for MC and "Select TWO answers." for multiselect — exactly matching STAAR wording.

### INVARIANT 3 — SPARSE NUMBER MANDATE
STAAR consistently uses numbers with one or more zero places (e.g., 15,090; 40,280; 90,241). A generator that only produces dense numbers (all places nonzero) trains students on the easy case. All number generators must produce sparse numbers at least 40% of the time.

**Sparse number definition:** A 5-digit number where at least one of the four lower places (thousands, hundreds, tens, ones) is zero.

### INVARIANT 4 — VALIDATOR INDEPENDENCE
Every generated item must pass a `validateItem()` check before being shown to a student. The validator must:
- Confirm the correct number of choices (4 for MC, 4–5 for multiselect)
- Confirm the correct number of correct answers (1 for MC, 2 for multiselect)
- Confirm declared answers match marked choices
- Confirm drag-drop answers exist in the answer bank and sum to the target number

**CRITICAL:** The drag-drop validator MUST validate against the item's own declared answers, not a hardcoded expected string. Hardcoding kills every non-matching item silently.

### INVARIANT 5 — NO DEAD FAMILIES
A family listed in the family registry MUST have a working generator. A family whose generator always returns null is a dead family. Dead families cause silent fallback to the simplest item type, producing a narrower question mix than intended without any error signal.

**Test for dead families:** After building, run `runtimeCoverageAudit()` and confirm every family has `familyExposure > 0` after 15 items. Add this check to the teacher panel.

### INVARIANT 6 — DIRECTION COVERAGE
For every representation transformation, both directions must exist as separate item formats:
- Standard form → expanded form ✓
- Expanded form → standard form ✓
- Standard form → expanded notation ✓
- **Expanded notation → standard form ✓** (commonly missed — STAAR 2015 Q1, 2018 Q21)

If STAAR has used both directions, the engine must train both.

### INVARIANT 7 — SYMBOLIC VALIDATOR SCOPE
The symbolic validator (`symbolicValidateItem`) must only validate what it can actually verify. For expression-comparison items (multiselect), do NOT use `safeEvalArithmetic` to determine which choices are "symbolically correct" — complex grouped expressions like `"1,000 + 5,000 + 90"` can fail eval even when mathematically valid. Instead: trust the generator's declared `correctAnswers` and verify that at least one declared answer evaluates to `targetNumber`.

### INVARIANT 8 — ANTI-STARVATION WINDOW
Every question family must appear at least once per `ANTI_STARVATION_WINDOW` items (default: 8). Implement this as a recency check, not a modulo counter. Modulo counters create predictable cycles and cause slot collisions when two modulos align on the same item number.

### INVARIANT 9 — NO LEGACY BYPASS
The adaptive template chooser (`chooseAdaptiveTemplate`) must route ALL item selection through the family router. Any branch that maps error patterns directly to 2–3 legacy templates bypasses 80%+ of the family system and must be removed.

### INVARIANT 10 — ITEM FAMILY COMPLETENESS BEFORE WEIGHTING
Define ALL item families and write ALL generators before writing ANY weighting logic. Weighting a family before its generator exists produces dead weight — a family that appears in probability calculations but never actually generates items.

---

## PART 3 — ARCHITECTURE (what goes in the file, in order)

```
1. HTML shell + CSS
2. Global state variables
3. Student model (mastery, streak, error pattern counters, telemetry)
4. Utility functions (randInt, shuffle, unique, formatNumber, etc.)
5. Number generators (sparse, full, place-part extractors)
6. String builders (makeExpandedFormString, makeExpandedNotationString)
7. Item generators — one function per family
8. Validators (validateItem, symbolicValidateItem)
9. Family registry (COMPOSE_REPRESENTATION_FAMILIES array)
10. Family weights (FAMILY_WEIGHTS object)
11. Misconception-to-family map (MISCONCEPTION_TO_FAMILY)
12. Family chooser (chooseComposeFamilyWeighted) — 5-step pipeline
13. Item renderer (renderItem)
14. Answer submission logic (submitAnswer)
15. Mastery loop + endgame (enterMasteryMode, finishFinalCheck, triggerWin)
16. Adaptive template router (chooseAdaptiveTemplate — always returns "__compose_family_router__")
17. Boot + coverage audit
```

---

## PART 4 — GROUND-UP BUILD PROCESS FOR ANY TEKS

### STEP 0 — READ THE RELEASED ITEMS FIRST
Do not write a single line of code until you have inventoried every released STAAR item for the target TEKS. For each item, record:
- Year and question number
- Item type (MC, multiselect, drag-drop, grid-in)
- The exact format/phrasing of the stem
- The correct answer
- The distractor structure (what makes each wrong answer plausible)
- The misconception each distractor targets

This inventory becomes your family list. You are not inventing families — you are reading them off of real tests.

### STEP 1 — IDENTIFY ITEM FAMILIES
Group the released items into families by what they are testing and how they present it. Each distinct (stimulus type × question direction × response mode) combination is a separate family.

**Example for TEKS 3.2A:**
| Family | Stimulus | Direction | Response |
|---|---|---|---|
| expanded_form_to_standard | Expanded form expression (scrambled) | → standard number | MC |
| standard_to_expanded_form | Standard number | → expanded form | MC |
| standard_to_expanded_notation | Standard number | → notation (d×p) | MC |
| notation_to_standard | Notation expression (d×p) | → standard number | MC |
| unit_language_to_standard | Word-unit description | → standard number | MC |
| unit_overflow_compose | Overflowing unit counts | → standard number | MC |
| place_label_mapping | Number + coefficient slots | → place name labels | Drag-drop |
| partial_plausible_multiselect | Standard number | → which 2 of 5 are equivalent | Multiselect |
| regrouped_correct | Standard number | → which is a valid non-canonical form | MC or MS |
| regrouped_near_miss | Standard number | → which split is valid (near-miss traps) | MC |
| truth_judgment | Standard number | → which statement is true (or NOT true) | MC |
| error_analysis | Wrong student expression | → what error was made | MC |
| notation_discrimination | Standard number | → which uses expanded notation (not form) | MC |

### STEP 2 — DEFINE MISCONCEPTION TAXONOMY
Identify 2–4 core misconceptions that cut across all families. Every family targets at least one misconception. This drives adaptive routing.

**Example for 3.2A:**
- `unit_to_digit_confusion` — treats a coefficient as a digit (70 hundreds → 70,___ instead of 7,000+___)
- `place_value_misalignment` — maps coefficient to wrong place (shifts left or right)
- `partial_decomposition_acceptance` — accepts an incomplete decomposition as correct

### STEP 3 — BUILD UTILITY LAYER FIRST
Before any generators, build:
- `randInt(min, max)`
- `shuffle(arr)` — Fisher-Yates, returns new array
- `unique(arr)` — deduplicates
- `formatNumber(n)` — locale string with commas
- `nonzeroPlaceParts(n)` — returns `[{digit, place, value}, ...]` for each nonzero place
- `makeSparseNumber()` — guarantees at least one zero place
- `makeExpandedFormString(n)` — "10,000 + 200 + 30"
- `makeExpandedNotationString(n)` — "(1 × 10,000) + (2 × 100) + (3 × 10)"

**Test each utility function before building generators.**

### STEP 4 — BUILD ONE GENERATOR PER FAMILY
Each generator is a function that:
1. Generates a number (use `makeSparseNumber()` ~50% of the time)
2. Constructs the correct answer
3. Constructs 3 wrong answers (for MC) or 3–4 traps + 2 correct (for multiselect)
4. Calls `unique()` on all choices and returns null if fewer than required unique choices exist
5. Returns a complete item object

**Item object schema (required fields):**
```javascript
{
  id: string,              // unique: templateId + Date.now() + random
  templateId: string,      // matches composeMC allowlist
  family: string,          // matches COMPOSE_REPRESENTATION_FAMILIES
  itemType: "multiple_choice" | "multiselect" | "drag_and_drop",
  skill: string,
  pattern: string,         // misconception key
  stem_en: string,
  stem_es: string,
  directions_en: string,   // "Select one answer." or "Select TWO answers."
  directions_es: string,
  visual: { type: "equation", text: string },
  answerKey: {
    mode: "single_select" | "multi_select_exact" | "ordered_text_list",
    correctAnswers: string[]
  },
  meta: { correctValue?: number, targetNumber?: number, notationExpr?: string },
  choices: [{ text: string, correct: boolean }]
}
```

**Generator return contract:**
- Return the complete item object on success
- Return `null` if uniqueness checks fail or inputs are degenerate
- Never throw — return null on edge cases

### STEP 5 — BUILD VALIDATORS
Build `validateItem(item)` before wiring up the chooser. The router loop calls this after every generation attempt and discards FAIL items. Without it, bad items reach students.

```
validateItem checks:
✓ Correct choice count (4 for MC, 4-5 for multiselect, 3 answers for drag-drop)
✓ Correct answer count (1 for MC, 2 for multiselect)
✓ Declared answers match marked choices
✓ templateId is in the composeMC allowlist
✓ Drag-drop: answers in bank, coefficients × declared places = targetNumber
✓ Symbolic spot-check for expression items (at least one correct eval to target)
```

### STEP 6 — BUILD THE FAMILY REGISTRY AND WEIGHTS
```javascript
const COMPOSE_REPRESENTATION_FAMILIES = [ /* all family names */ ];

const FAMILY_WEIGHTS = {
  // Higher = more frequent
  // Families targeting STAAR-confirmed trap types: weight 8-10
  // Families covering every STAAR format: weight 6-8
  // Supplementary families: weight 4-6
};

const MISCONCEPTION_TO_FAMILY = {
  misconception_key: ["family1", "family2", ...],
  ...
};
```

### STEP 7 — BUILD THE CHOOSER (5-step pipeline)
```
Step 1: Anti-starvation — force any family not seen in last N items
Step 2: Misconception priority — restrict pool if any error count ≥ 2
Step 3: Domination prevention — exclude families with > 1.5× average exposure
Step 4: Dedup — exclude the last chosen family
Step 5: Weighted sample from remaining pool
```

After every pick: update `familyExposure[chosen]++` and `familyLastSeen[chosen] = currentIndex`.

### STEP 8 — BUILD THE RENDERER
The renderer (`renderItem`) must:
- Set `data-shape="circle"` on all MC choice buttons
- Set `data-shape="square"` on all multiselect choice buttons
- Clear prior state (selected, feedback, visual visibility)
- Show answer bank for drag-drop items

### STEP 9 — BUILD SUBMIT + ADAPTIVE ROUTING
- On correct: update student model, advance mastery, auto-advance after delay
- On wrong: show structure support, increment pattern error counter, do NOT auto-advance
- `chooseAdaptiveTemplate()` must always return `"__compose_family_router__"` — no legacy bypass

### STEP 10 — ADD TEACHER PANEL + COVERAGE AUDIT
The teacher panel must show:
- Per-family exposure counts (so you can see dead families at a glance)
- STAAR trap family coverage (warns if any critical family is at zero after N items)
- Student model state
- Last item raw JSON

`runtimeCoverageAudit()` runs at boot and logs any family with zero coverage.

---

## PART 5 — DISTRACTOR DESIGN RULES

For every family, each wrong answer must target a specific, real misconception. Distractors must be:

1. **Plausible** — a student with a specific misconception would choose it
2. **Exclusive** — it must not evaluate to the correct answer
3. **Distinct** — all 4 choices must be unique strings and unique values

**Distractor patterns by family type:**

| Family type | Required distractor types |
|---|---|
| Standard → expanded form | Wrong place (digit instead of value), truncated (missing last place), notation instead of form |
| Expanded form → standard | Off by one place (shift), concatenation of digits, partial sum |
| Unit overflow | Concatenation of coefficients, digit-only (ignores multiplier), shifted place |
| Notation → standard | Off by one place unit, missing last place, last digit as ones not value |
| Multiselect equivalence | Missing one place, last place shifted, extra place added |
| Truth judgment / NOT | Swap tens↔ones, wrong digit for a place, drop one place |
| Error analysis | Blame wrong place, correct opposite diagnosis, "it's fine" |

---

## PART 6 — COMMON FAILURE MODES (and how to prevent them)

| Failure | Symptom | Prevention |
|---|---|---|
| Hardcoded validator | Drag-drop always fails, falls back to MC | Never hardcode expected answers in validator |
| Dead family | One family never appears despite being in registry | Check for generator body before adding to registry |
| Legacy bypass | Only 2–3 question types appear | `chooseAdaptiveTemplate` must always return `"__compose_family_router__"` |
| Modulo starvation | Families only appear every Nth question, many turns with nothing | Use anti-starvation window, not modulo |
| Dense-only numbers | Students never practice sparse-place items | `makeSparseNumber()` used ≥40% of the time |
| Symbolic validator over-reach | Valid expressions fail validation | Use declared answers as truth source, not arithmetic re-eval |
| Missing direction | Kids see notation → standard on STAAR but never practiced it | Both directions required for every transformation family |
| Regrouped-correct multiselect only | STAAR had it as MC in 2016 | Build both MC and multiselect variants |
| Skip button present | Kids skip hard items | No skip button. Auto-advance on correct only. |
| Wrong selector shape | Kids don't know how many answers to select | MC = circles, multiselect = squares (matches Cambium) |

---

## PART 7 — CHECKLIST BEFORE SHIPPING

Run through this before giving the file to students:

```
□ Every released STAAR item format (back to 2015) has a generator
□ makeSparseNumber() is used ≥40% of the time in all generators
□ No generator returns null for all inputs (test each one manually)
□ validateItem() rejects items with wrong choice counts
□ Drag-drop validator uses item's own declared answers, not hardcoded string
□ chooseAdaptiveTemplate() always returns "__compose_family_router__"
□ No Next Question / Skip button
□ MC choices have data-shape="circle"
□ Multiselect choices have data-shape="square"
□ Both directions covered for every transformation (standard→X AND X→standard)
□ runtimeCoverageAudit() shows 0 missing families at boot
□ Teacher panel shows per-family exposure counts
□ Bilingual (EN + ES) for all stems and directions
□ Brace balance in JS (open count === close count)
□ File loads and generates first item within 1 second on mobile
```

---

## PART 8 — HOW TO ADAPT THIS TO ANY TEKS

### Phase 1: Research (before any code)
1. Pull all released STAAR items for the target TEKS (2015–present)
2. Build the item inventory table (year, format, stem, correct answer, distractor analysis)
3. Identify item families from the inventory
4. Identify 2–4 core misconceptions
5. Map each family to the misconceptions it targets

### Phase 2: Design
6. Define the family registry (names, weights, misconception mapping)
7. Define the number/value generator appropriate to the TEKS domain
8. Define the distractor patterns for each family
9. Define the visual support (what the structure hint shows)

### Phase 3: Build (in strict order)
10. Utility layer
11. Domain-specific generators (e.g., fraction builders, coordinate generators)
12. Item generators — one per family
13. Validators
14. Family registry, weights, misconception map
15. Chooser
16. Renderer + submit logic
17. Mastery loop
18. Teacher panel + coverage audit

### Phase 4: Audit
19. Run the audit: every released item format covered? Both directions? Sparse inputs?
20. Play 20 questions and check teacher panel — every family appeared?
21. Fix any dead families, broken validators, or missing directions
22. Ship

---

## PART 9 — DOMAIN TEMPLATES FOR OTHER TEKS

### For fraction standards (e.g., 3.3A, 4.3A)
Number generator: fraction generator — `{numerator, denominator, value}`. Families: identify fraction on number line, equivalent fractions, compare fractions, compose from unit fractions. Misconception map: numerator-denominator confusion, benchmark confusion, part-whole vs part-group.

### For multiplication/division (e.g., 3.4A, 3.4K)
Number generator: factor pair generator. Families: array model, area model, equation completion, fact family, word problem structure. Misconception map: addition confusion, skip-count error, partial product.

### For geometry (e.g., 3.6A)
Stimulus generator: shape attribute list. Families: classify by attribute, identify by name, sort into categories, explain why not. Misconception map: prototype fixation (only equilateral triangles are triangles), orientation confusion.

### For data/graphs (e.g., 3.8A)
Stimulus generator: dataset generator with deliberate near-miss values. Families: read single bar, compare two bars, find total, find difference, what changed. Misconception map: read label vs value, axis scale confusion, off-by-one bar reading.

---

*This SOP was reverse-engineered from staar_engine_v32_chooser_fixed.html, which implements TEKS 3.2A place value. The architecture, invariants, and failure modes documented here apply universally.*
