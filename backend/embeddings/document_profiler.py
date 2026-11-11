
import json
import re
from pathlib import Path
from collections import defaultdict


# =========================================================
# PATH CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

METADATA_PATH = PROCESSED_DIR / "vector_metadata.json"

PROFILE_PATH = PROCESSED_DIR / "document_profiles.json"


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_line(line):
    line = re.sub(r"\s+", " ", line)
    return line.strip(" \t-•")


# =========================================================
# UNIT EXTRACTION
# =========================================================

def extract_units(text):

    pattern = r"\bUNIT\s*[-:]?\s*([IVXLCDM]+|\d+)\b"

    matches = re.findall(
        pattern,
        text,
        flags=re.IGNORECASE
    )

    units = []

    for match in matches:

        unit = f"Unit {match.upper()}"

        if unit not in units:
            units.append(unit)

    return units


# =========================================================
# SUBJECT EXTRACTION
# =========================================================

def extract_subject(all_text):

    lines = [
        clean_line(line)
        for line in all_text.splitlines()
        if clean_line(line)
    ]

    ignored_patterns = [
        r"^K\.",
        r"^ASSOC",
        r"^PROFESSOR",
        r"^CMREC",
        r"^DEPT",
        r"^UNIT\b"
    ]

    for line in lines[:40]:

        if any(
            re.match(pattern, line, re.IGNORECASE)
            for pattern in ignored_patterns
        ):
            continue

        line = re.sub(r"^\d+[\.)]\s*", "", line)

        if ":" in line:

            title_part = line.split(":", 1)[0].strip()

            if 2 <= len(title_part.split()) <= 8:
                return title_part.strip(" :-.")

        if len(line.split()) > 8:
            continue

        if line.endswith((".", "?", "!")):
            continue

        letters = [
            char for char in line
            if char.isalpha()
        ]

        if not letters:
            continue

        uppercase_ratio = (
            sum(char.isupper() for char in letters)
            / len(letters)
        )

        if uppercase_ratio >= 0.65:
            return line.strip(" :-.")

    return "Not identified"


# =========================================================
# TOPIC FILTERING
# =========================================================

# Lines starting with these words are usually explanatory text,
# instructions, or incomplete sentences rather than topic headings.

SENTENCE_START_WORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for",
    "and", "or", "but", "if", "when", "while", "since",
    "as", "because", "these", "those", "this", "that",
    "it", "we", "you", "they", "he", "she", "there",
    "here", "let", "suppose", "assume", "identify",
    "find", "explore", "forecast", "consider",
    "looking", "according", "all", "each"
}


# Common generic labels that are not useful as topics on their own.

GENERIC_SINGLE_WORDS = {
    "example",
    "examples",
    "question",
    "questions",
    "answer",
    "answers",
    "begin",
    "end",
    "remarks",
    "overview",
    "movies",
    "sentences",
    "labels",
    "relationships",
    "code",
    "program",
    "step"
}


# Common machine instructions and register names.

CODE_TOKENS = {
    "MOV", "ADD", "SUB", "MUL", "DIV", "GOTO",
    "HALT", "CALL", "RETURN", "CJ", "SP"
}


def looks_like_code(line):

    upper_line = line.upper()

    words = re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*",
        upper_line
    )

    if not words:
        return True

    # Register names such as R0, R1, R2
    if re.search(r"\bR\d+\b", upper_line):
        return True

    # Common instruction names
    if any(word in CODE_TOKENS for word in words):
        return True

    # Assignment and expression patterns
    if any(symbol in line for symbol in [
        ":=", "->", "=>", "/*", "*/"
    ]):
        return True

    # Lines dominated by code punctuation
    if line.count(",") >= 2:
        return True

    return False


# =========================================================
# HEADING IDENTIFICATION
# =========================================================

def is_heading(line):

    if not line:
        return False

    if len(line) > 100:
        return False

    words = line.split()

    if len(words) > 10:
        return False

    # Ignore unit labels
    if re.match(
        r"^UNIT\b",
        line,
        flags=re.IGNORECASE
    ):
        return False

    # Ignore professor names and institutional information
    ignored_patterns = [
        r"^K\.",
        r"^CMREC",
        r"^ASSOC",
        r"^PROFESSOR",
        r"^DEPT",
        r"^DEPARTMENT"
    ]

    if any(
        re.match(pattern, line, re.IGNORECASE)
        for pattern in ignored_patterns
    ):
        return False

    # Ignore generic one-word labels
    if len(words) == 1:

        if line.casefold() in GENERIC_SINGLE_WORDS:
            return False

        # Short uppercase machine instructions are not topics
        if line.upper() in CODE_TOKENS:
            return False

        if re.fullmatch(r"R\d+", line.upper()):
            return False

    # Ignore explanatory sentence starters
    first_word = re.sub(
        r"[^A-Za-z]",
        "",
        words[0]
    ).casefold()

    if first_word in SENTENCE_START_WORDS:
        return False

    # Ignore code statements
    if looks_like_code(line):
        return False

    # Ignore complete sentences
    if line.endswith((".", "?", "!")):
        return False

    # Ignore very long sentence-like headings
    if len(words) >= 8:
        return False

    # Numbered headings
    if re.match(r"^\d+[\.)]\s*[A-Za-z]", line):
        return True

    # Short colon headings
    if line.endswith(":") and len(words) <= 8:
        return True

    # Title-case headings
    if (
        2 <= len(words) <= 6
        and line[0].isupper()
        and not line.isupper()
    ):
        return True

    # Uppercase headings
    letters = [
        char for char in line
        if char.isalpha()
    ]

    if letters:

        uppercase_ratio = (
            sum(char.isupper() for char in letters)
            / len(letters)
        )

        if uppercase_ratio >= 0.75 and len(words) <= 6:
            return True

    return False


# =========================================================
# TOPIC EXTRACTION
# =========================================================

def extract_topics(all_text):

    topics = []

    seen = set()

    for raw_line in all_text.splitlines():

        line = clean_line(raw_line)

        if not is_heading(line):
            continue

        # Remove numbering
        line = re.sub(
            r"^\d+[\.)]\s*",
            "",
            line
        )

        line = line.rstrip(":.")

        key = line.casefold()

        if key not in seen:

            seen.add(key)

            topics.append(line)

    return topics


# =========================================================
# DOCUMENT PROFILE GENERATION
# =========================================================

def generate_document_profiles():

    if not METADATA_PATH.exists():

        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_PATH}"
        )

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(file)

    if not metadata:
        raise ValueError("Vector metadata is empty.")

    documents = defaultdict(list)

    # Group chunks by document
    for item in metadata:

        document_name = item.get("document")

        if document_name:
            documents[document_name].append(item)

    profiles = []

    print("\nDOCUMENT PROFILE GENERATION")
    print("=" * 60)

    for document_name, chunks in documents.items():

        print(f"\nProcessing: {document_name}")

        all_text = "\n".join(
            item.get("content", "")
            for item in chunks
            if item.get("content")
        )

        subject = extract_subject(all_text)

        units = extract_units(all_text)

        topics = extract_topics(all_text)

        profile = {
            "document": document_name,
            "subject": subject,
            "units": units,
            "topics": topics,
            "total_chunks": len(chunks),
            "representative_content": all_text[:2000]
        }

        profiles.append(profile)

        print(f"Subject: {subject}")
        print(f"Units found: {len(units)}")
        print(f"Topics found: {len(topics)}")

        print("Sample topics:")

        for topic in topics[:10]:
            print(f"  - {topic}")

    # Save profiles
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        PROFILE_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            profiles,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n" + "=" * 60)
    print("DOCUMENT PROFILE GENERATION COMPLETED")
    print(f"Documents processed: {len(profiles)}")
    print(f"Output: {PROFILE_PATH}")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    generate_document_profiles()
    