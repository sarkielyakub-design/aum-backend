from datetime import datetime
import os

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from app.config import (
    APP_NAME,
    APP_SHORT_NAME,
    APP_TAGLINE,
)


# ============================================================
# AUM MEMBERSHIP CARD GENERATOR
# AMB. USMAN MOVEMENT
# ============================================================


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)


# ============================================================
# STORAGE
# ============================================================

CARD_DIR = os.path.join(
    BASE_DIR,
    "uploads",
    "cards",
)

ASSET_DIR = os.path.join(
    BASE_DIR,
    "assets",
    "membership",
)


os.makedirs(
    CARD_DIR,
    exist_ok=True,
)

os.makedirs(
    ASSET_DIR,
    exist_ok=True,
)


# ============================================================
# CARD BACKGROUNDS
# ============================================================

FRONT_BACKGROUND = os.path.join(
    ASSET_DIR,
    "card_front_background.png",
)

BACK_BACKGROUND = os.path.join(
    ASSET_DIR,
    "card_back_background.png",
)


# ============================================================
# FALLBACK BACKGROUNDS
# ============================================================

FRONT_FALLBACKS = [
    os.path.join(
        BASE_DIR,
        "assets",
        "card_front_background.png",
    ),
    os.path.join(
        BASE_DIR,
        "assets",
        "membership",
        "front.png",
    ),
]


BACK_FALLBACKS = [
    os.path.join(
        BASE_DIR,
        "assets",
        "card_back_background.png",
    ),
    os.path.join(
        BASE_DIR,
        "assets",
        "membership",
        "back.png",
    ),
]


# ============================================================
# CARD SIZE
# ============================================================

WIDTH = 750
HEIGHT = 500


# ============================================================
# COLORS
# ============================================================

GREEN = HexColor("#075B30")
DARK_GREEN = HexColor("#064B28")

GOLD = HexColor("#D7A62A")
DARK_GOLD = HexColor("#B88616")

NAVY = HexColor("#0B2347")

WHITE = colors.white
BLACK = colors.black

LIGHT_TEXT = HexColor("#5B6573")
LINE_COLOR = HexColor("#C8D0D9")


# ============================================================
# TEXT
# ============================================================

OFFICIAL_MEMBER_TEXT = "OFFICIAL MEMBER"

VERIFICATION_TEXT = (
    "Scan the QR code to verify this membership."
)


# ============================================================
# PATH HELPER
# ============================================================

def resolve_file_path(path):
    """
    Convert a relative project path into an absolute path.
    """

    if not path:
        return None

    path = str(path).strip()

    if not path:
        return None

    if os.path.isabs(path):
        return path

    return os.path.abspath(
        os.path.join(
            BASE_DIR,
            path,
        )
    )


# ============================================================
# ASSET RESOLVER
# ============================================================

def resolve_asset(
    primary,
    fallbacks=None,
):
    """
    Resolve the primary asset first.
    If unavailable, try fallback assets.
    """

    if (
        primary
        and os.path.isfile(primary)
    ):
        return primary

    for path in fallbacks or []:

        if (
            path
            and os.path.isfile(path)
        ):
            return path

    return primary


# ============================================================
# DRAW BACKGROUND
# ============================================================

def draw_background(
    c,
    image_path,
):
    """
    Draw the supplied membership-card artwork.

    The artwork contains the complete visual design.
    Python only adds dynamic member information on top.
    """

    image_path = resolve_file_path(
        image_path
    )

    if (
        not image_path
        or not os.path.isfile(image_path)
    ):
        raise FileNotFoundError(
            "Membership card background not found: "
            f"{image_path}"
        )

    c.drawImage(
        ImageReader(image_path),
        0,
        0,
        width=WIDTH,
        height=HEIGHT,
        preserveAspectRatio=False,
        mask="auto",
    )


# ============================================================
# FIT TEXT
# ============================================================

def draw_fitted_text(
    c,
    text,
    x,
    y,
    max_width,
    font="Helvetica-Bold",
    font_size=9,
    min_font_size=6,
    color=NAVY,
):
    """
    Draw text and automatically reduce its size
    when it becomes too wide.
    """

    text = str(
        text
        if text is not None
        else "—"
    ).strip()

    if not text:
        text = "—"

    size = font_size

    while (
        size > min_font_size
        and stringWidth(
            text,
            font,
            size,
        ) > max_width
    ):
        size -= 0.5

    c.setFont(
        font,
        size,
    )

    c.setFillColor(
        color
    )

    c.drawString(
        x,
        y,
        text,
    )


# ============================================================
# JOINED DATE
# ============================================================

def get_joined_date(
    member,
):
    """
    Return formatted membership creation date.
    """

    created_at = getattr(
        member,
        "created_at",
        None,
    )

    if created_at:

        if isinstance(
            created_at,
            datetime,
        ):
            return created_at.strftime(
                "%d %B %Y"
            )

        if hasattr(
            created_at,
            "strftime",
        ):
            return created_at.strftime(
                "%d %B %Y"
            )

    return datetime.now().strftime(
        "%d %B %Y"
    )


# ============================================================
# DRAW MEMBER PHOTO
# ============================================================

def draw_member_photo(
    c,
    member,
):
    """
    Draw member passport photograph.

    FRONT ONLY.
    """

    passport = getattr(
        member,
        "passport",
        None,
    )

    passport = resolve_file_path(
        passport
    )

    if not passport:
        print(
            "⚠️ Member has no passport photo."
        )
        return

    if not os.path.isfile(passport):
        print(
            "⚠️ Passport photo not found: "
            f"{passport}"
        )
        return

    # ========================================================
    # PHOTO POSITION
    # ========================================================
    #
    # Adjust these coordinates if your final
    # front artwork has a different photo area.
    #
    # ========================================================

    x = 42
    y = 120

    photo_width = 175
    photo_height = 245

    try:

        # ----------------------------------------------------
        # White frame
        # ----------------------------------------------------

        c.setFillColor(
            WHITE
        )

        c.roundRect(
            x - 4,
            y - 4,
            photo_width + 8,
            photo_height + 8,
            12,
            fill=1,
            stroke=0,
        )

        # ----------------------------------------------------
        # Gold outer border
        # ----------------------------------------------------

        c.setStrokeColor(
            GOLD
        )

        c.setLineWidth(
            3
        )

        c.roundRect(
            x,
            y,
            photo_width,
            photo_height,
            10,
            fill=0,
            stroke=1,
        )

        # ----------------------------------------------------
        # Green inner border
        # ----------------------------------------------------

        c.setStrokeColor(
            GREEN
        )

        c.setLineWidth(
            1.5
        )

        c.roundRect(
            x + 2,
            y + 2,
            photo_width - 4,
            photo_height - 4,
            8,
            fill=0,
            stroke=1,
        )

        # ----------------------------------------------------
        # Passport
        # ----------------------------------------------------

        c.drawImage(
            ImageReader(passport),
            x + 4,
            y + 4,
            width=photo_width - 8,
            height=photo_height - 8,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

    except Exception as exc:

        print(
            "⚠️ Could not draw passport photo: "
            f"{exc}"
        )


# ============================================================
# OFFICIAL MEMBER BADGE
# ============================================================

def draw_official_member_badge(
    c,
):
    """
    Draw a small professional OFFICIAL MEMBER
    badge on the front.
    """

    x = 655
    y = 92

    outer_radius = 36
    inner_radius = 29

    # Gold outer circle
    c.setFillColor(
        GOLD
    )

    c.circle(
        x,
        y,
        outer_radius,
        fill=1,
        stroke=0,
    )

    # White inner circle
    c.setFillColor(
        WHITE
    )

    c.circle(
        x,
        y,
        inner_radius,
        fill=1,
        stroke=0,
    )

    # AUM
    c.setFillColor(
        GREEN
    )

    c.setFont(
        "Helvetica-Bold",
        8,
    )

    c.drawCentredString(
        x,
        y + 4,
        APP_SHORT_NAME,
    )

    c.setFont(
        "Helvetica-Bold",
        6,
    )

    c.drawCentredString(
        x,
        y - 7,
        "OFFICIAL",
    )

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        7,
    )

    c.drawCentredString(
        x,
        y - 17,
        "MEMBER",
    )


# ============================================================
# FRONT MEMBER INFORMATION
# ============================================================

def draw_member_information(
    c,
    member,
):
    """
    Draw dynamic member information.

    The background artwork contains the
    visual design and labels.

    This function only draws the values.
    """

    # ========================================================
    # VALUE COLUMN
    # ========================================================

    value_x = 385

    max_width = 300


    # ========================================================
    # MEMBERSHIP NUMBER
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "registration_no",
            "",
        ),
        value_x,
        370,
        max_width,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )


    # ========================================================
    # FULL NAME
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "name",
            "",
        ),
        value_x,
        339,
        max_width,
        font="Helvetica-Bold",
        font_size=9.5,
        min_font_size=6,
        color=NAVY,
    )


    # ========================================================
    # GENDER
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "gender",
            "",
        ),
        value_x,
        308,
        120,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )


    # ========================================================
    # AGE
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "age",
            "",
        ),
        value_x,
        277,
        80,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )


    # ========================================================
    # PHONE NUMBER
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "phone",
            "",
        ),
        value_x,
        246,
        240,
        font="Helvetica-Bold",
        font_size=8.5,
        min_font_size=6,
        color=NAVY,
    )


    # ========================================================
    # LGA
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "lga",
            "",
        ),
        value_x,
        215,
        180,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )


    # ========================================================
    # WARD
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "ward",
            "",
        ),
        value_x,
        184,
        180,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )


    # ========================================================
    # UNIT
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "unit",
            "",
        ),
        value_x,
        153,
        180,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )


    # ========================================================
    # JOINED
    # ========================================================

    draw_fitted_text(
        c,
        get_joined_date(
            member
        ),
        value_x,
        122,
        180,
        font="Helvetica-Bold",
        font_size=8,
        min_font_size=6,
        color=NAVY,
    )


# ============================================================
# FRONT
# ============================================================

def draw_front(
    c,
    member,
    front_background,
):
    """
    Generate FRONT of membership card.

    QR CODE IS NOT DRAWN HERE.
    """

    # --------------------------------------------------------
    # Background artwork
    # --------------------------------------------------------

    draw_background(
        c,
        front_background,
    )

    # --------------------------------------------------------
    # Passport
    # --------------------------------------------------------

    draw_member_photo(
        c,
        member,
    )

    # --------------------------------------------------------
    # Member information
    # --------------------------------------------------------

    draw_member_information(
        c,
        member,
    )

    # --------------------------------------------------------
    # Official member badge
    # --------------------------------------------------------

    draw_official_member_badge(
        c,
    )


# ============================================================
# DRAW QR CODE
# ============================================================

def draw_member_qr(
    c,
    qr_path,
):
    """
    Draw QR code on the BACK of the card.
    """

    qr_path = resolve_file_path(
        qr_path
    )

    if not qr_path:
        print(
            "⚠️ No QR code supplied."
        )
        return

    if not os.path.isfile(qr_path):
        print(
            "⚠️ QR code not found: "
            f"{qr_path}"
        )
        return

    # ========================================================
    # QR POSITION
    # ========================================================

    x = 535
    y = 160
    size = 125

    try:

        # White QR container
        c.setFillColor(
            WHITE
        )

        c.roundRect(
            x - 10,
            y - 10,
            size + 20,
            size + 20,
            12,
            fill=1,
            stroke=0,
        )

        # Gold border
        c.setStrokeColor(
            GOLD
        )

        c.setLineWidth(
            2
        )

        c.roundRect(
            x - 5,
            y - 5,
            size + 10,
            size + 10,
            8,
            fill=0,
            stroke=1,
        )

        # QR
        c.drawImage(
            ImageReader(qr_path),
            x,
            y,
            width=size,
            height=size,
            preserveAspectRatio=False,
            mask="auto",
        )

        # Label
        c.setFillColor(
            NAVY
        )

        c.setFont(
            "Helvetica-Bold",
            8,
        )

        c.drawCentredString(
            x + size / 2,
            y - 25,
            "SCAN TO VERIFY",
        )

    except Exception as exc:

        print(
            "⚠️ Could not draw QR code: "
            f"{exc}"
        )


# ============================================================
# BACK MEMBER DETAILS
# ============================================================

def draw_back_information(
    c,
    member,
):
    """
    Draw limited member information on the back.
    """

    # --------------------------------------------------------
    # Information panel
    # --------------------------------------------------------

    panel_x = 55
    panel_y = 155
    panel_width = 420
    panel_height = 205

    c.setFillColor(
        WHITE
    )

    c.roundRect(
        panel_x,
        panel_y,
        panel_width,
        panel_height,
        14,
        fill=1,
        stroke=0,
    )

    # Gold border
    c.setStrokeColor(
        GOLD
    )

    c.setLineWidth(
        1.5
    )

    c.roundRect(
        panel_x,
        panel_y,
        panel_width,
        panel_height,
        14,
        fill=0,
        stroke=1,
    )

    # --------------------------------------------------------
    # Heading
    # --------------------------------------------------------

    c.setFillColor(
        GREEN
    )

    c.setFont(
        "Helvetica-Bold",
        13,
    )

    c.drawString(
        panel_x + 20,
        panel_y + panel_height - 30,
        "MEMBERSHIP VERIFICATION",
    )

    # --------------------------------------------------------
    # Details
    # --------------------------------------------------------

    details = [
        (
            "MEMBERSHIP NO.",
            getattr(
                member,
                "registration_no",
                "",
            ),
        ),
        (
            "FULL NAME",
            getattr(
                member,
                "name",
                "",
            ),
        ),
        (
            "LGA",
            getattr(
                member,
                "lga",
                "",
            ),
        ),
        (
            "WARD",
            getattr(
                member,
                "ward",
                "",
            ),
        ),
        (
            "UNIT",
            getattr(
                member,
                "unit",
                "",
            ),
        ),
    ]

    y = panel_y + panel_height - 58

    for label, value in details:

        c.setFillColor(
            LIGHT_TEXT
        )

        c.setFont(
            "Helvetica-Bold",
            7,
        )

        c.drawString(
            panel_x + 20,
            y,
            label,
        )

        draw_fitted_text(
            c,
            value,
            panel_x + 125,
            y,
            270,
            font="Helvetica-Bold",
            font_size=8,
            min_font_size=6,
            color=NAVY,
        )

        y -= 27


# ============================================================
# BACK
# ============================================================

def draw_back(
    c,
    member,
    qr_path,
    back_background,
):
    """
    Generate BACK of membership card.
    """

    # --------------------------------------------------------
    # Background artwork
    # --------------------------------------------------------

    draw_background(
        c,
        back_background,
    )

    # --------------------------------------------------------
    # Verification title
    # --------------------------------------------------------

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        18,
    )

    c.drawString(
        55,
        405,
        "MEMBERSHIP VERIFICATION",
    )

    # --------------------------------------------------------
    # Verification subtitle
    # --------------------------------------------------------

    c.setFillColor(
        LIGHT_TEXT
    )

    c.setFont(
        "Helvetica",
        9,
    )

    c.drawString(
        55,
        385,
        VERIFICATION_TEXT,
    )

    # --------------------------------------------------------
    # Member details
    # --------------------------------------------------------

    draw_back_information(
        c,
        member,
    )

    # --------------------------------------------------------
    # QR CODE
    # --------------------------------------------------------

    draw_member_qr(
        c,
        qr_path,
    )

    # --------------------------------------------------------
    # Organization footer
    # --------------------------------------------------------

    c.setFillColor(
        GREEN
    )

    c.setFont(
        "Helvetica-Bold",
        10,
    )

    c.drawString(
        55,
        95,
        APP_NAME,
    )

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica",
        8,
    )

    c.drawString(
        55,
        78,
        APP_TAGLINE,
    )

    c.setFillColor(
        GOLD
    )

    c.setFont(
        "Helvetica-Bold",
        8,
    )

    c.drawRightString(
        695,
        78,
        "OFFICIAL MEMBER ID",
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_membership_card(
    member,
    qr_path=None,
):
    """
    Generate a two-page AUM membership card.

    PAGE 1:
        Front
        - Background artwork
        - Passport
        - Member information
        - Official Member badge
        - NO QR CODE

    PAGE 2:
        Back
        - Background artwork
        - Verification information
        - QR code
        - Official member footer

    Returns:
        Absolute PDF path.
    """

    # ========================================================
    # REGISTRATION NUMBER
    # ========================================================

    registration_no = getattr(
        member,
        "registration_no",
        None,
    )

    if not registration_no:
        raise ValueError(
            "Member registration number is required."
        )


    # ========================================================
    # RESOLVE BACKGROUNDS
    # ========================================================

    front_background = resolve_asset(
        FRONT_BACKGROUND,
        FRONT_FALLBACKS,
    )

    back_background = resolve_asset(
        BACK_BACKGROUND,
        BACK_FALLBACKS,
    )


    # ========================================================
    # VERIFY FRONT
    # ========================================================

    if (
        not front_background
        or not os.path.isfile(
            front_background
        )
    ):
        raise FileNotFoundError(
            "AUM front membership background not found: "
            f"{front_background}"
        )


    # ========================================================
    # VERIFY BACK
    # ========================================================

    if (
        not back_background
        or not os.path.isfile(
            back_background
        )
    ):
        raise FileNotFoundError(
            "AUM back membership background not found: "
            f"{back_background}"
        )


    # ========================================================
    # OUTPUT
    # ========================================================

    pdf_path = os.path.join(
        CARD_DIR,
        f"{registration_no}-membership-card.pdf",
    )


    # ========================================================
    # LOGGING
    # ========================================================

    print(
        "📄 Generating AUM membership card..."
    )

    print(
        f"   Organization: {APP_NAME}"
    )

    print(
        f"   Member: {registration_no}"
    )

    print(
        f"   Front: {front_background}"
    )

    print(
        f"   Back: {back_background}"
    )

    print(
        f"   QR: {qr_path or 'Not supplied'}"
    )

    print(
        f"   Output: {pdf_path}"
    )


    # ========================================================
    # CREATE PDF
    # ========================================================

    c = canvas.Canvas(
        pdf_path,
        pagesize=(
            WIDTH,
            HEIGHT,
        ),
    )


    c.setTitle(
        f"{APP_NAME} Membership Card - "
        f"{registration_no}"
    )

    c.setAuthor(
        APP_NAME
    )


    # ========================================================
    # PAGE 1 — FRONT
    # ========================================================

    draw_front(
        c,
        member,
        front_background,
    )

    c.showPage()


    # ========================================================
    # PAGE 2 — BACK
    # ========================================================

    draw_back(
        c,
        member,
        qr_path,
        back_background,
    )

    c.showPage()


    # ========================================================
    # SAVE
    # ========================================================

    c.save()


    # ========================================================
    # VERIFY
    # ========================================================

    if not os.path.isfile(
        pdf_path
    ):
        raise FileNotFoundError(
            "Membership card PDF was not generated: "
            f"{pdf_path}"
        )


    file_size = os.path.getsize(
        pdf_path
    )

    if file_size <= 0:
        raise RuntimeError(
            "Membership card PDF was generated "
            "but is empty."
        )


    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "✅ AUM membership card generated successfully."
    )

    print(
        f"   PDF: {pdf_path}"
    )

    print(
        f"   Size: {file_size:,} bytes"
    )


    return pdf_path