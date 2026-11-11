
import json
import re
from pathlib import Path
import tiktoken


# --------------------------------------------------
# 1. PROJECT PATHS AND SETTINGS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 75

ENCODING = tiktoken.get_encoding("cl100k_base")


# --------------------------------------------------
# 2. DOCUMENT-SPECIFIC PATHS
# --------------------------------------------------

def get_document_id(document_name):
    """Create a safe document identifier from its filename."""

    document_id = Path(document_name).stem.lower()

    document_id = re.sub(
        r"[^a-z0-9_-]+",
        "_",
        document_id
    )

    return document_id.strip("_")


def get_output_path(input_path):
    """Save chunks beside the corresponding unified document."""

    input_path = Path(input_path)

    return input_path.parent / "chunks.json"


def discover_unified_documents():
    """Find all document-specific unified JSON files."""

    return sorted(
        PROCESSED_DIR.glob("*/unified_document.json")
    )


# --------------------------------------------------
# 3. COUNT TOKENS
# --------------------------------------------------

def count_tokens(text):
    """Return the token count of a text string."""

    if not text:
        return 0

    return len(ENCODING.encode(str(text)))


# --------------------------------------------------
# 4. SPLIT TEXT INTO CHUNKS
# --------------------------------------------------

def split_text_into_chunks(
    text,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
):
    """Split text into token-based chunks with overlap."""

    if not text or not str(text).strip():
        return []

    if chunk_size <= 0:
        raise ValueError(
            "Chunk size must be greater than zero."
        )

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be non-negative "
            "and smaller than chunk size."
        )

    tokens = ENCODING.encode(str(text))

    chunks = []
    start = 0

    while start < len(tokens):

        end = min(start + chunk_size, len(tokens))

        chunk_tokens = tokens[start:end]

        chunk_text = ENCODING.decode(chunk_tokens)

        chunks.append(chunk_text)

        if end == len(tokens):
            break

        start = end - chunk_overlap

    return chunks


# --------------------------------------------------
# 5. CREATE PAGE CONTENT CHUNKS
# --------------------------------------------------

def create_page_chunks(page, document_name):

    document_id = get_document_id(document_name)

    page_text = page.get("text", "")

    if not page_text or not page_text.strip():
        return []

    text_chunks = split_text_into_chunks(page_text)

    results = []

    for index, chunk_text in enumerate(text_chunks, start=1):

        results.append({

            "chunk_id": (
                f"{document_id}_"
                f"page_{page.get('page')}_"
                f"chunk_{index}"
            ),

            "document": document_name,

            "page": page.get("page"),

            "chunk_number": index,

            "content_type": "page_content",

            "token_count": count_tokens(chunk_text),

            "content": chunk_text
        })

    return results


# --------------------------------------------------
# 6. CREATE UNMERGED PAGE TABLE CHUNKS
# --------------------------------------------------

def create_page_table_chunks(
    table,
    document_name,
    page_number,
    table_number
):
    """
    Create chunks from an original page table.

    These are tables that have not already been
    represented by merged-table chunks.
    """

    document_id = get_document_id(document_name)

    table_text = table.get("text", "")

    if not table_text or not str(table_text).strip():
        return []

    formatted_text = (
        f"PAGE TABLE\n"
        f"Page: {page_number}\n"
        f"Table number: {table_number}\n\n"
        f"{table_text}"
    )

    text_chunks = split_text_into_chunks(formatted_text)

    results = []

    for index, chunk_text in enumerate(text_chunks, start=1):

        results.append({

            "chunk_id": (
                f"{document_id}_"
                f"page_{page_number}_"
                f"table_{table_number}_"
                f"chunk_{index}"
            ),

            "document": document_name,

            "page": page_number,

            "table_number": table_number,

            "chunk_number": index,

            "content_type": "page_table",

            "token_count": count_tokens(chunk_text),

            "content": chunk_text
        })

    return results


# --------------------------------------------------
# 7. CREATE MERGED TABLE CHUNKS
# --------------------------------------------------

def create_table_chunks(table, document_name):

    document_id = get_document_id(document_name)

    table_content = table.get("content", "")

    if not table_content or not table_content.strip():
        return []

    text_chunks = split_text_into_chunks(table_content)

    results = []

    original_table_id = table.get("table_id", "table")

    unique_table_id = (
        f"{document_id}_{original_table_id}"
    )

    for index, chunk_text in enumerate(text_chunks, start=1):

        results.append({

            "chunk_id": (
                f"{unique_table_id}_chunk_{index}"
            ),

            "document": document_name,

            "table_id": unique_table_id,

            "table_title": table.get("table_title"),

            "source_pages": table.get("source_pages", []),

            "chunk_number": index,

            "content_type": "table",

            "token_count": count_tokens(chunk_text),

            "content": chunk_text
        })

    return results


# --------------------------------------------------
# 8. CREATE DIAGRAM CHUNKS
# --------------------------------------------------

def create_diagram_chunks(diagram, document_name):

    document_id = get_document_id(document_name)

    description = diagram.get("description", "")

    if not description or not description.strip():
        return []

    text_chunks = split_text_into_chunks(description)

    results = []

    for index, chunk_text in enumerate(text_chunks, start=1):

        results.append({

            "chunk_id": (
                f"{document_id}_"
                f"page_{diagram.get('page')}_"
                f"diagram_{diagram.get('region_number')}_"
                f"chunk_{index}"
            ),

            "document": document_name,

            "page": diagram.get("page"),

            "region_number": diagram.get("region_number"),

            "image_path": diagram.get("image_path"),

            "chunk_number": index,

            "content_type": "diagram",

            "token_count": count_tokens(chunk_text),

            "content": chunk_text
        })

    return results


# --------------------------------------------------
# 9. PROCESS ONE UNIFIED DOCUMENT
# --------------------------------------------------

def process_document(input_path):

    input_path = Path(input_path)

    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    if not input_path.exists():
        raise FileNotFoundError(
            f"Unified document not found: {input_path}"
        )

    print("\n" + "=" * 55)
    print("DOCUMENT CHUNKING")
    print("=" * 55)

    # Load unified document.
    print("\nStep 1: Loading unified document...")

    with open(input_path, "r", encoding="utf-8") as file:
        document_data = json.load(file)

    document_name = (
        document_data.get("document")
        or f"{input_path.parent.name}.pdf"
    )

    document_id = get_document_id(document_name)

    all_chunks = []

    # Create page chunks.
    print("\nStep 2: Creating page chunks...")

    for page in document_data.get("pages", []):

        page_chunks = create_page_chunks(
            page,
            document_name
        )

        all_chunks.extend(page_chunks)

    page_chunk_count = sum(
        1 for chunk in all_chunks
        if chunk["content_type"] == "page_content"
    )

    print(f"Page chunks created: {page_chunk_count}")

    # Create unmerged page-table chunks.
    print("\nStep 3: Creating unmerged page-table chunks...")

    page_table_chunk_count = 0

    for page in document_data.get("pages", []):

        page_number = page.get("page")

        merged_references = page.get(
            "merged_table_references",
            []
        )

        # The unified processor marks pages whose tables
        # are represented by merged-table references.
        if merged_references:
            continue

        for table_number, table in enumerate(
            page.get("page_tables", []),
            start=1
        ):

            table_chunks = create_page_table_chunks(
                table=table,
                document_name=document_name,
                page_number=page_number,
                table_number=table_number
            )

            all_chunks.extend(table_chunks)

            page_table_chunk_count += len(table_chunks)

    print(
        f"Unmerged page-table chunks created: "
        f"{page_table_chunk_count}"
    )

    # Create merged-table chunks.
    print("\nStep 4: Creating merged-table chunks...")

    table_chunk_count = 0

    for table in document_data.get("merged_tables", []):

        table_chunks = create_table_chunks(
            table,
            document_name
        )

        all_chunks.extend(table_chunks)

        table_chunk_count += len(table_chunks)

    print(f"Merged-table chunks created: {table_chunk_count}")

    # Create diagram chunks.
    print("\nStep 5: Creating diagram chunks...")

    diagram_chunk_count = 0

    for page in document_data.get("pages", []):

        for diagram in page.get("diagrams", []):

            diagram_chunks = create_diagram_chunks(
                diagram,
                document_name
            )

            all_chunks.extend(diagram_chunks)

            diagram_chunk_count += len(diagram_chunks)

    print(f"Diagram chunks created: {diagram_chunk_count}")

    # Calculate statistics.
    chunk_statistics = {

        "page_chunks": page_chunk_count,

        "page_table_chunks": page_table_chunk_count,

        "table_chunks": table_chunk_count,

        "diagram_chunks": diagram_chunk_count
    }

    return {

        "document": document_name,

        "document_id": document_id,

        "source_file": str(input_path),

        "total_chunks": len(all_chunks),

        "chunk_settings": {

            "chunk_size": CHUNK_SIZE,

            "chunk_overlap": CHUNK_OVERLAP,

            "tokenizer": "cl100k_base"
        },

        "statistics": chunk_statistics,

        "chunks": all_chunks
    }


# --------------------------------------------------
# 10. VALIDATE CHUNKS
# --------------------------------------------------

def validate_chunks(chunk_data):

    chunks = chunk_data.get("chunks", [])

    chunk_ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    duplicate_ids = len(chunk_ids) != len(set(chunk_ids))

    oversized_chunks = [
        chunk["chunk_id"]
        for chunk in chunks
        if chunk["token_count"] > CHUNK_SIZE
    ]

    missing_content = [
        chunk["chunk_id"]
        for chunk in chunks
        if not chunk.get("content", "").strip()
    ]

    print("\n" + "=" * 55)
    print("CHUNK VALIDATION")
    print("=" * 55)

    print(f"Duplicate chunk IDs: {duplicate_ids}")
    print(f"Oversized chunks: {len(oversized_chunks)}")
    print(f"Empty chunks: {len(missing_content)}")

    if duplicate_ids:
        print("Warning: Duplicate chunk IDs found.")

    if oversized_chunks:
        print("Oversized chunk IDs:", oversized_chunks)

    if missing_content:
        print("Empty chunk IDs:", missing_content)

    return (
        not duplicate_ids
        and not oversized_chunks
        and not missing_content
    )


# --------------------------------------------------
# 11. SAVE CHUNKS
# --------------------------------------------------

def save_chunks(chunk_data, output_path):

    output_path = Path(output_path)

    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as file:

        json.dump(
            chunk_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n" + "=" * 55)
    print("CHUNKING COMPLETED")
    print("=" * 55)

    print(f"Document: {chunk_data['document']}")
    print(f"Total chunks: {chunk_data['total_chunks']}")

    print(
        f"Page chunks: "
        f"{chunk_data['statistics']['page_chunks']}"
    )

    print(
        f"Unmerged page-table chunks: "
        f"{chunk_data['statistics']['page_table_chunks']}"
    )

    print(
        f"Merged-table chunks: "
        f"{chunk_data['statistics']['table_chunks']}"
    )

    print(
        f"Diagram chunks: "
        f"{chunk_data['statistics']['diagram_chunks']}"
    )

    print(f"Output: {output_path}")


# --------------------------------------------------
# 12. PROCESS ALL DOCUMENTS
# --------------------------------------------------

def process_all_documents():

    document_paths = discover_unified_documents()

    if not document_paths:
        print("No unified_document.json files found.")
        return

    print("\n" + "=" * 60)
    print("MULTI-DOCUMENT CHUNKING")
    print("=" * 60)

    print(f"Documents discovered: {len(document_paths)}")

    successful_documents = 0
    failed_documents = 0
    total_chunks = 0

    for input_path in document_paths:

        print("\n\nProcessing:", input_path.parent.name)

        try:

            chunk_data = process_document(input_path)

            is_valid = validate_chunks(chunk_data)

            output_path = get_output_path(input_path)

            save_chunks(chunk_data, output_path)

            if not is_valid:
                print(
                    "\nValidation failed for:",
                    chunk_data["document"]
                )
                failed_documents += 1
                continue

            successful_documents += 1
            total_chunks += chunk_data["total_chunks"]

            print("\nAll chunk validation checks passed.")

        except Exception as error:

            failed_documents += 1

            print(
                f"\nFailed to process {input_path.name}: {error}"
            )

    # Final summary.
    print("\n" + "=" * 60)
    print("MULTI-DOCUMENT CHUNKING SUMMARY")
    print("=" * 60)

    print(f"Total documents discovered: {len(document_paths)}")
    print(f"Successful documents: {successful_documents}")
    print(f"Failed documents: {failed_documents}")
    print(f"Total chunks generated: {total_chunks}")

    print("\nDocument-specific chunks.json files are saved.")


# --------------------------------------------------
# 13. MAIN FUNCTION
# --------------------------------------------------

def main():

    process_all_documents()


if __name__ == "__main__":

    main()
