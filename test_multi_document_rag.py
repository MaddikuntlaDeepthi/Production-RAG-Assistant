
from backend.rag_pipeline import (
    initialize_rag,
    ask_question
)


# =========================================================
# TEST QUESTIONS
# =========================================================

test_questions = [
    "Explain code generation.",
    "Explain NameNode and DataNodes.",
    "Explain collaborative filtering.",
    "Compare Hadoop and Compiler Design.",
    "Explain quantum computing."
]


# =========================================================
# MAIN TEST
# =========================================================

def main():

    print("\n" + "=" * 75)
    print("MULTI-DOCUMENT RAG PIPELINE TEST")
    print("=" * 75)

    # Initialize RAG pipeline only once
    model, index, metadata = initialize_rag()

    passed = 0
    failed = 0

    # Test each question
    for number, question in enumerate(
        test_questions,
        start=1
    ):

        print("\n\n" + "#" * 75)
        print(f"TEST {number}: {question}")
        print("#" * 75)

        try:

            answer, sources = ask_question(
                question=question,
                model=model,
                index=index,
                metadata=metadata
            )

            print("\nFINAL ANSWER")
            print("-" * 75)
            print(answer)

            print("\nRETRIEVED SOURCES")
            print("-" * 75)

            for source in sources:

                print(
                    f"Document: {source.get('document')} | "
                    f"Page: {source.get('page')} | "
                    f"Chunk: {source.get('chunk_id')} | "
                    f"Score: "
                    f"{source.get('similarity_score', 0):.4f}"
                )

            passed += 1
            print("\nTEST COMPLETED SUCCESSFULLY")

        except Exception as error:

            failed += 1

            print("\nTEST FAILED")
            print(f"Error: {error}")

    # =====================================================
    # FINAL TEST SUMMARY
    # =====================================================

    print("\n" + "=" * 75)
    print("FINAL TEST SUMMARY")
    print("=" * 75)

    print(f"Total tests : {len(test_questions)}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")

    if failed == 0:
        print("\nALL TESTS EXECUTED WITHOUT ERRORS!")
    else:
        print("\nSOME TESTS FAILED. CHECK THE OUTPUT ABOVE.")

    print("\n" + "=" * 75)
    print("MULTI-DOCUMENT RAG TESTING FINISHED")
    print("=" * 75)


if __name__ == "__main__":

    main()
