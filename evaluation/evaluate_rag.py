
import csv
import json
import os
import time
from pathlib import Path

import requests


# ============================================================
# 1. CONFIGURATION
# ============================================================

API_URL = os.getenv(
    "RAG_API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CSV_REPORT = RESULTS_DIR / "evaluation_results.csv"
JSON_REPORT = RESULTS_DIR / "evaluation_summary.json"

UNKNOWN_ANSWER = (
    "The provided documents do not contain sufficient information "
    "to answer this question."
)


# ============================================================
# 2. EVALUATION DATASET
# ============================================================

TEST_CASES = [

    {
        "id": "Q01",
        "question": "What is a NameNode in Hadoop?",
        "expected_document": "U3__Introduction_to_Hadoop.pdf",
        "expected_type": "answer"
    },

    {
        "id": "Q02",
        "question": "What is the role of a DataNode in Hadoop?",
        "expected_document": "U3__Introduction_to_Hadoop.pdf",
        "expected_type": "answer"
    },

    {
        "id": "Q03",
        "question": "Explain supervised and unsupervised learning.",
        "expected_document": "U5",
        "expected_type": "answer"
    },

    {
        "id": "Q04",
        "question": "What is code generation in compiler design?",
        "expected_document": "CD UNIT-4 PART-2.pdf",
        "expected_type": "answer"
    },

    {
        "id": "Q05",
        "question": "What is the capital of Mars?",
        "expected_document": None,
        "expected_type": "unknown"
    }

]


# ============================================================
# 3. BACKEND HEALTH CHECK
# ============================================================

def check_backend():

    print("\nChecking FastAPI backend...")

    try:

        response = requests.get(
            f"{API_URL}/health",
            timeout=10
        )

        response.raise_for_status()

        health = response.json()

        print("Backend status:", health.get("status"))
        print(
            "Indexed documents:",
            health.get("total_documents")
        )
        print(
            "Total vectors:",
            health.get("total_vectors")
        )

        return True

    except requests.RequestException as error:

        print("\nERROR: Cannot connect to FastAPI.")
        print("Details:", error)

        print(
            "\nStart the backend with:\n"
            "uvicorn backend.main:app --reload"
        )

        return False


# ============================================================
# 4. EVALUATE ONE QUESTION
# ============================================================

def evaluate_question(test_case):

    question_id = test_case["id"]
    question = test_case["question"]

    print("\n" + "=" * 65)
    print(f"Running {question_id}")
    print("Question:", question)

    start_time = time.perf_counter()

    try:

        response = requests.post(
            f"{API_URL}/ask",
            json={
                "question": question
            },
            timeout=(10, 180)
        )

        response.raise_for_status()

        result = response.json()

        elapsed_time = round(
            time.perf_counter() - start_time,
            3
        )

        answer = result.get("answer", "")

        sources = result.get("sources", [])

        answer_text = str(answer).strip()

        source_documents = sorted({
            source.get("document", "")
            for source in sources
            if source.get("document")
        })

        # ----------------------------------------------------
        # Answer availability
        # ----------------------------------------------------

        answer_generated = bool(answer_text)

        # ----------------------------------------------------
        # Retrieval evaluation
        # ----------------------------------------------------

        expected_document = test_case["expected_document"]

        if expected_document:

            retrieval_hit = any(
                expected_document.lower()
                in document.lower()
                for document in source_documents
            )

        else:

            retrieval_hit = len(sources) == 0

        # ----------------------------------------------------
        # Citation availability
        # ----------------------------------------------------

        citations_available = (
            len(sources) > 0
            and "[Source " in answer_text
        )

        # ----------------------------------------------------
        # Unknown-question handling
        # ----------------------------------------------------

        if test_case["expected_type"] == "unknown":

            unknown_rejected = (
                UNKNOWN_ANSWER.lower() in answer_text.lower()
                and len(sources) == 0
            )

            test_passed = unknown_rejected

        else:

            unknown_rejected = None

            test_passed = (
                answer_generated
                and retrieval_hit
                and citations_available
            )

        print("Answer generated:", answer_generated)
        print("Expected document retrieved:", retrieval_hit)
        print("Citations available:", citations_available)
        print("Response time:", elapsed_time, "seconds")
        print("Retrieved documents:", source_documents)

        print(
            "RESULT:",
            "PASS" if test_passed else "REVIEW"
        )

        return {

            "test_id": question_id,

            "question": question,

            "expected_document": (
                expected_document or "None"
            ),

            "retrieved_documents": ", ".join(
                source_documents
            ),

            "answer_generated": answer_generated,

            "retrieval_hit": retrieval_hit,

            "citations_available": citations_available,

            "unknown_rejected": unknown_rejected,

            "source_count": len(sources),

            "response_time_seconds": elapsed_time,

            "status": (
                "PASS" if test_passed else "REVIEW"
            ),

            "error": ""

        }

    except requests.Timeout:

        print("RESULT: TIMEOUT")

        return failed_result(
            test_case,
            "Request timed out"
        )

    except requests.RequestException as error:

        print("RESULT: ERROR")

        return failed_result(
            test_case,
            str(error)
        )

    except (ValueError, TypeError, KeyError) as error:

        print("RESULT: ERROR")

        return failed_result(
            test_case,
            str(error)
        )


# ============================================================
# 5. FAILED TEST RESULT
# ============================================================

def failed_result(test_case, error):

    return {

        "test_id": test_case["id"],

        "question": test_case["question"],

        "expected_document": (
            test_case["expected_document"] or "None"
        ),

        "retrieved_documents": "",

        "answer_generated": False,

        "retrieval_hit": False,

        "citations_available": False,

        "unknown_rejected": False,

        "source_count": 0,

        "response_time_seconds": None,

        "status": "ERROR",

        "error": error

    }


# ============================================================
# 6. SAVE CSV REPORT
# ============================================================

def save_csv(results):

    if not results:
        return

    with open(
        CSV_REPORT,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )

        writer.writeheader()

        writer.writerows(results)

    print("\nCSV report saved:", CSV_REPORT)


# ============================================================
# 7. GENERATE SUMMARY
# ============================================================

def generate_summary(results):

    total = len(results)

    passed = sum(
        item["status"] == "PASS"
        for item in results
    )

    reviewed = sum(
        item["status"] == "REVIEW"
        for item in results
    )

    errors = sum(
        item["status"] == "ERROR"
        for item in results
    )

    answer_generated = sum(
        item["answer_generated"]
        for item in results
    )

    retrieval_hits = sum(
        item["retrieval_hit"]
        for item in results
    )

    citation_count = sum(
        item["citations_available"]
        for item in results
    )

    unknown_tests = [
        item for item in results
        if item["unknown_rejected"] is not None
    ]

    unknown_passed = sum(
        item["unknown_rejected"] is True
        for item in unknown_tests
    )

    valid_times = [
        item["response_time_seconds"]
        for item in results
        if item["response_time_seconds"] is not None
    ]

    average_time = (
        round(sum(valid_times) / len(valid_times), 3)
        if valid_times else None
    )

    summary = {

        "total_tests": total,

        "passed": passed,

        "needs_review": reviewed,

        "errors": errors,

        "pass_rate_percent": round(
            passed / total * 100, 2
        ) if total else 0,

        "answer_generation_count": answer_generated,

        "retrieval_hits": retrieval_hits,

        "citation_count": citation_count,

        "unknown_question_tests": len(unknown_tests),

        "unknown_questions_rejected": unknown_passed,

        "average_response_time_seconds": average_time

    }

    with open(
        JSON_REPORT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            summary,
            file,
            indent=4
        )

    return summary


# ============================================================
# 8. MAIN EVALUATION
# ============================================================

def main():

    print("\n" + "=" * 65)

    print("       PRODUCTION RAG ASSISTANT")
    print("       AUTOMATED EVALUATION SYSTEM")

    print("=" * 65)

    if not check_backend():
        return

    results = []

    for test_case in TEST_CASES:

        result = evaluate_question(test_case)

        results.append(result)

    save_csv(results)

    summary = generate_summary(results)

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 65)

    print("             EVALUATION SUMMARY")

    print("=" * 65)

    print("Total tests:", summary["total_tests"])

    print("Passed:", summary["passed"])

    print("Needs review:", summary["needs_review"])

    print("Errors:", summary["errors"])

    print(
        "Pass rate:",
        str(summary["pass_rate_percent"]) + "%"
    )

    print(
        "Retrieval hits:",
        summary["retrieval_hits"]
    )

    print(
        "Citation availability:",
        summary["citation_count"]
    )

    print(
        "Unknown questions rejected:",
        summary["unknown_questions_rejected"],
        "/",
        summary["unknown_question_tests"]
    )

    print(
        "Average response time:",
        summary["average_response_time_seconds"]
    )

    print("\nJSON summary saved:", JSON_REPORT)

    print("\nEvaluation completed.")


if __name__ == "__main__":
    main()
