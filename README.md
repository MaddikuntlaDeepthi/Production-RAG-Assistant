# Production RAG Assistant

An AI-powered multi-document Retrieval-Augmented Generation (RAG) system that answers questions from PDF documents with source citations and evidence-based responses.

## Project Overview

Production RAG Assistant enables users to upload multiple PDF documents and ask questions using natural language. It retrieves relevant information using semantic and lexical search and generates answers grounded in the uploaded documents.

When sufficient information is unavailable, the system responds that the documents do not contain enough information.

## Key Features

- Multi-document PDF upload and processing.
- Text, table, and diagram extraction.
- Semantic and lexical hybrid retrieval.
- FAISS vector database for similarity search.
- LLM-powered question answering using Groq.
- Source citations with document names and page numbers.
- Evidence-based responses and unknown-question handling.
- FastAPI backend and Streamlit frontend.
- Docker containerization.
- Persistent document and vector storage.
- Automated RAG evaluation framework.

## Technology Stack

| Component            | Technology                |
| -------------------- | ------------------------- |
| Programming Language | Python                    |
| Backend              | FastAPI                   |
| Frontend             | Streamlit                 |
| LLM                  | Groq API                  |
| Embeddings           | Sentence Transformers     |
| Vector Database      | FAISS                     |
| PDF Processing       | PyMuPDF                   |
| Retrieval            | Semantic + Lexical Search |
| Deployment Setup     | Docker, Docker Compose    |

## System Architecture

```text
        PDF DOCUMENTS
              |
              v
       DOCUMENT UPLOAD
              |
              v
       PDF PROCESSING
      /      |       \
   TEXT    TABLES   DIAGRAMS
      \      |       /
              |
              v
         CHUNKING
              |
              v
         EMBEDDINGS
              |
              v
        FAISS INDEX
              |
              v
       HYBRID RETRIEVAL
      (Semantic + Lexical)
              |
              v
          GROQ LLM
              |
              v
       ANSWER GENERATION
              |
              v
      ANSWER WITH CITATIONS
```

## Project Structure

```text
PRODUCTION_RAG_ASSISTANT/
│
├── backend/
│   ├── document_processing/
│   ├── embeddings/
│   ├── llm/
│   ├── main.py
│   ├── rag_pipeline.py
│   ├── groq_client.py
│   └── upload_service.py
│
├── evaluation/
│   └── evaluate_rag.py
│
├── data/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── .gitignore
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/MaddikuntlaDeepthi/Production-RAG-Assistant.git
cd Production-RAG-Assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Keep your API key private. Never commit the `.env` file to GitHub.

### 5. Start the backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 6. Start the frontend

Open another terminal and run:

```bash
streamlit run app.py
```

## Run with Docker

Make sure Docker Desktop is running.

```bash
docker-compose up -d --build
```

To stop the containers:

```bash
docker-compose down
```

## Application URLs

- **Streamlit Interface:** http://localhost:8501
- **FastAPI Backend:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Evaluation

The project includes an automated evaluation framework to test:

- Document retrieval.
- Expected source document matching.
- Citation availability.
- Handling of questions without supporting information.

## Future Enhancements

- Dedicated re-ranking for improved retrieval.
- User authentication and access control.
- Document management and deletion.
- Expanded evaluation benchmark.
- Cloud deployment and scalability improvements.

## Author

**Deepthi Maddikuntla**

GitHub: [MaddikuntlaDeepthi](https://github.com/MaddikuntlaDeepthi)

---

_Production RAG Assistant — Intelligent, document-grounded question answering._
