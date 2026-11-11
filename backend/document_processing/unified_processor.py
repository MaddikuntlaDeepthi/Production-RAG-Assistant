
import json
import re
from pathlib import Path

from backend.document_processing.pdf_extractor import extract_pdf
from backend.document_processing.diagram_storage import (
    load_diagram_descriptions
)


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DIAGRAM_PATH = PROCESSED_DIR / "diagram_descriptions.json"


# --------------------------------------------------
# 2. DOCUMENT-SPECIFIC PATHS
# --------------------------------------------------

def get_document_paths(pdf_path):
    """
    Generate separate processing paths for each PDF.
    """

    pdf_path = Path(pdf_path)

    document_id = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        pdf_path.stem
    ).strip("_").lower()

    if not document_id:
        raise ValueError("Invalid PDF filename.")

    document_dir = PROCESSED_DIR / document_id

    return {
        "document_id": document_id,
        "document_dir": document_dir,
        "merged_table_path": document_dir / "merged_tables.json",
        "output_path": document_dir / "unified_document.json"
    }


# --------------------------------------------------
# 3. TEXT FORMATTING
# --------------------------------------------------

def format_bullets(text):

    if not text:
        return ""

    lines = str(text).splitlines()

    formatted_lines = []

    for line in lines:

        stripped_line = line.strip()

        if stripped_line == "o":
            formatted_lines.append("• ")

        elif stripped_line.startswith("o "):
            formatted_lines.append(
                "• " + stripped_line[2:]
            )

        else:
            formatted_lines.append(line)

    return "\n".join(formatted_lines)


# --------------------------------------------------
# 4. LOAD MERGED TABLES
# --------------------------------------------------

def load_merged_tables(input_path):

    input_path = Path(input_path)

    if not input_path.exists():

        print(
            "No merged table file found. "
            "Continuing without merged tables."
        )

        return []

    with open(input_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict) and "merged_tables" in data:
        return data["merged_tables"]

    if isinstance(data, dict) and "rows" in data:
        return [data]

    if isinstance(data, list):
        return data

    print("Unrecognized merged table JSON structure.")

    return []


# --------------------------------------------------
# 5. GET DOCUMENT-SPECIFIC DIAGRAM DATA
# --------------------------------------------------

def get_diagram_data(document_name, diagram_data):
    """
    Return diagrams belonging only to the requested PDF.
    """

    matching_diagrams = []

    for diagram in diagram_data:

        if diagram.get("document") == document_name:

            matching_diagrams.append({

                "page": diagram.get("page"),

                "region_number": diagram.get("region_number"),

                "image_path": diagram.get("image_path"),

                "description": diagram.get("description", "")
            })

    return matching_diagrams


# --------------------------------------------------
# 6. CONVERT GENERIC MERGED TABLE INTO SEARCHABLE TEXT
# --------------------------------------------------

def merged_table_to_text(table):
    """
    Convert different table structures into searchable text.

    Supports:
    1. Dictionary-based rows.
    2. List-based rows.
    3. Existing Hadoop-specific table data.
    """

    table_title = table.get(
        "table_title",
        "Merged Table"
    )

    headers = table.get("headers", [])

    rows = table.get("rows", [])

    content_parts = [
        f"TABLE: {table_title}"
    ]

    if headers:

        content_parts.append(
            "COLUMNS: " + " | ".join(
                str(header) for header in headers
            )
        )

    for row in rows:

        # Dictionary-based rows.
        if isinstance(row, dict):

            row_parts = []

            for key, value in row.items():

                if key in ["source_pages", "page"]:
                    continue

                if isinstance(value, list):

                    value = ", ".join(
                        str(item) for item in value
                    )

                if value is not None and str(value).strip():

                    row_parts.append(
                        f"{key}: "
                        f"{format_bullets(str(value))}"
                    )

            row_text = "\n".join(row_parts)

        # List-based rows.
        elif isinstance(row, list):

            row_text = " | ".join(
                str(value) if value is not None else ""
                for value in row
            )

        # Other row formats.
        else:

            row_text = str(row)

        if row_text.strip():

            content_parts.append(row_text)

    return "\n\n".join(content_parts)


# --------------------------------------------------
# 7. FIND MERGED TABLE REFERENCES
# --------------------------------------------------

def get_page_table_references(page_number, merged_tables):

    references = []

    for table in merged_tables:

        source_pages = table.get("source_pages", [])

        if page_number in source_pages:

            references.append({

                "table_id": table.get("table_id"),

                "table_title": table.get("table_title"),

                "source_pages": source_pages
            })

    return references


# --------------------------------------------------
# 8. ORGANIZE PAGE INFORMATION
# --------------------------------------------------

def organize_pages(
    extracted_pages,
    diagram_data,
    merged_tables,
    document_name
):

    organized_pages = []

    for page_data in extracted_pages:

        page_number = page_data.get("page")

        page_text = format_bullets(
            page_data.get("text", "")
        )

        page_tables = page_data.get("tables", [])

        page_diagrams = [

            diagram

            for diagram in diagram_data

            if diagram.get("page") == page_number
        ]

        merged_table_references = get_page_table_references(
            page_number,
            merged_tables
        )

        content_parts = []

        # Page text.
        if page_text.strip():

            content_parts.append(
                "PAGE TEXT:\n" + page_text
            )

        # Original tables.
        # Skip original tables on pages already represented
        # by a merged table, to avoid duplicate content.
        if not merged_table_references:

            for table in page_tables:

                table_text = format_bullets(
                    table.get("text", "")
                )

                if table_text.strip():

                    content_parts.append(
                        "PAGE TABLE:\n" + table_text
                    )

        # Diagram descriptions.
        for diagram in page_diagrams:

            description = diagram.get(
                "description",
                ""
            )

            if description.strip():

                content_parts.append(
                    "DIAGRAM DESCRIPTION:\n" + description
                )

        # Merged table references.
        for reference in merged_table_references:

            reference_text = (

                f"MERGED TABLE REFERENCE: "
                f"{reference.get('table_title')}\n"

                f"Table ID: {reference.get('table_id')}\n"

                f"Source pages: {reference.get('source_pages')}"
            )

            content_parts.append(reference_text)

        organized_pages.append({

            "document": document_name,

            "page": page_number,

            "has_text": bool(page_text.strip()),

            "text": page_text,

            "page_tables": page_tables,

            "merged_table_references": merged_table_references,

            "diagrams": page_diagrams,

            "diagram_count": len(page_diagrams),

            "content": "\n\n".join(content_parts)
        })

    return organized_pages


# --------------------------------------------------
# 9. BUILD THE UNIFIED DOCUMENT
# --------------------------------------------------

def build_unified_document(
    pdf_path,
    merged_table_path=None
):
    """
    Process any PDF and build its unified document JSON.
    """

    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():

        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":

        raise ValueError(
            "Only PDF files are supported."
        )

    paths = get_document_paths(pdf_path)

    document_name = pdf_path.name

    if merged_table_path is None:

        merged_table_path = paths["merged_table_path"]

    merged_table_path = Path(merged_table_path)

    print("\n" + "=" * 60)
    print("UNIFIED DOCUMENT PROCESSING")
    print("=" * 60)

    print(f"Document: {document_name}")

    # Step 1: Extract PDF.
    print("\nStep 1: Extracting PDF information...")

    extracted_pages = extract_pdf(pdf_path)

    print(
        f"Pages extracted: {len(extracted_pages)}"
    )

    # Step 2: Load diagram descriptions.
    print("\nStep 2: Loading diagram descriptions...")

    if DIAGRAM_PATH.exists():

        all_diagrams = load_diagram_descriptions(
            DIAGRAM_PATH
        )

        diagram_data = get_diagram_data(
            document_name,
            all_diagrams
        )

    else:

        diagram_data = []

        print("Diagram storage not found.")

    print(
        f"Diagrams for this document: {len(diagram_data)}"
    )

    # Step 3: Load document-specific merged tables.
    print("\nStep 3: Loading merged tables...")

    merged_tables = load_merged_tables(
        merged_table_path
    )

    print(
        f"Merged tables loaded: {len(merged_tables)}"
    )

    # Step 4: Organize pages.
    print("\nStep 4: Combining extracted information...")

    organized_pages = organize_pages(

        extracted_pages=extracted_pages,

        diagram_data=diagram_data,

        merged_tables=merged_tables,

        document_name=document_name
    )

    # Step 5: Prepare merged table content.
    final_merged_tables = []

    for index, table in enumerate(merged_tables, start=1):

        final_merged_tables.append({

            "table_id": table.get(

                "table_id",

                f"{paths['document_id']}_table_{index}"
            ),

            "table_title": table.get(
                "table_title",
                "Merged Table"
            ),

            "headers": table.get("headers", []),

            "source_pages": table.get("source_pages", []),

            "rows": table.get("rows", []),

            "content": merged_table_to_text(table)
        })

    # Step 6: Statistics.
    total_pages = len(organized_pages)

    pages_with_text = sum(

        1 for page in organized_pages

        if page["has_text"]
    )

    pages_without_text = [

        page["page"]

        for page in organized_pages

        if not page["has_text"]
    ]

    pages_with_diagrams = sum(

        1 for page in organized_pages

        if page["diagram_count"] > 0
    )

    pages_with_tables = sum(

        1 for page in organized_pages

        if page["page_tables"]
        or page["merged_table_references"]
    )

    # Step 7: Build unified document.
    unified_document = {

        "document": document_name,

        "document_id": paths["document_id"],

        "total_pages": total_pages,

        "total_diagrams": len(diagram_data),

        "total_merged_tables": len(final_merged_tables),

        "statistics": {

            "pages_with_text": pages_with_text,

            "pages_without_text": pages_without_text,

            "pages_with_diagrams": pages_with_diagrams,

            "pages_with_tables": pages_with_tables
        },

        "pages": organized_pages,

        "merged_tables": final_merged_tables
    }

    return unified_document


# --------------------------------------------------
# 10. SAVE THE UNIFIED DOCUMENT
# --------------------------------------------------

def save_unified_document(
    unified_document,
    output_path=None
):

    if output_path is None:

        paths = get_document_paths(
            unified_document["document"]
        )

        output_path = paths["output_path"]

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

            unified_document,

            file,

            indent=4,

            ensure_ascii=False
        )

    print("\n" + "=" * 60)
    print("UNIFIED DOCUMENT SAVED SUCCESSFULLY")
    print("=" * 60)

    print(
        f"Document: {unified_document['document']}"
    )

    print(
        f"Total pages: {unified_document['total_pages']}"
    )

    print(
        f"Total diagrams: {unified_document['total_diagrams']}"
    )

    print(
        f"Merged tables: {unified_document['total_merged_tables']}"
    )

    print(
        "Pages without text:",
        unified_document["statistics"]["pages_without_text"]
    )

    print(
        f"Output: {output_path}"
    )


# --------------------------------------------------
# 11. PROCESS ALL PDF DOCUMENTS
# --------------------------------------------------

def process_all_pdfs():
    """
    Discover and process every PDF in data/raw.

    Each PDF gets its own processed folder and JSON file.
    """

    if not RAW_DIR.exists():

        raise FileNotFoundError(
            f"Raw data folder not found: {RAW_DIR}"
        )

    pdf_files = sorted(
        RAW_DIR.glob("*.pdf"),
        key=lambda path: path.name.lower()
    )

    if not pdf_files:

        print("No PDF files found in data/raw.")

        return

    print("\n" + "=" * 60)
    print("MULTI-DOCUMENT PROCESSING")
    print("=" * 60)

    print(
        f"Total PDF documents found: {len(pdf_files)}"
    )

    successful_documents = []

    failed_documents = []

    for pdf_path in pdf_files:

        print("\n" + "#" * 60)
        print(f"PROCESSING: {pdf_path.name}")
        print("#" * 60)

        try:

            unified_document = build_unified_document(
                pdf_path=pdf_path
            )

            save_unified_document(
                unified_document
            )

            successful_documents.append(
                pdf_path.name
            )

        except Exception as error:

            print(
                f"\nERROR processing {pdf_path.name}: {error}"
            )

            failed_documents.append({

                "document": pdf_path.name,

                "error": str(error)
            })

    # Final summary.
    print("\n" + "=" * 60)
    print("MULTI-DOCUMENT PROCESSING SUMMARY")
    print("=" * 60)

    print(
        f"Total PDFs: {len(pdf_files)}"
    )

    print(
        f"Successfully processed: {len(successful_documents)}"
    )

    print(
        f"Failed: {len(failed_documents)}"
    )

    if successful_documents:

        print("\nSuccessful documents:")

        for document in successful_documents:

            print(f"  - {document}")

    if failed_documents:

        print("\nFailed documents:")

        for document in failed_documents:

            print(
                f"  - {document['document']}: "
                f"{document['error']}"
            )


# --------------------------------------------------
# 12. MAIN EXECUTION
# --------------------------------------------------

if __name__ == "__main__":

    process_all_pdfs()
