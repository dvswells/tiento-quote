"""
PDF Quote Generator

Generates professional PDF quotes from processing results.
Uses reportlab for PDF generation.
"""

from datetime import datetime
from typing import Optional
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from modules.domain import ProcessingResult, DfmIssue


def generate_quote_pdf(processing_result: ProcessingResult) -> bytes:
    """
    Generate a professional PDF quote from processing results.

    Args:
        processing_result: Complete processing result with features, quote, and DFM issues

    Returns:
        PDF content as bytes

    Page 1 includes:
    - Header with company name and quote version
    - Quote date and part UUID
    - Specifications (material, finish, tolerance, lead time)
    - Pricing summary and breakdown
    - DFM warnings (if any)
    - Disclaimer

    Future: Page 2 with 3D preview (Prompt 26)
    """
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    # Container for PDF elements
    elements = []

    # Get styles
    styles = getSampleStyleSheet()

    # Add custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        spaceBefore=12
    )

    # Header
    elements.append(Paragraph("Tiento Quote v0.1", title_style))
    elements.append(Spacer(1, 6*mm))

    # Quote metadata
    quote_date = datetime.now().strftime("%Y-%m-%d")
    metadata = [
        ["Quote Date:", quote_date],
        ["Part ID:", processing_result.part_id]
    ]

    metadata_table = Table(metadata, colWidths=[40*mm, 120*mm])
    metadata_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(metadata_table)
    elements.append(Spacer(1, 8*mm))

    # Specifications
    elements.append(Paragraph("Specifications", heading_style))

    specs = [
        ["Material:", "Aluminum 6061-T6"],
        ["Finish:", "As-machined"],
        ["Tolerance:", "±0.1mm (standard)"],
        ["Lead Time:", "5-7 business days"]
    ]

    specs_table = Table(specs, colWidths=[40*mm, 120*mm])
    specs_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
    ]))

    elements.append(specs_table)
    elements.append(Spacer(1, 8*mm))

    # Pricing Summary
    if processing_result.quote:
        elements.append(Paragraph("Pricing Summary", heading_style))

        quote = processing_result.quote

        pricing_data = [
            ["Description", "Value"],
            ["Quantity", str(quote.quantity)],
            ["Price per Unit", f"€{quote.price_per_unit:.2f}"],
            ["Total Price", f"€{quote.total_price:.2f}"],
        ]

        if quote.minimum_applied:
            pricing_data.append(["", "(Minimum order applied)"])

        pricing_table = Table(pricing_data, colWidths=[80*mm, 80*mm])
        pricing_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.white),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#e0e0e0')),
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#2c3e50')),
            ('FONT', (0, -2), (-1, -2), 'Helvetica-Bold', 11),
        ]))

        elements.append(pricing_table)
        elements.append(Spacer(1, 6*mm))

        # Pricing Breakdown
        if quote.breakdown:
            elements.append(Paragraph("Cost Breakdown", heading_style))

            breakdown_data = [["Component", "Cost"]]
            for component, cost in quote.breakdown.items():
                breakdown_data.append([component.replace('_', ' ').title(), f"€{cost:.2f}"])

            breakdown_table = Table(breakdown_data, colWidths=[80*mm, 80*mm])
            breakdown_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ]))

            elements.append(breakdown_table)
            elements.append(Spacer(1, 8*mm))

    # DFM Warnings
    if processing_result.dfm_issues:
        elements.append(Paragraph("Manufacturing Considerations", heading_style))

        # Group by severity
        critical_issues = [i for i in processing_result.dfm_issues if i.severity == "critical"]
        warning_issues = [i for i in processing_result.dfm_issues if i.severity == "warning"]
        info_issues = [i for i in processing_result.dfm_issues if i.severity == "info"]

        dfm_data = []

        for issue in critical_issues:
            dfm_data.append(["⚠ CRITICAL", issue.message])

        for issue in warning_issues:
            dfm_data.append(["⚠ Warning", issue.message])

        for issue in info_issues:
            dfm_data.append(["ℹ Info", issue.message])

        if dfm_data:
            dfm_table = Table(dfm_data, colWidths=[30*mm, 130*mm])
            dfm_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff9e6')),
            ]))

            elements.append(dfm_table)
            elements.append(Spacer(1, 8*mm))

    # Disclaimer
    elements.append(Spacer(1, 10*mm))
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_LEFT
    )

    disclaimer_text = """
    <b>Disclaimer:</b> This quote is automatically generated based on 3D model analysis.
    Final pricing may vary based on manual review of manufacturing requirements.
    All prices are in EUR and exclude VAT and shipping. Quote valid for 30 days.
    """

    elements.append(Paragraph(disclaimer_text, disclaimer_style))

    # Build PDF
    doc.build(elements)

    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
