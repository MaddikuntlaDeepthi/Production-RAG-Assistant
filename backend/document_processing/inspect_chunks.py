
import json
from pathlib import Path

CHUNKS_PATH = Path("data/processed/chunks.json")


def inspect_chunks():

    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    print("\n========== CHUNK INSPECTION ==========")

    print("Document:", data["document"])
    print("Total chunks:", data["total_chunks"])

    for chunk in data["chunks"]:

        print("\n" + "-" * 60)

        print("Chunk ID:", chunk["chunk_id"])
        print("Content Type:", chunk["content_type"])
        print("Page:", chunk.get("page", chunk.get("source_pages")))
        print("Token Count:", chunk["token_count"])

        print("\nContent Preview:")
        print(chunk["content"][:500])

    print("\n========== INSPECTION COMPLETE ==========")


if __name__ == "__main__":
    inspect_chunks()
