from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


BASE_DIR = Path(__file__).resolve().parents[2]

REPORT_DIR = BASE_DIR / "uploads" / "reports"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


ORGANIZATION_NAME = "AMB. USMAN MOVEMENT"
ORGANIZATION_SHORT_NAME = "AUM"
TAGLINE = "Together for Progress."


def generate_volunteer_report(volunteers):
    """
    Generate an official AUM volunteer report PDF.

    Returns:
        Absolute path to generated PDF.
    """

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"AUM-volunteer-report-{timestamp}.pdf"
    )

    file_path = REPORT_DIR / filename

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.textColor = colors.HexColor(
        "#0B2347"
    )

    subtitle_style = styles["Normal"]

    elements = []

    # ========================================================
    # HEADER
    # ========================================================

    elements.append(
        Paragraph(
            ORGANIZATION_NAME,
            title_style,
        )
    )

    elements.append(
        Paragraph(
            ORGANIZATION_SHORT_NAME,
            styles["Heading2"],
        )
    )

    elements.append(
        Paragraph(
            TAGLINE,
            subtitle_style,
        )
    )

    elements.append(
        Spacer(
            1,
            10,
        )
    )

    elements.append(
        Paragraph(
            "OFFICIAL VOLUNTEER REGISTRATION REPORT",
            styles["Heading2"],
        )
    )

    elements.append(
        Spacer(
            1,
            10,
        )
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    total = len(volunteers)

    male = sum(
        1
        for volunteer in volunteers
        if str(
            getattr(
                volunteer,
                "gender",
                "",
            )
        ).lower()
        == "male"
    )

    female = sum(
        1
        for volunteer in volunteers
        if str(
            getattr(
                volunteer,
                "gender",
                "",
            )
        ).lower()
        == "female"
    )

    employed = sum(
        1
        for volunteer in volunteers
        if str(
            getattr(
                volunteer,
                "employment_status",
                "",
            )
        ).lower()
        == "employed"
    )

    unemployed = sum(
        1
        for volunteer in volunteers
        if str(
            getattr(
                volunteer,
                "employment_status",
                "",
            )
        ).lower()
        == "unemployed"
    )

    summary_data = [
        [
            "Total Volunteers",
            "Male",
            "Female",
            "Employed",
            "Unemployed",
        ],
        [
            str(total),
            str(male),
            str(female),
            str(employed),
            str(unemployed),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            32 * mm,
            25 * mm,
            25 * mm,
            30 * mm,
            32 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0B2347"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    colors.HexColor("#F1F5F9"),
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    elements.append(
        summary_table
    )

    elements.append(
        Spacer(
            1,
            15,
        )
    )

    # ========================================================
    # VOLUNTEER TABLE
    # ========================================================

    data = [
        [
            "Registration No.",
            "Full Name",
            "Gender",
            "Phone",
            "LGA",
            "Ward",
            "Unit",
        ]
    ]

    for volunteer in volunteers:

        data.append(
            [
                getattr(
                    volunteer,
                    "registration_no",
                    "",
                ),
                getattr(
                    volunteer,
                    "name",
                    "",
                ),
                getattr(
                    volunteer,
                    "gender",
                    "",
                ),
                getattr(
                    volunteer,
                    "phone",
                    "",
                ),
                getattr(
                    volunteer,
                    "lga",
                    "",
                ),
                getattr(
                    volunteer,
                    "ward",
                    "",
                ),
                getattr(
                    volunteer,
                    "unit",
                    "",
                ),
            ]
        )

    table = Table(
        data,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#087A3D"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC"),
                    ],
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    elements.append(table)

    elements.append(
        Spacer(
            1,
            15,
        )
    )

    elements.append(
        Paragraph(
            (
                f"Generated on "
                f"{datetime.now().strftime('%d %B %Y %H:%M')}"
            ),
            styles["Normal"],
        )
    )

    # ========================================================
    # BUILD
    # ========================================================

    document.build(
        elements
    )

    if not file_path.is_file():

        raise RuntimeError(
            "AUM volunteer report was not generated."
        )

    if file_path.stat().st_size <= 0:

        raise RuntimeError(
            "AUM volunteer report is empty."
        )

    return str(file_path)