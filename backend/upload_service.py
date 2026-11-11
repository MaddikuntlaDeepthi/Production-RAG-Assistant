
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

import faiss
import pymupdf

from backend.document_processing.diagram_processor import run_diagram_pipeline
from backend.document_processing.unified_processor import build_unified_document
from backend.document_processing.chunker import (
    process_document as create_chunks,
    save_chunks,
)
from backend.embeddings.embedding_generator import (
    process_document as create_embeddings,
)
from backend.embeddings.vector_store import (
    process_all_documents as rebuild_vector_store,
    FAISS_INDEX_PATH,
    METADATA_PATH,
)
from backend.embeddings.document_profiler import generate_document_profiles


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DIAGRAM_PATH = PROCESSED_DIR / "diagram_descriptions.json"
PROFILE_PATH = PROCESSED_DIR / "document_profiles.json"

DIAGRAM_DIR = PROCESSED_DIR / "diagrams"

SHARED_FILES = [
    FAISS_INDEX_PATH,
    METADATA_PATH,
    PROFILE_PATH,
    DIAGRAM_PATH,
]


# --------------------------------------------------
# DOCUMENT ID
# --------------------------------------------------

def get_document_id(filename):
    """
    Generate a safe document ID from the PDF filename.
    """

    stem = Path(filename).stem.lower()

    document_id = re.sub(
        r"[^a-z0-9_-]+",
        "_",
        stem
    ).strip("_")

    if not document_id:
        raise ValueError("Invalid PDF filename.")

    return document_id


# --------------------------------------------------
# RESTORE SHARED FILES
# --------------------------------------------------

def restore_file_snapshot(snapshot_dir, original_states):
    """
    Restore shared files to their original state.
    """

    errors = []

    for file_path, existed_before in original_states.items():

        backup_path = snapshot_dir / file_path.name

        try:
            if existed_before:

                if not backup_path.exists():
                    raise FileNotFoundError(
                        f"Backup missing for {file_path.name}"
                    )

                file_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                restore_path = file_path.with_name(
                    file_path.name + ".restore"
                )

                shutil.copy2(
                    backup_path,
                    restore_path
                )

                os.replace(
                    restore_path,
                    file_path
                )

            else:

                if file_path.exists():
                    file_path.unlink()

        except Exception as error:
            errors.append(
                f"{file_path.name}: {error}"
            )

    return errors


# --------------------------------------------------
# CLEAN UP UPLOADED DOCUMENT ARTIFACTS
# --------------------------------------------------

def cleanup_document_artifacts(document_dir, pdf_path):

    if document_dir.exists():
        shutil.rmtree(
            document_dir,
            ignore_errors=True
        )

    if DIAGRAM_DIR.exists():

        pattern = (
            f"{pdf_path.stem}_page_*_region_*.png"
        )

        for image_path in DIAGRAM_DIR.rglob(pattern):

            try:
                image_path.unlink()
            except OSError:
                pass


# --------------------------------------------------
# PROCESS UPLOADED PDF
# --------------------------------------------------

def process_uploaded_pdf(pdf_path, embedding_model):

    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    document_id = get_document_id(
        pdf_path.name
    )

    document_dir = PROCESSED_DIR / document_id

    if document_dir.exists():
        raise ValueError(
            f"Document '{pdf_path.name}' has already been processed."
        )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # BACKUP EXISTING SHARED FILES
    # --------------------------------------------------

    snapshot_dir = Path(
        tempfile.mkdtemp(
            prefix="rag_upload_backup_"
        )
    )

    original_states = {}

    try:

        for file_path in SHARED_FILES:

            original_states[file_path] = (
                file_path.exists()
            )

            if file_path.exists():

                shutil.copy2(
                    file_path,
                    snapshot_dir / file_path.name
                )

    except Exception:

        shutil.rmtree(
            snapshot_dir,
            ignore_errors=True
        )

        raise

    # --------------------------------------------------
    # PROCESSING
    # --------------------------------------------------

    try:

        # Ensure diagram descriptions file exists.
        # This is required by unified_processor.py.

        if not DIAGRAM_PATH.exists():

            DIAGRAM_PATH.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            DIAGRAM_PATH.write_text(
                "[]",
                encoding="utf-8"
            )

        # ----------------------------------------------
        # STEP 1: READ PDF
        # ----------------------------------------------

        with pymupdf.open(pdf_path) as pdf:

            page_count = len(pdf)

            if page_count == 0:
                raise ValueError(
                    "The uploaded PDF contains no pages."
                )

            # ------------------------------------------
            # STEP 2: PROCESS DIAGRAMS
            # ------------------------------------------

            for page_number in range(
                1,
                page_count + 1
            ):

                run_diagram_pipeline(
                    pdf_path,
                    page_number
                )

        # ----------------------------------------------
        # STEP 3: BUILD UNIFIED DOCUMENT
        # ----------------------------------------------

        unified_data = build_unified_document(
            pdf_path
        )

        document_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        unified_path = (
            document_dir / "unified_document.json"
        )

        temporary_unified_path = (
            document_dir / "unified_document.tmp"
        )

        with open(
            temporary_unified_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                unified_data,
                file,
                ensure_ascii=False,
                indent=2
            )

        os.replace(
            temporary_unified_path,
            unified_path
        )

        # ----------------------------------------------
        # STEP 4: CREATE CHUNKS
        # ----------------------------------------------

        chunks = create_chunks(
            unified_path
        )

        if not chunks:
            raise ValueError(
                "No chunks were generated from the PDF."
            )

        chunks_path = (
            document_dir / "chunks.json"
        )

        save_chunks(
            chunks,
            output_path=chunks_path
        )

        # ----------------------------------------------
        # STEP 5: GENERATE EMBEDDINGS
        # ----------------------------------------------

        embedding_count = create_embeddings(
            embedding_model,
            chunks_path
        )

        if not embedding_count or embedding_count <= 0:
            raise ValueError(
                "Embedding generation failed."
            )

        # ----------------------------------------------
        # STEP 6: REBUILD VECTOR STORE
        # ----------------------------------------------

        rebuild_vector_store()

        # ----------------------------------------------
        # STEP 7: REGENERATE DOCUMENT PROFILES
        # ----------------------------------------------

        generate_document_profiles()

        # ----------------------------------------------
        # STEP 8: VERIFY VECTOR STORE
        # ----------------------------------------------

        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                "FAISS index was not generated."
            )

        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                "Vector metadata was not generated."
            )

        index = faiss.read_index(
            str(FAISS_INDEX_PATH)
        )

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            metadata = json.load(file)

        if index.ntotal != len(metadata):
            raise ValueError(
                "FAISS index and metadata counts do not match."
            )

        uploaded_document_vectors = sum(
            1
            for item in metadata
            if item.get("document") == pdf_path.name
        )

        if uploaded_document_vectors != embedding_count:

            raise ValueError(
                "Uploaded document embedding count does not match "
                "the vector metadata."
            )

        # ----------------------------------------------
        # STEP 9: SUCCESS
        # ----------------------------------------------

        result = {
            "document": pdf_path.name,
            "document_id": document_id,
            "pages": page_count,
            "chunks": len(chunks),
            "embeddings": embedding_count,
            "total_vectors": index.ntotal,
            "index": index,
            "metadata": metadata,
        }

        # Remove temporary backup after successful processing.

        shutil.rmtree(
            snapshot_dir,
            ignore_errors=True
        )

        return result

    # --------------------------------------------------
    # ROLLBACK IF ANY STEP FAILS
    # --------------------------------------------------

    except Exception as original_error:

        rollback_errors = []

        try:

            cleanup_document_artifacts(
                document_dir,
                pdf_path
            )

        except Exception as error:

            rollback_errors.append(
                f"Document cleanup failed: {error}"
            )

        try:

            rollback_errors.extend(
                restore_file_snapshot(
                    snapshot_dir,
                    original_states
                )
            )

        except Exception as error:

            rollback_errors.append(
                f"Shared-file restoration failed: {error}"
            )

        try:

            if pdf_path.exists():
                pdf_path.unlink()

        except Exception as error:

            rollback_errors.append(
                f"Uploaded PDF cleanup failed: {error}"
            )

        if rollback_errors:

            raise RuntimeError(
                "Upload failed and rollback encountered errors. "
                f"Backup files have been preserved at: {snapshot_dir}. "
                f"Original error: {original_error}. "
                f"Rollback errors: {'; '.join(rollback_errors)}"
            ) from original_error

        shutil.rmtree(
            snapshot_dir,
            ignore_errors=True
        )

        raise RuntimeError(
            "Upload failed. Previous shared data was restored. "
            f"Reason: {original_error}"
        ) from original_error
