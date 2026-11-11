
import pymupdf
from pathlib import Path

from backend.document_processing.table_processor import (
    clean_table,
    table_to_text
)


def extract_pdf(pdf_path):
    """
    Extract text and tables from a PDF document.

    Returns:
        A list containing page-wise text and table information.
    """

    pdf_path = Path(pdf_path)

    # Check whether the PDF exists
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Validate file extension
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    extracted_data = []

    # Open PDF safely
    with pymupdf.open(pdf_path) as document:

        # Process each page
        for page_number, page in enumerate(document, start=1):

            # --------------------------------
            # 1. Extract normal text
            # --------------------------------

            text = page.get_text("text")

            # --------------------------------
            # 2. Detect and extract tables
            # --------------------------------

            tables_data = []

            try:
                tables = page.find_tables()

                for table_number, table in enumerate(
                    tables.tables, start=1
                ):

                    # Extract original table
                    raw_table = table.extract()

                    # Clean table structure
                    cleaned_rows = clean_table(raw_table)

                    # Convert table into retrieval-friendly text
                    cleaned_text = table_to_text(cleaned_rows)

                    # Store both formats
                    if cleaned_rows:
                        tables_data.append({
                            "table_number": table_number,
                            "rows": cleaned_rows,
                            "text": cleaned_text
                        })

            except Exception as error:
                print(
                    f"Table detection issue on page "
                    f"{page_number}: {error}"
                )

            # --------------------------------
            # 3. Store page information
            # --------------------------------

            page_data = {
                "document": pdf_path.name,
                "page": page_number,
                "text": text.strip(),
                "tables": tables_data
            }

            extracted_data.append(page_data)

    return extracted_data


# --------------------------------
# 4. Run extractor independently
# --------------------------------

if __name__ == "__main__":

    pdf_path = "data/raw/sample.pdf"

    pages = extract_pdf(pdf_path)

    print("\nPDF EXTRACTION COMPLETED")
    print(f"Total pages extracted: {len(pages)}")

    for page in pages:

        print("\n" + "=" * 60)
        print(f"DOCUMENT: {page['document']}")
        print(f"PAGE: {page['page']}")

        print("\nEXTRACTED TEXT:")
        print(page["text"][:500])

        if page["tables"]:

            print("\nEXTRACTED TABLES:")

            for table in page["tables"]:

                print(
                    f"\nTable Number: {table['table_number']}"
                )

                print("\nSTRUCTURED TABLE:")

                for row in table["rows"]:
                    print(row)

                print("\nCLEAN TABLE TEXT:")
                print(table["text"])

