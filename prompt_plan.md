## Development outline (step-by-step)

1. **Repo + tooling foundation**

   * Create project skeleton (`modules/`, `training/`, `tests/`, `config/`).
   * Add `pytest`, formatting/linting basics, and a minimal CI workflow.
   * Define “domain objects” (dataclasses) that every module will share:

     * `PartFeatures`, `FeatureConfidence`, `DfmIssue`, `QuoteResult`, `ProcessingResult`.

2. **Configuration + environment**

   * Centralize settings: paths (`DATABASE_PATH`, `UPLOADS_PATH`, `TEMP_PATH`), limits (`MAX_UPLOAD_SIZE`, bbox limits), and static dropdown options.
   * Implement config loader for `pricing_coefficients.json` with strict validation.

3. **Database layer (training)**

   * Provide a small DB module:

     * create/open SQLite DB
     * ensure `training_parts` exists
     * insert a training record
     * query training rows (for training script)
   * Tests: schema creation, inserts, and simple query round-trips.

4. **CAD I/O primitives**

   * Implement `load_step(path) -> cadquery.Shape/Workplane` with clear error types.
   * Tests: generate simple CAD in tests via cadquery → export STEP → reload.

5. **File handling**

   * Validate upload: extension, size, readable STEP, has solid.
   * Persist STEP to `/uploads/<uuid>.step`.
   * Return a `part_id` and stored path.
   * Tests: invalid extension, oversized bytes, corrupted STEP, no-solid STEP.

6. **Feature detection MVP v0**

   * Compute **bounding box** + **volume** (100% confidence).
   * Enforce bounding box max (600×400×500mm) early.
   * Tests: known box dimensions; volume matches expected (with tolerance).

7. **Pricing engine MVP**

   * Load coefficients JSON, normalize features using stored scaler, compute per-unit + total with minimum order.
   * Handle “model not trained” (`r_squared == 0`) and missing keys.
   * Tests: deterministic config fixture with known means/stds/coeffs.

8. **Processing pipeline (glue)**

   * Build a single orchestration function:

     * `process_quote(step_path, quantity) -> ProcessingResult`
   * Tests: end-to-end happy path using generated STEP.

9. **Streamlit UI skeleton**

   * Single-page app:

     * upload + progress messages
     * quantity input
     * show bbox/volume + price result (even before holes/pockets exist)
   * Keep UI thin; all logic stays in modules.

10. **STL conversion + viewer**

* Implement STEP→STL conversion with adaptive deflection.
* Add Streamlit component wrapper that renders a Three.js viewer (local STL).
* Tests: conversion creates non-empty STL; HTML builder produces expected markup.

11. **Feature detection v1: holes**

* Implement cylindrical face detection and hole grouping.
* Classify **through vs blind**.
* Compute blind-hole depth/diameter ratios (avg/max).
* Compute non-standard holes vs `STANDARD_HOLE_SIZES`.
* Tests: generate parts with known hole sets (through + blind, standard + non-standard).

12. **Feature detection v1: pockets**

* Start narrow: detect *simple prismatic pockets* aligned to primary axes (good MVP constraint).
* Compute pocket count, depths, and approximate pocket volumes.
* Tests: generated pocket part with known depth(s).

13. **DFM analyzer MVP**

* Implement checks in increasing difficulty:

  * deep holes ratio thresholds (easy, derived from blind holes)
  * small features threshold (derived from smallest detected hole diameter for MVP)
  * tight pocket internal corner flag (only if detectable; otherwise “unknown” and manual review)
  * thin walls / sharp corners: initially “not implemented” but structured for later
* Tests: deep hole warning/critical triggers; small feature triggers.

14. **PDF generation**

* Generate PDF page 1 summary + warnings + breakdown.
* Page 2: embed a simple isometric raster from STL (headless-safe approach).
* Tests: PDF bytes non-empty, contains key strings (via PDF text extraction).

15. **Training script**

* Read DB → train `StandardScaler` + `LinearRegression` → write `pricing_coefficients.json`.
* Tests: small synthetic dataset yields nonzero R² and writes config.

16. **Deployment hardening**

* Add Render start command, persistent disk notes, env var documentation.
* Add runtime guards (missing cadquery deps, missing config, etc.).

---

## First breakdown: iterative blocks that build on each other

### Block A — “Runs locally with tests”

* Repo structure + pytest + shared dataclasses
* Settings/config loader
* DB layer (schema + insert/query)

### Block B — “Can ingest STEP safely”

* STEP loader utility
* File validation + storage by UUID
* Bounding box limit enforcement

### Block C — “Can quote (even with limited features)”

* Feature detection: bbox + volume
* Pricing engine with config + normalization + minimum
* End-to-end pipeline tests

### Block D — “UI for internal testing”

* Streamlit skeleton wired to pipeline
* Clear error states and progress indicators

### Block E — “3D preview”

* STEP→STL conversion
* Three.js viewer embedding

### Block F — “Feature coverage for MVP”

* Holes: through + blind + non-standard
* Pockets: simple prismatic pockets (explicit MVP constraint)
* Confidence scoring

### Block G — “DFM + outputs”

* DFM checks (start with deep holes)
* PDF generation
* mailto “manual review” link

### Block H — “Training workflow”

* Train script reads DB, writes coefficients JSON
* App displays R² score

---

## Second breakdown: make blocks smaller (implementation-sized steps)

### Block A micro-steps

1. Add `modules/__init__.py`, `tests/`, `pyproject.toml` or `requirements-dev.txt`, pytest config.
2. Create `modules/domain.py` dataclasses + unit tests for serialization (dict conversion).
3. Create `modules/settings.py` reading env vars + defaults + tests.

### Block B micro-steps

4. Implement `modules/cad_io.py: load_step()` with typed exceptions + tests with generated STEP.
5. Implement `modules/file_handler.py: validate_extension/size()` + tests.
6. Implement `store_upload(bytes, original_name) -> StoredFile` (uuid path) + tests.
7. Add “parse STEP and ensure solid” validation + tests.
8. Add bbox limit check + tests.

### Block C micro-steps

9. Implement `feature_detector.py` with `detect_bbox_volume()` + tests.
10. Add `pricing_engine.py` config validation + tests.
11. Add `calculate_quote(features, quantity)` + tests (min order, q>50 message, model not trained).
12. Add `pipeline.py: process_quote()` + end-to-end test.

### Block D micro-steps

13. Build Streamlit UI layout + wire upload to `store_upload()` (no viewer yet).
14. Add progress messages + show computed bbox/volume + quote.
15. Add “quantity” re-run logic (cached features, recompute price).

### Block E micro-steps

16. Implement `visualization.py: step_to_stl()` + tests.
17. Implement `visualization.py: build_viewer_html(stl_url_or_bytes)` + tests.
18. Integrate viewer into Streamlit (component) + basic manual smoke check.

### Block F micro-steps

19. Add hole candidate detection (cylindrical faces) + tests on simple geometry.
20. Add through vs blind classification + tests.
21. Add non-standard hole matching + tests.
22. Add blind hole depth/diameter ratios + tests.
23. Add pocket detection v0 (count/depth only) + tests.
24. Add pocket volume approximation + tests.
25. Add confidence scores per feature + tests.

### Block G micro-steps

26. Add DFM deep-hole checks + tests.
27. Add small-feature checks + tests.
28. Add tight pocket corner flag (if detectable) or “unknown” behavior + tests.
29. Add PDF generator page 1 + tests.
30. Add PDF page 2 image from STL + tests.
31. Add mailto link builder + tests.
32. Integrate DFM + PDF + mailto into UI.

### Block H micro-steps

33. Implement `training/train_model.py` core functions (load df, train, write json) + tests with synthetic DB.
34. Add CLI entrypoint + docs.
35. App displays model R² + “last_updated”.

At this point, each step is:

* small enough to test (unit/integration),
* big enough to produce visible progress,
* and always connected to the pipeline/UI (no orphan code).

---

## Prompts for a code-generating LLM (test-driven, incremental)

### `text` Prompt 01 — Project scaffold + test harness ✅ COMPLETE

You are implementing **Tiento Quote v0.1** in Python. Create the repo skeleton and testing harness.

**Do this (TDD):**

1. Add folders: `modules/`, `training/`, `tests/`, `config/`.
2. Make `modules/` a package (`__init__.py`).
3. Add `pytest` configuration (e.g., `pytest.ini`) and a minimal CI workflow (GitHub Actions) that runs `pytest`.
4. Add a `requirements.txt` and `requirements-dev.txt` (or equivalent). Include at least: `pytest`, `cadquery`, `numpy`, `pandas`, `scikit-learn`, `reportlab`, `streamlit`.

**Acceptance:**

* `pytest` runs successfully with a placeholder test.
* CI config exists and points to `pytest`.

**Implementation Notes:**
- Created full project structure with modules/, training/, tests/, config/
- Added pytest.ini with sensible defaults
- Created GitHub Actions CI workflow (.github/workflows/ci.yml)
- Added requirements.txt with all production dependencies
- Added requirements-dev.txt with testing/linting tools
- Created 3 placeholder tests - all passing
- Added .gitignore for Python project

---

### `text` Prompt 02 — Shared domain models (dataclasses) ✅ COMPLETE

Create `modules/domain.py` with shared dataclasses that will be used across the app:

* `PartFeatures` (all feature fields from spec; default zeros)
* `FeatureConfidence` (per-feature confidence 0–1)
* `DfmIssue` (`severity`: `"critical"|"warning"|"info"`, `message`)
* `QuoteResult` (per-unit, total, breakdown dict, flags)
* `ProcessingResult` (part_id, stored paths, features, confidence, dfm_issues, quote, errors list)

**TDD:**

* Add unit tests verifying:

  * defaults are correct
  * `.to_dict()` / `.from_dict()` round-trip works (implement these methods)

**Acceptance:**

* All tests pass; no business logic yet.

**Implementation Notes:**
- Created modules/domain.py with 5 dataclasses
- PartFeatures: 13 fields covering all features from spec, all default to 0
- FeatureConfidence: 5 confidence scores (0.0-1.0)
- DfmIssue: severity (Literal type) + message
- QuoteResult: pricing with breakdown dict
- ProcessingResult: complete result container with optional quote
- All dataclasses have to_dict() and from_dict() methods
- Comprehensive test suite with 27 tests covering defaults, custom values, serialization, and round-trips
- All tests passing (30/30 total)

---

### `text` Prompt 03 — Settings + env var handling ✅ COMPLETE

Create `modules/settings.py` with a `Settings` dataclass that reads:

* `DATABASE_PATH`, `UPLOADS_PATH`, `TEMP_PATH`, `MAX_UPLOAD_SIZE`
* bounding box max dims (hardcode from spec)
* quantity limits (1–50)
  Provide `get_settings()` with caching-safe behavior.

**TDD:**

* Tests for default values when env vars missing
* Tests that env vars override defaults

**Acceptance:**

* Other modules can import `get_settings()` without side effects.

**Implementation Notes:**
- Created modules/settings.py with Settings dataclass
- Environment variable support with sensible defaults:
  * DATABASE_PATH: "training/training_data.db"
  * UPLOADS_PATH: "uploads"
  * TEMP_PATH: "temp"
  * MAX_UPLOAD_SIZE: 52428800 (50MB)
- Hardcoded values from spec (not overridable):
  * BOUNDING_BOX_MAX: 600×400×500mm
  * QUANTITY limits: 1-50
  * MINIMUM_ORDER_PRICE: €30
- Implemented get_settings() with global caching
- __post_init__ reads env vars and overrides defaults
- 22 comprehensive tests covering defaults, overrides, caching, validation
- All tests passing (52/52 total)

---

### `text` Prompt 04 — Pricing config loader + validation ✅ COMPLETE

Create `modules/pricing_config.py`:

* `load_pricing_config(path) -> dict` with strict validation:

  * required keys: base_price, minimum_order_price, coefficients, r_squared, scaler_mean, scaler_std
  * coefficients must include all required feature names from `PartFeatures`

**TDD:**

* Tests:

  * valid config loads
  * missing keys raises a clear exception
  * coefficients missing a feature raises

**Acceptance:**

* Loader returns a validated dict ready for pricing.

**Implementation Notes:**
- Created modules/pricing_config.py with load_pricing_config() function
- Defined REQUIRED_COEFFICIENT_FEATURES constant with 10 pricing features:
  * volume, through_hole_count, blind_hole_count
  * blind_hole_avg_depth_to_diameter, blind_hole_max_depth_to_diameter
  * pocket_count, pocket_total_volume, pocket_avg_depth, pocket_max_depth
  * non_standard_hole_count
- Custom PricingConfigError exception for clear error messages
- Strict validation of all required keys and features
- Created config/pricing_coefficients.json template (untrained model)
- 15 comprehensive tests covering:
  * Valid configs load successfully (including R²=0)
  * Missing keys raise clear exceptions
  * Missing features in coefficients raise
  * Invalid JSON and file not found handled
- All tests passing (67/67 total)

---

### `text` Prompt 05 — SQLite DB module (training schema) ✅ COMPLETE

Create `modules/db.py`:

* `connect(db_path)`
* `ensure_schema(conn)` creates `training_parts` table if missing (per spec)
* `insert_training_part(conn, row_dict)`
* `fetch_training_parts(conn) -> pandas.DataFrame`

**TDD:**

* Use a temporary sqlite file in tests:

  * schema is created
  * insert then fetch returns expected columns

**Acceptance:**

* No Streamlit dependency in DB code.

**Implementation Notes:**
- Created modules/db.py with 4 functions for training data management
- connect(): Simple SQLite connection wrapper
- ensure_schema(): Creates training_parts table with exact schema from spec:
  * 19 columns: id, file_path, upload_date, quantity, pricing, features
  * Auto-incrementing ID
  * Proper defaults (0 for optional feature fields)
  * Idempotent (safe to call multiple times)
- insert_training_part(): Dynamic INSERT based on row_dict keys
- fetch_training_parts(): Returns pandas DataFrame with all columns
- No Streamlit dependency - pure SQLite + pandas
- Comprehensive test suite (16 tests):
  * Connection creation and reuse
  * Schema validation (correct columns)
  * Insert minimal and full feature sets
  * Fetch empty and populated tables
  * Integration test for complete workflow
- All tests passing (83/83 total)

---

### `text` Prompt 06 — CAD I/O utility: load STEP ✅ COMPLETE

Create `modules/cad_io.py`:

* `load_step(step_path)` that attempts to import STEP via cadquery
* Raise a custom exception `StepLoadError` with a helpful message

**TDD:**

* In tests, generate a simple cadquery box, export it to STEP in a temp dir, then load it and assert it returns a shape/solid.
* Also test that loading a non-STEP file raises `StepLoadError`.

**Acceptance:**

* This becomes the single entrypoint for STEP parsing.

**Implementation Notes:**
- Created modules/cad_io.py with STEP file loading functionality
- StepLoadError custom exception with helpful error messages
- load_step(step_path) function:
  * Uses cadquery.importers.importStep()
  * Returns cadquery Workplane (wraps if needed)
  * Comprehensive error handling:
    - File not found (helpful message includes path)
    - Empty file detection
    - Invalid STEP format (parse errors)
    - Generic load errors with context
  * All errors wrapped in StepLoadError with helpful messages
- Single entrypoint for all STEP parsing in the application
- Comprehensive test suite (14 tests):
  * Load valid STEP files (simple boxes)
  * Verify loaded geometry is correct (Workplane, solid, volume)
  * Complex geometries (boxes with holes, multiple operations)
  * Error cases: nonexistent, invalid, non-STEP, empty files
  * Exception behavior validation
- All tests passing (97/97 total)

---

### `text` Prompt 07 — File validation helpers (extension/size)

Create `modules/file_handler.py` (start small):

* `validate_extension(filename)`: only `.step`/`.stp`
* `validate_size(num_bytes, max_bytes)`
  Return errors as exceptions with spec-aligned messages.

**TDD:**

* Tests for valid/invalid extensions
* Tests for boundary size exactly max vs max+1

**Acceptance:**

* Pure functions; no filesystem yet.

---

### `text` Prompt 08 — Store upload to /uploads with UUID

Extend `modules/file_handler.py`:

* `store_upload(file_bytes, original_filename, uploads_dir) -> (part_id, stored_path)`
* Use UUID v4 naming; preserve `.step` extension.
* Ensure uploads_dir exists.

**TDD:**

* Test writes file, returns UUID-like string, and file exists with same bytes.

**Acceptance:**

* No STEP parsing yet in this step.

---

### `text` Prompt 09 — Upload validation: STEP parse + solid presence

Extend `modules/file_handler.py`:

* Add `validate_step_geometry(step_path)` that uses `cad_io.load_step()`
* Reject if no solid geometry (define a reasonable check)
* Use spec error message: “File requires manual review - please contact us”

**TDD:**

* Test with a valid exported STEP passes.
* Test with an empty file or garbage bytes fails with the correct message.

**Acceptance:**

* Errors are deterministic and user-friendly.

---

### `text` Prompt 10 — Feature detector v0: bounding box + volume

Create `modules/feature_detector.py`:

* `detect_bbox_and_volume(step_path) -> (PartFeatures, FeatureConfidence)`
  Compute:
* bbox x/y/z in mm
* volume in mm³
  Set confidence for these to 1.0.

**TDD:**

* Generate a known box (e.g., 10×20×30 mm) in tests, export STEP, detect, assert bbox matches (within tolerance) and volume equals 6000 mm³ (within tolerance).

**Acceptance:**

* No holes/pockets yet; those remain zero.

---

### `text` Prompt 11 — Bounding box limit validation (600×400×500)

Add `validate_bounding_box_limits(features, settings)` in `feature_detector.py` or `file_handler.py` (your choice, but keep responsibilities clear).

* Reject oversized parts with the exact spec message.

**TDD:**

* Test a part slightly exceeding X fails.
* Test a part at the exact limit passes.

**Acceptance:**

* This runs before any expensive detection.

---

### `text` Prompt 12 — Pricing engine v0 (config + normalization + min order)

Create `modules/pricing_engine.py`:

* `normalize_features(features_dict, mean, std) -> dict`
* `calculate_quote(part_features: PartFeatures, quantity: int, pricing_config: dict) -> QuoteResult`
  Rules:
* if `r_squared == 0.0`: return/raise “System not ready - training required”
* quantity > 50: return a result with an error/message flag (no quote)
* apply minimum order price (€30 per order)

**TDD:**

* Use a small deterministic config fixture and assert:

  * min order applies
  * quantity scaling works
  * “model not trained” path triggers

**Acceptance:**

* Produces a stable breakdown dict.

---

### `text` Prompt 13 — Pipeline orchestrator (end-to-end core)

Create `modules/pipeline.py`:

* `process_quote(step_path, quantity, pricing_config_path) -> ProcessingResult`
  Sequence:

1. load settings
2. detect bbox+volume
3. validate bbox limits
4. calculate quote
   Return a complete `ProcessingResult`.

**TDD:**

* End-to-end test with a generated STEP and a deterministic pricing config.

**Acceptance:**

* No Streamlit here; purely callable logic.

---

### `text` Prompt 14 — Streamlit app skeleton wired to pipeline

Create `app.py`:

* Header per spec
* STEP upload widget
* quantity input (1–50, autocorrect invalid to 1)
* progress messages for pipeline stages
* display quote summary + disclaimer
  For now, show features (bbox/volume) and quote; holes/pockets remain 0.

**Acceptance (manual):**

* `streamlit run app.py` works locally and you can upload a STEP and see a quote.

---

### `text` Prompt 15 — STEP→STL conversion (visualization module)

Create `modules/visualization.py`:

* `step_to_stl(step_path, stl_path, linear_deflection, angular_deflection)`
* helper to compute adaptive deflection from bbox (per spec)

**TDD:**

* Generate a STEP in tests, convert to STL, assert STL exists and file size > 0.

**Acceptance:**

* Conversion does not crash on simple solids.

---

### `text` Prompt 16 — Three.js viewer component (HTML builder)

In `modules/visualization.py`, add:

* `build_threejs_viewer_html(stl_bytes_or_url) -> str`
  Keep it self-contained HTML using CDN `three.js`, `STLLoader`, `OrbitControls`.

**TDD:**

* Unit test that the HTML contains the expected loader/control strings and a placeholder for STL source.

**Acceptance:**

* Streamlit can render it via `components.html()`.

---

### `text` Prompt 17 — Integrate 3D viewer into Streamlit

Update `app.py`:

* After processing, run STEP→STL into `TEMP_PATH`
* Render the viewer HTML
* Ensure temp STL is cleaned up best-effort at end of run/session

**Acceptance (manual):**

* Model displays; user can rotate/zoom/pan.

---

### `text` Prompt 18 — Feature detection v1: hole candidates (cylindrical faces)

Extend `modules/feature_detector.py`:

* Add internal utilities to find cylindrical faces and estimate diameter.
* Return additional fields:

  * `through_hole_count`
  * `blind_hole_count` (classification comes next step; start by finding candidates only)

**TDD:**

* Create test part with known number of cylindrical holes (cadquery cut operations), export STEP, assert candidate count matches expectation.

**Acceptance:**

* Keep logic conservative; if uncertain, undercount and reduce confidence.

---

### `text` Prompt 19 — Classify through vs blind + ratios + non-standard

Extend hole logic:

* Determine through vs blind by checking if the cylindrical feature opens on two opposite sides (through) or one side (blind).
* Compute blind hole depth and ratios (avg/max depth:diameter).
* Match diameters to `STANDARD_HOLE_SIZES` with ±0.1mm tolerance; count non-standard.

**TDD:**

* Build two test parts:

  1. through holes only (standard sizes)
  2. blind holes with known depth/diameter ratios + a non-standard diameter
* Assert counts and ratio thresholds.

**Acceptance:**

* Populate `FeatureConfidence` for holes (e.g., 0.85–0.95) based on heuristics.

---

### `text` Prompt 20 — Pocket detection v0 (simple prismatic pockets)

Implement **MVP constraint**: only detect prismatic pockets aligned to primary axes (created by planar-face cuts).

Compute:

* `pocket_count`
* `pocket_avg_depth`
* `pocket_max_depth`
  Leave `pocket_total_volume` at 0 for now (next step).

**TDD:**

* Generate a block with one rectangular pocket of known depth, assert detection.

**Acceptance:**

* If pocket detection fails, return 0 pockets and reduce confidence instead of crashing.

---

### `text` Prompt 21 — Pocket volume approximation

Extend pocket detection to compute:

* `pocket_total_volume`
  Approach can be conservative (approximate) but must be consistent and tested.

**TDD:**

* Pocket volume for a simple rectangular pocket should match within tolerance.

**Acceptance:**

* Confidence improves when volume can be computed.

---

### `text` Prompt 22 — DFM analyzer MVP (derived checks first)

Create `modules/dfm_analyzer.py`:

* Input: `PartFeatures`
* Output: list of `DfmIssue`
  Implement first:
* deep holes warning/critical based on blind hole max ratio
* small features (<0.9mm) using smallest detected hole diameter (MVP proxy)
* non-standard holes → warning/info message

**TDD:**

* Tests that the right severities trigger at the specified thresholds.

**Acceptance:**

* No geometry-heavy thin-wall analysis yet; structure code for adding later.

---

### `text` Prompt 23 — PDF generator page 1 (summary + tables)

Create `modules/pdf_generator.py`:

* `generate_quote_pdf(processing_result) -> bytes`
  Include:
* header details
* quote date + part UUID
* specs (material/finish/tolerance/lead time)
* pricing summary + breakdown
* dfm warnings
* disclaimer

**TDD:**

* Test PDF bytes length > 0
* Extract text (add a lightweight PDF text dependency if needed) and assert it contains “Tiento Quote v0.1” and the UUID.

**Acceptance:**

* Streamlit can download the PDF.

---

### `text` Prompt 24 — PDF page 2: embed STL snapshot (headless-safe)

Extend `pdf_generator.py`:

* Create a simple raster render from STL (headless-safe; e.g., matplotlib trisurf snapshot) and embed it on page 2.
* Overlay bbox dimensions as text.

**TDD:**

* Test generated PDF is larger than page-1-only version and still contains expected strings.

**Acceptance:**

* If rendering fails, fall back gracefully to page 1 only (and log).

---

### `text` Prompt 25 — Mailto link builder + UI integration

Create `modules/contact.py`:

* `build_mailto_link(processing_result, to="david@wellsglobal.eu") -> str`
  URL-encode subject/body per spec template.

**TDD:**

* Test the generated link contains encoded UUID and key fields.

Update `app.py`:

* Add “Download PDF Quote” button
* Add “Contact for Manual Review” link/button

**Acceptance:**

* No orphan features: everything is reachable from the UI.

---

### `text` Prompt 26 — Training script v0 (DB → model → pricing_coefficients.json)

Implement `training/train_model.py`:

* Read `training_parts` into pandas
* Train `StandardScaler` + `LinearRegression`
* Write `config/pricing_coefficients.json` with intercept, coefficients, scaler stats, r², last_updated

**TDD:**

* Use a temp sqlite DB with synthetic rows to verify output JSON structure and `r_squared > 0`.

**Acceptance:**

* App shows R² score and blocks quoting if r² == 0.

---

### `text` Prompt 27 — Tighten error handling + logging + final wiring

Polish pass:

* Ensure every module raises typed exceptions with spec messages.
* Ensure pipeline catches exceptions and returns them in `ProcessingResult.errors`.
* Add consistent logging (stdout) for: upload UUID, validation failures, feature results, dfm issues, pricing breakdown.

**TDD:**

* Add tests asserting error messages match spec for common failure modes.

**Acceptance:**

* Robust behavior: failures become user-facing messages + engineer-review guidance.

---

If you want, I can also produce a **single “meta-prompt”** you can reuse to run each of the prompts above (e.g., “write failing tests first, then implement, keep diffs minimal, don’t refactor unrelated code”).
