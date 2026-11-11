
import pymupdf
from pathlib import Path


# --------------------------------------------------
# 1. DETECT TABLES IN A PDF PAGE
# --------------------------------------------------

def detect_tables(pdf_path, page_number):
    """
    Detect complete tables on a specific PDF page.

    Page numbering starts from 1.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    with pymupdf.open(pdf_path) as document:

        if page_number < 1 or page_number > len(document):
            raise ValueError(
                f"Invalid page number. "
                f"PDF has {len(document)} pages."
            )

        page = document[page_number - 1]

        print(f"\nScanning page {page_number} for tables...")

        # Use PyMuPDF's table detection
        table_finder = page.find_tables()

        detected_tables = []

        for index, table in enumerate(
            table_finder.tables,
            start=1
        ):

            bbox = pymupdf.Rect(table.bbox)

            # Extract table contents
            extracted_data = table.extract()

            detected_tables.append({

                "page": page_number,

                "table_number": index,

                "bbox": tuple(bbox),

                "rows": table.row_count,

                "columns": table.col_count,

                "data": extracted_data

            })

        return detected_tables


# --------------------------------------------------
# 2. DISPLAY TABLE DETECTION RESULTS
# --------------------------------------------------

def display_tables(tables):

    print("\n" + "=" * 60)
    print("TABLE DETECTION RESULTS")
    print("=" * 60)

    print(f"\nTotal tables detected: {len(tables)}")

    for table in tables:

        print(f"\nTable {table['table_number']}")

        print(f"Page: {table['page']}")

        print(f"Rows: {table['rows']}")

        print(f"Columns: {table['columns']}")

        print(f"Bounding box: {table['bbox']}")

        print("\nExtracted content:")

        for row in table["data"]:

            print(row)


# --------------------------------------------------
# 3. CROP COMPLETE TABLES
# --------------------------------------------------

def crop_tables(
    pdf_path,
    page_number,
    output_dir="data/processed/diagrams/tables",
    dpi=200,
    padding=5
):
    """
    Crop complete detected tables from a PDF page.

    Padding adds a small margin around each table
    to preserve its outer borders.
    """

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Detect tables first
    tables = detect_tables(
        pdf_path,
        page_number
    )

    if not tables:

        print(
            f"\nNo tables detected on page {page_number}."
        )

        return []

    saved_images = []

    with pymupdf.open(pdf_path) as document:

        page = document[page_number - 1]

        page_bounds = page.rect

        for table in tables:

            original_rect = pymupdf.Rect(
                table["bbox"]
            )

            # Expand the table boundary slightly
            crop_rect = pymupdf.Rect(
                max(
                    page_bounds.x0,
                    original_rect.x0 - padding
                ),
                max(
                    page_bounds.y0,
                    original_rect.y0 - padding
                ),
                min(
                    page_bounds.x1,
                    original_rect.x1 + padding
                ),
                min(
                    page_bounds.y1,
                    original_rect.y1 + padding
                )
            )

            # Render the complete table region
            pixmap = page.get_pixmap(
                dpi=dpi,
                clip=crop_rect,
                alpha=False
            )

            image_name = (
                f"{pdf_path.stem}_page_{page_number}"
                f"_table_{table['table_number']}.png"
            )

            image_path = output_dir / image_name

            pixmap.save(str(image_path))

            saved_images.append({

                "page": page_number,

                "table_number": table["table_number"],

                "rows": table["rows"],

                "columns": table["columns"],

                "image_path": str(image_path)

            })

            print(
                f"\nTable {table['table_number']} cropped successfully."
            )

            print(
                f"Dimensions: "
                f"{table['rows']} rows x "
                f"{table['columns']} columns"
            )

            print(f"Saved: {image_path}")

    return saved_images


# --------------------------------------------------
# 4. MAIN TEST
# --------------------------------------------------

if __name__ == "__main__":

    pdf_path = "data/raw/sample.pdf"

    test_pages = [7, 8, 9]

    print("\n" + "=" * 60)
    print("PRODUCTION RAG - TABLE DETECTION")
    print("=" * 60)

    total_tables = 0

    for page_number in test_pages:

        print("\n" + "#" * 60)
        print(f"PROCESSING PAGE {page_number}")
        print("#" * 60)

        tables = detect_tables(
            pdf_path,
            page_number
        )

        display_tables(tables)

        print("\nCROPPING COMPLETE TABLES...")

        saved_images = crop_tables(
            pdf_path,
            page_number,
            dpi=200,
            padding=5
        )

        total_tables += len(saved_images)

    print("\n" + "=" * 60)
    print("TABLE DETECTION COMPLETED")
    print("=" * 60)

    print(f"Total table images created: {total_tables}")

    print(
        "Output folder: "
        "data/processed/diagrams/tables"
    )
