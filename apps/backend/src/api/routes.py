"""
API Routes - production-friendly implementation.

Key upgrades:
- Async document processing for large PDFs (no frontend request timeout on upload)
- Persistent MongoDB metadata for documents/quizzes/attempts/chat history
- Richer history/progress endpoints for analytics views
- External chatbot proxy endpoints
"""

from __future__ import annotations

import asyncio
import os
import re
import threading
import uuid
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from pymongo import DESCENDING, MongoClient

from api.schemas import (
    AttemptInfo,
    ChatRequest,
    ChatResponse,
    ChatbotProxyRequest,
    DocumentInfo,
    DocumentStatusResponse,
    DocumentUploadResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizResult,
    QuizSubmitRequest,
    StudyPlanCreateRequest,
    StudyPlanGenerateRequest,
    StudyPlanStatusRequest,
    VisionResponse,
)
from api.document_utils import resolve_upload_kind, safe_datetime, serialize_document_meta
from chatbot.service import PersonalizedChatbotService
from config import settings
from services.background_processor import process_uploaded_document

router = APIRouter()

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent / "data"
UPLOAD_DIR.mkdir(exist_ok=True)

# Collections
MAIN_COLLECTION = "quiz_tutor"
DOCUMENTS_META_COLLECTION = "documents_meta"
QUIZZES_COLLECTION = "quizzes"
ATTEMPTS_COLLECTION = "attempts"
CHAT_HISTORY_COLLECTION = "chat_history"
REMINDERS_COLLECTION = "reminders"

# MongoDB
mongo_client = MongoClient(settings.MONGODB_URI)
db = mongo_client[settings.MONGODB_DATABASE]
documents_meta_collection = db[DOCUMENTS_META_COLLECTION]
quizzes_collection = db[QUIZZES_COLLECTION]
attempts_collection = db[ATTEMPTS_COLLECTION]
chat_history_collection = db[CHAT_HISTORY_COLLECTION]
reminders_collection = db[REMINDERS_COLLECTION]

PROCESSING_TIMEOUT_MINUTES = 20

chatbot_service = PersonalizedChatbotService(
    db=db,
    main_collection=MAIN_COLLECTION,
    attempts_collection_name=ATTEMPTS_COLLECTION,
    documents_collection_name=DOCUMENTS_META_COLLECTION,
)


def _create_supabase_client() -> Optional[Any]:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None

    try:
        from supabase import create_client

        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as exc:
        print(f"⚠️ Supabase storage unavailable; local storage only. Details: {exc}")
        return None


supabase_client = _create_supabase_client()


def _build_supabase_public_url(object_path: str) -> str:
    if not object_path:
        return ""

    if settings.SUPABASE_PUBLIC_URL_BASE:
        return f"{settings.SUPABASE_PUBLIC_URL_BASE.rstrip('/')}/{object_path.lstrip('/')}"

    base_url = str(settings.SUPABASE_URL or "").rstrip("/")
    bucket = str(settings.SUPABASE_BUCKET or "documents").strip("/")
    if not base_url or not bucket:
        return ""

    return f"{base_url}/storage/v1/object/public/{bucket}/{object_path.lstrip('/')}"


def _upload_to_supabase(
    document_id: str,
    filename: str,
    file_bytes: bytes,
    content_type: str,
) -> Dict[str, str]:
    if not supabase_client:
        return {"url": "", "path": ""}

    bucket = str(settings.SUPABASE_BUCKET or "documents")
    object_path = f"{document_id}/{Path(filename).name}"

    try:
        supabase_client.storage.from_(bucket).upload(
            object_path,
            file_bytes,
            {
                "content-type": content_type or "application/pdf",
                "upsert": "true",
            },
        )

        public_url = ""
        try:
            url_value = supabase_client.storage.from_(bucket).get_public_url(object_path)
            if isinstance(url_value, str):
                public_url = url_value
            elif isinstance(url_value, dict):
                public_url = str(url_value.get("publicUrl") or url_value.get("public_url") or "")
        except Exception:
            public_url = ""

        if not public_url:
            public_url = _build_supabase_public_url(object_path)

        return {"url": public_url, "path": object_path}
    except Exception as exc:
        print(f"⚠️ Supabase upload skipped for {document_id}; using local file. Details: {exc}")
        return {"url": "", "path": ""}


def _delete_supabase_object(object_path: str) -> None:
    if not supabase_client or not object_path:
        return

    try:
        bucket = str(settings.SUPABASE_BUCKET or "documents")
        supabase_client.storage.from_(bucket).remove([object_path])
    except Exception as exc:
        print(f"⚠️ Failed to remove Supabase object {object_path}: {exc}")


def _refresh_document_attempt_stats(document_id: str) -> None:
    total_attempts = attempts_collection.count_documents({"document_id": document_id})
    aggregation = list(
        attempts_collection.aggregate(
            [
                {"$match": {"document_id": document_id}},
                {"$group": {"_id": "$document_id", "avg_score": {"$avg": "$score"}}},
            ]
        )
    )

    avg_score = float(aggregation[0]["avg_score"]) if aggregation else 0.0

    documents_meta_collection.update_one(
        {"_id": document_id},
        {
            "$set": {
                "attempts_count": int(total_attempts),
                "average_score": avg_score,
                "updated_at": datetime.utcnow(),
            }
        },
    )


def _extract_weak_areas(user_attempts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    topic_stats: Dict[str, Dict[str, float]] = {}

    for attempt in user_attempts:
        for area in attempt.get("weak_areas", []) or []:
            topic = area.get("topic") or "General"
            accuracy = float(area.get("accuracy", 0.0))

            if topic not in topic_stats:
                topic_stats[topic] = {"sum_accuracy": 0.0, "count": 0, "min_accuracy": 1.0}

            topic_stats[topic]["sum_accuracy"] += accuracy
            topic_stats[topic]["count"] += 1
            topic_stats[topic]["min_accuracy"] = min(topic_stats[topic]["min_accuracy"], accuracy)

    output: List[Dict[str, Any]] = []
    for topic, stats in topic_stats.items():
        avg_accuracy = stats["sum_accuracy"] / max(stats["count"], 1)
        output.append(
            {
                "topic": topic,
                "accuracy": avg_accuracy,
                "attempts": int(stats["count"]),
                "priority": "high" if avg_accuracy < 0.5 else "medium" if avg_accuracy < 0.7 else "low",
            }
        )

    output.sort(key=lambda item: item["accuracy"])
    return output[:10]


def _determine_trend(user_attempts: List[Dict[str, Any]]) -> str:
    if len(user_attempts) < 4:
        return "stable"

    ordered = sorted(user_attempts, key=lambda x: x.get("completed_at", datetime.utcnow()))
    scores = [float(a.get("score", 0.0)) for a in ordered]

    pivot = max(len(scores) // 2, 1)
    first_avg = sum(scores[:pivot]) / len(scores[:pivot])
    second_avg = sum(scores[pivot:]) / len(scores[pivot:])

    if second_avg - first_avg > 0.08:
        return "improving"
    if first_avg - second_avg > 0.08:
        return "needs_work"
    return "stable"


def _build_review_notifications(user_id: str, user_attempts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    notifications: List[Dict[str, Any]] = []

    if not user_attempts:
        notifications.append(
            {
                "id": f"note-{uuid.uuid4()}",
                "type": "reminder",
                "title": "Start your first quiz",
                "message": "Upload a document and complete a quiz to start tracking progress.",
                "created_at": datetime.utcnow(),
            }
        )
        return notifications

    avg_score = sum(float(a.get("score", 0.0)) for a in user_attempts) / len(user_attempts)
    weak_areas = _extract_weak_areas(user_attempts)

    if avg_score < 0.6:
        notifications.append(
            {
                "id": f"note-{uuid.uuid4()}",
                "type": "review",
                "title": "Review recommended",
                "message": "Your recent average is below 60%. Revisit weak topics before taking the next quiz.",
                "created_at": datetime.utcnow(),
            }
        )

    for area in weak_areas[:3]:
        notifications.append(
            {
                "id": f"note-{uuid.uuid4()}",
                "type": "topic",
                "title": f"Focus on {area['topic']}",
                "message": f"Current accuracy is {area['accuracy'] * 100:.0f}%. Practice this topic with a short-answer quiz.",
                "created_at": datetime.utcnow(),
            }
        )

    return notifications


def _tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 2]


def _deduplicate_chunks(chunks: List[Dict[str, Any]], max_items: int = 8) -> List[Dict[str, Any]]:
    seen = set()
    output: List[Dict[str, Any]] = []

    for chunk in chunks:
        text = (chunk.get("text") or "").strip()
        if not text:
            continue

        key = text[:240].lower()
        if key in seen:
            continue

        seen.add(key)
        output.append(chunk)

        if len(output) >= max_items:
            break

    return output


def _rank_chunks_for_query(chunks: List[Dict[str, Any]], query: str, top_k: int = 8) -> List[Dict[str, Any]]:
    query_tokens = _tokenize(query)
    normalized: List[Dict[str, Any]] = []

    for chunk in chunks:
        text = (chunk.get("text") or "").strip()
        if not text:
            continue

        lowered = text.lower()
        lexical_score = 0.0

        if query_tokens:
            overlap = sum(1 for token in query_tokens if token in lowered)
            lexical_score = overlap / max(len(query_tokens), 1)

        existing_score = float(chunk.get("score", 0.0) or 0.0)
        final_score = max(existing_score, lexical_score)

        normalized.append(
            {
                "text": text,
                "metadata": chunk.get("metadata", {}) or {},
                "score": final_score,
            }
        )

    if not normalized:
        return []

    normalized.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)

    if query_tokens:
        positive = [chunk for chunk in normalized if float(chunk.get("score", 0.0)) > 0.0]
        if positive:
            normalized = positive

    return _deduplicate_chunks(normalized, max_items=top_k)


def _build_context_from_chunks(chunks: List[Dict[str, Any]], max_chars: int = 12000) -> str:
    parts: List[str] = []
    total_chars = 0

    for chunk in chunks:
        text = (chunk.get("text") or "").strip()
        if not text:
            continue

        remaining = max_chars - total_chars
        if remaining <= 0:
            break

        snippet = text if len(text) <= remaining else text[:remaining]
        parts.append(snippet)
        total_chars += len(snippet)

    return "\n\n".join(parts).strip()


def _compute_confidence(chunks: List[Dict[str, Any]]) -> float:
    if not chunks:
        return 0.0

    avg_score = sum(float(chunk.get("score", 0.0) or 0.0) for chunk in chunks) / len(chunks)
    return max(0.05, min(avg_score, 1.0))


def _estimate_table_indicators(chunks: List[Dict[str, Any]]) -> int:
    """Estimate table count from retrieved chunks and metadata signals."""
    table_hits = 0

    for chunk in chunks:
        metadata = chunk.get("metadata", {}) or {}
        text = str(chunk.get("text") or "")
        lowered = text.lower()

        chunk_type = str(metadata.get("type") or "").strip().lower()
        if chunk_type == "table":
            table_hits += 1
            continue

        if text.lstrip().startswith("TABLE:"):
            table_hits += 1
            continue

        if "|" in text and "---" in text:
            table_hits += 1
            continue

        # Lightweight fallback for OCR/plain extraction where tables lose structure.
        if "table" in lowered:
            table_hits += max(1, lowered.count("table"))

    return max(0, table_hits)


def _is_table_query(query: str) -> bool:
    lowered = (query or "").lower()
    table_terms = ["table", "tables", "tabular"]
    return any(term in lowered for term in table_terms)


def _is_table_count_query(query: str) -> bool:
    lowered = (query or "").lower()
    checks = ["how many table", "number of table", "tables in", "table count"]
    return any(check in lowered for check in checks)


def _is_table_explain_query(query: str) -> bool:
    lowered = (query or "").lower()
    checks = [
        "what are the tables",
        "list the tables",
        "show the tables",
        "explain each table",
        "explain the tables",
        "table contents",
    ]
    return any(check in lowered for check in checks)


def _is_generic_image_query(query: str) -> bool:
    lowered = (query or "").strip().lower()
    generic_patterns = [
        "what is this",
        "what is this photo",
        "what are this photo include",
        "what ar this photo include",
        "what does this photo include",
        "what does this image include",
        "what is in this photo",
        "what is in this image",
    ]
    if any(pattern in lowered for pattern in generic_patterns):
        return True

    query_tokens = _tokenize(lowered)
    generic_tokens = {"what", "this", "photo", "image", "include", "contains", "mean", "explain"}
    if query_tokens and all(token in generic_tokens for token in query_tokens):
        return True

    return False


def _build_image_ocr_summary(chunks: List[Dict[str, Any]], max_items: int = 4) -> str:
    if not chunks:
        return (
            "I could not find extracted OCR text for this image yet. "
            "Try re-uploading a clearer image with visible text."
        )

    snippets: List[str] = []
    for chunk in chunks[:max_items]:
        text = " ".join(str(chunk.get("text") or "").split()).strip()
        if text:
            snippets.append(text[:260])

    if not snippets:
        return (
            "I could not find extracted OCR text for this image yet. "
            "Try re-uploading a clearer image with visible text."
        )

    preview = "\n- " + "\n- ".join(snippets)
    return (
        "This upload is processed with OCR, so I can read text that appears in the image but I cannot "
        "reliably describe non-text visual objects yet.\n"
        "Here is the extracted text I found:" + preview
    )


def _build_grounded_timeout_fallback(chunks: List[Dict[str, Any]], max_items: int = 3) -> str:
    """Return a grounded fallback response when the LLM generation path times out."""
    snippets: List[str] = []
    for chunk in chunks[:max_items]:
        text = " ".join(str(chunk.get("text") or "").split()).strip()
        if text:
            snippets.append(text[:220])

    if not snippets:
        return "I don't have enough information about that in the document."

    return (
        "I could not complete full answer generation in time, but here are relevant document excerpts:\n"
        + "\n".join([f"- {snippet}" for snippet in snippets])
    )


def _fetch_table_chunks_for_document(document_id: str, limit: int = 2000, top_k: int = 10) -> List[Dict[str, Any]]:
    from services.document_service import document_service

    all_doc_chunks = document_service.get_document_chunks(
        document_id=document_id,
        collection_name=MAIN_COLLECTION,
        limit=limit,
    )

    table_like: List[Dict[str, Any]] = []
    for chunk in all_doc_chunks:
        text = str(chunk.get("text") or "")
        lowered = text.lower()
        metadata = chunk.get("metadata", {}) or {}

        chunk_type = str(metadata.get("type") or "").strip().lower()
        has_markdown_table = "|" in text and "---" in text
        has_table_prefix = text.lstrip().startswith("TABLE:")
        has_table_word = "table" in lowered

        if chunk_type == "table" or has_markdown_table or has_table_prefix or has_table_word:
            table_like.append(
                {
                    "text": text,
                    "metadata": metadata,
                    "score": float(chunk.get("score", 0.8) or 0.8),
                }
            )

    return _deduplicate_chunks(table_like, max_items=top_k)


def _merge_priority_chunks(primary: List[Dict[str, Any]], secondary: List[Dict[str, Any]], max_items: int = 10) -> List[Dict[str, Any]]:
    merged = primary + secondary
    return _deduplicate_chunks(merged, max_items=max_items)


def _build_table_summary(table_chunks: List[Dict[str, Any]]) -> str:
    if not table_chunks:
        return (
            "I could not find reliably extracted table blocks in this document context. "
            "Tables may be flattened into plain text during OCR/extraction."
        )

    lines = [f"I found {len(table_chunks)} extracted table block(s) in this document context:"]
    for idx, chunk in enumerate(table_chunks, start=1):
        metadata = chunk.get("metadata", {}) or {}
        page = metadata.get("page_label") or metadata.get("page") or metadata.get("page_number") or "unknown"
        preview = " ".join(str(chunk.get("text") or "").split())
        preview = preview[:180]
        lines.append(f"Table {idx} (page {page}): {preview}")

    lines.append("Ask me: 'explain table 1' or 'compare table 1 and 2' for deeper analysis.")
    return "\n".join(lines)


def _fetch_relevant_chunks(query: str, document_id: Optional[str], limit: int = 8) -> List[Dict[str, Any]]:
    from services.document_service import document_service

    vector_hits = document_service.search_documents(
        query=query,
        collection_name=MAIN_COLLECTION,
        limit=limit,
        document_id=document_id,
    )

    ranked = _rank_chunks_for_query(vector_hits, query, top_k=limit)

    if document_id and len(ranked) < min(3, limit):
        # Fallback: semantic search can miss chunks if top candidates are from other docs.
        all_doc_chunks = document_service.get_document_chunks(
            document_id=document_id,
            collection_name=MAIN_COLLECTION,
            limit=900,
        )
        fallback_ranked = _rank_chunks_for_query(all_doc_chunks, query, top_k=max(limit, 8))
        merged = ranked + fallback_ranked
        merged.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        ranked = _deduplicate_chunks(merged, max_items=limit)

    if document_id and not ranked:
        # Last resort for document chat: return a few deterministic chunks so users still get an answer.
        basic_chunks = document_service.get_document_chunks(
            document_id=document_id,
            collection_name=MAIN_COLLECTION,
            limit=limit,
        )
        ranked = _rank_chunks_for_query(basic_chunks, query, top_k=limit)

    return ranked

# Assistant logic is implemented in chatbot.service (separate module).


# ============================================================================
# Document Endpoints
# ============================================================================


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    """
    Upload a document and process in background.

    This avoids request timeouts for large PDFs while still preserving a single upload API.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing file name")

        doc_id = str(uuid.uuid4())
        file_bytes = await file.read()
        file_type = file.content_type or "application/pdf"
        upload_kind = resolve_upload_kind(filename=file.filename, file_type=file_type)

        if upload_kind == "unsupported":
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload a PDF or image file (PNG, JPG, JPEG, WEBP, TIFF, BMP, HEIC).",
            )

        file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
        with open(file_path, "wb") as handle:
            handle.write(file_bytes)

        supabase_result = _upload_to_supabase(
            document_id=doc_id,
            filename=file.filename,
            file_bytes=file_bytes,
            content_type=file_type,
        )

        created_at = datetime.utcnow()
        documents_meta_collection.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "user_id": user_id,
                    "title": file.filename,
                    "file_type": file_type,
                    "status": "processing",
                    "message": "Upload successful. Processing started.",
                    "pages": 0,
                    "tables_count": 0,
                    "chunks_count": 0,
                    "quizzes_generated": 0,
                    "attempts_count": 0,
                    "average_score": 0.0,
                    "local_file_path": str(file_path),
                    "supabase_url": supabase_result.get("url") or None,
                    "supabase_object_path": supabase_result.get("path") or None,
                    "storage_provider": "hybrid" if supabase_result.get("url") else "local",
                    "upload_kind": upload_kind,
                    "processing_error": None,
                    "created_at": created_at,
                    "updated_at": created_at,
                }
            },
            upsert=True,
        )

        processing_thread = threading.Thread(
            target=process_uploaded_document,
            args=(
                doc_id,
                str(file_path),
                user_id,
                file.filename,
                file_type,
                upload_kind,
                MAIN_COLLECTION,
                documents_meta_collection,
            ),
            daemon=True,
        )
        processing_thread.start()

        return DocumentUploadResponse(
            document_id=doc_id,
            title=file.filename,
            status="processing",
            message="Upload successful. Processing started in background.",
            chunks_count=0,
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Upload error: {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/documents")
async def list_documents(user_id: str):
    docs_cursor = list(documents_meta_collection.find({"user_id": user_id}).sort("created_at", DESCENDING))
    docs = [serialize_document_meta(doc) for doc in docs_cursor]

    return {"documents": docs, "total": len(docs)}


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    document = documents_meta_collection.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return serialize_document_meta(document)


@router.get("/documents/{document_id}/file")
async def get_document_file(document_id: str):
    document = documents_meta_collection.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = str(document.get("local_file_path") or "")
    supabase_url = str(document.get("supabase_url") or "")

    if not file_path or not os.path.exists(file_path):
        if supabase_url:
            return RedirectResponse(url=supabase_url, status_code=307)
        raise HTTPException(status_code=404, detail="Local file not found")

    return FileResponse(
        path=file_path,
        media_type=str(document.get("file_type") or "application/pdf"),
        filename=str(document.get("title") or os.path.basename(file_path) or "document.pdf"),
    )


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    document = documents_meta_collection.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    status = str(document.get("status", "processing") or "processing")
    message = str(document.get("message", "Processing") or "Processing")
    chunks_count = int(document.get("chunks_count", 0) or 0)
    processing_error = document.get("processing_error")

    if status == "processing":
        updated_at = safe_datetime(document.get("updated_at")) or safe_datetime(document.get("created_at"))
        if updated_at is not None:
            age_minutes = (datetime.utcnow() - updated_at).total_seconds() / 60.0
            if age_minutes >= PROCESSING_TIMEOUT_MINUTES:
                status = "failed"
                message = (
                    "Processing timed out. The background worker may have restarted. "
                    "Please retry upload."
                )
                processing_error = "processing_timeout"

                documents_meta_collection.update_one(
                    {"_id": document_id},
                    {
                        "$set": {
                            "status": status,
                            "message": message,
                            "processing_error": processing_error,
                            "updated_at": datetime.utcnow(),
                        }
                    },
                )

    return DocumentStatusResponse(
        document_id=document_id,
        status=status,
        message=message,
        chunks_count=chunks_count,
        processing_error=processing_error,
    )


@router.post("/documents/{document_id}/refresh-metadata")
async def refresh_document_metadata(document_id: str):
    """Recompute page/table/chunk stats from stored chunks for existing documents."""
    from services.document_service import document_service

    document = documents_meta_collection.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = document_service.get_document_chunks(
        document_id=document_id,
        collection_name=MAIN_COLLECTION,
        limit=5000,
    )

    page_numbers = set()
    for chunk in chunks:
        metadata = chunk.get("metadata", {}) or {}
        page_value = metadata.get("page_label") or metadata.get("page_number") or metadata.get("page")
        try:
            if page_value is not None:
                page_numbers.add(int(str(page_value).strip()))
        except Exception:
            continue

    recomputed_pages = len(page_numbers) if page_numbers else int(document.get("pages", 0) or 0)
    recomputed_tables = _estimate_table_indicators(chunks)
    recomputed_chunks = len(chunks) if chunks else int(document.get("chunks_count", 0) or 0)

    update_message = f"Metadata refreshed: {recomputed_pages} page(s), {recomputed_tables} table indicator(s)."

    documents_meta_collection.update_one(
        {"_id": document_id},
        {
            "$set": {
                "pages": recomputed_pages,
                "tables_count": recomputed_tables,
                "chunks_count": recomputed_chunks,
                "updated_at": datetime.utcnow(),
                "message": update_message,
            }
        },
    )

    return {
        "document_id": document_id,
        "pages": recomputed_pages,
        "tables_count": recomputed_tables,
        "chunks_count": recomputed_chunks,
        "message": update_message,
    }


@router.get("/documents/{document_id}/quizzes")
async def list_document_quizzes(document_id: str):
    quizzes = list(
        quizzes_collection.find({"document_id": document_id}, {"questions": 0}).sort("created_at", DESCENDING)
    )
    for quiz in quizzes:
        quiz["quiz_id"] = str(quiz.get("_id"))
        quiz.pop("_id", None)
    return {"quizzes": quizzes, "total": len(quizzes)}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    document = documents_meta_collection.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    local_file_path = str(document.get("local_file_path") or "")
    if local_file_path and os.path.exists(local_file_path):
        try:
            os.remove(local_file_path)
        except OSError as exc:
            print(f"⚠️ Failed to remove local file {local_file_path}: {exc}")

    _delete_supabase_object(str(document.get("supabase_object_path") or ""))

    result = documents_meta_collection.delete_one({"_id": document_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}


# ============================================================================
# Quiz Endpoints
# ============================================================================


@router.post("/quizzes/generate", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest):
    try:
        from services.document_service import document_service
        from services.quiz_service import quiz_service

        doc_info = documents_meta_collection.find_one({"_id": request.document_id})
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")

        doc_status = doc_info.get("status", "processing")
        if doc_status != "ready":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Document is still processing. Please wait until status is 'ready' "
                    "before generating a quiz."
                ),
            )

        all_chunks = document_service.get_document_chunks(
            document_id=request.document_id,
            collection_name=MAIN_COLLECTION,
            limit=1200,
        )

        if not all_chunks:
            # Fallback to targeted vector search
            for query in [
                "What is this document about?",
                "What are the key concepts?",
                "Summarize the important points",
                "Definitions and explanations",
            ]:
                all_chunks.extend(
                    document_service.search_documents(
                        query=query,
                        collection_name=MAIN_COLLECTION,
                        limit=20,
                        document_id=request.document_id,
                    )
                )

        unique_chunks: List[Dict[str, Any]] = []
        seen_texts = set()
        for chunk in all_chunks:
            text = (chunk.get("text") or "").strip()
            if not text:
                continue
            key = text[:220]
            if key in seen_texts:
                continue
            seen_texts.add(key)
            unique_chunks.append({"text": text, "metadata": chunk.get("metadata", {}), "score": chunk.get("score", 1.0)})

        context_text = "\n\n".join([chunk["text"] for chunk in unique_chunks[:40]])
        if not context_text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable content found for this document. Please re-upload the file "
                    "or wait for processing to complete."
                ),
            )

        quiz = quiz_service.generate_quiz(
            document_content=context_text,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            question_type=request.question_type,
            max_context_chars=12000,
        )

        owner_id = str(doc_info.get("user_id", "anonymous"))
        quiz_service.save_quiz(quiz, request.document_id, owner_id)

        documents_meta_collection.update_one(
            {"_id": request.document_id},
            {
                "$inc": {"quizzes_generated": 1},
                "$set": {"last_quiz_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            },
        )

        return QuizGenerateResponse(
            quiz_id=str(quiz["_id"]),
            document_id=request.document_id,
            questions=quiz["questions"],
            total_questions=len(quiz["questions"]),
            created_at=quiz["created_at"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Error generating quiz: {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/quizzes/{quiz_id}")
async def get_quiz(quiz_id: str):
    from services.quiz_service import quiz_service

    quiz = quiz_service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz["quiz_id"] = str(quiz.get("_id"))
    quiz.pop("_id", None)
    return quiz


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(quiz_id: str, request: QuizSubmitRequest):
    try:
        from services.quiz_service import quiz_service

        quiz = quiz_service.get_quiz(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        result = quiz_service.grade_quiz(quiz_id, request.answers)
        user_id = request.user_id or quiz.get("user_id", "anonymous")

        attempt_id = str(uuid.uuid4())
        attempt_record = {
            "_id": attempt_id,
            "attempt_id": attempt_id,
            "quiz_id": quiz_id,
            "document_id": quiz.get("document_id"),
            "user_id": user_id,
            "score": result["score"],
            "correct_count": result["correct_count"],
            "total_questions": result["total_questions"],
            "percentage": result["percentage"],
            "weak_areas": result.get("weak_areas", []),
            "recommendations": result.get("recommendations", []),
            "topic_performance": result.get("topic_performance", {}),
            "graded_questions": result.get("graded_questions", []),
            "completed_at": datetime.utcnow(),
        }

        attempts_collection.insert_one(attempt_record)

        document_id = attempt_record.get("document_id")
        if document_id:
            _refresh_document_attempt_stats(str(document_id))

        return QuizResult(
            quiz_id=quiz_id,
            score=float(result["score"]),
            correct_count=int(result["correct_count"]),
            total_questions=int(result["total_questions"]),
            weak_areas=result.get("weak_areas", []),
            recommendations=result.get("recommendations", []),
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Error submitting quiz: {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/quizzes/{quiz_id}/results/{attempt_id}")
async def get_quiz_results(quiz_id: str, attempt_id: str):
    attempt = attempts_collection.find_one({"_id": attempt_id, "quiz_id": quiz_id})
    if not attempt:
        raise HTTPException(status_code=404, detail="Results not found")

    attempt["attempt_id"] = str(attempt.get("_id"))
    attempt.pop("_id", None)
    return attempt


@router.get("/attempts")
async def list_attempts(user_id: str, document_id: Optional[str] = None):
    query: Dict[str, Any] = {"user_id": user_id}
    if document_id:
        query["document_id"] = document_id

    attempts = list(attempts_collection.find(query).sort("completed_at", DESCENDING).limit(100))
    document_cache: Dict[str, str] = {}

    for attempt in attempts:
        attempt["attempt_id"] = str(attempt.get("_id"))
        attempt.pop("_id", None)

        doc_id = attempt.get("document_id")
        if doc_id:
            if doc_id not in document_cache:
                doc_meta = documents_meta_collection.find_one({"_id": doc_id}, {"title": 1})
                document_cache[doc_id] = doc_meta.get("title", "Untitled") if doc_meta else "Untitled"
            attempt["document_title"] = document_cache[doc_id]

    return {"attempts": attempts, "total": len(attempts)}


@router.get("/documents/{document_id}/attempts")
async def list_document_attempts(document_id: str, user_id: Optional[str] = None):
    query: Dict[str, Any] = {"document_id": document_id}
    if user_id:
        query["user_id"] = user_id

    attempts = list(attempts_collection.find(query).sort("completed_at", DESCENDING).limit(100))
    for attempt in attempts:
        attempt["attempt_id"] = str(attempt.get("_id"))
        attempt.pop("_id", None)

    return {"attempts": attempts, "total": len(attempts)}


# ============================================================================
# Progress Endpoints
# ============================================================================


@router.get("/progress")
async def get_progress(user_id: str):
    user_attempts = list(attempts_collection.find({"user_id": user_id}).sort("completed_at", DESCENDING))

    if not user_attempts:
        return {
            "total_quizzes": 0,
            "average_score": 0.0,
            "quizzes_completed": 0,
            "weak_areas": [],
            "recent_activity": [],
            "improvement_trend": "no_data",
        }

    avg_score = sum(float(a.get("score", 0.0)) for a in user_attempts) / len(user_attempts)
    weak_areas = _extract_weak_areas(user_attempts)
    trend = _determine_trend(user_attempts)

    recent_activity = []
    for attempt in user_attempts[:8]:
        recent_activity.append(
            {
                "attempt_id": str(attempt.get("_id")),
                "quiz_id": attempt.get("quiz_id"),
                "document_id": attempt.get("document_id"),
                "score": attempt.get("score", 0.0),
                "percentage": attempt.get("percentage", "0%"),
                "completed_at": attempt.get("completed_at"),
            }
        )

    return {
        "total_quizzes": len(user_attempts),
        "average_score": avg_score,
        "quizzes_completed": len(user_attempts),
        "weak_areas": weak_areas,
        "recent_activity": recent_activity,
        "improvement_trend": trend,
    }


@router.get("/progress/weak-areas")
async def get_weak_areas(user_id: str):
    user_attempts = list(attempts_collection.find({"user_id": user_id}).sort("completed_at", DESCENDING).limit(200))
    return _extract_weak_areas(user_attempts)


@router.get("/progress/notifications")
async def get_review_notifications(user_id: str):
    user_attempts = list(attempts_collection.find({"user_id": user_id}).sort("completed_at", DESCENDING).limit(200))
    notifications = _build_review_notifications(user_id, user_attempts)
    return {"notifications": notifications, "total": len(notifications)}


# ============================================================================
# RAG Chat Endpoints
# ============================================================================


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        from services.quiz_service import quiz_service
        from services.vision_service import vision_service

        doc_info: Optional[Dict[str, Any]] = None
        if request.document_id:
            doc_info = documents_meta_collection.find_one({"_id": request.document_id})
            if not doc_info:
                raise HTTPException(status_code=404, detail="Document not found")

            doc_status = str(doc_info.get("status", "processing") or "processing")
            if doc_status != "ready":
                progress_message = str(doc_info.get("message") or "Document is still processing")
                chunks_so_far = int(doc_info.get("chunks_count", 0) or 0)
                pages_so_far = int(doc_info.get("pages", 0) or 0)
                return ChatResponse(
                    response=(
                        f"This document is still processing ({doc_status}). {progress_message}. "
                        f"Detected so far: {pages_so_far} page(s), {chunks_so_far} chunk(s). "
                        "Please wait until status becomes ready for complete answers."
                    ),
                    sources=[],
                    confidence=0.0,
                )

        # Route image queries to vision model first
        upload_kind = str((doc_info or {}).get("upload_kind") or "").lower()
        if request.document_id and upload_kind == "image":
            file_path = str(doc_info.get("local_file_path") or "")
            if file_path and os.path.exists(file_path):
                try:
                    vision_result = await asyncio.wait_for(
                        asyncio.to_thread(
                            vision_service.analyze_image,
                            file_path,
                            request.message or None,
                            512,
                        ),
                        timeout=35.0,
                    )
                    if vision_result.get("success"):
                        return ChatResponse(
                            response=vision_result.get("content", ""),
                            sources=[{"text": f"Image analyzed with {vision_result.get('model', 'unknown')} vision model", "score": 0.95}],
                            confidence=0.95,
                        )
                except asyncio.TimeoutError:
                    print(f"⚠️  Vision model timeout for document {request.document_id}. Falling back to OCR.")
                except Exception as e:
                    print(f"⚠️  Vision analysis failed: {e}. Falling back to OCR.")

        results = await asyncio.to_thread(
            _fetch_relevant_chunks,
            request.message,
            request.document_id,
            10,
        )

        table_query = _is_table_query(request.message)
        table_chunks: List[Dict[str, Any]] = []
        if request.document_id and table_query:
            table_chunks = await asyncio.to_thread(_fetch_table_chunks_for_document, request.document_id, 2000, 10)
            if table_chunks:
                results = _merge_priority_chunks(table_chunks, results, max_items=10)

        if not results:
            return ChatResponse(
                response="I couldn't find relevant information about that in your document.",
                sources=[],
                confidence=0.0,
            )

        context = _build_context_from_chunks(results, max_chars=12000)
        if len(context.strip()) < 40:
            answer = "I don't have enough information about that in the document."
        else:
            try:
                answer = await asyncio.wait_for(
                    asyncio.to_thread(quiz_service._generate_answer, request.message, context),
                    timeout=45.0,
                )
            except asyncio.TimeoutError:
                answer = _build_grounded_timeout_fallback(results)

        if request.document_id and upload_kind == "image" and _is_generic_image_query(request.message):
            answer = _build_image_ocr_summary(results)

        if request.document_id and doc_info:
            pages_value = int(doc_info.get("pages", 0) or 0)
            tables_value = int(doc_info.get("tables_count", 0) or 0)
            q = (request.message or "").lower()

            if any(token in q for token in ["how many pages", "total pages", "pages in", "number of pages"]):
                answer = (
                    f"This uploaded document currently has {pages_value} page(s) in processed metadata. "
                    "If you need, I can also summarize page-by-page sections."
                )
            elif _is_table_count_query(q):
                estimated_tables = tables_value
                if estimated_tables <= 0:
                    try:
                        from services.document_service import document_service

                        all_doc_chunks = document_service.get_document_chunks(
                            document_id=request.document_id,
                            collection_name=MAIN_COLLECTION,
                            limit=2200,
                        )
                        estimated_tables = _estimate_table_indicators(all_doc_chunks)
                    except Exception:
                        estimated_tables = 0

                if estimated_tables <= 0:
                    answer = (
                        "I cannot reliably detect table structures in this extraction output yet. "
                        "The document may still contain tables, but they were flattened into plain text by the current pipeline."
                    )
                else:
                    answer = (
                        f"I detected approximately {estimated_tables} table indicator(s) in extracted content. "
                        "This is an estimate and can be lower than the visual table count in the original PDF."
                    )
            elif _is_table_explain_query(q):
                answer = _build_table_summary(table_chunks)

        sources = [
            {
                "text": (r.get("text", "")[:220]).strip(),
                "score": float(r.get("score", 0.0)),
            }
            for r in results
        ]

        confidence = _compute_confidence(results)
        if request.document_id and confidence < 0.2:
            confidence = 0.2

        if request.user_id:
            chat_history_collection.insert_one(
                {
                    "_id": str(uuid.uuid4()),
                    "user_id": request.user_id,
                    "document_id": request.document_id,
                    "question": request.message,
                    "response": answer,
                    "sources": sources,
                    "confidence": confidence,
                    "created_at": datetime.utcnow(),
                }
            )

        return ChatResponse(response=answer, sources=sources, confidence=confidence)

    except Exception as exc:
        print(f"❌ Chat error: {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/chat/history")
async def chat_history(user_id: str, document_id: Optional[str] = None):
    query: Dict[str, Any] = {"user_id": user_id}
    if document_id:
        query["document_id"] = document_id

    items = list(chat_history_collection.find(query).sort("created_at", DESCENDING).limit(200))
    for item in items:
        item["chat_id"] = str(item.get("_id"))
        item.pop("_id", None)

    return {"messages": items, "total": len(items)}


@router.post("/vision/analyze", response_model=VisionResponse)
async def vision_analyze(request: ChatRequest):
    """
    Analyze an image using vision model (Claude or local BLIP).
    Requires document_id pointing to an image upload.
    """
    try:
        if not request.document_id:
            raise HTTPException(status_code=400, detail="document_id is required for vision analysis")

        doc_info = documents_meta_collection.find_one({"_id": request.document_id})
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")

        upload_kind = str((doc_info or {}).get("upload_kind") or "").lower()
        if upload_kind != "image":
            raise HTTPException(status_code=400, detail="Document must be an image upload")

        file_path = str(doc_info.get("local_file_path") or "")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image file not found on disk")

        from services.vision_service import vision_service

        result = await asyncio.to_thread(
            vision_service.analyze_image,
            file_path,
            request.message or None,
            512,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Vision analysis failed"))

        return VisionResponse(
            content=result.get("content", ""),
            model=result.get("model", "none"),
            success=True,
            usage=result.get("usage"),
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Vision analysis error: {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# Personal Assistant and Study Plan Endpoints
# ============================================================================


@router.post("/assistant/chat", response_model=ChatResponse)
async def assistant_chat(request: ChatRequest):
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        payload = await asyncio.to_thread(
            chatbot_service.chat,
            request.user_id,
            request.message,
            request.document_id,
        )

        return ChatResponse(
            response=payload.get("response", ""),
            sources=payload.get("sources", []),
            confidence=float(payload.get("confidence", 0.0) or 0.0),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        print(f"❌ Assistant chat error: {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/assistant/history")
async def assistant_history(user_id: str, document_id: Optional[str] = None):
    items = chatbot_service.get_history(user_id=user_id, document_id=document_id, limit=300)
    return {"messages": items, "total": len(items)}


@router.post("/chatbot/message")
async def send_external_chat_message(request: ChatbotProxyRequest):
    payload = chatbot_service.chat(
        user_id=request.user_id,
        message=request.message,
        document_id=request.document_id,
    )
    return {"provider": "local_assistant", **payload}


@router.get("/chatbot/history")
async def get_external_chat_history(user_id: str):
    items = chatbot_service.get_history(user_id=user_id, document_id=None, limit=300)
    return {"provider": "local_assistant", "messages": items, "total": len(items)}


@router.post("/study-plans")
async def create_study_plan(request: StudyPlanCreateRequest):
    try:
        item = chatbot_service.create_study_plan(
            user_id=request.user_id,
            title=request.title,
            target_date=request.target_date,
            document_id=request.document_id,
            document_title=request.document_title,
            notes=request.notes,
            reminder_days_before=request.reminder_days_before,
            user_email=request.user_email,
        )
        return item
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        print(f"❌ Study plan create error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/study-plans")
async def list_study_plans(user_id: str):
    items = chatbot_service.list_study_plans(user_id=user_id)
    return {"plans": items, "total": len(items)}


@router.get("/study-plans/notifications")
async def list_study_plan_notifications(user_id: str):
    items = chatbot_service.get_study_plan_notifications(user_id=user_id)
    return {"notifications": items, "total": len(items)}


@router.post("/study-plans/generate")
async def generate_personalized_study_plan(request: StudyPlanGenerateRequest):
    """Generate personalized study schedules for existing pending plans using AI"""
    try:
        if not request.plan_ids:
            raise ValueError("Please select at least one not-done plan")
        if not request.available_days:
            raise ValueError("Please select at least one available day")
        
        result = chatbot_service.generate_personalized_study_plan(
            user_id=request.user_id,
            plan_ids=request.plan_ids,
            available_days=request.available_days,
            study_days=request.study_days,
            hours_per_day=request.hours_per_day,
            preferred_start_time=request.preferred_start_time,
            exam_date=request.exam_date,
            learning_style=request.learning_style,
            difficulty_level=request.difficulty_level,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        print(f"❌ Study plan generation error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/study-plans/{plan_id}")
async def update_study_plan(plan_id: str, request: StudyPlanStatusRequest):
    try:
        item = chatbot_service.update_study_plan_status(
            user_id=request.user_id,
            plan_id=plan_id,
            status=request.status,
        )
        return item
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        print(f"❌ Study plan update error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/study-plans/{plan_id}")
async def delete_study_plan(plan_id: str, user_id: str):
    deleted = chatbot_service.delete_study_plan(user_id=user_id, plan_id=plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return {"status": "deleted"}


# ============================================================================
# Reminder Endpoints
# ============================================================================


@router.post("/reminders")
async def create_reminder(topic: str = Form(...), user_id: str = Form(...), review_after_hours: int = Form(24)):
    reminder_id = str(uuid.uuid4())
    scheduled_for = datetime.utcnow()

    reminders_collection.insert_one(
        {
            "_id": reminder_id,
            "user_id": user_id,
            "topic": topic,
            "review_after_hours": review_after_hours,
            "scheduled_for": scheduled_for,
            "status": "pending",
            "created_at": datetime.utcnow(),
        }
    )

    return {"reminder_id": reminder_id, "topic": topic, "scheduled_for": scheduled_for, "status": "pending"}


@router.get("/reminders")
async def list_reminders(user_id: str):
    reminders = list(reminders_collection.find({"user_id": user_id}).sort("created_at", DESCENDING).limit(100))
    for reminder in reminders:
        reminder["reminder_id"] = str(reminder.get("_id"))
        reminder.pop("_id", None)
    return {"reminders": reminders, "total": len(reminders)}


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    result = reminders_collection.delete_one({"_id": reminder_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "deleted"}
