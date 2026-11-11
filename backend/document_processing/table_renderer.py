
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

INPUT_PATH = Path("data/processed/merged_tables.json")

OUTPUT_DIR = Path(
    "data/processed/diagrams/combined_tables"
)

OUTPUT_PATH = OUTPUT_DIR / "complete_hadoop_distro_table.png"


# --------------------------------------------------
# 2. Table design settings
# --------------------------------------------------

IMAGE_WIDTH = 1800

PADDING = 25
HEADER_HEIGHT = 90

FONT_SIZE = 25
HEADER_FONT_SIZE = 29

LINE_SPACING = 10
CELL_PADDING = 22

COLUMN_RATIOS = [0.22, 0.53, 0.25]

BACKGROUND_COLOR = "#FFFFFF"
HEADER_COLOR = "#243447"
HEADER_TEXT_COLOR = "#FFFFFF"

ROW_COLORS = ["#F0F4F8", "#FFFFFF"]

TEXT_COLOR = "#222222"
BORDER_COLOR = "#AAB7C4"


# --------------------------------------------------
# 3. Load fonts
# --------------------------------------------------

def load_font(size, bold=False):

    if bold:
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf"
        ]
    else:
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf"
        ]

    for font_path in font_paths:

        if Path(font_path).exists():

            return ImageFont.truetype(
                font_path,
                size
            )

    return ImageFont.load_default()


FONT = load_font(FONT_SIZE)
HEADER_FONT = load_font(HEADER_FONT_SIZE, bold=True)


# --------------------------------------------------
# 4. Convert extracted 'o' markers to bullets
# --------------------------------------------------

def format_bullets(text):

    lines = text.splitlines()

    formatted_lines = []

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if line.lower() == "o" and i + 1 < len(lines):

            next_line = lines[i + 1].strip()

            if next_line:
                formatted_lines.append("• " + next_line)

            i += 2

        else:

            if line:
                formatted_lines.append(line)

            i += 1

    return "\n".join(formatted_lines)


# --------------------------------------------------
# 5. Wrap text according to column width
# --------------------------------------------------

def wrap_text(text, font, max_width, draw):

    wrapped_lines = []

    paragraphs = text.splitlines()

    for paragraph in paragraphs:

        words = paragraph.split()

        if not words:
            wrapped_lines.append("")
            continue

        current_line = ""

        for word in words:

            test_line = (
                word if not current_line
                else current_line + " " + word
            )

            text_width = draw.textbbox(
                (0, 0),
                test_line,
                font=font
            )[2]

            if text_width <= max_width:

                current_line = test_line

            else:

                if current_line:
                    wrapped_lines.append(current_line)

                current_line = word

        if current_line:
            wrapped_lines.append(current_line)

    return wrapped_lines


# --------------------------------------------------
# 6. Prepare cell content
# --------------------------------------------------

def prepare_cell(text, font, width, draw):

    text = str(text or "").strip()

    text = format_bullets(text)

    available_width = width - (2 * CELL_PADDING)

    return wrap_text(
        text,
        font,
        available_width,
        draw
    )


# --------------------------------------------------
# 7. Calculate row height automatically
# --------------------------------------------------

def calculate_row_height(row, column_widths, draw):

    maximum_lines = 1

    for index, value in enumerate(row):

        lines = prepare_cell(
            value,
            FONT,
            column_widths[index],
            draw
        )

        maximum_lines = max(
            maximum_lines,
            len(lines)
        )

    line_height = FONT_SIZE + LINE_SPACING

    row_height = (
        maximum_lines * line_height
        + (2 * CELL_PADDING)
    )

    return row_height


# --------------------------------------------------
# 8. Draw text inside a cell
# --------------------------------------------------

def draw_cell_text(
    draw,
    text,
    x,
    y,
    width,
    font,
    color
):

    lines = prepare_cell(
        text,
        font,
        width,
        draw
    )

    line_height = font.size + LINE_SPACING

    current_y = y + CELL_PADDING

    for line in lines:

        draw.text(
            (x + CELL_PADDING, current_y),
            line,
            font=font,
            fill=color
        )

        current_y += line_height


# --------------------------------------------------
# 9. Render the complete table
# --------------------------------------------------

def render_table(data):

    headers = data["headers"]
    rows = data["rows"]

    column_widths = [
        int(IMAGE_WIDTH * ratio)
        for ratio in COLUMN_RATIOS
    ]

    # Adjust final column to use remaining width
    column_widths[-1] = (
        IMAGE_WIDTH - sum(column_widths[:-1])
    )

    # Temporary image for text measurement
    temp_image = Image.new(
        "RGB",
        (IMAGE_WIDTH, 100),
        BACKGROUND_COLOR
    )

    temp_draw = ImageDraw.Draw(temp_image)

    # Calculate all row heights
    row_heights = []

    for row in rows:

        row_values = [
            row.get("distro", ""),
            row.get("remarks", ""),
            row.get("free_premium", "")
        ]

        height = calculate_row_height(
            row_values,
            column_widths,
            temp_draw
        )

        row_heights.append(height)

    # Calculate total image height
    total_height = (
        (2 * PADDING)
        + HEADER_HEIGHT
        + sum(row_heights)
    )

    # Create final image
    image = Image.new(
        "RGB",
        (IMAGE_WIDTH, total_height),
        BACKGROUND_COLOR
    )

    draw = ImageDraw.Draw(image)

    # Starting coordinates
    x_start = PADDING
    y_start = PADDING

    table_width = IMAGE_WIDTH - (2 * PADDING)

    # Recalculate widths inside table boundaries
    column_widths = [
        int(table_width * ratio)
        for ratio in COLUMN_RATIOS
    ]

    column_widths[-1] = (
        table_width - sum(column_widths[:-1])
    )

    # ----------------------------------------------
    # Draw header
    # ----------------------------------------------

    draw.rectangle(
        [
            x_start,
            y_start,
            x_start + table_width,
            y_start + HEADER_HEIGHT
        ],
        fill=HEADER_COLOR
    )

    current_x = x_start

    for index, header in enumerate(headers):

        draw_cell_text(
            draw,
            header,
            current_x,
            y_start,
            column_widths[index],
            HEADER_FONT,
            HEADER_TEXT_COLOR
        )

        current_x += column_widths[index]

    # ----------------------------------------------
    # Draw table rows
    # ----------------------------------------------

    current_y = y_start + HEADER_HEIGHT

    for row_index, row in enumerate(rows):

        row_values = [
            row.get("distro", ""),
            row.get("remarks", ""),
            row.get("free_premium", "")
        ]

        row_height = row_heights[row_index]

        row_color = ROW_COLORS[
            row_index % len(ROW_COLORS)
        ]

        draw.rectangle(
            [
                x_start,
                current_y,
                x_start + table_width,
                current_y + row_height
            ],
            fill=row_color
        )

        current_x = x_start

        for column_index, value in enumerate(row_values):

            draw_cell_text(
                draw,
                value,
                current_x,
                current_y,
                column_widths[column_index],
                FONT,
                TEXT_COLOR
            )

            current_x += column_widths[column_index]

        current_y += row_height

    # ----------------------------------------------
    # Draw outer border
    # ----------------------------------------------

    draw.rectangle(
        [
            x_start,
            y_start,
            x_start + table_width,
            current_y
        ],
        outline=HEADER_COLOR,
        width=3
    )

    # ----------------------------------------------
    # Draw vertical column borders
    # ----------------------------------------------

    current_x = x_start

    for column_width in column_widths[:-1]:

        current_x += column_width

        draw.line(
            [
                (current_x, y_start),
                (current_x, current_y)
            ],
            fill=BORDER_COLOR,
            width=2
        )

    # ----------------------------------------------
    # Draw header bottom border
    # ----------------------------------------------

    draw.line(
        [
            (x_start, y_start + HEADER_HEIGHT),
            (x_start + table_width, y_start + HEADER_HEIGHT)
        ],
        fill=BORDER_COLOR,
        width=2
    )

    # Save image
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    image.save(
        OUTPUT_PATH,
        format="PNG"
    )

    print("\nTable rendering completed successfully!")

    print(f"Total rows: {len(rows)}")

    print(f"Image size: {image.size}")

    print(f"Saved at: {OUTPUT_PATH}")


# --------------------------------------------------
# 10. Main execution
# --------------------------------------------------

def main():

    if not INPUT_PATH.exists():

        raise FileNotFoundError(
            f"Input JSON not found: {INPUT_PATH}"
        )

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    render_table(data)


if __name__ == "__main__":

    main()
