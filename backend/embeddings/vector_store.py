
import json
import os
import uuid
from pathlib import Path

import faiss
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

FAISS_INDEX_PATH = PROCESSED_DIR / "faiss_index.bin"
METADATA_PATH = PROCESSED_DIR / "vector_metadata.json"

EXPECTED_DIMENSIONS = 384


def load_all_embeddings():
    """Load embeddings from every processed document."""

    embedding_files = sorted(
        PROCESSED_DIR.glob("*/embeddings.json")
    )

    if not embedding_files:
        raise FileNotFoundError(
            "No embeddings.json files found."
        )

    all_records = []

    print(f"Documents discovered: {len(embedding_files)}")

    for file_path in embedding_files:

        print(f"\nLoading: {file_path.parent.name}")

        with open(file_path, "r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list) or not records:
            raise ValueError(
                f"No valid embedding records in {file_path}"
            )

        print(f"Embedding records: {len(records)}")

        all_records.extend(records)

    return all_records


def prepare_vectors(records):
    """Validate and prepare the embedding matrix."""

    if not records:
        raise ValueError("No embedding records supplied.")

    vectors = []

    for position, record in enumerate(records):

        if "embedding" not in record:
            raise ValueError(
                f"Missing embedding at record {position}"
            )

        vector = np.asarray(
            record["embedding"],
            dtype=np.float32
        )

        if vector.ndim != 1:
            raise ValueError(
                f"Invalid vector shape at record {position}"
            )

        if len(vector) != EXPECTED_DIMENSIONS:
            raise ValueError(
                f"Expected {EXPECTED_DIMENSIONS} dimensions, "
                f"got {len(vector)} at record {position}"
            )

        if not np.all(np.isfinite(vector)):
            raise ValueError(
                f"Non-finite values in record {position}"
            )

        norm = np.linalg.norm(vector)

        if not np.isclose(norm, 1.0, atol=1e-3):
            raise ValueError(
                f"Embedding is not normalized at record {position}"
            )

        vectors.append(vector)

    return np.vstack(vectors).astype(np.float32)


def prepare_metadata(records):
    """Remove embedding vectors from metadata."""

    return [
        {
            key: value
            for key, value in record.items()
            if key != "embedding"
        }
        for record in records
    ]


def validate_metadata(metadata):
    """Check required metadata and duplicate chunk IDs."""

    chunk_ids = []

    for position, record in enumerate(metadata):

        chunk_id = record.get("chunk_id")
        document = record.get("document")

        if not chunk_id:
            raise ValueError(
                f"Missing chunk_id at record {position}"
            )

        if not document:
            raise ValueError(
                f"Missing document name at record {position}"
            )

        chunk_ids.append(chunk_id)

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError(
            "Duplicate chunk IDs detected across documents."
        )


def build_faiss_index(vectors):
    """Build a cosine-similarity index."""

    index = faiss.IndexFlatIP(EXPECTED_DIMENSIONS)
    index.add(vectors)

    return index


def save_vector_store(index, metadata):
    """
    Save index and metadata using temporary files.

    Existing files are backed up before replacement.
    If replacement fails, the previous files are restored.
    """

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if index.ntotal != len(metadata):
        raise ValueError(
            "FAISS index and metadata counts do not match."
        )

    token = uuid.uuid4().hex

    temporary_index = PROCESSED_DIR / f"faiss_{token}.tmp"
    temporary_metadata = PROCESSED_DIR / f"metadata_{token}.tmp"

    backup_index = PROCESSED_DIR / f"faiss_{token}.bak"
    backup_metadata = PROCESSED_DIR / f"metadata_{token}.bak"

    old_index_exists = FAISS_INDEX_PATH.exists()
    old_metadata_exists = METADATA_PATH.exists()

    index_replaced = False
    metadata_replaced = False

    try:

        # Write new files without touching existing files.
        faiss.write_index(
            index,
            str(temporary_index)
        )

        with open(
            temporary_metadata,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
                ensure_ascii=False
            )

            file.flush()
            os.fsync(file.fileno())

        # Validate temporary files before replacement.
        test_index = faiss.read_index(
            str(temporary_index)
        )

        with open(
            temporary_metadata,
            "r",
            encoding="utf-8"
        ) as file:

            test_metadata = json.load(file)

        if test_index.ntotal != len(test_metadata):
            raise ValueError(
                "Temporary vector store validation failed."
            )

        # Preserve the existing files.
        if old_index_exists:
            os.replace(
                FAISS_INDEX_PATH,
                backup_index
            )

        if old_metadata_exists:
            os.replace(
                METADATA_PATH,
                backup_metadata
            )

        # Install new files.
        os.replace(
            temporary_index,
            FAISS_INDEX_PATH
        )
        index_replaced = True

        os.replace(
            temporary_metadata,
            METADATA_PATH
        )
        metadata_replaced = True

        # Final validation.
        saved_index = faiss.read_index(
            str(FAISS_INDEX_PATH)
        )

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            saved_metadata = json.load(file)

        if saved_index.ntotal != len(saved_metadata):
            raise ValueError(
                "Final vector store validation failed."
            )

        print("\nFAISS index saved:", FAISS_INDEX_PATH)
        print("Metadata saved:", METADATA_PATH)

    except Exception:

        # Restore the previous files if replacement failed.
        if index_replaced and FAISS_INDEX_PATH.exists():
            FAISS_INDEX_PATH.unlink()

        if metadata_replaced and METADATA_PATH.exists():
            METADATA_PATH.unlink()

        if backup_index.exists():
            os.replace(
                backup_index,
                FAISS_INDEX_PATH
            )

        if backup_metadata.exists():
            os.replace(
                backup_metadata,
                METADATA_PATH
            )

        raise

    finally:

        # Remove temporary files.
        for path in [
            temporary_index,
            temporary_metadata,
            backup_index,
            backup_metadata
        ]:

            if path.exists():
                path.unlink()


def process_all_documents():

    print("=" * 60)
    print("PRODUCTION RAG ASSISTANT - VECTOR STORE")
    print("=" * 60)

    print("\nRebuilding multi-document FAISS index...")

    records = load_all_embeddings()

    print("\nPreparing vectors...")

    vectors = prepare_vectors(records)
    metadata = prepare_metadata(records)

    validate_metadata(metadata)

    print(f"Total embedding records: {len(records)}")
    print(f"Vector dimensions: {vectors.shape[1]}")

    print("\nBuilding FAISS index...")

    index = build_faiss_index(vectors)

    if index.ntotal != len(metadata):
        raise ValueError(
            "FAISS index and metadata counts do not match."
        )

    save_vector_store(index, metadata)

    print("\n" + "=" * 60)
    print("VECTOR STORE SUMMARY")
    print("=" * 60)

    document_counts = {}

    for record in metadata:

        document = record["document"]

        document_counts[document] = (
            document_counts.get(document, 0) + 1
        )

    for document, count in document_counts.items():
        print(f"{document}: {count} vectors")

    print("-" * 60)
    print(f"Total documents: {len(document_counts)}")
    print(f"Total FAISS vectors: {index.ntotal}")
    print(f"Total metadata records: {len(metadata)}")
    print(f"Vector dimensions: {EXPECTED_DIMENSIONS}")

    print("\nMulti-document vector store completed successfully.")


if __name__ == "__main__":
    process_all_documents()
