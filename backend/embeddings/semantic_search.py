
import json
import faiss
import numpy as np

from pathlib import Path
from collections import Counter
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INDEX_PATH = PROJECT_ROOT / "data" / "processed" / "faiss_index.bin"
METADATA_PATH = PROJECT_ROOT / "data" / "processed" / "vector_metadata.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EXPECTED_DIMENSION = 384

# Initial threshold; validate against the test questions.
MIN_SIMILARITY_SCORE = 0.30

TOP_K = 3


def load_model():

    print("\nLoading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    if model.get_embedding_dimension() != EXPECTED_DIMENSION:
        raise ValueError("Unexpected embedding dimension.")

    print("Embedding model loaded successfully!")

    return model


def load_faiss_index():

    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {INDEX_PATH}"
        )

    index = faiss.read_index(str(INDEX_PATH))

    if index.ntotal == 0:
        raise ValueError("FAISS index is empty.")

    if index.d != EXPECTED_DIMENSION:
        raise ValueError(
            f"Expected dimension {EXPECTED_DIMENSION}, got {index.d}"
        )

    return index


def load_metadata():

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_PATH}"
        )

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    if not isinstance(metadata, list):
        raise ValueError("Metadata must be a list.")

    return metadata


def validate_vector_store(index, metadata):

    if index.ntotal != len(metadata):
        raise ValueError(
            f"Index/metadata mismatch: {index.ntotal} vs {len(metadata)}"
        )

    chunk_ids = []

    for position, record in enumerate(metadata):

        if not isinstance(record, dict):
            raise ValueError(f"Invalid metadata at position {position}")

        if not record.get("chunk_id") or not record.get("document"):
            raise ValueError(f"Incomplete metadata at position {position}")

        chunk_ids.append(record["chunk_id"])

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Duplicate chunk IDs found.")

    counts = Counter(record["document"] for record in metadata)

    print("\nVector store validation successful.")

    for document, count in counts.items():
        print(f"{document}: {count} vectors")

    print(f"Total vectors: {index.ntotal}")


def generate_query_embedding(question, model):

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Please enter a valid question.")

    vector = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    vector = np.asarray(vector, dtype=np.float32)

    if vector.shape != (1, EXPECTED_DIMENSION):
        raise ValueError(
            f"Unexpected embedding shape: {vector.shape}"
        )

    return vector


def search_similar_chunks(
    question,
    model,
    index,
    metadata,
    top_k=TOP_K,
    allowed_documents=None,
    min_score=MIN_SIMILARITY_SCORE
):

    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    if not isinstance(min_score, (int, float)):
        raise ValueError("min_score must be numeric.")

    if index.ntotal != len(metadata):
        raise ValueError("FAISS index and metadata counts do not match.")

    if allowed_documents is not None:

        if not isinstance(allowed_documents, (list, tuple, set)):
            raise TypeError("allowed_documents must be a list, tuple, set, or None.")

        allowed_documents = set(allowed_documents)

        if not allowed_documents:
            return []

    query_vector = generate_query_embedding(question, model)

    scores, indices = index.search(
        query_vector,
        index.ntotal
    )

    results = []
    document_counts = Counter()

    for score, position in zip(scores[0], indices[0]):

        if position < 0:
            continue

        score = float(score)

        # Reject weak semantic matches.
        if score < min_score:
            break

        record = metadata[int(position)]

        document_name = record.get("document")

        if (
            allowed_documents is not None
            and document_name not in allowed_documents
        ):
            continue

        if document_counts[document_name] >= top_k:
            continue

        result = record.copy()
        result["similarity_score"] = score

        results.append(result)
        document_counts[document_name] += 1

    return results


def display_results(question, results):

    print("\n" + "=" * 70)
    print("QUESTION:", question)
    print("=" * 70)

    if not results:
        print("No sufficiently relevant chunks found.")
        return

    for number, result in enumerate(results, start=1):

        print(f"\nRESULT {number}")
        print("Document:", result.get("document"))
        print("Page:", result.get("page"))
        print("Type:", result.get("content_type"))
        print("Score:", result.get("similarity_score"))
        print("Content:", result.get("content", ""))


def main():

    question = "What is the role of NameNode in HDFS?"

    model = load_model()
    index = load_faiss_index()
    metadata = load_metadata()

    validate_vector_store(index, metadata)

    results = search_similar_chunks(
        question,
        model,
        index,
        metadata
    )

    display_results(question, results)


if __name__ == "__main__":
    main()
