
import re
import threading
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File
)

from pydantic import BaseModel, Field

from backend.rag_pipeline import (
    initialize_rag,
    ask_question
)

from backend.upload_service import process_uploaded_pdf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

MAX_UPLOAD_SIZE = 50 * 1024 * 1024

# Prevent simultaneous uploads from rebuilding the index together.
upload_lock = threading.Lock()


# --------------------------------------------------
# 1. APPLICATION LIFESPAN
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("\nStarting Production RAG Assistant...")

    model, index, metadata = initialize_rag()

    app.state.model = model
    app.state.index = index
    app.state.metadata = metadata
    app.state.rag_ready = True

    print("RAG components loaded successfully!")
    print("Application is ready to accept questions.\n")

    yield

    print("\nShutting down Production RAG Assistant...")

    app.state.rag_ready = False


# --------------------------------------------------
# 2. CREATE APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Production RAG Assistant",
    description="An AI-powered multi-document question-answering system",
    version="1.1.0",
    lifespan=lifespan
)


# --------------------------------------------------
# 3. QUESTION REQUEST
# --------------------------------------------------

class QuestionRequest(BaseModel):

    question: str = Field(
        min_length=1,
        description="Question asked by the user"
    )


# --------------------------------------------------
# 4. SAFE FILENAME
# --------------------------------------------------

def safe_filename(filename):

    filename = Path(filename or "").name

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    stem = Path(filename).stem

    stem = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        stem
    ).strip("_")

    if not stem:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF filename."
        )

    return f"{stem}.pdf"


# --------------------------------------------------
# 5. HOME
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "Welcome to Production RAG Assistant!",
        "status": "Backend is running successfully"
    }


# --------------------------------------------------
# 6. HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():

    if not getattr(app.state, "rag_ready", False):

        raise HTTPException(
            status_code=503,
            detail="RAG application is not ready."
        )

    return {
        "status": "healthy",
        "application": "Production RAG Assistant",
        "rag_status": "ready",
        "total_vectors": app.state.index.ntotal,
        "total_documents": len({
            record.get("document")
            for record in app.state.metadata
        })
    }


# --------------------------------------------------
# 7. PDF UPLOAD
# --------------------------------------------------

@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):

    if not getattr(app.state, "rag_ready", False):

        raise HTTPException(
            status_code=503,
            detail="RAG application is not ready."
        )

    filename = safe_filename(file.filename)

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    pdf_path = RAW_DIR / filename

    with upload_lock:

        if pdf_path.exists():

            raise HTTPException(
                status_code=409,
                detail="A PDF with this filename already exists."
            )

        try:

            content = file.file.read(
                MAX_UPLOAD_SIZE + 1
            )

            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded PDF is empty."
                )

            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="PDF exceeds the 50 MB upload limit."
                )

            if not content.startswith(b"%PDF-"):
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is not a valid PDF."
                )

            with open(pdf_path, "wb") as output_file:
                output_file.write(content)

            result = process_uploaded_pdf(
                pdf_path=pdf_path,
                embedding_model=app.state.model
            )

            # Update the live application only after
            # successful processing and validation.
            app.state.index = result["index"]
            app.state.metadata = result["metadata"]

            return {
                "status": "success",
                "message": "PDF uploaded and processed successfully.",
                "document": result["document"],
                "pages": result["pages"],
                "chunks": result["chunks"],
                "embeddings": result["embeddings"],
                "total_vectors": result["total_vectors"]
            }

        except HTTPException:
            raise

        except Exception as error:

            print("\nPDF UPLOAD FAILED:", str(error))

            raise HTTPException(
                status_code=500,
                detail=f"PDF processing failed: {str(error)}"
            )

        finally:
            file.file.close()


# --------------------------------------------------
# 8. QUESTION ANSWERING
# --------------------------------------------------

@app.post("/ask")
def ask(request: QuestionRequest):

    if not getattr(app.state, "rag_ready", False):

        raise HTTPException(
            status_code=503,
            detail="RAG application is not ready."
        )

    try:

        answer, retrieved_chunks = ask_question(
            question=request.question,
            model=app.state.model,
            index=app.state.index,
            metadata=app.state.metadata
        )

        sources = []

        for chunk in retrieved_chunks:

            sources.append({
                "document": chunk.get("document"),
                "page": chunk.get("page"),
                "source_pages": chunk.get("source_pages"),
                "chunk_id": chunk.get("chunk_id"),
                "content_type": chunk.get("content_type"),
                "similarity_score": chunk.get("similarity_score")
            })

        return {
            "question": request.question,
            "answer": answer,
            "sources": sources
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Question processing failed: {str(error)}"
        )
