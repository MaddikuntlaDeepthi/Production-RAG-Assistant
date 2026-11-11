
import json
from pathlib import Path


INPUT_PATH = Path("data/processed/embeddings.json")


def inspect_embeddings():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {INPUT_PATH}"
        )

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        records = json.load(file)

    print("=" * 55)
    print("EMBEDDINGS INSPECTION")
    print("=" * 55)

    print(f"\nTotal records: {len(records)}")

    first_record = records[0]

    print("\nFirst record details:")

    print("Chunk ID:", first_record["chunk_id"])

    print("Document:", first_record["document"])

    print("Content type:", first_record["content_type"])

    print("Page:", first_record["page"])

    print("\nOriginal text:")
    print(first_record["content"][:300])

    print("\nEmbedding details:")

    print(
        "Vector dimensions:",
        len(first_record["embedding"])
    )

    print(
        "First 10 vector values:",
        first_record["embedding"][:10]
    )

    print("\n" + "=" * 55)

    print("INSPECTION COMPLETED")


if __name__ == "__main__":
    inspect_embeddings()
