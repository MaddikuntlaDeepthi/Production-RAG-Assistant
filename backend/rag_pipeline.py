
from backend.embeddings.semantic_search import (
    load_model,
    load_faiss_index,
    load_metadata,
    search_similar_chunks
)

from backend.embeddings.document_selector import (
    select_relevant_documents
)

from backend.llm.llm_generator import generate_answer


UNKNOWN_ANSWER = (
    "The provided documents do not contain sufficient "
    "information to answer this question."
)


def initialize_rag():

    print("Initializing RAG pipeline...")

    model = load_model()
    index = load_faiss_index()
    metadata = load_metadata()

    if index.ntotal != len(metadata):
        raise ValueError(
            "FAISS index and metadata counts do not match."
        )

    print("RAG pipeline initialized successfully!")
    print(f"Total vectors: {index.ntotal}")
    print(f"Total metadata records: {len(metadata)}")

    return model, index, metadata


def ask_question(question, model, index, metadata):

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Please enter a valid question.")

    print("\n" + "=" * 70)
    print("DYNAMIC DOCUMENT IDENTIFICATION")
    print("=" * 70)

    selected_documents = select_relevant_documents(
        question=question,
        model=model
    )

    if not selected_documents:
        print("\nNo sufficiently relevant document selected.")
        return UNKNOWN_ANSWER, []

    print("\nSelected documents:")

    for document in selected_documents:
        print(f" - {document}")

    print("\n" + "=" * 70)
    print("RETRIEVING RELEVANT DOCUMENT CHUNKS")
    print("=" * 70)

    retrieved_chunks = search_similar_chunks(
        question=question,
        model=model,
        index=index,
        metadata=metadata,
        top_k=3,
        allowed_documents=selected_documents
    )

    print(f"\nRetrieved relevant chunks: {len(retrieved_chunks)}")

    if not retrieved_chunks:
        print("No chunks passed the similarity threshold.")
        return UNKNOWN_ANSWER, []

    print("\nGenerating answer using Groq...")

    answer = generate_answer(
        question=question,
        retrieved_chunks=retrieved_chunks
    )

    return answer, retrieved_chunks


def main():

    model, index, metadata = initialize_rag()

    question = "What is the role of NameNode in HDFS?"

    answer, sources = ask_question(
        question,
        model,
        index,
        metadata
    )

    print("\n" + "=" * 70)
    print("FINAL RAG ANSWER")
    print("=" * 70)

    print(answer)

    print("\n" + "=" * 70)
    print("RETRIEVED SOURCES")
    print("=" * 70)

    for source in sources:
        print(
            f"Document: {source.get('document')} | "
            f"Page: {source.get('page')} | "
            f"Chunk: {source.get('chunk_id')} | "
            f"Score: {source.get('similarity_score', 0):.4f}"
        )


if __name__ == "__main__":
    main()
