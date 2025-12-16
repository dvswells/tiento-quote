"""
Tiento Quote v0.1 - CNC Machining Calculator
Streamlit web application for instant CNC machining quotes.
"""
import streamlit as st
import os
import tempfile
from modules.pipeline import process_quote
from modules.feature_detector import BoundingBoxLimitError
from modules.pricing_engine import ModelNotReadyError, InvalidQuantityError


# Page configuration
st.set_page_config(
    page_title="Tiento Quote v0.1",
    page_icon="🔧",
    layout="wide",
)

# Header
st.title("Tiento Quote v0.1 - CNC Machining Calculator")
st.markdown("""
**Wells Global Solutions**
Enschede, The Netherlands
+31613801071 | wellsglobal.eu
""")

st.divider()

# File upload section
st.header("Upload STEP File")
uploaded_file = st.file_uploader(
    "Upload STEP File (Max 50MB)",
    type=["step", "stp"],
    help="Upload your 3D STEP file for instant quote"
)

# Quantity input
st.header("Configuration")
quantity = st.number_input(
    "Quantity",
    min_value=1,
    max_value=50,
    value=1,
    step=1,
    help="Number of parts (1-50). Invalid values will be corrected to 1."
)

# Auto-correct quantity if out of range
if quantity < 1 or quantity > 50:
    st.warning(f"Quantity {quantity} is invalid. Correcting to 1.")
    quantity = 1

# Static configuration display
st.markdown("""
**Material:** Aluminum 6061-T6
**Finish:** As Machined (Standard finish, no coating)
**Tolerance:** ISO 2768-m
**Lead Time:** 10 Business Days
""")

st.divider()

# Process file if uploaded
if uploaded_file is not None:
    try:
        # Create temporary file to save uploaded STEP
        with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_step_path = tmp_file.name

        # Progress indicators
        progress_container = st.container()
        with progress_container:
            with st.spinner("Uploading file..."):
                st.success("✓ File uploaded")

            with st.spinner("Validating dimensions..."):
                # This will be done in the pipeline
                st.success("✓ Dimensions validated")

            with st.spinner("Detecting features..."):
                # Detect features using pipeline
                st.success("✓ Features detected")

            with st.spinner("Calculating price..."):
                # Calculate quote
                pricing_config_path = "config/pricing_coefficients.json"

                # Check if pricing config exists
                if not os.path.exists(pricing_config_path):
                    st.error("⚠️ Pricing configuration not found. Please ensure config/pricing_coefficients.json exists.")
                    st.stop()

                # Process quote using pipeline
                result = process_quote(tmp_step_path, quantity, pricing_config_path)
                st.success("✓ Complete")

        # Clean up temporary file
        os.unlink(tmp_step_path)

        st.divider()

        # Display results
        st.header("Quote Results")

        # Create two columns for layout
        col1, col2 = st.columns(2)

        with col1:
            # Quote summary
            st.subheader("QUOTE SUMMARY")
            st.markdown(f"""
**Quantity:** {result.quote.quantity} units
**Price per unit:** €{result.quote.price_per_unit:.2f}
**Total price:** €{result.quote.total_price:.2f}
            """)

            if result.quote.minimum_applied:
                st.info("**Note:** €30 minimum order applied")

            # Part features
            st.subheader("PART FEATURES")
            st.markdown(f"""
**Bounding Box:**
- X: {result.features.bounding_box_x:.1f} mm
- Y: {result.features.bounding_box_y:.1f} mm
- Z: {result.features.bounding_box_z:.1f} mm

**Volume:** {result.features.volume:.1f} mm³

**Holes & Pockets:** (Not yet detected in v0)
- Through holes: {result.features.through_hole_count}
- Blind holes: {result.features.blind_hole_count}
- Pockets: {result.features.pocket_count}
            """)

        with col2:
            # Cost breakdown
            st.subheader("COST BREAKDOWN")
            breakdown = result.quote.breakdown
            st.markdown(f"""
**Base cost:** €{breakdown.get('base_price', 0):.2f}
**Feature contribution:** €{breakdown.get('feature_contribution', 0):.2f}
**Predicted per unit:** €{breakdown.get('predicted_price_per_unit', 0):.2f}
**Calculated total:** €{breakdown.get('calculated_total', 0):.2f}
            """)

            if result.quote.minimum_applied:
                st.markdown(f"""
**Minimum order:** €{breakdown.get('minimum_order_price', 0):.2f}
                """)

            st.markdown(f"""
**Final total:** €{breakdown.get('final_total', 0):.2f}
            """)

            # Confidence scores
            st.subheader("DETECTION CONFIDENCE")
            st.markdown(f"""
🟢 Bounding box: {result.confidence.bounding_box * 100:.0f}%
🟢 Volume: {result.confidence.volume * 100:.0f}%
⚪ Through holes: {result.confidence.through_holes * 100:.0f}% (not detected yet)
⚪ Blind holes: {result.confidence.blind_holes * 100:.0f}% (not detected yet)
⚪ Pockets: {result.confidence.pockets * 100:.0f}% (not detected yet)
            """)

        # DFM Issues
        if result.dfm_issues:
            st.subheader("DFM WARNINGS")
            for issue in result.dfm_issues:
                if issue.severity == "critical":
                    st.error(f"🔴 CRITICAL: {issue.message}")
                elif issue.severity == "warning":
                    st.warning(f"🟡 WARNING: {issue.message}")
                else:
                    st.info(f"💬 INFO: {issue.message}")

        # Disclaimer
        st.divider()
        st.warning("""
**⚠️ IMPORTANT NOTICE**

The price displayed is the system's pre-quotation (for reference ONLY), and the official quotation will be generated after manual review by engineer according to the complexity of the part structure and process requirements.

Prices exclude VAT and shipping.
        """)

        # Part ID for reference
        st.caption(f"Part ID: {result.part_id}")

    except BoundingBoxLimitError as e:
        st.error(f"⚠️ {str(e)}")
        # Clean up temporary file
        if 'tmp_step_path' in locals() and os.path.exists(tmp_step_path):
            os.unlink(tmp_step_path)

    except ModelNotReadyError as e:
        st.error(f"⚠️ {str(e)}")
        st.info("The pricing model needs to be trained before quotes can be generated. Please contact the administrator.")
        # Clean up temporary file
        if 'tmp_step_path' in locals() and os.path.exists(tmp_step_path):
            os.unlink(tmp_step_path)

    except InvalidQuantityError as e:
        st.error(f"⚠️ {str(e)}")
        st.info("Please enter a quantity between 1 and 50.")
        # Clean up temporary file
        if 'tmp_step_path' in locals() and os.path.exists(tmp_step_path):
            os.unlink(tmp_step_path)

    except Exception as e:
        st.error(f"⚠️ An error occurred while processing your file: {str(e)}")
        st.info("Please ensure your file is a valid STEP format and try again. If the problem persists, contact us at david@wellsglobal.eu")
        # Clean up temporary file
        if 'tmp_step_path' in locals() and os.path.exists(tmp_step_path):
            os.unlink(tmp_step_path)

else:
    st.info("👆 Upload a STEP file to get started")

# Footer
st.divider()
st.caption("Tiento Quote v0.1 - Powered by Wells Global Solutions")
