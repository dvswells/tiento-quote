#!/bin/bash
# Startup script for Render deployment

# Exit on error
set -e

echo "Starting Tiento Quote v0.1..."

# Create necessary directories
echo "Creating required directories..."
mkdir -p uploads
mkdir -p temp
mkdir -p training
mkdir -p config

# Check if pricing config exists, if not create a default one
if [ ! -f "config/pricing_coefficients.json" ]; then
    echo "Warning: pricing_coefficients.json not found. Creating default config..."
    cat > config/pricing_coefficients.json << 'EOF'
{
  "base_price": 20.0,
  "minimum_order_price": 30.0,
  "r_squared": 0.0,
  "coefficients": {
    "volume": 0.0001,
    "bounding_box_x": 0.01,
    "bounding_box_y": 0.01,
    "bounding_box_z": 0.01,
    "through_hole_count": 1.5,
    "blind_hole_count": 2.0,
    "blind_hole_max_depth_to_diameter": 0.5,
    "pocket_count": 3.0,
    "pocket_total_volume": 0.0002,
    "non_standard_hole_count": 2.5
  },
  "scaler_mean": {
    "volume": 100000.0,
    "bounding_box_x": 100.0,
    "bounding_box_y": 100.0,
    "bounding_box_z": 100.0,
    "through_hole_count": 2.0,
    "blind_hole_count": 1.0,
    "blind_hole_max_depth_to_diameter": 5.0,
    "pocket_count": 1.0,
    "pocket_total_volume": 5000.0,
    "non_standard_hole_count": 0.5
  },
  "scaler_std": {
    "volume": 50000.0,
    "bounding_box_x": 50.0,
    "bounding_box_y": 50.0,
    "bounding_box_z": 50.0,
    "through_hole_count": 1.5,
    "blind_hole_count": 1.0,
    "blind_hole_max_depth_to_diameter": 3.0,
    "pocket_count": 1.0,
    "pocket_total_volume": 3000.0,
    "non_standard_hole_count": 0.5
  },
  "last_updated": "2024-01-01T00:00:00Z"
}
EOF
fi

# Set environment variables with defaults
export DATABASE_PATH=${DATABASE_PATH:-"training/training_data.db"}
export UPLOADS_PATH=${UPLOADS_PATH:-"uploads"}
export TEMP_PATH=${TEMP_PATH:-"temp"}
export MAX_UPLOAD_SIZE=${MAX_UPLOAD_SIZE:-52428800}

echo "Environment configured:"
echo "  DATABASE_PATH: $DATABASE_PATH"
echo "  UPLOADS_PATH: $UPLOADS_PATH"
echo "  TEMP_PATH: $TEMP_PATH"

# Start Streamlit
echo "Starting Streamlit server..."
streamlit run app.py \
  --server.port=${PORT:-8501} \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
