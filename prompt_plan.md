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

### `text` Prompt 07 — File validation helpers (extension/size) ✅ COMPLETE

Create `modules/file_handler.py` (start small):

* `validate_extension(filename)`: only `.step`/`.stp`
* `validate_size(num_bytes, max_bytes)`
  Return errors as exceptions with spec-aligned messages.

**TDD:**

* Tests for valid/invalid extensions
* Tests for boundary size exactly max vs max+1

**Acceptance:**

* Pure functions; no filesystem yet.

**Implementation Notes:**
- Created modules/file_handler.py with file validation helpers
- Custom exceptions with spec-aligned messages:
  * InvalidExtensionError: "Invalid file format - please upload .STEP file"
  * FileSizeError: "File size exceeds 50MB limit" (or dynamic for other limits)
- validate_extension(filename):
  * Case-insensitive validation for .step and .stp
  * Handles multiple dots in filename correctly
  * Pure function - no filesystem access
- validate_size(num_bytes, max_bytes):
  * Boundary testing: size <= max_bytes passes, size > max_bytes raises
  * Special handling for 50MB limit from spec
  * Pure function - no side effects
- Comprehensive test suite (29 tests):
  * Valid extensions: .step, .STEP, .stp, .STP (case-insensitive)
  * Invalid extensions: .stl, .obj, .txt, no extension
  * Size validation: within limit, at limit, 1 byte over, far over
  * Boundary testing verified
  * Error message validation (spec-aligned)
  * Pure function verification (no filesystem access)
- All tests passing (126/126 total)

---

### `text` Prompt 08 — Store upload to /uploads with UUID ✅ COMPLETE

Extend `modules/file_handler.py`:

* `store_upload(file_bytes, original_filename, uploads_dir) -> (part_id, stored_path)`
* Use UUID v4 naming; preserve `.step` extension.
* Ensure uploads_dir exists.

**TDD:**

* Test writes file, returns UUID-like string, and file exists with same bytes.

**Acceptance:**

* No STEP parsing yet in this step.

**Implementation Notes:**
- Extended modules/file_handler.py with store_upload function
- store_upload(file_bytes, original_filename, uploads_dir):
  * Generates UUID v4 using uuid.uuid4()
  * Extracts extension from original filename (preserves .step or .stp)
  * Creates filename as {uuid}{extension}
  * Ensures uploads directory exists with os.makedirs(exist_ok=True)
  * Writes file bytes in binary mode
  * Returns tuple: (part_id, stored_path)
- No STEP parsing in this implementation (deferred to Prompt 09)
- Comprehensive test suite (12 tests):
  * File creation and existence
  * UUID validation (can be parsed as UUID)
  * Extension preservation (.step and .stp)
  * Byte-for-byte content verification
  * Directory creation (including nested non-existent paths)
  * Multiple uploads get unique UUIDs
  * Large files (1MB) and empty files
  * Binary content with null bytes
  * Filename format: UUID.extension
- All tests passing (138/138 total)

---

### `text` Prompt 09 — Upload validation: STEP parse + solid presence ✅ COMPLETE

Extend `modules/file_handler.py`:

* Add `validate_step_geometry(step_path)` that uses `cad_io.load_step()`
* Reject if no solid geometry (define a reasonable check)
* Use spec error message: "File requires manual review - please contact us"

**TDD:**

* Test with a valid exported STEP passes.
* Test with an empty file or garbage bytes fails with the correct message.

**Acceptance:**

* Errors are deterministic and user-friendly.

**Implementation Notes:**
- Extended modules/file_handler.py with geometry validation
- GeometryValidationError custom exception for invalid geometry
- validate_step_geometry(step_path) function:
  * Uses cad_io.load_step() to parse STEP file
  * Validates solid geometry presence (workplane.val())
  * Checks for Volume attribute on solid
  * Ensures volume > 0 (valid solid)
  * Catches all error types:
    - StepLoadError (from cad_io)
    - Invalid/missing geometry
    - Any other parsing errors
  * Always returns spec-aligned error message
- Error message matches spec exactly: "File requires manual review - please contact us"
- Deterministic errors (same input = same error)
- Comprehensive test suite (11 tests):
  * Valid STEP files pass (simple box, complex geometry with holes)
  * Empty files raise GeometryValidationError
  * Garbage content raises GeometryValidationError
  * Invalid STEP format raises GeometryValidationError
  * Nonexistent files raise GeometryValidationError
  * Error messages verified to be spec-aligned
  * Determinism verified (same error for same file)
  * Exception behavior validation
- All tests passing (149/149 total)

---

### `text` Prompt 10 — Feature detector v0: bounding box + volume

✅ **COMPLETE**

**Implementation:**
- Created `modules/feature_detector.py` with `detect_bbox_and_volume(step_path)`
- Function returns `(PartFeatures, FeatureConfidence)` tuple
- Uses `cad_io.load_step()` for STEP parsing
- Computes bounding box dimensions (x, y, z) in mm using `solid.BoundingBox()`
- Calculates volume in mm³ using `solid.Volume()`
- Sets confidence to 1.0 for bbox and volume (deterministic geometric calculations)
- All other features (holes, pockets) remain at zero as specified

**Test Coverage (16 tests):**
- Known geometry: 10×20×30mm box = 6000mm³, 5×5×5mm cube = 125mm³
- Bounding box accuracy within 0.1mm tolerance
- Volume accuracy within 1mm³ tolerance
- Complex shapes with holes tested
- Confidence scores validation (bbox=1.0, volume=1.0, others=0.0)
- Verified holes/pockets remain zero
- Error handling for nonexistent files

**Files:**
- `modules/feature_detector.py` (76 lines)
- `tests/test_feature_detector.py` (195 lines, 16 tests)

**Tests:** All 165 tests passing (149 previous + 16 new)

**Commits:** 53ae048

---

### `text` Prompt 11 — Bounding box limit validation (600×400×500)

✅ **COMPLETE**

**Implementation:**
- Extended `modules/feature_detector.py` with `validate_bounding_box_limits(features, settings)`
- Added `BoundingBoxLimitError` custom exception
- Validates part dimensions against settings limits (600×400×500mm)
- Uses Settings dataclass to read BOUNDING_BOX_MAX_X/Y/Z values
- Raises exception with spec-aligned error message including contact email
- Designed to be called after bbox detection but before expensive operations (holes/pockets)

**Validation Logic:**
- Checks if any dimension (X, Y, or Z) exceeds maximum limits
- Uses > comparison (parts exactly at limit pass, anything over fails)
- Error message: "Part exceeds maximum dimensions of 600×400×500mm. Please contact us for large part quoting at david@wellsglobal.eu"

**Test Coverage (13 tests):**
- Parts within limits pass (100×200×300mm)
- Parts exactly at limits pass (600.0, 400.0, 500.0mm individually and combined)
- Parts exceeding X limit fail (601mm, 600.1mm)
- Parts exceeding Y limit fail (401mm)
- Parts exceeding Z limit fail (501mm)
- Parts exceeding multiple limits fail (700×500×600mm)
- Error message spec validation (dimensions + contact email)
- Exception type validation (BoundingBoxLimitError)

**Files:**
- `modules/feature_detector.py` (119 lines, +43 lines)
- `tests/test_feature_detector.py` (403 lines, +209 lines)

**Tests:** All 178 tests passing (165 previous + 13 new)

**Commits:** 9e8379f

---

### `text` Prompt 12 — Pricing engine v0 (config + normalization + min order)

✅ **COMPLETE**

**Implementation:**
- Created `modules/pricing_engine.py` with pricing calculation logic
- Added `ModelNotReadyError` and `InvalidQuantityError` custom exceptions
- Implemented `normalize_features(features_dict, mean, std)`: Standard scaler normalization formula (x - mean) / std
- Implemented `calculate_quote(part_features, quantity, pricing_config)`: Linear pricing model with validation

**Pricing Logic:**
- Validates model is trained: r_squared > 0.0, else raises "System not ready - training required"
- Validates quantity range: 1-50, else raises error with quantity limits message
- Extracts 10 pricing features from PartFeatures (volume, holes, pockets)
- Normalizes features using scaler_mean and scaler_std from config
- Calculates predicted price: base_price + sum(coefficient × normalized_feature)
- Clamps negative predictions to 0.0 (non-negative prices)
- Applies minimum order price (€30) when calculated_total < minimum
- Recalculates price_per_unit when minimum applies
- Returns QuoteResult with stable breakdown dict

**Breakdown Dictionary:**
- base_price: Base price from config
- feature_contribution: Sum of all feature contributions
- predicted_price_per_unit: Predicted price before minimum
- calculated_total: Total before minimum (price × quantity)
- minimum_order_price: Minimum applied amount (0 if not applied)
- final_total: Final total price

**Test Coverage (18 tests):**
- Feature normalization: simple values, zero mean, multiple features, dict return
- Untrained model error: r_squared = 0.0 raises ModelNotReadyError
- Quantity validation: <1, >50 raises InvalidQuantityError; 1 and 50 pass
- Minimum order logic: applies for small orders, doesn't apply for large orders
- Quantity scaling: price_per_unit consistent, total scales correctly
- Breakdown validation: stable keys, includes base_price, deterministic
- QuoteResult structure: all required fields present

**Files:**
- `modules/pricing_engine.py` (156 lines)
- `tests/test_pricing_engine.py` (325 lines, 18 tests)

**Tests:** All 196 tests passing (178 previous + 18 new)

**Commits:** 41d08b6

---

### `text` Prompt 13 — Pipeline orchestrator (end-to-end core)

✅ **COMPLETE**

**Implementation:**
- Created `modules/pipeline.py` with end-to-end orchestration
- Implemented `process_quote(step_path, quantity, pricing_config_path) -> ProcessingResult`
- Generates unique part_id using UUID v4
- Coordinates all modules in sequence: settings → detection → validation → pricing
- Returns complete ProcessingResult with all data
- Pure Python logic, no Streamlit dependencies

**Pipeline Sequence:**
1. **Load settings**: `get_settings()` - loads application configuration
2. **Detect features**: `detect_bbox_and_volume(step_path)` - detects bbox dimensions and volume
3. **Validate limits**: `validate_bounding_box_limits(features, settings)` - rejects oversized parts
4. **Load pricing config**: `load_pricing_config(pricing_config_path)` - loads trained model
5. **Calculate quote**: `calculate_quote(features, quantity, pricing_config)` - generates pricing
6. **Return result**: Complete ProcessingResult with all data

**ProcessingResult Contents:**
- part_id: Generated UUID v4 string
- step_file_path: Path to input STEP file
- stl_file_path: Empty string (STL export not yet implemented)
- features: Detected PartFeatures (bbox, volume, holes=0, pockets=0)
- confidence: FeatureConfidence scores (bbox=1.0, volume=1.0, others=0.0)
- dfm_issues: Empty list (DFM checks not yet implemented)
- quote: Calculated QuoteResult with pricing breakdown
- errors: Empty list on successful processing

**Test Coverage (16 tests):**
- End-to-end processing: returns ProcessingResult, all fields present
- Feature detection: 10×20×30mm box → 6000mm³ volume detected correctly
- Confidence validation: bbox and volume confidence = 1.0
- Quote generation: pricing calculated, minimum order (€30) applied correctly
- Validation enforcement: oversized parts (>600×400×500mm) rejected
- Quantity validation: quantity >50 rejected, 1-50 accepted
- Multiple quantities: quantity 1 (minimum applies) and 10 (calculated price) both work
- Serialization: result.to_dict() produces valid dictionary
- Error handling: successful processing has empty errors list

**Files:**
- `modules/pipeline.py` (72 lines)
- `tests/test_pipeline.py` (234 lines, 16 tests)

**Tests:** All 212 tests passing (196 previous + 16 new)

**Commits:** 5f85b05

---

### `text` Prompt 14 — Streamlit app skeleton wired to pipeline

✅ **COMPLETE**

**Implementation:**
- Created `app.py` - Streamlit web application for CNC machining quotes
- Wired to `process_quote()` pipeline for end-to-end processing
- Single-page application with responsive two-column layout

**UI Components:**
- **Header**: "Tiento Quote v0.1 - CNC Machining Calculator" with Wells Global Solutions contact info
- **File Upload**: STEP/STP files, max 50MB, with helpful tooltip
- **Quantity Input**: Number input (1-50) with auto-correction to 1 if out of range
- **Static Configuration**: Material (Aluminum 6061-T6), Finish (As Machined), Tolerance (ISO 2768-m), Lead Time (10 Business Days)
- **Progress Indicators**: Sequential spinners for Upload → Validate → Detect → Calculate → Complete

**Results Display:**
- **Quote Summary**: Quantity, price per unit, total price, minimum order notice
- **Part Features**: Bounding box dimensions (X/Y/Z in mm), volume (mm³), holes/pockets (currently 0)
- **Cost Breakdown**: Base cost, feature contribution, predicted per unit, calculated total, minimum order (if applied), final total
- **Detection Confidence**: Color-coded scores (🟢 bbox=100%, volume=100%; ⚪ others=0%)
- **DFM Warnings**: Section for critical/warning/info messages (empty in v0)
- **Part ID**: Display for reference

**Disclaimer:**
- Important notice: Pre-quotation for reference only, manual review required
- Prices exclude VAT and shipping

**Error Handling:**
- `BoundingBoxLimitError`: Oversized parts rejected with contact information
- `ModelNotReadyError`: Training required message with admin contact info
- `InvalidQuantityError`: Quantity validation with helpful message
- Generic exceptions: User-friendly error messages with contact email
- Temporary file cleanup on all error paths (including exceptions)

**Testing:**
- Acceptance: Manual testing with `streamlit run app.py`
- Upload STEP file → See quote with bbox/volume
- Quantity validation working (1-50, auto-correct)
- Error handling for oversized parts and invalid files
- Progress indicators show during processing

**Files:**
- `app.py` (224 lines)

**Commits:** 23027ce

---

### `text` Prompt 15 — STEP→STL conversion (visualization module)

✅ **COMPLETE**

**Implementation:**
- Created `modules/visualization.py` with STEP to STL conversion
- Implemented `compute_adaptive_deflection(features)`: Calculates mesh resolution from part size
- Implemented `step_to_stl(step_path, stl_path, linear_deflection, angular_deflection)`: Converts geometry

**Adaptive Deflection Calculation:**
- **Linear deflection**: 0.1% of largest bounding box dimension (max_dimension × 0.001)
- **Angular deflection**: Fixed at 0.5 degrees per spec
- Examples:
  - 30mm part → 0.03mm linear deflection
  - 600mm part → 0.6mm linear deflection
- Ensures appropriate mesh detail for part size

**STL Conversion Process:**
1. Load STEP file using `cadquery.importers.importStep()`
2. Convert to Workplane if needed
3. Export to STL with tolerance parameters using `cadquery.exporters.export()`
4. Binary STL format (80-byte header + triangle data)
5. Create parent directories automatically if needed

**Error Handling:**
- Missing STEP files raise exceptions with helpful messages
- Export failures captured and reported
- File path validation

**Test Coverage (14 tests):**
- **Adaptive deflection**: Returns tuple, calculates 0.1%, angular=0.5°, uses max dimension
- **Small parts**: 10×20×30mm → 0.03mm linear deflection
- **Large parts**: 600×400×500mm → 0.6mm linear deflection
- **STL creation**: File exists, has content, size >100 bytes
- **Complex geometry**: Parts with holes/pockets convert successfully
- **Mesh detail**: Finer deflection produces same or more detail
- **Error handling**: Nonexistent files raise exceptions
- **Binary format**: Valid 80-byte STL header
- **Directory creation**: Parent dirs created automatically

**Files:**
- `modules/visualization.py` (99 lines)
- `tests/test_visualization.py` (216 lines, 14 tests)

**Tests:** All 226 tests passing (212 previous + 14 new)

**Commits:** e7583fc

---

### `text` Prompt 16 — Three.js viewer component (HTML builder)

✅ **COMPLETE**

**Implementation:**
- Added `build_threejs_viewer_html(stl_bytes_or_url)` to `modules/visualization.py`
- Generates self-contained HTML with Three.js viewer from CDN libraries
- Uses Three.js v0.158.0 from cdn.jsdelivr.net (STLLoader + OrbitControls)

**Viewer Features:**
- **Interactive controls**: OrbitControls for rotate/zoom/pan (damping enabled)
- **Auto-centering**: Geometry centered at origin with camera positioned automatically
- **Lighting**: Ambient light + 2 directional lights for 3D depth perception
- **Material**: PhongMaterial with blue color (0x5555ff) and specular highlights
- **Responsive**: Handles window resize events
- **Camera**: PerspectiveCamera with distance calculated from bounding box

**HTML Structure:**
- Complete HTML document with DOCTYPE
- Embedded CSS for full-height container (600px)
- Three.js libraries loaded from CDN (no local dependencies)
- Inline JavaScript with scene setup, loader, and animation loop
- STL source injected into loader URL parameter

**Test Coverage (11 tests):**
- Returns string with content
- HTML structure validation (html/head/body tags)
- CDN verification (Three.js from jsdelivr/unpkg/cdnjs)
- STLLoader and OrbitControls present in HTML
- STL source placeholder correctly embedded
- Works with URLs, data URLs, and file paths
- Self-contained (no local script file references)
- Has container div for rendering
- Contains script tags

**Files:**
- `modules/visualization.py` (245 lines, +146 new)
- `tests/test_visualization.py` (305 lines, +90 new)

**Tests:** All 237 tests passing (226 previous + 11 new)

**Commits:** c5640b5

---

### `text` Prompt 17 — Integrate 3D viewer into Streamlit

✅ **COMPLETE**

**Implementation:**
- Integrated Three.js 3D viewer into Streamlit app for interactive model visualization
- Added STL generation after successful quote processing
- Converted STL to base64 data URL for browser access
- Rendered viewer with `st.components.html()` at top of results section

**Flow:**
1. Process quote successfully
2. Compute adaptive deflection from part features (0.1% of max dimension, 0.5° angular)
3. Convert STEP to STL in `TEMP_PATH` directory
4. Read STL as binary bytes and encode to base64
5. Create data URL: `data:application/octet-stream;base64,{encoded_data}`
6. Build Three.js viewer HTML with embedded data URL
7. Render viewer with Streamlit components (height=620px)
8. Display quote results below 3D preview
9. Clean up temp STL file (best-effort in all code paths)

**Data URL Approach:**
- STL file read as binary and base64-encoded
- Embedded directly in HTML as data URL
- Browser loads from data URL without server file access
- Works with Streamlit's component sandboxing
- No need for static file serving

**Error Handling:**
- STL generation failures show warning but don't block quote display
- Viewer rendering failures show warning with fallback to quote results
- Cleanup failures are silent (best-effort)
- All 4 exception handlers clean up both STEP and STL temp files

**Integration Points in app.py:**
- Import `base64` for encoding (line 9)
- Import visualization functions: `step_to_stl`, `compute_adaptive_deflection`, `build_threejs_viewer_html` (line 13)
- Import `get_settings` for TEMP_PATH access (line 14)
- Generate STL after quote processing (lines 102-121)
- Convert to data URL and render viewer (lines 132-151)
- Cleanup in success path (lines 231-236)
- Cleanup in all exception handlers (4 handlers updated)

**User Experience:**
- 3D model preview displays prominently at top of results
- Interactive OrbitControls for rotate (drag), zoom (scroll), pan (right-drag)
- Model auto-centered with camera positioned for optimal view
- Blue PhongMaterial with proper lighting
- Graceful fallback if 3D preview fails

**Cleanup Strategy:**
- STL files stored in TEMP_PATH with part_id as filename
- Cleanup at end of successful processing
- Cleanup in all exception paths
- Best-effort: doesn't fail if cleanup fails
- Uses try-except around os.unlink() calls

**Acceptance Criteria (Manual Testing):**
✓ Model displays in browser after quote processing
✓ User can rotate model with mouse drag
✓ User can zoom with scroll wheel
✓ User can pan with right-click drag
✓ Quote results display below 3D viewer
✓ Temp files cleaned up after display

**Files:**
- `app.py` (292 lines, +78 modified)

**Tests:** All 237 tests passing (no new automated tests for Streamlit UI - manual acceptance testing required)

**Commits:** 0706585

---

### `text` Prompt 18 — Feature detection v1: hole candidates (cylindrical faces)

✅ **COMPLETE**

**Implementation:**
- Extended `modules/feature_detector.py` with hole candidate detection
- Added internal helper functions:
  - `_find_cylindrical_faces(solid)`: Finds all cylindrical faces in solid
  - `_estimate_hole_diameter(face)`: Estimates diameter from bounding box (0.5-50mm range)
  - `_detect_holes(solid)`: Main detection logic with conservative filtering
- Updated `detect_bbox_and_volume()` to detect holes and populate counts
- Returns hole candidates with heuristic confidence (0.7)

**Detection Logic:**
- Find all cylindrical faces using `face.geomType() == "CYLINDER"`
- Estimate diameter from face bounding box (average of two smallest spans)
- Filter by diameter range: 0.5mm to 50mm (conservative)
- Count each cylindrical face as a hole candidate
- For v1: all holes counted as through_hole_count (classification in Prompt 19)
- Conservative approach: undercount if uncertain, reduce confidence

**Test Coverage (8 new tests):**
- Box with no holes → detects 0
- Box with one through hole → detects ≥1
- Box with two through holes → detects ≥2
- Box with blind hole → detects ≥1
- Box with multiple mixed holes → detects ≥3
- Confidence < 1.0 for heuristic detection
- Conservative detection (no overcounting)
- No crashes on complex geometry

**Files:**
- `modules/feature_detector.py` (230 lines, +111 new)
- `tests/test_feature_detector.py` (560 lines, +157 new)

**Tests:** All 245 tests passing (237 previous + 8 new)

**Commits:** 2688116

---

### `text` Prompt 19 — Classify through vs blind + ratios + non-standard

✅ **COMPLETE**

**Implementation:**
- Extended hole detection with classification and analysis capabilities
- Added through vs blind classification using heuristic analysis
- Implemented depth:diameter ratio calculations for blind holes
- Added non-standard hole size detection with tolerance matching

**Through vs Blind Classification:**
- Added `_classify_hole_type(face, solid_bbox)`: Classifies holes by comparing face span to solid dimensions
- Heuristic: Through holes span >90% of a part dimension, blind holes are shorter
- Defaults to "through" if classification is uncertain (conservative)
- Populates `through_hole_count` and `blind_hole_count` separately

**Blind Hole Depth Ratios:**
- Added `_estimate_hole_depth(face, solid_bbox)`: Estimates depth from cylindrical face (largest span)
- Computes depth:diameter ratio for each blind hole
- Returns `blind_hole_avg_depth_to_diameter` and `blind_hole_max_depth_to_diameter`
- Used for DFM analysis to detect deep hole warnings (ratio thresholds)

**Non-Standard Hole Detection:**
- Added `STANDARD_HOLE_SIZES` constant: [3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0] mm (M3-M12)
- Added `HOLE_SIZE_TOLERANCE` constant: 0.1mm
- Added `_is_standard_hole_size(diameter)`: Checks if diameter matches standard size ±0.1mm
- Populates `non_standard_hole_count` for pricing adjustments and DFM warnings

**Improved Confidence:**
- Upgraded confidence from 0.7 (v1 heuristic) to 0.85 (v2 with classification)
- Reflects improved detection accuracy with through/blind analysis
- Range: 0.85-0.90 as specified in acceptance criteria

**Updated Function Signatures:**
- `_detect_holes(solid)` now returns 6 values:
  - (through_count, blind_count, avg_ratio, max_ratio, confidence, non_standard_count)
- `detect_bbox_and_volume()` updated to unpack and populate all new fields

**Test Coverage (15 new tests):**
- TestClassifyThroughVsBlindHoles (4 tests):
  - Through hole classified correctly
  - Blind hole classified correctly
  - Mixed holes both detected
  - Multiple through holes detected
- TestBlindHoleDepthRatios (4 tests):
  - Ratios computed for blind holes
  - Avg and max ratios correct with multiple holes
  - Shallow blind hole has small ratio
  - Deep blind hole has large ratio
- TestStandardVsNonStandardHoles (5 tests):
  - Standard holes not counted as non-standard
  - Non-standard holes detected
  - Multiple standard holes work correctly
  - Mix of standard and non-standard
  - Tolerance (±0.1mm) applied correctly
- TestHoleConfidenceScores (2 tests):
  - Through hole confidence in range (0.7-1.0)
  - Blind hole confidence reasonable

**Files:**
- `modules/feature_detector.py` (348 lines, +118 new)
- `tests/test_feature_detector.py` (899 lines, +339 new)

**Tests:** All 260 tests passing (245 previous + 15 new)

**Commits:** 8c54784

---

### `text` Prompt 20 — Pocket detection v0 (simple prismatic pockets)

✅ **COMPLETE**

**Implementation:**
- Implemented MVP pocket detection for simple prismatic pockets aligned to primary axes
- Conservative heuristic approach using planar face analysis
- Returns count and depth statistics (volume deferred to Prompt 21)

**Pocket Detection Logic:**
- Added `_find_planar_faces(solid)`: Finds all planar (PLANE type) faces in solid
- Added `_is_pocket_face(face, solid_bbox)`: Checks if planar face is inset pocket
  * Heuristic: Pocket faces are inset from part boundaries (not at X/Y/Z edges)
  * Must be at least 1mm below top surface to qualify
  * Uses 0.5mm tolerance for boundary detection
  * Filters out external faces (top, bottom, sides)
- Added `_estimate_pocket_depth(face, solid_bbox)`: Calculates depth from face to top
  * Depth = solid_top_z - face_z
  * Minimum 0.5mm deep to count as pocket
- Added `_detect_pockets(solid)`: Main detection with statistics

**Returns:**
- `pocket_count`: Number of detected pockets
- `pocket_avg_depth`: Average depth across all pockets (mm)
- `pocket_max_depth`: Maximum depth of any pocket (mm)
- `pocket_confidence`: 0.7 for heuristic detection

**MVP Constraint (as specified):**
- Only detects simple prismatic pockets (planar bottom faces)
- Aligned to primary axes (created by planar-face cuts)
- Conservative: undercounts rather than overcounts
- `pocket_total_volume` remains 0 (deferred to Prompt 21)

**Error Handling:**
- If detection fails, returns zeros and confidence=0.0
- No crashes on complex geometry (safe conservative fallback)
- Exception handling in all helper functions

**Updated detect_bbox_and_volume():**
- Now calls `_detect_pockets(solid)`
- Populates `pocket_count`, `pocket_avg_depth`, `pocket_max_depth`
- Sets `pocket_confidence` in FeatureConfidence
- Updated docstring to v3 (adds pocket detection)
- Note: `pocket_total_volume` remains 0

**Test Coverage (10 new tests in TestDetectPockets):**
- Box with no pockets → detects 0
- Box with one rectangular pocket → detected
- Pocket depth detected correctly
- Multiple pockets detected
- Avg and max depth with different depths
- Shallow pocket (2mm) handling
- Deep pocket (18mm) detection
- pocket_total_volume remains 0 (verified)
- No crashes on complex geometry (holes + pockets)
- Pocket confidence set correctly (0.7 when detected, 0.0 when none)

**Files:**
- `modules/feature_detector.py` (521 lines, +109 new)
- `tests/test_feature_detector.py` (1104 lines, +205 new)

**Tests:** All 270 tests passing (260 previous + 10 new)

**Commits:** 1cdd664

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
