# Improvement: Visual Forensics, User Corrections, and Artifact Intent Need Stronger Gates

**Date:** 2026-06-02  
**System:** MetaBlooms OS — visual planning, forensic scene reconstruction, image generation, artifact delivery intent  
**Priority:** HIGH  
**Source:** ChatGPT garden/backyard buffalo-grass planning session  
**Status:** OPEN

---

## Problem Statement

During the backyard/garden analysis workflow, image generation was used for a spatial planning task before the scene model was sufficiently locked. The generated map contradicted user-provided facts: wrong compass orientation, wrong swing-set side, wrong raised-bed count, wrong bed sizes, wrong bed distance from fence, wrong overgrown-corner placement, and an oversized buffalo grass zone.

The user then supplied corrections and annotated images. Those corrections improved the output, but the workflow did not have a machine-enforced correction ledger or generated-map QA gate. The session also showed a separate artifact-intent gap: when the user asked for a plan "as markdown," the system first returned inline markdown instead of immediately creating a downloadable `.md` file.

---

## Gaps

### Gap 1 — Spatial inference from photos is overconfident

**Impact:** A generated plan can appear authoritative while being spatially wrong.

**Root cause:** No required forensic scene reconstruction schema separates direct visual evidence, user-stated facts, inference, uncertainty, and contradicted assumptions.

### Gap 2 — User corrections do not automatically supersede prior assumptions

**Impact:** Once the user corrects map facts, prior visual assumptions may remain active and contaminate later outputs.

**Root cause:** No durable user-correction supersession ledger for spatial/visual workflows.

### Gap 3 — Image generation is not gated for planning accuracy

**Impact:** Image generation can be triggered as if it were a deterministic planning renderer. It may invent extra objects or move landmarks.

**Root cause:** No visual-planning image gate requires structured scene evidence and user confirmation before generating map-like outputs.

### Gap 4 — Generated visual artifacts lack deterministic QA

**Impact:** Wrong maps are presented even when they fail simple checks: number of beds, compass orientation, swing-set side, grass-zone extent, and user-stated path placement.

**Root cause:** No generated-artifact validator for image/layout outputs.

### Gap 5 — Markdown/file artifact intent is under-detected

**Impact:** The user asked for a markdown plan intended as a downloadable file, but the first response was inline.

**Root cause:** No markdown artifact intent detector treats "as markdown" / "markdown plan" as a default downloadable `.md` request.

---

## Desired State

1. Photo-forensic workflows must build a structured evidence table before producing maps or plans.
2. User corrections become explicit constraints that supersede model inference and generated images.
3. Image generation for planning outputs is marked illustrative unless validated against a correction ledger.
4. Generated planning images must pass deterministic QA before being presented as useful.
5. Markdown plan requests create downloadable `.md` artifacts by default.

---

## Action Items

### Immediate

- [ ] **V1:** Add `forensic_scene_reconstruction_schema` with fields: object, direct evidence, user-stated correction, confidence, conflict status, and map impact.
- [ ] **V2:** Add `user_correction_supersession_ledger` for spatial workflows. Any correction becomes a durable constraint; contradicted generated artifacts are marked stale/superseded.
- [ ] **V3:** Add `visual_planning_image_gate`: do not generate final maps until fixed anchors, object counts, compass directions, and uncertainty flags are explicitly recorded.
- [ ] **V4:** Add generated visual QA checks for map-like outputs: object counts, orientation, user-stated positions, labels, and forbidden contradictions.
- [ ] **V5:** Add a `markdown_artifact_intent_gate`: if a user asks for "as markdown", "markdown plan", or "turn this into markdown", create a downloadable `.md` file unless inline-only is explicitly requested.

### Medium-term

- [ ] **V6:** Add a deterministic SVG/HTML map renderer for planning diagrams where exact object counts and locations matter. Use image generation only as illustrative art, not as authoritative geometry.
- [ ] **V7:** Add a stale-artifact marker that flags prior generated images after user corrections so they are not reused as authority.

---

## Durable Corrections Captured from the Session

```text
North = house/patio side.
South = long/back fence and water-tower/background-fence side.
East = swing set / play area side, by fence and up by patio.
West = opposite side yard / gate path side.
Exactly two raised beds.
One raised bed is larger; one is smaller.
Beds are about 8 ft from south/back fence.
Most non-red-highlighted area is mulch.
Overgrown corner is mulch, not buffalo grass.
Buffalo grass footprint is the user's red-marked zone, not the large prior generated area.
There is a sidewalk/path from patio to west-side gate.
```

---

## Evidence

- User explicitly rejected the generated map as wrong on orientation, bed count, bed sizing, swing-set position, overgrown-corner placement, and buffalo-zone size.
- User supplied corrected orientation: swing-set panorama is east; fence/water-tower panorama is south; open-sky panorama is east.
- User supplied corrected geometry: beds are about 8 ft from fence; black lines indicate sidewalk from patio to gate; red areas indicate buffalo grass; most highlighted area is mulch.
- User clarified downloadable markdown intent after inline output: "turn this into a markdown file that I can download."
