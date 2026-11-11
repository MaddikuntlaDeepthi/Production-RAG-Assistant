
import json
import pymupdf

from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PDF_PATH = "data/raw/sample.pdf"

OUTPUT_PATH = "data/processed/merged_tables.json"

# Three actual columns inside the detected table
COLUMN_INDICES = [0, 3, 6]


# --------------------------------------------------
# 1. CLEAN TEXT
# --------------------------------------------------

def clean_text(text):

    if not text:
        return ""

    lines = []

    for line in text.splitlines():

        line = " ".join(line.split())

        if line:
            lines.append(line)

    return "\n".join(lines)


# --------------------------------------------------
# 2. EXTRACT TEXT USING CELL COORDINATES
# --------------------------------------------------

def extract_table_rows(pdf_path, page_number, table_index):

    print(f"\nExtracting page {page_number}...")

    rows_data = []

    with pymupdf.open(pdf_path) as document:

        page = document[page_number - 1]

        finder = page.find_tables()

        if table_index >= len(finder.tables):

            raise ValueError(
                f"Table {table_index + 1} not found "
                f"on page {page_number}"
            )

        table = finder.tables[table_index]

        for row_number, row in enumerate(
            table.rows,
            start=1
        ):

            logical_cells = []

            for column_index in COLUMN_INDICES:

                if column_index >= len(row.cells):

                    logical_cells.append("")
                    continue

                cell = row.cells[column_index]

                if cell is None:

                    logical_cells.append("")
                    continue

                # Read text from the actual cell rectangle
                rect = pymupdf.Rect(cell)

                text = page.get_text(
                    "text",
                    clip=rect
                )

                logical_cells.append(
                    clean_text(text)
                )

            # Ignore empty physical rows
            if not any(logical_cells):
                continue

            record = {

                "page": page_number,

                "original_row": row_number,

                "distro": logical_cells[0],

                "remarks": logical_cells[1],

                "free_premium": logical_cells[2]

            }

            rows_data.append(record)

    print(f"Logical rows extracted: {len(rows_data)}")

    return rows_data


# --------------------------------------------------
# 3. REMOVE REPEATED HEADERS
# --------------------------------------------------

def remove_headers(rows):

    result = []

    for row in rows:

        if row["distro"].strip().lower() == "distro":
            continue

        result.append(row)

    return result


# --------------------------------------------------
# 4. MERGE CONTINUATION ROW
# --------------------------------------------------

def merge_continuation(page8_rows, page9_rows):

    if not page8_rows or not page9_rows:

        raise ValueError(
            "Cannot merge: one of the pages has no data rows."
        )

    # Last data row on page 8
    first_part = page8_rows[-1]

    # First data row on page 9
    second_part = page9_rows[0]

    if "cloudera" not in first_part["distro"].lower():

        raise ValueError(
            "Expected Cloudera as the last row on page 8."
        )

    if "cloudera.com" not in second_part["distro"].lower():

        raise ValueError(
            "Expected Cloudera website as the first row on page 9."
        )

    print("\nMerging Cloudera continuation...")

    first_part["distro"] = "\n".join(
        filter(
            None,
            [
                first_part["distro"],
                second_part["distro"]
            ]
        )
    )

    first_part["remarks"] = "\n".join(
        filter(
            None,
            [
                first_part["remarks"],
                second_part["remarks"]
            ]
        )
    )

    first_part["free_premium"] = " ".join(
        filter(
            None,
            [
                first_part["free_premium"],
                second_part["free_premium"]
            ]
        )
    )

    first_part["source_pages"] = [8, 9]

    # Remove the continuation row from page 9
    remaining_page9_rows = page9_rows[1:]

    return page8_rows + remaining_page9_rows


# --------------------------------------------------
# 5. BUILD COMPLETE TABLE
# --------------------------------------------------

def build_complete_table(pdf_path):

    # Page 8: second detected table
    page8_rows = extract_table_rows(
        pdf_path,
        page_number=8,
        table_index=1
    )

    # Page 9: first detected table
    page9_rows = extract_table_rows(
        pdf_path,
        page_number=9,
        table_index=0
    )

    # Remove repeated headers
    page8_rows = remove_headers(page8_rows)

    page9_rows = remove_headers(page9_rows)

    print("\nPAGE 8 DATA ROWS:", len(page8_rows))
    print("PAGE 9 DATA ROWS:", len(page9_rows))

    # Merge the continuation
    complete_rows = merge_continuation(
        page8_rows,
        page9_rows
    )

    # Add source page information to other rows
    for row in complete_rows:

        if "source_pages" not in row:

            row["source_pages"] = [row["page"]]

    return {

        "document": Path(pdf_path).name,

        "table_title": "Hadoop Distributions",

        "headers": [
            "Distro",
            "Remarks",
            "Free / Premium"
        ],

        "source_pages": [8, 9],

        "rows": complete_rows

    }


# --------------------------------------------------
# 6. SAVE JSON
# --------------------------------------------------

def save_json(data, output_path):

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nSaved JSON: {output_path}")


# --------------------------------------------------
# 7. DISPLAY RESULT
# --------------------------------------------------

def display_table(data):

    print("\n" + "=" * 70)
    print("FINAL MERGED TABLE")
    print("=" * 70)

    for index, row in enumerate(data["rows"], start=1):

        print(f"\nROW {index}")

        print("Distro:")
        print(row["distro"])

        print("\nRemarks:")
        print(row["remarks"])

        print("\nFree / Premium:")
        print(row["free_premium"])

        print("\nSource pages:")
        print(row["source_pages"])

        print("-" * 70)


# --------------------------------------------------
# 8. MAIN
# --------------------------------------------------

if __name__ == "__main__":

    print("\nPRODUCTION RAG - TABLE MERGER")

    merged_data = build_complete_table(PDF_PATH)

    display_table(merged_data)

    save_json(
        merged_data,
        OUTPUT_PATH
    )

    print("\nTABLE MERGING COMPLETED")


