
import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EXPECTED_DIMENSIONS = 384


# --------------------------------------------------
# 2. DOCUMENT-SPECIFIC PATHS
# --------------------------------------------------

def get_output_path(input_path):

    input_path = Path(input_path)

    return input_path.parent / "embeddings.json"


def discover_chunk_files():
    """Find all document-specific chunks.json files."""

    return sorted(
        PROCESSED_DIR.glob("*/chunks.json")
    )


# --------------------------------------------------
# 3. LOAD EMBEDDING MODEL
# --------------------------------------------------

def load_embedding_model():

    print("\nLoading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    dimensions = model.get_embedding_dimension()

    if dimensions != EXPECTED_DIMENSIONS:
        raise ValueError(
            f"Unexpected embedding dimensions: {dimensions}"
        )

    print("Embedding model loaded successfully!")

    print(f"Model: {MODEL_NAME}")

    print(f"Embedding dimensions: {dimensions}")

    return model


# --------------------------------------------------
# 4. LOAD DOCUMENT CHUNKS
# --------------------------------------------------

def load_chunks(input_path):

    input_path = Path(input_path)

    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    if not input_path.exists():
        raise FileNotFoundError(
            f"Chunk file not found: {input_path}"
        )

    with open(input_path, "r", encoding="utf-8") as file:

        data = json.load(file)

    chunks = data.get("chunks", [])

    if not chunks:
        raise ValueError(
            "No chunks found in the input file."
        )

    for index, chunk in enumerate(chunks):

        if not chunk.get("content", "").strip():
            raise ValueError(
                f"Empty content found in chunk {index}."
            )

        if not chunk.get("chunk_id"):
            raise ValueError(
                f"Missing chunk ID in chunk {index}."
            )

        if not chunk.get("document"):
            raise ValueError(
                f"Missing document name in chunk {index}."
            )

    print(f"Total chunks loaded: {len(chunks)}")

    print(f"Document: {data.get('document', 'Unknown')}")

    return chunks


# --------------------------------------------------
# 5. GENERATE EMBEDDINGS
# --------------------------------------------------

def generate_embeddings(model, chunks):

    print("\nGenerating embeddings...")

    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    vectors = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    vectors = np.asarray(vectors, dtype=np.float32)

    if len(vectors) != len(chunks):
        raise ValueError(
            "Number of embeddings does not match number of chunks."
        )

    if vectors.ndim != 2:
        raise ValueError(
            "Embedding output must be a two-dimensional array."
        )

    if vectors.shape[1] != EXPECTED_DIMENSIONS:
        raise ValueError(
            f"Expected {EXPECTED_DIMENSIONS} dimensions, "
            f"but received {vectors.shape[1]}."
        )

    if not np.isfinite(vectors).all():
        raise ValueError(
            "Embedding vectors contain invalid numeric values."
        )

    # Verify vectors are normalized
    vector_norms = np.linalg.norm(vectors, axis=1)

    if not np.allclose(vector_norms, 1.0, atol=1e-5):
        raise ValueError(
            "Some embedding vectors are not normalized."
        )

    print("Embeddings generated successfully!")

    return vectors


# --------------------------------------------------
# 6. COMBINE EMBEDDINGS WITH METADATA
# --------------------------------------------------

def prepare_embedding_records(chunks, vectors):

    if len(chunks) != len(vectors):
        raise ValueError(
            "Chunks and embeddings count do not match."
        )

    records = []

    for chunk, vector in zip(chunks, vectors):

        record = {

            "chunk_id": chunk["chunk_id"],

            "document": chunk["document"],

            "content_type": chunk["content_type"],

            "page": chunk.get("page"),

            "table_id": chunk.get("table_id"),

            "table_title": chunk.get("table_title"),

            "source_pages": chunk.get("source_pages"),

            "region_number": chunk.get("region_number"),

            "image_path": chunk.get("image_path"),

            "content": chunk["content"],

            "embedding": vector.tolist()

        }

        records.append(record)

    return records


# --------------------------------------------------
# 7. SAVE EMBEDDINGS
# --------------------------------------------------

def save_embeddings(records, output_path):

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as file:

        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nEmbeddings saved to: {output_path}")


# --------------------------------------------------
# 8. PROCESS ONE DOCUMENT
# --------------------------------------------------

def process_document(model, input_path):

    print("\n" + "=" * 55)
    print("PROCESSING DOCUMENT EMBEDDINGS")
    print("=" * 55)

    print(f"Input: {input_path}")

    # Load chunks
    chunks = load_chunks(input_path)

    # Generate vectors
    vectors = generate_embeddings(
        model,
        chunks
    )

    # Prepare metadata and vectors
    records = prepare_embedding_records(
        chunks,
        vectors
    )

    # Save document-specific embeddings
    output_path = get_output_path(input_path)

    save_embeddings(
        records,
        output_path
    )

    # Display statistics
    print("\n" + "=" * 55)
    print("DOCUMENT EMBEDDING SUMMARY")
    print("=" * 55)

    print(f"Total embeddings: {len(records)}")

    print(
        f"Embedding dimensions: "
        f"{len(records[0]['embedding'])}"
    )

    print(
        f"First chunk ID: {records[0]['chunk_id']}"
    )

    return len(records)


# --------------------------------------------------
# 9. PROCESS ALL DOCUMENTS
# --------------------------------------------------

def process_all_documents():

    chunk_files = discover_chunk_files()

    if not chunk_files:
        print("No chunks.json files found.")
        return

    print("\n" + "=" * 60)
    print("MULTI-DOCUMENT EMBEDDING GENERATION")
    print("=" * 60)

    print(f"Documents discovered: {len(chunk_files)}")

    # Load model only once
    model = load_embedding_model()

    successful_documents = 0
    failed_documents = 0
    total_embeddings = 0

    for input_path in chunk_files:

        print("\n\nProcessing:", input_path.parent.name)

        try:

            embedding_count = process_document(
                model,
                input_path
            )

            successful_documents += 1

            total_embeddings += embedding_count

        except Exception as error:

            failed_documents += 1

            print(
                f"\nFailed to process "
                f"{input_path.parent.name}: {error}"
            )

    # Final summary
    print("\n" + "=" * 60)
    print("MULTI-DOCUMENT EMBEDDING SUMMARY")
    print("=" * 60)

    print(f"Total documents discovered: {len(chunk_files)}")

    print(f"Successful documents: {successful_documents}")

    print(f"Failed documents: {failed_documents}")

    print(f"Total embeddings generated: {total_embeddings}")

    print("\nDocument-specific embeddings.json files are saved.")


# --------------------------------------------------
# 10. MAIN FUNCTION
# --------------------------------------------------

def main():

    print("=" * 60)
    print("PRODUCTION RAG ASSISTANT - EMBEDDING GENERATOR")
    print("=" * 60)

    process_all_documents()


if __name__ == "__main__":

    main()
