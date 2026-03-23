from __future__ import annotations

import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from pymongo.collection import Collection

from services.document_service import document_service


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _summarize_document_stats(documents: list) -> Dict[str, int]:
    """Build stable metadata even when one page is split into many chunks."""
    page_numbers = set()
    estimated_tables = 0

    for doc in documents:
        metadata = getattr(doc, "metadata", {}) or {}
        page_num = _safe_int(metadata.get("page_label") or metadata.get("page_number") or metadata.get("page"))
        if page_num is not None:
            page_numbers.add(page_num)

        chunk_type = str(metadata.get("type") or "").strip().lower()
        if chunk_type == "table":
            estimated_tables += 1
            continue

        text = str(getattr(doc, "text", "") or "")
        lowered = text.lower()
        # Heuristic table signals from markdown/plain extraction outputs.
        if text.lstrip().startswith("TABLE:"):
            estimated_tables += 1
        elif "|" in text and "---" in text:
            estimated_tables += 1
        elif "table" in lowered:
            estimated_tables += lowered.count("table")

    pages = len(page_numbers)
    if pages <= 0:
        pages = len(documents)

    return {
        "pages": pages,
        "tables_count": max(0, estimated_tables),
    }


def _set_processing_state(
    documents_meta_collection: Collection,
    doc_id: str,
    message: str,
    *,
    status: str = "processing",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    payload: Dict[str, Any] = {
        "status": status,
        "message": message,
        "updated_at": datetime.utcnow(),
    }
    if extra:
        payload.update(extra)

    documents_meta_collection.update_one({"_id": doc_id}, {"$set": payload})


def process_uploaded_document(
    doc_id: str,
    file_path: str,
    user_id: str,
    filename: str,
    file_type: str,
    upload_kind: str,
    main_collection: str,
    documents_meta_collection: Collection,
) -> None:
    """Background task for heavy PDF/image processing and vector indexing."""
    try:
        print("\n" + "=" * 60)
        print(f"Background processing started: {filename}")
        print("=" * 60)

        _set_processing_state(
            documents_meta_collection,
            doc_id,
            "Preparing file for text extraction...",
            status="processing",
            extra={"processing_error": None},
        )

        def _progress(stage: str) -> None:
            print(f"📍 [{doc_id}] {stage}")
            _set_processing_state(documents_meta_collection, doc_id, stage, status="processing")

        if upload_kind == "image":
            documents = document_service.process_image_hybrid(file_path, progress_callback=_progress)
            processing_mode = "image_hybrid"
        elif upload_kind == "pdf":
            documents = document_service.process_pdf_hybrid(file_path, progress_callback=_progress)
            processing_mode = "pdf_hybrid"
        else:
            raise ValueError("Unsupported file type. Please upload a PDF or image file.")

        documents = [doc for doc in documents if str(getattr(doc, "text", "") or "").strip()]
        if not documents:
            raise ValueError("No readable text could be extracted from this file.")

        stats = _summarize_document_stats(documents)

        _set_processing_state(
            documents_meta_collection,
            doc_id,
            "Text extracted. Creating vector index...",
            status="processing",
            extra={
                "chunks_count": len(documents),
                "pages": stats["pages"],
                "tables_count": stats["tables_count"],
            },
        )

        for doc in documents:
            doc.metadata["upload_id"] = doc_id
            doc.metadata["document_id"] = doc_id
            doc.metadata["user_id"] = user_id
            doc.metadata["filename"] = filename
            doc.metadata["file_type"] = file_type
            doc.metadata["upload_kind"] = upload_kind

        document_service.create_vector_index(documents, main_collection)

        _set_processing_state(
            documents_meta_collection,
            doc_id,
            f"Processed {len(documents)} chunks via {processing_mode}",
            status="ready",
            extra={
                "chunks_count": len(documents),
                "pages": stats["pages"],
                "tables_count": stats["tables_count"],
                "upload_kind": upload_kind,
                "processing_error": None,
            },
        )

        print(f"✅ Background processing completed for {doc_id} with {len(documents)} chunks")
    except Exception as exc:
        print(f"❌ Background processing failed for {doc_id}: {exc}")
        traceback.print_exc()
        _set_processing_state(
            documents_meta_collection,
            doc_id,
            "Document processing failed",
            status="failed",
            extra={"processing_error": str(exc)},
        )
