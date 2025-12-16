# Tiento Quote v0.1 - CNC Machining Calculator
## Comprehensive Development Specification

---

## 1. PROJECT OVERVIEW

### 1.1 Purpose
Build an MVP automated quoting system that analyzes STEP files of CNC machined parts, detects machining features, and generates price quotes based on machine learning regression trained on PCBWay pricing data.

### 1.2 Core Objectives
- Accept STEP file uploads (aluminum 6061 parts only initially)
- Detect Tier 1 machining features (bounding box, holes, pockets)
- Generate automated quotes in EUR using hybrid rule-based + ML pricing
- Provide basic web UI for testing with 3D visualization
- Flag DFM issues and non-standard features for manual review

### 1.3 Technology Stack
- **Language**: Python 3.9+
- **Web Framework**: Streamlit (easiest Python framework)
- **CAD Processing**: cadquery
- **3D Visualization**: Three.js with STL conversion
- **Database**: SQLite
- **ML**: scikit-learn (LinearRegression)
- **PDF Generation**: reportlab (easiest)
- **Deployment**: Render.com (free tier)

---

## 2. SYSTEM ARCHITECTURE

### 2.1 Application Structure
```
tiento-quote/
├── app.py                          # Main Streamlit application
├── config/
│   └── pricing_coefficients.json  # Regression coefficients
├── modules/
│   ├── file_handler.py            # Upload, validation, storage
│   ├── feature_detector.py        # CAD analysis and feature extraction
│   ├── pricing_engine.py          # Quote calculation
│   ├── dfm_analyzer.py            # Design for Manufacturing checks
│   ├── pdf_generator.py           # Quote PDF creation
│   └── visualization.py           # STEP to STL conversion
├── training/
│   ├── train_model.py             # Regression training script
│   └── training_data.db           # SQLite database
├── uploads/                        # Stored STEP files (by UUID)
├── temp/                           # Temporary STL files
├── requirements.txt
└── README.md
```

### 2.2 Processing Flow
```
User uploads STEP file
    ↓
Validate file (extension, size, format)
    ↓
Check bounding box dimensions
    ↓
Extract Tier 1 features (holes, pockets, volume)
    ↓
Detect DFM issues
    ↓
Convert STEP → STL for visualization
    ↓
Calculate price using regression model
    ↓
Display results (3D view, price breakdown, warnings)
    ↓
Generate PDF quote
```

---

## 3. DATABASE SCHEMA

### 3.1 Training Data Table: `training_parts`

```sql
CREATE TABLE training_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- User inputs
    quantity INTEGER NOT NULL,
    
    -- PCBWay pricing
    pcbway_price_eur REAL NOT NULL,
    price_per_unit REAL NOT NULL,
    
    -- Bounding box
    bounding_box_x REAL NOT NULL,
    bounding_box_y REAL NOT NULL,
    bounding_box_z REAL NOT NULL,
    
    -- Volume
    volume REAL NOT NULL,
    
    -- Through holes
    through_hole_count INTEGER DEFAULT 0,
    
    -- Blind holes
    blind_hole_count INTEGER DEFAULT 0,
    blind_hole_avg_depth_to_diameter REAL DEFAULT 0,
    blind_hole_max_depth_to_diameter REAL DEFAULT 0,
    
    -- Pockets
    pocket_count INTEGER DEFAULT 0,
    pocket_total_volume REAL DEFAULT 0,
    pocket_avg_depth REAL DEFAULT 0,
    pocket_max_depth REAL DEFAULT 0,
    
    -- Non-standard features
    non_standard_hole_count INTEGER DEFAULT 0
);
```

### 3.2 Column Descriptions
- **file_path**: UUID-based filename in `/uploads/` directory
- **quantity**: Number of parts quoted by PCBWay
- **pcbway_price_eur**: Total quote from PCBWay in EUR
- **price_per_unit**: Calculated as `pcbway_price_eur / quantity`
- **bounding_box_x/y/z**: Part dimensions in mm
- **volume**: Part solid volume in mm³
- **through_hole_count**: Total count of through holes
- **blind_hole_count**: Total count of blind holes
- **blind_hole_avg/max_depth_to_diameter**: Ratios for blind hole complexity
- **pocket_count**: Total number of pockets/cavities
- **pocket_total_volume**: Sum of all cavity volumes in mm³
- **pocket_avg/max_depth**: Pocket depth statistics in mm
- **non_standard_hole_count**: Holes not matching standard drill sizes

---

## 4. FEATURE DETECTION SPECIFICATIONS

### 4.1 Tier 1 Features (MVP Priority)

#### 4.1.1 Bounding Box
- **Detection**: Extract min/max coordinates in X, Y, Z
- **Storage**: Three separate values (x, y, z in mm)
- **Validation**: Reject if any dimension > limits (600×400×500mm)
- **Confidence**: 100% (geometric calculation)

#### 4.1.2 Volume
- **Detection**: Calculate solid volume using cadquery
- **Storage**: Single float value in mm³
- **Usage**: Primary cost driver for material
- **Confidence**: 100% (direct calculation)

#### 4.1.3 Through Holes
- **Detection**: 
  - Identify cylindrical features passing through entire part
  - Tolerance: ±0.5mm or ±2% of diameter (whichever larger)
- **Classification**: Compare diameter to `STANDARD_HOLE_SIZES`
- **Storage**: Total count
- **Confidence**: 85-95% (depends on geometry complexity)

**Standard Hole Sizes (mm)**:
```python
STANDARD_HOLE_SIZES = [
    # Metric
    1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 
    7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0, 16.0, 18.0, 20.0,
    # Clearance holes
    2.2, 3.3, 4.5, 5.5, 6.6, 9.0, 10.5, 13.0, 14.5, 17.0, 21.0
]
```

#### 4.1.4 Blind Holes
- **Detection**:
  - Cylindrical features not passing through part
  - Assume flat bottom (end mill) for MVP
  - Measure depth from surface to bottom
- **Depth-to-Diameter Ratio**:
  - Calculate for each blind hole: `depth / diameter`
  - Store average and maximum ratios
- **Storage**: Count, avg_ratio, max_ratio
- **Confidence**: 80-90%
- **Cost Factor**: 2-3× through hole coefficient

#### 4.1.5 Pockets/Cavities
- **Detection**:
  - Identify enclosed volumes/voids in part
  - Use cadquery's automatic cavity volume calculation
- **Measurements**:
  - Individual pocket volume (mm³)
  - Pocket depth (mm)
- **Depth Classification** (hardcoded):
  - Shallow: < 10mm
  - Deep: 10-25mm
  - Very deep: > 25mm
- **Storage**: 
  - Total count
  - Total volume (sum of all pockets)
  - Average depth
  - Maximum depth
- **Confidence**: 75-85%

#### 4.1.6 Non-Standard Holes
- **Detection**: Holes with diameters not in `STANDARD_HOLE_SIZES`
- **Tolerance**: ±0.1mm for size matching
- **Storage**: Count only (not specific diameters)
- **Cost Impact**: Additional coefficient in regression
- **User Notification**: Flag for manual review

---

### 4.2 Design for Manufacturing (DFM) Checks

#### 4.2.1 Critical Issues (Red Flags)
1. **Thin Walls**: < 0.5mm thickness
2. **Sharp Internal Corners**: < 0.5mm radius
3. **Deep Holes**: Depth-to-diameter ratio > 6:1
4. **Small Features**: < 0.9mm for metals

#### 4.2.2 Warning Issues (Yellow Flags)
1. **Thin Walls**: 0.5-1.0mm thickness
2. **Sharp Internal Corners**: 0.5-1.0mm radius
3. **Deep Holes**: Depth-to-diameter ratio 5-6:1

#### 4.2.3 Pocket-Specific DFM
- **Tight Internal Corners**: < 1mm radius
  - **Detection**: Analyze pocket corner radii
  - **Action**: Binary flag only, display message
  - **Message**: "Part contains tight internal corners (<1mm) - requires manual review and higher cost"

#### 4.2.4 User Notification
- Display inline alerts color-coded by severity
- **Red (Critical)**: "⚠ CRITICAL: [Issue description]"
- **Yellow (Warning)**: "⚠ WARNING: [Issue description]"
- Always include: "This part requires manual engineer review"
- Still display calculated quote with disclaimer

---

### 4.3 Unsupported Features (MVP)
**Threaded Holes**:
- **Detection**: Identify by pilot hole diameter patterns
- **Action**: Display message to user
- **Message**: "Threaded holes detected but not supported in MVP - will be included in manual review pricing"
- **Impact**: Does not block quote generation

---

## 5. PRICING ENGINE

### 5.1 Hybrid Model Architecture

#### Phase 1 (Week 1-4): 90% Rule-Based
```python
price = max(
    BASE_PRICE + 
    (coeff_volume × volume) + 
    (coeff_through_holes × through_hole_count) +
    (coeff_blind_holes × blind_hole_count) +
    (coeff_pocket_volume × pocket_total_volume) +
    (coeff_pocket_depth × pocket_max_depth) +
    (coeff_non_standard × non_standard_hole_count),
    MINIMUM_ORDER_PRICE
)
```

#### Phase 2-3 (Future): Increase ML Weight
- Month 2-3: 70% rule-based, 30% ML correction factor
- Month 4+: 50% rule-based, 50% ML
- ML learns complex feature interactions

### 5.2 Coefficient Derivation

#### 5.2.1 Training Script: `train_model.py`
```python
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import sqlite3
import json

# Load training data
conn = sqlite3.connect('training_data.db')
df = pd.read_sql_query("SELECT * FROM training_parts", conn)

# Feature matrix X
features = [
    'volume',
    'through_hole_count',
    'blind_hole_count',
    'blind_hole_avg_depth_to_diameter',
    'blind_hole_max_depth_to_diameter',
    'pocket_count',
    'pocket_total_volume',
    'pocket_avg_depth',
    'pocket_max_depth',
    'non_standard_hole_count'
]
X = df[features]
y = df['price_per_unit']

# Normalize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train linear regression
model = LinearRegression()
model.fit(X_scaled, y)

# Output coefficients (manual copy to config)
print("=== COEFFICIENTS FOR pricing_coefficients.json ===")
print(json.dumps({
    "base_price": float(model.intercept_),
    "coefficients": {
        features[i]: float(model.coef_[i]) 
        for i in range(len(features))
    },
    "r_squared": float(model.score(X_scaled, y)),
    "scaler_mean": scaler.mean_.tolist(),
    "scaler_std": scaler.scale_.tolist()
}, indent=2))
```

#### 5.2.2 Configuration File: `pricing_coefficients.json`
```json
{
  "base_price": 30.0,
  "minimum_order_price": 30.0,
  "coefficients": {
    "volume": 0.0,
    "through_hole_count": 0.0,
    "blind_hole_count": 0.0,
    "blind_hole_avg_depth_to_diameter": 0.0,
    "blind_hole_max_depth_to_diameter": 0.0,
    "pocket_count": 0.0,
    "pocket_total_volume": 0.0,
    "pocket_avg_depth": 0.0,
    "pocket_max_depth": 0.0,
    "non_standard_hole_count": 0.0
  },
  "r_squared": 0.0,
  "scaler_mean": [],
  "scaler_std": [],
  "last_updated": "YYYY-MM-DD"
}
```

### 5.3 Quote Calculation Logic

```python
def calculate_quote(features, quantity):
    # Load coefficients
    with open('config/pricing_coefficients.json') as f:
        config = json.load(f)
    
    # Check if model trained
    if config['r_squared'] == 0.0:
        return {"error": "System not ready - training required"}
    
    # Normalize features using stored scaler
    X = normalize_features(features, config['scaler_mean'], config['scaler_std'])
    
    # Calculate base price per unit
    price_per_unit = config['base_price']
    breakdown = {"Base cost": config['base_price']}
    
    for feature_name, value in features.items():
        coeff = config['coefficients'][feature_name]
        contribution = coeff * X[feature_name]
        price_per_unit += contribution
        
        if contribution != 0:
            breakdown[feature_name] = contribution
    
    # Apply quantity
    total_price = max(price_per_unit * quantity, config['minimum_order_price'])
    
    return {
        "price_per_unit": round(price_per_unit, 2),
        "total_price": round(total_price, 2),
        "quantity": quantity,
        "breakdown": breakdown,
        "minimum_applied": total_price == config['minimum_order_price']
    }
```

### 5.4 Special Pricing Rules
- **Blind Hole Premium**: Coefficient 2-3× through holes
- **Non-Standard Holes**: Additional cost per hole (from regression)
- **Minimum Order**: €30 per order (not per unit)
- **Quantity > 50**: Display "Quantities over 50 require manual quotation - contact us"

---

## 6. USER INTERFACE SPECIFICATIONS

### 6.1 Single-Page Application Layout

#### 6.1.1 Header
```
┌─────────────────────────────────────────────────┐
│  Tiento Quote v0.1 - CNC Machining Calculator   │
│  Wells Global Solutions                          │
│  Enschede, The Netherlands                       │
│  +31613801071 | wellsglobal.eu                   │
└─────────────────────────────────────────────────┘
```

#### 6.1.2 Upload Section
- **File Upload Widget**: 
  - Label: "Upload STEP File (Max 50MB)"
  - Accepted: `.step`, `.stp`
  - Max size: 50MB
- **Progress Indicators**:
  1. "Uploading file..."
  2. "Validating dimensions..."
  3. "Detecting features..."
  4. "Calculating price..."
  5. "Complete"

#### 6.1.3 Configuration Section (After Upload)
- **Material Dropdown**: 
  - Single option: "Aluminum 6061-T6"
- **Finish Dropdown**: 
  - Single option: "As Machined (Standard finish, no coating)"
- **Tolerance Dropdown**: 
  - Single option: "ISO 2768-m"
- **Quantity Input**: 
  - Type: Number
  - Default: 1
  - Min: 1
  - Max: 50
  - Auto-correct invalid to 1
- **Lead Time Display**: 
  - Static text: "10 Business Days"

#### 6.1.4 Results Section
**3D Visualization**:
- Interactive Three.js viewer (rotate, zoom, pan)
- Default view: Isometric
- Display converted STL mesh
- No feature highlighting

**Price Display**:
```
┌─────────────────────────────────────────────────┐
│  QUOTE SUMMARY                                   │
│  ─────────────────────────────────────────────  │
│  Quantity: [X] units                             │
│  Price per unit: €XX.XX                          │
│  Total price: €XXX.XX                            │
│                                                  │
│  [If minimum applied]                            │
│  Note: €30 minimum order applied                 │
└─────────────────────────────────────────────────┘
```

**Price Breakdown**:
```
┌─────────────────────────────────────────────────┐
│  COST BREAKDOWN (Testing)                        │
│  ─────────────────────────────────────────────  │
│  Base cost: €30.00                               │
│  Volume (12500 mm³): €5.23                       │
│  Through holes (8 × €2.50): €20.00               │
│  Blind holes (4 × €6.00): €24.00                 │
│  Pockets (2 × €8.50): €17.00                     │
│  Non-standard holes (3 × €5.00): €15.00          │
│  ─────────────────────────────────────────────  │
│  Subtotal per unit: €111.23                      │
└─────────────────────────────────────────────────┘
```

**Model Info**:
```
┌─────────────────────────────────────────────────┐
│  MODEL ACCURACY (R² Score): 0.87                 │
└─────────────────────────────────────────────────┘
```

**Confidence Scores** (Color-coded):
```
Feature Detection Confidence:
  🟢 Bounding box: 100%
  🟢 Volume: 100%
  🟢 Through holes: 92%
  🟡 Blind holes: 85%
  🟡 Pockets: 78%
```
- Green (🟢): ≥70%
- Yellow (🟡): <70%
- Red (🔴): <50%

**DFM Warnings** (Inline Alerts):
```
🔴 CRITICAL: Thin walls detected (<0.5mm) - Part requires manual review
🟡 WARNING: Deep blind holes (depth:diameter > 5:1) detected
⚠️  Non-standard hole sizes detected - Will incur additional cost
💬  Threaded holes detected but not supported in MVP - Will be priced in manual review
```

**Disclaimer**:
```
┌─────────────────────────────────────────────────┐
│  ⚠️  IMPORTANT NOTICE                            │
│  ─────────────────────────────────────────────  │
│  The price displayed is the system's             │
│  pre-quotation (for reference ONLY), and the     │
│  official quotation will be generated after      │
│  manual review by engineer according to the      │
│  complexity of the part structure and process    │
│  requirements.                                   │
│                                                  │
│  Prices exclude VAT and shipping.                │
└─────────────────────────────────────────────────┘
```

#### 6.1.5 Action Buttons
1. **Download PDF Quote**
   - Generates PDF with all quote details
   - Filename: `tiento_quote_[UUID].pdf`

2. **Contact for Manual Review**
   - Opens mailto: link
   - To: david@wellsglobal.eu
   - Subject: "Manual Review Request - Tiento Quote [UUID]"
   - Body: (Pre-filled with all quote data)

---

## 7. PDF QUOTE GENERATION

### 7.1 PDF Content Structure

**Page 1: Quote Summary**
```
┌─────────────────────────────────────────────────┐
│                                                  │
│        Tiento Quote v0.1                         │
│        CNC Machining Calculator                  │
│                                                  │
│  Wells Global Solutions                          │
│  Enschede, The Netherlands                       │
│  +31613801071                                    │
│  david@wellsglobal.eu                            │
│  wellsglobal.eu                                  │
│                                                  │
│  ──────────────────────────────────────────────│
│                                                  │
│  Quote Date: [YYYY-MM-DD]                        │
│  Part ID: [UUID]                                 │
│                                                  │
│  SPECIFICATIONS                                  │
│  Material: Aluminum 6061-T6                      │
│  Finish: As Machined (Standard, no coating)      │
│  Tolerance: ISO 2768-m                           │
│  Lead Time: 10 Business Days                     │
│                                                  │
│  PRICING                                         │
│  Quantity: [X] units                             │
│  Price per unit: €XX.XX                          │
│  Total Price: €XXX.XX EUR                        │
│                                                  │
│  [Price breakdown table]                         │
│                                                  │
│  DFM WARNINGS (if any)                           │
│  • [List of warnings]                            │
│                                                  │
│  ──────────────────────────────────────────────│
│                                                  │
│  IMPORTANT NOTICE                                │
│  The price displayed is the system's             │
│  pre-quotation (for reference ONLY), and the     │
│  official quotation will be generated after      │
│  manual review by engineer according to the      │
│  complexity of the part structure and process    │
│  requirements.                                   │
│                                                  │
│  Prices exclude VAT and shipping.                │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Page 2: Part Visualization**
- Embedded rendered image of STL (isometric view)
- Bounding box dimensions overlay

### 7.2 PDF Generation Library
- **Tool**: reportlab
- **Filename**: `tiento_quote_[UUID].pdf`
- **Storage**: Temporary (serve for download, don't persist)

---

## 8. FILE HANDLING & STORAGE

### 8.1 Upload Validation

#### 8.1.1 Pre-Processing Checks
1. **File Extension**: Must be `.step` or `.stp`
   - Error: "Invalid file format - please upload .STEP file"
   
2. **File Size**: Max 50MB
   - Error: "File size exceeds 50MB limit"

3. **STEP Format Validity**: Attempt parse with cadquery
   - Error: "File requires manual review - please contact us"

4. **Geometry Validation**: Contains valid 3D solid
   - Error: "File requires manual review - please contact us"

#### 8.1.2 Bounding Box Check (Before Feature Detection)
- Extract X, Y, Z dimensions
- Reject if any dimension > 600×400×500mm
- Error: "Part exceeds maximum dimensions of 600×400×500mm. Please contact us for large part quoting at david@wellsglobal.eu"

### 8.2 File Storage

#### 8.2.1 Uploaded STEP Files
- **Location**: `/uploads/`
- **Naming**: UUID v4 (e.g., `a3f5b2c1-...-.step`)
- **Persistence**: Permanent storage
- **Purpose**: Training data collection, review

#### 8.2.2 Temporary STL Files
- **Location**: `/temp/`
- **Naming**: `[UUID].stl`
- **Persistence**: Delete after session/response
- **Purpose**: 3D visualization only

---

## 9. 3D VISUALIZATION

### 9.1 STEP to STL Conversion

#### 9.1.1 Conversion Parameters
```python
# Adaptive tolerance based on bounding box
max_dimension = max(bbox_x, bbox_y, bbox_z)
linear_deflection = max_dimension * 0.001  # 0.1% of largest dimension
angular_deflection = 0.5  # degrees
```

#### 9.1.2 Process
1. Load STEP file with cadquery
2. Extract geometry
3. Mesh with adaptive tolerance
4. Export to STL format
5. Save to `/temp/[UUID].stl`

### 9.2 Three.js Integration

#### 9.2.1 Viewer Configuration
- **Library**: Three.js (via CDN)
- **Loader**: STLLoader
- **Controls**: OrbitControls (rotate, zoom, pan)
- **Camera**: PerspectiveCamera
- **Initial View**: Isometric (45° angles)
- **Lighting**: Ambient + Directional
- **Material**: MeshPhongMaterial (gray)
- **Background**: Light gray (#f0f0f0)

#### 9.2.2 Auto-Framing
- Calculate bounding sphere from STL
- Position camera to fit entire part
- Center part at origin

---

## 10. ERROR HANDLING

### 10.1 Upload Errors

| Error Condition | User Message | Action |
|----------------|--------------|--------|
| Wrong extension | "Invalid file format - please upload .STEP file" | Reject upload |
| File > 50MB | "File size exceeds 50MB limit" | Reject upload |
| Corrupted STEP | "File requires manual review - please contact us" | Accept but flag |
| No geometry | "File requires manual review - please contact us" | Accept but flag |
| Oversized part | "Part exceeds maximum dimensions of 600×400×500mm. Please contact us for large part quoting at david@wellsglobal.eu" | Reject upload |

### 10.2 Feature Detection Errors

| Error Condition | Handling | User Impact |
|----------------|----------|-------------|
| Low confidence (<70%) | Flag with yellow/red indicator | Display warning |
| Threaded holes detected | Display info message | No price impact |
| Tight corners detected | Display critical warning | Manual review required |
| DFM issues | Display color-coded alerts | Manual review required |
| Non-standard holes | Count and add premium | Higher cost noted |

### 10.3 Pricing Errors

| Error Condition | User Message | Action |
|----------------|--------------|--------|
| Model not trained (R²=0) | "System not ready - training required" | Block quote generation |
| Quantity > 50 | "Quantities over 50 require manual quotation - contact us" | Display message, no quote |
| Quantity invalid | Auto-correct to 1 | Silent correction |
| Missing coefficients | "System configuration error - contact support" | Block quote generation |

### 10.4 Logging Strategy (MVP)
- **Method**: Print to console/stdout
- **What to log**:
  - File uploads (UUID, filename, size)
  - Validation failures (type, reason)
  - Feature detection results (all features + confidence)
  - DFM warnings triggered
  - Price calculations (breakdown)
  - Errors/exceptions (full stack trace)

---

## 11. TRAINING DATA COLLECTION

### 11.1 Suggested 20 Training Parts

#### Category 1: Simple Baseline (4 parts)
1. **Simple Block with Through Holes**
   - Dimensions: 100×80×30mm
   - Features: 4 through holes (5mm, 8mm)
   - Purpose: Baseline cost with minimal complexity

2. **Thin Plate Multi-Hole**
   - Dimensions: 150×100×10mm
   - Features: 8 through holes (mixed sizes: 3mm, 6mm, 10mm)
   - Purpose: High hole density on thin stock

3. **Small Cube with Blind Holes**
   - Dimensions: 50×50×50mm
   - Features: 2 blind holes (6mm diameter, 15mm depth)
   - Purpose: Blind hole baseline

4. **Large Block No Features**
   - Dimensions: 300×200×100mm
   - Features: None
   - Purpose: Material volume baseline

#### Category 2: Hole Variations (6 parts)
5. **Medium Complexity Mixed Holes**
   - Features: 6 through + 4 blind (standard sizes, 10-20mm depth)
   - Purpose: Combined hole types

6. **Deep Blind Holes - Warning Threshold**
   - Features: 4 blind holes, depth:diameter = 5:1
   - Purpose: Test warning threshold

7. **Very Deep Blind Holes - Critical**
   - Features: 2 blind holes, depth:diameter = 7:1
   - Purpose: Test critical DFM flag

8. **Non-Standard Hole Sizes**
   - Features: 6 holes (2.7mm, 4.3mm, 7.5mm, 11.2mm, 15.8mm, 18.3mm)
   - Purpose: Non-standard premium testing

9. **Small Holes**
   - Features: 8 holes between 1.0-2.5mm diameter
   - Purpose: Small tool requirements

10. **Large Holes**
    - Features: 4 holes between 14-20mm diameter
    - Purpose: Large tool costs

#### Category 3: Pocket Variations (6 parts)
11. **Shallow Pockets**
    - Features: 3 pockets <10mm deep, varying floor areas
    - Purpose: Shallow cavity baseline

12. **Deep Pockets**
    - Features: 2 pockets 15-20mm deep
    - Purpose: Deep cavity costs

13. **Very Deep Pocket**
    - Features: 1 pocket 30mm deep
    - Purpose: Very deep cavity (>25mm)

14. **Multiple Shallow Pockets**
    - Features: 6 small pockets <10mm deep
    - Purpose: Setup complexity

15. **Large Single Pocket**
    - Features: 1 pocket covering 60% of face, 15mm deep
    - Purpose: High material removal

16. **Mixed Pocket Depths**
    - Features: 2 shallow + 1 deep pocket
    - Purpose: Depth variation impact

#### Category 4: Complex Combinations (4 parts)
17. **Holes + Shallow Pockets**
    - Features: 6 through holes + 2 shallow pockets
    - Purpose: Combined feature interaction

18. **Holes + Deep Pocket**
    - Features: 4 blind holes + 1 deep pocket (20mm)
    - Purpose: Complex machining paths

19. **Maximum Complexity**
    - Features: 8 mixed holes + 3 pockets (varying depths) + large bounding box (400×300×150mm)
    - Purpose: High-end cost calibration

20. **Edge Case - Small Dense Part**
    - Dimensions: 30×30×30mm
    - Features: 2 holes + 1 pocket
    - Purpose: Minimum size complexity

### 11.2 Training Data Collection Workflow

1. **Design Parts in CAD**: Create 20 parts per specifications above
2. **Export to STEP**: Save each as individual `.step` file
3. **Upload to PCBWay**: 
   - Material: Aluminum 6061-T6
   - Finish: As Machined
   - Tolerance: ISO 2768-m
   - Lead time: Standard (10 days)
   - Quantities: Test 1, 5, 10, 25 units per part (80 quotes total recommended)
4. **Record Quotes**: Save PCBWay price in EUR
5. **Store in Database**: 
   ```python
   # Run feature detection on each part
   features = detect_features(step_file)
   
   # Insert into training_parts table
   INSERT INTO training_parts VALUES (
       file_path, upload_date, quantity, pcbway_price_eur, 
       price_per_unit, bounding_box_x, bounding_box_y, 
       bounding_box_z, volume, through_hole_count, 
       blind_hole_count, ...
   )
   ```
6. **Train Model**: Run `python train_model.py`
7. **Validate**: Check R² score, test on sample parts
8. **Iterate**: If R² < 0.75, add more training data

---

## 12. DEPLOYMENT

### 12.1 Render.com Configuration

#### 12.1.1 Repository Setup
- Create GitHub repository with project structure
- Add `.gitignore`:
  ```
  __pycache__/
  *.pyc
  .env
  uploads/*
  temp/*
  *.db
  !training_data.db
  ```

#### 12.1.2 Render Service Settings
- **Service Type**: Web Service
- **Environment**: Python 3.9+
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  streamlit run app.py --server.port $PORT --server.address 0.0.0.0
  ```
- **Plan**: Free Tier (512MB RAM)
- **Auto-Deploy**: Enable (on git push)

#### 12.1.3 Persistent Storage
- **Disk**: Mount persistent volume for `/uploads/` directory
- **Size**: 1GB minimum
- **Backup**: Manual backup of training_data.db weekly

#### 12.1.4 Environment Variables
```bash
DATABASE_PATH=/var/data/training_data.db
UPLOADS_PATH=/var/data/uploads
TEMP_PATH=/tmp
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes
```

### 12.2 Requirements.txt
```
streamlit>=1.28.0
cadquery>=2.3.1
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
reportlab>=4.0.0
Pillow>=10.0.0
pythreejs>=2.4.0
```

---

## 13. TESTING PLAN

### 13.1 Unit Testing (Development Phase)

#### 13.1.1 File Upload Tests
- [ ] Valid STEP file (.step extension)
- [ ] Valid STEP file (.stp extension)
- [ ] Invalid extension (.stl, .obj, .txt)
- [ ] File size exactly 50MB
- [ ] File size > 50MB
- [ ] Corrupted STEP file
- [ ] Empty file
- [ ] STEP file with no solid geometry

#### 13.1.2 Bounding Box Validation Tests
- [ ] Part within limits (100×100×100mm)
- [ ] Part at exact limit (600×400×500mm)
- [ ] Part exceeding X dimension
- [ ] Part exceeding Y dimension
- [ ] Part exceeding Z dimension
- [ ] Part exceeding all dimensions

#### 13.1.3 Feature Detection Tests
**Through Holes:**
- [ ] Single standard through hole (5mm)
- [ ] Multiple through holes (mixed sizes)
- [ ] Non-cylindrical holes (should not detect)
- [ ] Nearly cylindrical (within tolerance)
- [ ] Very small holes (<1mm)
- [ ] Very large holes (>20mm)

**Blind Holes:**
- [ ] Single standard blind hole
- [ ] Blind hole depth:diameter = 3:1 (normal)
- [ ] Blind hole depth:diameter = 5:1 (warning)
- [ ] Blind hole depth:diameter = 7:1 (critical)
- [ ] Very shallow blind holes (<2mm depth)

**Pockets:**
- [ ] Single shallow pocket (<10mm)
- [ ] Single deep pocket (15mm)
- [ ] Single very deep pocket (30mm)
- [ ] Multiple pockets (varying depths)
- [ ] Pocket with tight corners (<1mm radius)
- [ ] Pocket with acceptable corners (>2mm radius)

**Non-Standard Holes:**
- [ ] Hole exactly matching standard size (6.0mm)
- [ ] Hole slightly off standard (6.05mm - should match)
- [ ] Hole clearly non-standard (6.3mm)
- [ ] Multiple non-standard holes

#### 13.1.4 DFM Detection Tests
- [ ] Thin wall 0.3mm (critical)
- [ ] Thin wall 0.7mm (warning)
- [ ] Thin wall 1.2mm (acceptable)
- [ ] Sharp corner 0.3mm radius (critical)
- [ ] Sharp corner 0.7mm radius (warning)
- [ ] Sharp corner 1.5mm radius (acceptable)
- [ ] Deep hole ratio 7:1 (critical)
- [ ] Deep hole ratio 5.5:1 (warning)
- [ ] Small feature 0.6mm (critical for metals)

#### 13.1.5 Pricing Tests
- [ ] Simple part (baseline)
- [ ] Part with only through holes
- [ ] Part with only blind holes
- [ ] Part with only pockets
- [ ] Complex part (all features)
- [ ] Part triggering minimum order (€30)
- [ ] Quantity = 1
- [ ] Quantity = 10
- [ ] Quantity = 50
- [ ] Quantity = 51 (should show manual quote message)
- [ ] Non-standard holes premium application

#### 13.1.6 UI Tests
- [ ] File upload widget renders
- [ ] Material dropdown (single option)
- [ ] Finish dropdown (single option)
- [ ] Tolerance dropdown (single option)
- [ ] Quantity input (default = 1)
- [ ] Quantity input (invalid = auto-correct to 1)
- [ ] Progress indicators display correctly
- [ ] 3D viewer loads STL
- [ ] 3D viewer allows rotation/zoom/pan
- [ ] Price breakdown displays correctly
- [ ] R² score displays
- [ ] Confidence scores color-coded
- [ ] DFM warnings display (color-coded)
- [ ] Disclaimer text visible
- [ ] PDF download button works
- [ ] mailto link pre-fills correctly

### 13.2 Integration Testing

#### 13.2.1 End-to-End Workflow
1. [ ] Upload valid STEP file → successful processing
2. [ ] Modify quantity → recalculate price
3. [ ] Change material (future) → update price
4. [ ] Download PDF → verify content
5. [ ] Click "Contact for Review" → email opens
6. [ ] Upload oversized part → rejection message
7. [ ] Upload part with DFM issues → warnings display
8. [ ] Upload part with quantity >50 → manual quote message

#### 13.2.2 Training Workflow
1. [ ] Add training data to database
2. [ ] Run `train_model.py`
3. [ ] Copy coefficients to JSON config
4. [ ] Restart app
5. [ ] Upload test part → verify quote calculation
6. [ ] Check R² score display

### 13.3 Performance Testing

#### 13.3.1 Processing Time Benchmarks
- [ ] Simple part (<100mm³): <5 seconds
- [ ] Medium complexity: <15 seconds
- [ ] Complex part (max features): <30 seconds
- [ ] STL conversion: <10 seconds

#### 13.3.2 File Size Limits
- [ ] 1MB STEP file
- [ ] 10MB STEP file
- [ ] 50MB STEP file (max)

### 13.4 Accuracy Testing (Post-Training)

#### 13.4.1 Quote Accuracy
- [ ] Compare predicted vs actual PCBWay quotes
- [ ] Target: ±15% accuracy on 80% of test parts
- [ ] R² score: >0.75 minimum, >0.85 ideal

#### 13.4.2 Feature Detection Accuracy
- [ ] Manual verification of hole counts
- [ ] Manual verification of pocket volumes
- [ ] Compare bounding boxes to CAD measurements

### 13.5 Production Readiness Checklist

#### 13.5.1 Configuration
- [ ] `pricing_coefficients.json` populated
- [ ] R² score > 0.75
- [ ] All 20 training parts in database
- [ ] Environment variables set

#### 13.5.2 Deployment
- [ ] GitHub repository configured
- [ ] Render.com service created
- [ ] Persistent volume mounted
- [ ] Auto-deploy enabled
- [ ] Service accessible via HTTPS

#### 13.5.3 Functionality
- [ ] Upload works on production
- [ ] 3D viewer renders
- [ ] Quotes calculate correctly
- [ ] PDF downloads work
- [ ] mailto links work

---

## 14. FUTURE ENHANCEMENTS (Post-MVP)

### 14.1 Phase 2 Features
- Additional materials (stainless steel 304, brass)
- Multiple finish options (anodizing, powder coating)
- Precision tolerance tiers
- Thread detection and pricing
- Chamfer/fillet detection
- Surface complexity analysis (curved surfaces)
- Multi-setup cost calculation

### 14.2 Phase 3 Features
- User accounts and quote history
- Real-time pricing API integration
- Advanced ML model (neural network)
- Automated CAD file optimization suggestions
- Bulk upload (multiple parts)
- Export to ERP systems

### 14.3 UI/UX Improvements
- Professional frontend redesign
- Drag-and-drop file upload
- Interactive feature highlighting in 3D viewer
- Real-time quote updates as parameters change
- Mobile-responsive design
- Multi-language support

---

## 15. IMPLEMENTATION ROADMAP

### Week 1: Core Infrastructure
- [ ] Set up project structure
- [ ] Initialize SQLite database
- [ ] Implement file upload handler
- [ ] Create basic Streamlit UI skeleton

### Week 2: Feature Detection
- [ ] Implement bounding box extraction
- [ ] Implement volume calculation
- [ ] Implement through hole detection
- [ ] Implement blind hole detection
- [ ] Implement pocket detection
- [ ] Implement DFM checks

### Week 3: Pricing & Training
- [ ] Design 20 training parts in CAD
- [ ] Upload to PCBWay and collect quotes
- [ ] Populate training database
- [ ] Implement `train_model.py` script
- [ ] Train regression model
- [ ] Implement pricing calculation logic

### Week 4: Visualization & Output
- [ ] Implement STEP to STL conversion
- [ ] Integrate Three.js viewer
- [ ] Implement PDF generation
- [ ] Add mailto functionality
- [ ] Complete UI polish (progress bars, alerts)

### Week 5: Testing & Deployment
- [ ] Run full test suite
- [ ] Fix bugs and edge cases
- [ ] Configure Render.com deployment
- [ ] Deploy to production
- [ ] Validate with real test uploads

---

## 16. CONTACT & SUPPORT

**Technical Owner**: David  
**Company**: Wells Global Solutions  
**Email**: david@wellsglobal.eu  
**Phone**: +31613801071  
**Location**: Enschede, The Netherlands  
**Website**: wellsglobal.eu

---

## APPENDIX A: Standard Hole Sizes Reference

```python
STANDARD_HOLE_SIZES = [
    # Metric drill sizes (mm)
    1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 
    6.0, 6.5, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0, 
    16.0, 18.0, 20.0,
    
    # Common clearance holes
    2.2,   # M2 clearance
    3.3,   # M3 clearance
    4.5,   # M4 clearance
    5.5,   # M5 clearance
    6.6,   # M6 clearance
    9.0,   # M8 clearance
    10.5,  # M10 clearance
    13.0,  # M12 clearance
    14.5,  # M14 clearance
    17.0,  # M16 clearance
    21.0   # M20 clearance
]

# Tolerance for matching: ±0.1mm
```

---

## APPENDIX B: DFM Thresholds

```python
DFM_THRESHOLDS = {
    "thin_walls": {
        "critical": 0.5,  # mm
        "warning": 1.0    # mm
    },
    "sharp_corners": {
        "critical": 0.5,  # mm radius
        "warning": 1.0    # mm radius
    },
    "deep_holes": {
        "critical": 6.0,  # depth:diameter ratio
        "warning": 5.0    # depth:diameter ratio
    },
    "small_features": {
        "critical_metal": 0.9,   # mm
        "critical_plastic": 0.5  # mm
    },
    "tight_pocket_corners": {
        "flag": 1.0  # mm radius
    }
}
```

---

## APPENDIX C: Email Template

**Subject**: Manual Review Request - Tiento Quote [UUID]

**Body**:
```
Hello,

I am requesting a manual review for the following CNC machining quote:

PART DETAILS:
- Part ID: [UUID]
- Material: Aluminum 6061-T6
- Finish: As Machined (Standard finish, no coating)
- Tolerance: ISO 2768-m
- Lead Time: 10 Business Days

QUOTE SUMMARY:
- Quantity: [X] units
- Automated Quote: €XXX.XX EUR (€XX.XX per unit)

DESIGN FOR MANUFACTURING WARNINGS:
[List of DFM issues if any]

DETECTED FEATURES:
- Bounding Box: [X]×[Y]×[Z] mm
- Volume: [V] mm³
- Through Holes: [N]
- Blind Holes: [N]
- Pockets: [N]
- Non-Standard Holes: [N]

Please provide an official quotation after manual review.

Thank you,
[User can add their details here]
```

---

## DOCUMENT VERSION

**Version**: 1.0  
**Date**: 2024-12-16  
**Status**: Developer-Ready Specification  
**Next Review**: After MVP deployment and initial testing

---

**END OF SPECIFICATION**

This specification is comprehensive and ready for handoff to a development team. All requirements, technical decisions, workflows, and acceptance criteria have been defined to enable immediate implementation.
