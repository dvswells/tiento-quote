# Admin Training Guide: Pricing Model Training & Testing

This guide explains how to train, test, and improve the automated pricing model for Tiento Quote.

## 📊 How the ML System Works

The pricing system uses **Linear Regression** to predict prices based on part features:

```
Part Features → Trained Model → Price Prediction
```

**Features used** (10 total):
1. `volume` - Part volume in mm³
2. `through_hole_count` - Number of through holes
3. `blind_hole_count` - Number of blind holes
4. `blind_hole_avg_depth_to_diameter` - Average depth-to-diameter ratio
5. `blind_hole_max_depth_to_diameter` - Maximum depth-to-diameter ratio
6. `pocket_count` - Number of pockets detected
7. `pocket_total_volume` - Total volume of all pockets
8. `pocket_avg_depth` - Average pocket depth
9. `pocket_max_depth` - Maximum pocket depth
10. `non_standard_hole_count` - Number of non-standard holes

**Model**: StandardScaler + LinearRegression
- StandardScaler normalizes features (mean=0, std=1)
- LinearRegression learns coefficients for each feature
- Output: `pricing_coefficients.json` with model parameters

---

## 🗄️ Step 1: Collect Training Data

To train an accurate model, you need **real quotes** from actual parts.

### Data Collection Process

For each part you want to add to training:

1. **Get a real quote** from PCBWay (or your actual manufacturer)
2. **Process the STEP file** through the app to extract features
3. **Record both the real price and extracted features**

### Recommended Minimum Data

- **Minimum**: 20 parts (more is better)
- **Ideal**: 50-100 parts
- **Variety matters**: Include different:
  - Sizes (small, medium, large)
  - Complexities (simple box, parts with holes, parts with pockets)
  - Quantities (1, 10, 25, 50 units)
  - Materials (if you support multiple materials)

### Example Data Collection Spreadsheet

| Part Name | STEP File | Quantity | Real Price | Price/Unit | Notes |
|-----------|-----------|----------|------------|------------|-------|
| bracket-01 | bracket-01.step | 10 | €450 | €45 | Simple, no holes |
| housing-02 | housing-02.step | 25 | €875 | €35 | 6 through holes |
| cover-03 | cover-03.step | 1 | €125 | €125 | Complex pockets |

---

## 🔧 Step 2: Set Up Training Database

### Create the Database

```bash
# Create database and initialize schema
python -c "
from modules.db import connect, ensure_schema

# Connect and create schema
conn = connect('training/training_data.db')
ensure_schema(conn)
conn.close()
print('✓ Database created at training/training_data.db')
"
```

This creates `training/training_data.db` with the proper schema.

---

## 📥 Step 3: Add Training Data

You have two options for adding training data:

### Option A: Process STEP Files Through App (Recommended)

This is easier because the app automatically extracts features:

1. **Process the STEP file** through the web app (or programmatically)
2. **Copy the extracted features** from the results
3. **Add to database** with the real price

**Python script to add training data**:

```python
# add_training_data.py
import sqlite3
from modules.db import connect, ensure_schema, insert_training_part
from modules.pipeline import process_quote

# Configuration
DB_PATH = "training/training_data.db"
PRICING_CONFIG = "config/pricing_coefficients.json"

# Connect to database
conn = connect(DB_PATH)
ensure_schema(conn)

# Example: Add a part with real pricing from PCBWay
step_file = "path/to/bracket-01.step"
quantity = 10
real_total_price = 450.0  # € from PCBWay quote
real_price_per_unit = 45.0  # € per unit

# Process the STEP file to extract features
result = process_quote(step_file, quantity, PRICING_CONFIG)

if result.errors:
    print(f"Error processing file: {result.errors}")
else:
    # Build training row from extracted features
    training_row = {
        "file_path": step_file,
        "quantity": quantity,
        "pcbway_price_eur": real_total_price,
        "price_per_unit": real_price_per_unit,

        # Bounding box (from extracted features)
        "bounding_box_x": result.features.bounding_box_x,
        "bounding_box_y": result.features.bounding_box_y,
        "bounding_box_z": result.features.bounding_box_z,

        # Volume
        "volume": result.features.volume,

        # Holes
        "through_hole_count": result.features.through_hole_count,
        "blind_hole_count": result.features.blind_hole_count,
        "blind_hole_avg_depth_to_diameter": result.features.blind_hole_avg_depth_to_diameter,
        "blind_hole_max_depth_to_diameter": result.features.blind_hole_max_depth_to_diameter,

        # Pockets
        "pocket_count": result.features.pocket_count,
        "pocket_total_volume": result.features.pocket_total_volume,
        "pocket_avg_depth": result.features.pocket_avg_depth,
        "pocket_max_depth": result.features.pocket_max_depth,

        # Non-standard features
        "non_standard_hole_count": result.features.non_standard_hole_count,
    }

    # Insert into database
    insert_training_part(conn, training_row)
    print(f"✓ Added {step_file} to training database")

conn.close()
```

**Save this as `add_training_data.py` and run**:
```bash
python add_training_data.py
```

### Option B: Batch Import from CSV

If you have many parts, create a CSV and import:

**1. Create CSV file** (`training_data.csv`):
```csv
file_path,quantity,pcbway_price_eur,price_per_unit,bounding_box_x,bounding_box_y,bounding_box_z,volume,through_hole_count,blind_hole_count,blind_hole_avg_depth_to_diameter,blind_hole_max_depth_to_diameter,pocket_count,pocket_total_volume,pocket_avg_depth,pocket_max_depth,non_standard_hole_count
parts/bracket-01.step,10,450,45,100,50,30,125000,0,0,0,0,0,0,0,0,0
parts/housing-02.step,25,875,35,200,150,80,1800000,6,0,0,0,0,0,0,0,0
parts/cover-03.step,1,125,125,150,150,40,750000,2,4,3.5,5.2,2,15000,25,45,1
```

**2. Import script** (`import_csv.py`):
```python
import pandas as pd
from modules.db import connect, ensure_schema, insert_training_part

# Read CSV
df = pd.read_csv('training_data.csv')

# Connect to database
conn = connect('training/training_data.db')
ensure_schema(conn)

# Insert each row
for idx, row in df.iterrows():
    insert_training_part(conn, row.to_dict())
    print(f"✓ Imported row {idx + 1}/{len(df)}: {row['file_path']}")

conn.close()
print(f"\n✓ Successfully imported {len(df)} training parts")
```

**Run**:
```bash
python import_csv.py
```

---

## 🎓 Step 4: Train the Model

Once you have at least **2 training parts** (20+ recommended), train the model:

```bash
python -m training.train_model
```

**With custom paths**:
```bash
python -m training.train_model \
  --db training/training_data.db \
  --output config/pricing_coefficients.json
```

**Output**:
```
Training pricing model...
  Database: training/training_data.db
  Output: config/pricing_coefficients.json
✓ Training complete!
  R² score: 0.8542
  Base price: €22.45
  Minimum order: €30.00
  Last updated: 2024-12-19T10:30:00Z
```

### What Gets Created

The training script creates `config/pricing_coefficients.json`:

```json
{
  "base_price": 22.45,
  "minimum_order_price": 30.0,
  "r_squared": 0.8542,
  "coefficients": {
    "volume": 0.00015,
    "through_hole_count": 2.3,
    "blind_hole_count": 3.1,
    "blind_hole_avg_depth_to_diameter": 1.2,
    "blind_hole_max_depth_to_diameter": 0.8,
    "pocket_count": 4.5,
    "pocket_total_volume": 0.0003,
    "pocket_avg_depth": 0.15,
    "pocket_max_depth": 0.25,
    "non_standard_hole_count": 3.0
  },
  "scaler_mean": { ... },
  "scaler_std": { ... },
  "last_updated": "2024-12-19T10:30:00Z"
}
```

---

## 📈 Step 5: Evaluate Model Accuracy

### Understanding R² Score

The **R² (R-squared) score** measures how well the model fits the training data:

- **R² = 1.0**: Perfect predictions (100% accuracy)
- **R² = 0.9**: Excellent (explains 90% of price variance)
- **R² = 0.8**: Good (explains 80% of price variance)
- **R² = 0.7**: Acceptable for initial model
- **R² = 0.5**: Poor (only explains 50% of variance)
- **R² < 0.5**: Very poor, need more/better data

### R² Score Guidelines

| R² Score | Quality | Action |
|----------|---------|--------|
| 0.90 - 1.00 | Excellent | Deploy to production |
| 0.80 - 0.89 | Good | Deploy, monitor for edge cases |
| 0.70 - 0.79 | Acceptable | Consider collecting more data |
| 0.50 - 0.69 | Poor | Need more diverse training data |
| < 0.50 | Very Poor | Features may not correlate with price |

### Testing Predictions

Create a test script to compare predictions vs reality:

```python
# test_model.py
from modules.pipeline import process_quote
from modules.db import connect, fetch_training_parts

PRICING_CONFIG = "config/pricing_coefficients.json"

# Get training data
conn = connect('training/training_data.db')
df = fetch_training_parts(conn)
conn.close()

print("Testing model predictions vs actual prices:\n")
print(f"{'Part':<30} {'Actual':>10} {'Predicted':>10} {'Error':>10} {'Error %':>10}")
print("-" * 80)

errors = []
for idx, row in df.iterrows():
    # Get prediction
    result = process_quote(row['file_path'], row['quantity'], PRICING_CONFIG)

    if result.errors:
        continue

    actual = row['price_per_unit']
    predicted = result.quote.price_per_unit if result.quote else 0
    error = predicted - actual
    error_pct = (error / actual) * 100 if actual > 0 else 0

    errors.append(abs(error_pct))

    print(f"{row['file_path']:<30} €{actual:>8.2f} €{predicted:>8.2f} €{error:>8.2f} {error_pct:>8.1f}%")

print("-" * 80)
print(f"Average absolute error: {sum(errors)/len(errors):.1f}%")
print(f"Max error: {max(errors):.1f}%")
```

**Run**:
```bash
python test_model.py
```

**Example output**:
```
Testing model predictions vs actual prices:

Part                              Actual  Predicted      Error   Error %
--------------------------------------------------------------------------------
parts/bracket-01.step              €45.00     €43.20     €-1.80      -4.0%
parts/housing-02.step              €35.00     €36.50      €1.50       4.3%
parts/cover-03.step               €125.00    €118.30     €-6.70      -5.4%
--------------------------------------------------------------------------------
Average absolute error: 4.6%
Max error: 5.4%
```

### Cross-Validation (Advanced)

For a more robust accuracy test, use train/test split:

```python
# cross_validate.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error
from modules.db import connect, fetch_training_parts
from modules.pricing_config import REQUIRED_COEFFICIENT_FEATURES

# Load data
conn = connect('training/training_data.db')
df = fetch_training_parts(conn)
conn.close()

# Prepare features and target
X = df[REQUIRED_COEFFICIENT_FEATURES].values
y = df['price_per_unit'].values

# Split 80% train, 20% test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LinearRegression()
model.fit(X_train_scaled, y_train)

# Evaluate on test set
y_pred = model.predict(X_test_scaled)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
mape = mean_absolute_percentage_error(y_test, y_pred) * 100

print(f"Cross-validation results:")
print(f"  Training set size: {len(X_train)} parts")
print(f"  Test set size: {len(X_test)} parts")
print(f"  R² score on test set: {r2:.4f}")
print(f"  Mean Absolute Error: €{mae:.2f}")
print(f"  Mean Absolute Percentage Error: {mape:.1f}%")
```

---

## 🚀 Step 6: Deploy the New Model

### Local Deployment

1. **Replace the config file**:
   ```bash
   cp config/pricing_coefficients.json config/pricing_coefficients_backup.json
   # Your new model is already at config/pricing_coefficients.json
   ```

2. **Test locally**:
   ```bash
   streamlit run app.py
   ```

3. **Verify predictions** with a few test STEP files

### Production Deployment (Render)

1. **Commit the new model**:
   ```bash
   git add config/pricing_coefficients.json
   git commit -m "Update pricing model - R²=0.85 with 50 training parts"
   git push origin main
   ```

2. **Render automatically redeploys** (if auto-deploy enabled)
   - Or manually deploy from Render dashboard

3. **Verify in production**: Upload a test STEP file and check the price

---

## 💡 Step 7: Improve Model Accuracy

### Strategies for Better Accuracy

#### 1. **Add More Training Data**
- Target: 50-100 parts minimum
- Focus on parts that are currently predicted poorly

#### 2. **Add Diverse Training Data**
- Include variety in sizes, complexities, quantities
- Cover edge cases (very small parts, very large parts, complex geometries)

#### 3. **Identify Outliers**
When a prediction is very wrong, investigate:

```python
# Find parts with large prediction errors
from modules.pipeline import process_quote

# Test each training part
for row in training_data:
    result = process_quote(row['file_path'], row['quantity'], config)
    actual = row['price_per_unit']
    predicted = result.quote.price_per_unit
    error_pct = abs((predicted - actual) / actual) * 100

    if error_pct > 20:  # More than 20% error
        print(f"Large error on {row['file_path']}: {error_pct:.1f}%")
        print(f"  Actual: €{actual:.2f}, Predicted: €{predicted:.2f}")
        print(f"  Features: {result.features}")
```

**Common causes of outliers**:
- Special materials (stainless steel vs aluminum)
- Rush orders (expedited manufacturing)
- Special finishes (anodizing, powder coating)
- Extremely complex geometry not captured by features

#### 4. **Add New Features**

If certain types of parts are consistently mispriced, you may need to add new features:

**Example new features to consider**:
- Material type (aluminum, steel, plastic)
- Surface finish (none, anodized, painted)
- Tolerance requirements (standard, tight)
- Minimum wall thickness
- Undercuts presence
- Thread count

To add a new feature:
1. Update `modules/domain.py` - add field to `PartFeatures`
2. Update `modules/feature_detector.py` - extract the feature
3. Update `modules/pricing_config.py` - add to `REQUIRED_COEFFICIENT_FEATURES`
4. Update database schema - add column to `training_parts` table
5. Re-extract features for all training parts
6. Retrain model

#### 5. **Separate Models by Category**

For very different part types, consider training separate models:
- **Model A**: Small brackets (< 100mm)
- **Model B**: Medium housings (100-300mm)
- **Model C**: Large enclosures (> 300mm)

Then route to appropriate model based on bounding box size.

---

## 📝 Step 8: Monitoring & Continuous Improvement

### Track Model Performance Over Time

Keep a log of model versions:

```bash
# models/model_history.json
{
  "models": [
    {
      "version": "v1",
      "date": "2024-12-01",
      "r_squared": 0.72,
      "training_parts": 20,
      "notes": "Initial model"
    },
    {
      "version": "v2",
      "date": "2024-12-15",
      "r_squared": 0.85,
      "training_parts": 50,
      "notes": "Added more diverse parts, improved pocket detection"
    }
  ]
}
```

### Collect Feedback

When users request manual review, collect that data:

1. Save the STEP file
2. Get the actual quote from manufacturer
3. Add to training database
4. Periodically retrain (e.g., monthly)

### A/B Testing (Advanced)

Test new models before full deployment:
- Deploy new model to 10% of users
- Compare manual review request rate
- If lower, roll out to 100%

---

## 🔧 Troubleshooting

### "Insufficient training data" Error

```
InsufficientTrainingDataError: Insufficient training data: 1 rows found, at least 2 required
```

**Solution**: Add more training parts to database (minimum 2, recommended 20+)

### Low R² Score (< 0.5)

**Possible causes**:
1. **Not enough data**: Add more training parts
2. **Bad data**: Check for data entry errors (wrong prices, wrong features)
3. **Features don't correlate**: Your prices may depend on factors not captured (material, finish, supplier mood)
4. **Model too simple**: May need non-linear model (try polynomial features)

### Negative Prices Predicted

**Cause**: Model learned negative coefficients with bad training data

**Solution**:
1. Check training data for errors
2. Ensure price_per_unit is always positive
3. Add more realistic training data
4. Consider adding constraints (minimum price = €30)

### Predictions Way Off for Certain Parts

**Cause**: Missing feature detection or outlier parts

**Solution**:
1. Check feature extraction is working correctly
2. Verify STEP file is valid
3. Add similar parts to training data
4. May need manual review for edge cases

---

## 📊 Example Complete Workflow

Here's a realistic workflow for training your first model:

### Week 1: Initial Data Collection
1. Get quotes from PCBWay for 10 different parts
2. Process each STEP file through app
3. Record real prices + extracted features
4. Add to database using `add_training_data.py`

### Week 2: First Model Training
1. Train initial model: `python -m training.train_model`
2. R² = 0.68 (acceptable for MVP)
3. Test on 3 new parts: average 12% error
4. Deploy to Render for beta testing

### Week 3-4: Collect Feedback
1. Beta users upload 15 parts
2. 5 parts have manual review requests
3. Get real quotes for those 5 parts
4. Add to training database

### Week 5: Retrain
1. Now have 25 training parts total
2. Retrain model: R² = 0.81 (good!)
3. Test again: average 7% error
4. Deploy updated model to production

### Ongoing: Monthly Retraining
1. Collect manual review cases each month
2. Add 5-10 new training parts/month
3. Retrain monthly
4. Monitor R² and error rates
5. Target: R² > 0.85, error < 10%

---

## 🎯 Quick Reference

### Key Commands

```bash
# Create database
python -c "from modules.db import connect, ensure_schema; conn = connect('training/training_data.db'); ensure_schema(conn); conn.close()"

# Train model
python -m training.train_model

# Train with custom paths
python -m training.train_model --db my_data.db --output my_model.json

# Test predictions
python test_model.py

# Cross-validation
python cross_validate.py
```

### Key Files

- `training/training_data.db` - SQLite database with training parts
- `config/pricing_coefficients.json` - Trained model coefficients
- `modules/db.py` - Database functions
- `training/train_model.py` - Training script
- `modules/pricing_config.py` - Required features list

### Success Metrics

- **Minimum viable**: R² > 0.70, 20+ training parts
- **Good**: R² > 0.80, 50+ training parts, <10% avg error
- **Excellent**: R² > 0.90, 100+ training parts, <5% avg error

---

## 📚 Additional Resources

- **Scikit-learn LinearRegression**: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html
- **Understanding R²**: https://en.wikipedia.org/wiki/Coefficient_of_determination
- **StandardScaler**: https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html

---

**Questions or issues?** Open an issue in the repository or contact the development team.
