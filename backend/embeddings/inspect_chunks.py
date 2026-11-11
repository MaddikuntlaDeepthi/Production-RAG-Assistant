
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cd_unit-4_part-2"
    / "chunks.json"
)


def main():

    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    chunks = data.get("chunks", [])

    print("=" * 70)
    print("CD UNIT-4: ALL CHUNKS SUMMARY")
    print("=" * 70)

    print(f"Document: {data.get('document')}")
    print(f"Total chunks: {len(chunks)}")

    for number, chunk in enumerate(chunks, start=1):

        content = chunk.get("content", "")

        print("\n" + "-" * 70)
        print(
            f"CHUNK {number} | "
            f"Page: {chunk.get('page')} | "
            f"Tokens: {chunk.get('token_count')}"
        )

        print(content[:300].replace("\n", " "))


if __name__ == "__main__":
    main()
