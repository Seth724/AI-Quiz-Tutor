from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf"}


def safe_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    return None


def resolve_upload_kind(filename: str, file_type: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    normalized_type = (file_type or "").lower()

    if normalized_type.startswith("image/") or suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"

    if normalized_type == "application/pdf" or suffix in SUPPORTED_DOCUMENT_EXTENSIONS:
        return "pdf"

    return "unsupported"


def serialize_document_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "document_id": str(meta.get("_id", "")),
        "title": meta.get("title", "Untitled"),
        "file_type": meta.get("file_type", "application/pdf"),
        "supabase_url": str(meta.get("supabase_url") or "") or None,
        "pages": int(meta.get("pages", 0) or 0),
        "tables_count": int(meta.get("tables_count", 0) or 0),
        "created_at": safe_datetime(meta.get("created_at")) or datetime.utcnow(),
        "updated_at": safe_datetime(meta.get("updated_at")) or safe_datetime(meta.get("created_at")) or datetime.utcnow(),
        "status": meta.get("status", "processing"),
        "message": str(meta.get("message") or ""),
        "processing_error": str(meta.get("processing_error") or "") or None,
        "chunks_count": int(meta.get("chunks_count", 0) or 0),
        "quizzes_generated": int(meta.get("quizzes_generated", 0) or 0),
        "attempts_count": int(meta.get("attempts_count", 0) or 0),
        "average_score": float(meta.get("average_score", 0.0) or 0.0),
    }
