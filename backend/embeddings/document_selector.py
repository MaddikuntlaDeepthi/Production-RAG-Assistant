
import json
import re
from pathlib import Path

import numpy as np

from backend.embeddings.semantic_search import load_model


# =========================================================
# 1. PATH CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROFILE_PATH = PROCESSED_DIR / "document_profiles.json"


# =========================================================
# 2. SELECTION CONFIGURATION
# =========================================================

SIMILARITY_THRESHOLD = 0.30

LEXICAL_THRESHOLD = 0.15

COMPARISON_THRESHOLD = 0.38

COMPARISON_KEYWORDS = {
    "compare",
    "comparison",
    "versus",
    "vs",
    "difference",
    "differences",
    "between"
}


STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "what", "why", "when", "where", "who", "which",
    "how", "explain", "describe", "discuss", "tell",
    "me", "about", "of", "to", "in", "on", "for",
    "and", "or", "with", "from", "by", "as", "at",
    "this", "that", "these", "those", "it", "its",
    "can", "could", "would", "should", "please",
    "important", "concept", "concepts", "topic", "topics"
}


# =========================================================
# 3. LOAD DOCUMENT PROFILES
# =========================================================

def load_document_profiles():

    if not PROFILE_PATH.exists():

        raise FileNotFoundError(
            f"Document profiles not found: {PROFILE_PATH}"
        )

    with open(
        PROFILE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        profiles = json.load(file)

    if not isinstance(profiles, list) or not profiles:

        raise ValueError(
            "Document profiles are empty or invalid."
        )

    for profile in profiles:

        if not profile.get("document"):

            raise ValueError(
                "A document profile is missing its document name."
            )

    return profiles


# =========================================================
# 4. TEXT PREPARATION
# =========================================================

def tokenize(text):

    words = re.findall(
        r"[a-zA-Z0-9]+",
        str(text).casefold()
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 1
    ]


def build_profile_text(profile):

    parts = []

    document = profile.get("document", "")

    subject = profile.get("subject", "")

    units = profile.get("units", [])

    topics = profile.get("topics", [])

    representative_content = profile.get(
        "representative_content",
        ""
    )

    parts.append(str(document))

    parts.append(str(subject))

    parts.extend(
        str(unit) for unit in units
    )

    parts.extend(
        str(topic) for topic in topics
    )

    parts.append(str(representative_content))

    return " ".join(parts)


# =========================================================
# 5. LEXICAL RELEVANCE
# =========================================================

def calculate_lexical_score(question, profile_text):

    question_words = set(tokenize(question))

    profile_words = set(tokenize(profile_text))

    if not question_words:
        return 0.0

    matching_words = question_words.intersection(
        profile_words
    )

    return (
        len(matching_words) / len(question_words)
    )


# =========================================================
# 6. COMPARISON QUESTION DETECTION
# =========================================================

def is_comparison_question(question):

    words = set(tokenize(question))

    return bool(
        words.intersection(COMPARISON_KEYWORDS)
    )


# =========================================================
# 7. RANK DOCUMENT PROFILES
# =========================================================

def rank_document_profiles(
    question,
    profiles=None,
    model=None
):

    if not question or not question.strip():

        raise ValueError(
            "Please enter a valid question."
        )

    if profiles is None:
        profiles = load_document_profiles()

    if model is None:
        model = load_model()

    profile_texts = [
        build_profile_text(profile)
        for profile in profiles
    ]

    print("\nGenerating question embedding...")

    question_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    profile_embeddings = model.encode(
        profile_texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    semantic_scores = np.dot(
        profile_embeddings,
        question_embedding[0]
    )

    ranked_results = []

    for index, profile in enumerate(profiles):

        lexical_score = calculate_lexical_score(
            question,
            profile_texts[index]
        )

        semantic_score = float(
            semantic_scores[index]
        )

        combined_score = (
            0.75 * semantic_score
            + 0.25 * lexical_score
        )

        ranked_results.append({

            "document": profile["document"],

            "subject": profile.get(
                "subject",
                "Not identified"
            ),

            "semantic_score": semantic_score,

            "lexical_score": lexical_score,

            "combined_score": combined_score
        })

    ranked_results.sort(
        key=lambda item: item["combined_score"],
        reverse=True
    )

    return ranked_results


# =========================================================
# 8. SELECT RELEVANT DOCUMENTS
# =========================================================

def select_relevant_documents(
    question,
    profiles=None,
    model=None
):

    if profiles is None:
        profiles = load_document_profiles()

    ranked_results = rank_document_profiles(
        question=question,
        profiles=profiles,
        model=model
    )

    print("\nDOCUMENT RELEVANCE SCORES")

    print("=" * 65)

    for result in ranked_results:

        print(
            f"{result['document']} | "
            f"Subject: {result['subject']} | "
            f"Semantic: {result['semantic_score']:.4f} | "
            f"Lexical: {result['lexical_score']:.4f} | "
            f"Combined: {result['combined_score']:.4f}"
        )

    if not ranked_results:
        return []

    comparison_question = is_comparison_question(
        question
    )

    # -----------------------------------------------------
    # COMPARISON QUESTIONS
    # -----------------------------------------------------

    if comparison_question:

        selected = []

        for result in ranked_results:

            is_relevant = (

                result["combined_score"]
                >= COMPARISON_THRESHOLD

                or (

                    result["lexical_score"]
                    >= LEXICAL_THRESHOLD

                    and result["semantic_score"]
                    >= 0.25
                )
            )

            if is_relevant:

                selected.append(
                    result["document"]
                )

        if len(selected) >= 2:

            print(
                "\nComparison question detected."
            )

            print("\nSelected documents:")

            for document in selected:
                print(f"  - {document}")

            return selected

    # -----------------------------------------------------
    # NORMAL QUESTIONS
    # -----------------------------------------------------

    best_result = ranked_results[0]

    is_relevant = (

        best_result["combined_score"]
        >= SIMILARITY_THRESHOLD

        or (

            best_result["lexical_score"]
            >= LEXICAL_THRESHOLD

            and best_result["semantic_score"]
            >= 0.25
        )
    )

    if is_relevant:

        print("\nSelected document:")

        print(
            f"  - {best_result['document']}"
        )

        return [
            best_result["document"]
        ]

    # -----------------------------------------------------
    # NO CONFIDENT DOCUMENT MATCH
    # -----------------------------------------------------

    print(
        "\nNo sufficiently confident document match."
    )

    print(
        "No documents selected."
    )

    return []


# =========================================================
# 9. TEST
# =========================================================

def main():

    profiles = load_document_profiles()

    print("\nDYNAMIC DOCUMENT SELECTOR")

    print("=" * 65)

    print(
        f"Total document profiles: {len(profiles)}"
    )

    model = load_model()

    test_questions = [

        "Explain code generation",

        "Explain NameNode and DataNodes",

        "Explain collaborative filtering",

        "Compare Hadoop and Compiler Design",

        "What is the capital of Mars?"
    ]

    for question in test_questions:

        print("\n" + "=" * 65)

        print(f"QUESTION: {question}")

        selected = select_relevant_documents(
            question=question,
            profiles=profiles,
            model=model
        )

        print("\nFINAL SELECTION:")

        for document in selected:
            print(f"  - {document}")


if __name__ == "__main__":

    main()
