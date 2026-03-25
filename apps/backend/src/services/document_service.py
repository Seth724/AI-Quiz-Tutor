"""
Document Service

Uses EXACT code from tutorial-3 working files:
- pdf_rag_simple.py (simple PDF reader)
- pdf_rag_complete.py (production version with features)
- simple_ocr.py (OCR for images)
"""

import os
import sys
import json
import re
import importlib
import threading
import time
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pymongo import MongoClient
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.huggingface_api import HuggingFaceInferenceAPIEmbedding
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
from llama_index.readers.file import PDFReader
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import easyocr

from config import settings


class ProcessingMode(Enum):
    """PDF processing strategy selection"""
    SIMPLE_TEXT = "simple_text"  # Text-heavy PDFs, embedded text
    OCR_HYBRID = "ocr_hybrid"  # Mixed text/image PDFs
    OCR_FULL = "ocr_full"  # Scanned/image-only PDFs
    DOCLING_BATCH = "docling_batch"  # Complex PDFs with tables, many images


class DocumentService:
    """
    Document processing service
    
    Uses working code from tutorial-3-mongodb:
    - pdf_rag_simple.py
    - pdf_rag_complete.py
    - simple_ocr.py
    """
    
    def __init__(self):
        """Initialize document service"""
        # Keep HuggingFace cache paths optional and environment-driven.
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        for env_name in ("HF_HOME", "HF_HUB_CACHE", "SENTENCE_TRANSFORMERS_HOME"):
            configured_path = (os.getenv(env_name) or "").strip()
            if configured_path:
                os.makedirs(configured_path, exist_ok=True)
        
        # MongoDB connection
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.db = self.mongo_client[settings.MONGODB_DATABASE]
        self.collection = self.db["documents"]
        
        # Embedding model (from tutorial-3)
        self.embed_model = HuggingFaceInferenceAPIEmbedding(
            api_key=settings.HF_TOKEN,
            model_name=settings.EMBEDDING_MODEL
        )
        
        # Set in Settings (from tutorial-3)
        Settings.embed_model = self.embed_model

        self.cv2 = None
        try:
            self.cv2 = importlib.import_module("cv2")
            print("✅ OpenCV preprocessing enabled")
        except Exception:
            print("⚠️ OpenCV not available. Using PIL preprocessing fallback.")

        try:
            pillow_heif = importlib.import_module("pillow_heif")
            pillow_heif.register_heif_opener()
            print("✅ HEIF image support enabled")
        except Exception:
            print("⚠️ HEIF support not available. Install pillow-heif for iPhone image uploads.")
        
        # OCR reader is lazily initialized to avoid startup OOM on small instances.
        self.ocr_reader = None
        self._ocr_initialized = False
        # EasyOCR is not thread-safe in this app's shared singleton usage.
        self._ocr_lock = threading.Lock()
        self._ocr_init_lock = threading.Lock()

    def _get_ocr_reader(self):
        """Create EasyOCR reader on first use, not during API startup."""
        if self._ocr_initialized and self.ocr_reader is not None:
            return self.ocr_reader

        with self._ocr_init_lock:
            if self._ocr_initialized and self.ocr_reader is not None:
                return self.ocr_reader

            print("ℹ️ Initializing EasyOCR model on demand...")
            self.ocr_reader = easyocr.Reader(["en"], gpu=False)
            self._ocr_initialized = True
            return self.ocr_reader

    def _readtext_safe(self, image_array: np.ndarray):
        """Run OCR in a critical section to avoid deadlocks across concurrent uploads."""
        reader = self._get_ocr_reader()
        with self._ocr_lock:
            return reader.readtext(image_array)

    def detect_processing_mode(self, file_path: str, sample_pages: int = 3) -> ProcessingMode:
        """Detect PDF characteristics to select optimal processing mode."""
        forced_mode = str(getattr(settings, "FORCE_PROCESSING_MODE", "") or "").strip().lower()
        if forced_mode:
            mode_map = {
                ProcessingMode.SIMPLE_TEXT.value: ProcessingMode.SIMPLE_TEXT,
                ProcessingMode.OCR_HYBRID.value: ProcessingMode.OCR_HYBRID,
                ProcessingMode.OCR_FULL.value: ProcessingMode.OCR_FULL,
                ProcessingMode.DOCLING_BATCH.value: ProcessingMode.DOCLING_BATCH,
            }
            selected = mode_map.get(forced_mode)
            if selected is not None:
                print(f"📌 Forced processing mode: {selected.value}")
                return selected
            print(f"⚠️  Unknown FORCE_PROCESSING_MODE='{forced_mode}', using auto detection")

        try:
            import fitz
            pdf = fitz.open(file_path)
            total_pages = len(pdf)
            text_chars, image_count = 0, 0
            
            for page_idx in range(min(sample_pages, total_pages)):
                page = pdf.load_page(page_idx)
                text_chars += len(page.get_text())
                image_count += len(page.get_images())
            pdf.close()
            
            avg_text_per_page = text_chars / max(sample_pages, 1)
            avg_images_per_page = image_count / max(sample_pages, 1)
            
            print(f"📊 PDF Analysis: {total_pages}p, {avg_text_per_page:.0f}c/p, {avg_images_per_page:.1f}i/p")
            
            # Decision tree: prioritize page count for large documents
            if total_pages > 200:
                # Large document: use DOCLING_BATCH for better structure extraction
                mode = ProcessingMode.DOCLING_BATCH
                print(f"  → {mode.value}: Large document (200+ pages)")
            elif avg_text_per_page < 300 and total_pages <= 80:
                # Text-sparse pages often hide tabular structure in layout; prefer Docling parsing.
                mode = ProcessingMode.DOCLING_BATCH
                print(f"  → {mode.value}: Text-sparse layout likely containing structured blocks")
            elif avg_images_per_page >= 1.5 and avg_text_per_page < 1500:
                # Image/table-rich layouts benefit from Docling's structural extraction.
                mode = ProcessingMode.DOCLING_BATCH
                print(f"  → {mode.value}: Table/image-rich layout")
            elif avg_text_per_page < 100 and total_pages < 100:
                # Small, text-sparse → likely scanned/image PDF
                mode = ProcessingMode.OCR_FULL
                print(f"  → {mode.value}: Scanned/image-heavy")
            elif total_pages > 50:
                # 50-200 pages with mixed content
                mode = ProcessingMode.OCR_HYBRID
                print(f"  → {mode.value}: Large document, mixed content")
            else:
                # Standard small text-heavy document
                mode = ProcessingMode.SIMPLE_TEXT
                print(f"  → {mode.value}: Standard text-heavy")
            
            return mode
        except Exception as e:
            print(f"⚠️  Detection error: {e}, using SIMPLE_TEXT")
            return ProcessingMode.SIMPLE_TEXT

    @staticmethod
    def _normalize_text(value: Optional[str]) -> str:
        """Return normalized text or empty string."""
        return (value or "").strip()

    def _extract_text_from_node_content(self, node_content: str) -> str:
        """Extract text fallback from LlamaIndex _node_content payload."""
        if not node_content:
            return ""

        try:
            payload = json.loads(node_content)
            return self._normalize_text(payload.get("text", ""))
        except Exception:
            return ""

    def extract_text_from_record(self, record: Dict[str, Any]) -> str:
        """Extract text from MongoDB chunk record using all known fallback fields."""
        text = self._normalize_text(record.get("text", ""))
        if text:
            return text

        metadata = record.get("metadata", {}) or {}
        return self._extract_text_from_node_content(metadata.get("_node_content", ""))

    @staticmethod
    def _document_match_filter(document_id: str) -> Dict[str, Any]:
        """Build Mongo match filter for uploaded document id across known metadata variants."""
        return {
            "$or": [
                {"metadata.upload_id": document_id},
                {"metadata.document_id": document_id},
                {"metadata.filename": {"$regex": f"^{re.escape(document_id)}_"}},
                {"metadata.file_name": {"$regex": f"^{re.escape(document_id)}_"}},
                {"metadata.source": {"$regex": f"{re.escape(document_id)}_"}},
            ]
        }

    def _ocr_pdf_pages(
        self,
        file_path: str,
        page_numbers: Optional[List[int]] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Document]:
        """Extract PDF page text with EasyOCR using rendered page images."""
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF (fitz) is required for PDF OCR fallback") from exc

        pdf = fitz.open(file_path)
        target_pages = page_numbers if page_numbers is not None else list(range(len(pdf)))
        documents: List[Document] = []

        try:
            total_target_pages = len(target_pages)
            for page_position, page_idx in enumerate(target_pages, start=1):
                if progress_callback:
                    progress_callback(f"OCR page {page_position}/{total_target_pages}")

                page = pdf.load_page(page_idx)
                pix = page.get_pixmap(dpi=220)
                mode = "RGBA" if pix.alpha else "RGB"
                image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)

                prepared_image = self._preprocess_image_for_ocr(image)

                results = self._readtext_safe(np.array(prepared_image))
                strict_lines = [text.strip() for _, text, conf in results if text and float(conf or 0.0) >= 0.15]
                if strict_lines:
                    page_text = "\n".join(strict_lines).strip()
                else:
                    # Fallback for noisy scans where confidence scores are pessimistic.
                    relaxed_lines = [text.strip() for _, text, _ in results if text and text.strip()]
                    page_text = "\n".join(relaxed_lines).strip()

                if page_text:
                    documents.append(
                        Document(
                            text=page_text,
                            metadata={
                                "page_label": str(page_idx + 1),
                                "source": file_path,
                                "extraction_method": "easyocr_pdf_fallback",
                            },
                        )
                    )
        finally:
            pdf.close()

        return documents

    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess scans for OCR: auto-orientation, denoise, and contrast enhancement."""
        working = ImageOps.exif_transpose(image).convert("RGB")

        # Downscale very large photos before OCR to prevent extreme CPU stalls.
        max_allowed_dim = 2400
        current_max_dim = max(working.width, working.height)
        if current_max_dim > max_allowed_dim:
            downscale = max_allowed_dim / current_max_dim
            resized_down = (
                max(1, int(working.width * downscale)),
                max(1, int(working.height * downscale)),
            )
            working = working.resize(resized_down, Image.LANCZOS)

        max_dim = max(working.width, working.height)
        if max_dim < 1400:
            scale = 1400 / max(max_dim, 1)
            resized = (
                max(1, int(working.width * scale)),
                max(1, int(working.height * scale)),
            )
            working = working.resize(resized, Image.LANCZOS)

        if self.cv2 is not None:
            cv2 = self.cv2
            np_img = np.array(working)
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8))
            contrasted = clahe.apply(denoised)
            blurred = cv2.GaussianBlur(contrasted, (0, 0), 1.1)
            sharpened = cv2.addWeighted(contrasted, 1.5, blurred, -0.5, 0)
            return Image.fromarray(sharpened)

        gray = ImageOps.grayscale(working)
        denoised = gray.filter(ImageFilter.MedianFilter(size=3))
        contrasted = ImageEnhance.Contrast(denoised).enhance(1.85)
        sharpened = contrasted.filter(ImageFilter.UnsharpMask(radius=1.2, percent=180, threshold=2))
        return sharpened

    def _ocr_image_candidate(self, image: Image.Image) -> Dict[str, Any]:
        """Run OCR on a preprocessed image and return text quality metrics."""
        result = self._readtext_safe(np.array(image))

        lines: List[str] = []
        confidence_total = 0.0
        valid_lines = 0

        for _, text, conf in result:
            cleaned = (text or "").strip()
            confidence = float(conf or 0.0)
            if not cleaned or confidence < 0.2:
                continue

            lines.append(cleaned)
            confidence_total += confidence
            valid_lines += 1

        merged_text = " ".join(lines).strip()
        avg_confidence = confidence_total / max(valid_lines, 1)
        score = (len(merged_text) * 0.72) + (avg_confidence * 150.0)

        return {
            "text": merged_text,
            "avg_confidence": avg_confidence,
            "line_count": valid_lines,
            "score": score,
        }

    def process_pdf_docling_batch(
        self,
        file_path: str,
        max_pages: Optional[int] = None,
        batch_size: int = 5,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Document]:
        """Process complex PDFs with Docling batch processing."""
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode, TableStructureOptions
            from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
            from docling_core.types.doc import TextItem, TableItem, SectionHeaderItem
            import fitz

            print("🔄 Using Docling batch processing...")
            
            total_pages = len(fitz.open(file_path))
            max_pages = max_pages or total_pages
            
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False
            pipeline_options.do_table_structure = True
            pipeline_options.table_structure_options = TableStructureOptions(do_cell_matching=False, mode=TableFormerMode.FAST)
            pipeline_options.document_timeout = 300.0
            pipeline_options.accelerator_options = AcceleratorOptions(num_threads=2, device=AcceleratorDevice.CPU)

            batch_timeout_seconds = max(30, int(getattr(settings, "DOCLING_BATCH_TIMEOUT_SECONDS", 180) or 180))
            heartbeat_seconds = max(5, int(getattr(settings, "DOCLING_PROGRESS_HEARTBEAT_SECONDS", 15) or 15))
            
            converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)})
            all_documents: List[Document] = []

            for batch_start in range(0, min(max_pages, total_pages), batch_size):
                batch_end = min(batch_start + batch_size, total_pages)
                if progress_callback:
                    progress_callback(f"Docling batch pages {batch_start + 1}-{batch_end}/{total_pages}")
                print(f"  [{batch_start+1}-{batch_end}/{total_pages}]", end="")

                try:
                    executor = ThreadPoolExecutor(max_workers=1)
                    future = executor.submit(converter.convert, file_path, page_range=(batch_start + 1, batch_end))
                    started_at = time.monotonic()
                    result = None

                    try:
                        while True:
                            elapsed = time.monotonic() - started_at
                            remaining = batch_timeout_seconds - elapsed
                            if remaining <= 0:
                                future.cancel()
                                timeout_msg = (
                                    f"Docling timeout on pages {batch_start + 1}-{batch_end}. "
                                    "Switching to OCR fallback"
                                )
                                print(" ✗ timeout")
                                print(f"⚠️  {timeout_msg}")
                                if progress_callback:
                                    progress_callback(timeout_msg)
                                return []

                            try:
                                result = future.result(timeout=min(heartbeat_seconds, remaining))
                                break
                            except FutureTimeoutError:
                                if progress_callback:
                                    progress_callback(
                                        f"Docling working on pages {batch_start + 1}-{batch_end}/{total_pages} "
                                        f"({int(elapsed)}s elapsed)"
                                    )
                                continue
                    finally:
                        executor.shutdown(wait=False, cancel_futures=True)

                    if not result or not result.document:
                        print(" (empty)")
                        continue

                    batch_docs = []
                    for element, level in result.document.iterate_items():
                        try:
                            page_no = element.prov[0].page_no if element.prov else batch_start + 1
                            if isinstance(element, SectionHeaderItem):
                                batch_docs.append(Document(text=element.text, metadata={"type": "header", "page": page_no, "level": level}))
                            elif isinstance(element, TextItem) and len((element.text or "").strip()) > 50:
                                batch_docs.append(Document(text=element.text, metadata={"type": "text", "page": page_no}))
                            elif isinstance(element, TableItem):
                                try:
                                    df = element.export_to_dataframe(doc=result.document)
                                    batch_docs.append(Document(text=f"TABLE:\n{df.to_markdown()}", metadata={"type": "table", "page": page_no}))
                                except:
                                    pass
                        except:
                            continue
                    
                    all_documents.extend(batch_docs)
                    print(f" ✓ {len(batch_docs)}")
                except Exception as e:
                    print(f" ✗ {str(e)[:40]}")

            print(f"✅ Docling: {len(all_documents)} docs from {total_pages}p")
            return all_documents
        except ImportError:
            print("⚠️  Docling unavailable, fallback to simple PDF")
            return self.process_pdf_simple(file_path, use_hybrid=False)
        except Exception as e:
            print(f"❌ Docling error: {e}, fallback")
            return self.process_pdf_simple(file_path, use_hybrid=False)

    def process_pdf_hybrid(self, file_path: str, progress_callback: Optional[Callable[[str], None]] = None) -> List[Document]:
        """Smart processor selecting best strategy based on PDF characteristics."""
        mode = self.detect_processing_mode(file_path)
        
        if mode == ProcessingMode.OCR_FULL:
            if progress_callback:
                progress_callback("Running full-page OCR (scanned PDF)")
            return self._ocr_pdf_pages(file_path, progress_callback=progress_callback)
        elif mode == ProcessingMode.DOCLING_BATCH:
            if progress_callback:
                progress_callback("Running Docling batch extraction")
            documents = self.process_pdf_docling_batch(file_path, progress_callback=progress_callback)
            if documents and any(self._normalize_text(d.text) for d in documents):
                return documents

            print("⚠️  Docling returned no readable chunks. Falling back to full-page OCR...")
            if progress_callback:
                progress_callback("Docling returned no readable text. Running full-page OCR fallback")

            ocr_documents = self._ocr_pdf_pages(file_path, progress_callback=progress_callback)
            if ocr_documents and any(self._normalize_text(d.text) for d in ocr_documents):
                return ocr_documents

            print("⚠️  OCR fallback also returned no readable text. Trying simple reader fallback...")
            if progress_callback:
                progress_callback("OCR fallback empty. Trying simple reader fallback")

            return self.process_pdf_simple(file_path, use_hybrid=False, progress_callback=progress_callback)
        elif mode == ProcessingMode.OCR_HYBRID:
            if progress_callback:
                progress_callback("Running hybrid extraction")
            documents = self.process_pdf_simple(file_path, use_hybrid=False, progress_callback=progress_callback)
            if documents and any(self._normalize_text(d.text) for d in documents):
                return documents
            return self._ocr_pdf_pages(file_path, progress_callback=progress_callback)
        else:
            return self.process_pdf_simple(file_path, use_hybrid=False, progress_callback=progress_callback)

    def process_pdf_simple(
        self,
        file_path: str,
        use_hybrid: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Document]:
        """
        Process PDF using simple PDF reader (or hybrid if needed)
        From: tutorial-3-mongodb/pdf_rag_simple.py
        
        Best for: Text-heavy PDFs without complex layouts
        """
        try:
            print(f"Processing PDF: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF not found: {file_path}")
            
            # Try hybrid approach first for better user experience.
            # Disable this branch when called from hybrid mode to avoid recursion.
            if use_hybrid:
                try:
                    documents = self.process_pdf_hybrid(file_path, progress_callback=progress_callback)
                    if documents and any(self._normalize_text(d.text) for d in documents):
                        return documents
                except Exception as e:
                    print(f"⚠️  Hybrid processing failed: {e}, trying basic PDF reader")
            
            # Fallback to simple PDF reader
            try:
                reader = PDFReader()
                documents = reader.load_data(Path(file_path))
                
                print(f"✅ Loaded {len(documents)} pages from PDF")
                
                # Detect scanned PDFs and fallback to OCR
                empty_page_indexes = [
                    idx for idx, document in enumerate(documents)
                    if not self._normalize_text(document.text)
                ]
                
                if documents and len(empty_page_indexes) == len(documents):
                    print("⚠️  No embedded PDF text detected. Running OCR fallback on all pages...")
                    documents = self._ocr_pdf_pages(file_path, progress_callback=progress_callback)
                elif empty_page_indexes:
                    print(f"⚠️  {len(empty_page_indexes)} page(s) had no embedded text. Running OCR fallback...")
                    ocr_documents = self._ocr_pdf_pages(
                        file_path,
                        page_numbers=empty_page_indexes,
                        progress_callback=progress_callback,
                    )
                    ocr_by_page = {
                        doc.metadata.get("page_label", ""): doc
                        for doc in ocr_documents
                    }
                    
                    merged_documents: List[Document] = []
                    for idx, document in enumerate(documents):
                        if self._normalize_text(document.text):
                            merged_documents.append(document)
                            continue
                        
                        replacement = ocr_by_page.get(str(idx + 1))
                        if replacement is not None:
                            merged_documents.append(replacement)
                    
                    documents = merged_documents
                
                documents = [doc for doc in documents if self._normalize_text(doc.text)]
                if not documents:
                    raise ValueError("No extractable text found in this PDF")
                
                print(f"✅ Extracted text chunks: {len(documents)}")
                return documents
                
            except Exception as pdf_error:
                # Handle encrypted PDFs, corrupted PDFs by falling back to OCR
                error_str = str(pdf_error).lower()
                if "decrypted" in error_str or "encrypted" in error_str or "corrupted" in error_str:
                    print(f"⚠️  PDF is encrypted/protected/corrupted. Attempting OCR fallback: {pdf_error}")
                    try:
                        documents = self._ocr_pdf_pages(file_path, progress_callback=progress_callback)
                        if not documents:
                            return [Document(text="[PDF could not be processed - encrypted or corrupted]", metadata={"source": file_path, "type": "error", "error": "encrypted_or_corrupted"})]
                        print(f"✅ OCR fallback successful: {len(documents)} pages extracted")
                        return documents
                    except Exception as ocr_error:
                        print(f"⚠️  OCR fallback also failed: {ocr_error}")
                        return [Document(text="[PDF could not be processed - encrypted, corrupted, or unreadable]", metadata={"source": file_path, "type": "error", "error": "encrypted_or_corrupted"})]
                else:
                    print(f"❌ Error processing PDF: {pdf_error}")
                    raise
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            raise
    
    def process_pdf_complete(
        self,
        file_path: str,
        max_pages_total: Optional[int] = None,
        batch_size: int = 5
    ) -> List[Document]:
        """
        Process PDF with production features
        From: tutorial-3-mongodb/pdf_rag_complete.py
        
        Features:
        - Process ALL pages (no limit)
        - Batch processing to save memory
        - Progress tracking
        """
        try:
            print(f"Processing PDF (complete mode): {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF not found: {file_path}")
            
            # Load PDF
            reader = PDFReader()
            documents = reader.load_data(Path(file_path))
            
            # Limit pages if specified (from pdf_rag_complete.py)
            if max_pages_total and len(documents) > max_pages_total:
                documents = documents[:max_pages_total]
                print(f"Limited to {max_pages_total} pages")
            
            print(f"✅ Loaded {len(documents)} pages")
            
            return documents
            
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            raise

    def process_image_hybrid(
        self,
        image_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Document]:
        """Use Docling OCR for images first, fallback to EasyOCR pipeline."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            if progress_callback:
                progress_callback("Running Docling OCR for image")
            result = converter.convert(image_path)

            extracted_text = ""
            if result and getattr(result, "document", None):
                try:
                    extracted_text = str(result.document.export_to_markdown() or "").strip()
                except Exception:
                    extracted_text = ""

                if not extracted_text:
                    lines: List[str] = []
                    try:
                        for element, _ in result.document.iterate_items():
                            maybe_text = str(getattr(element, "text", "") or "").strip()
                            if maybe_text:
                                lines.append(maybe_text)
                    except Exception:
                        lines = []

                    extracted_text = "\n".join(lines).strip()

            if self._is_meaningful_ocr_text(extracted_text):
                cleaned_text = self._clean_ocr_text(extracted_text)
                print(f"✅ Docling image OCR extracted {len(cleaned_text)} meaningful characters")
                return [
                    Document(
                        text=cleaned_text,
                        metadata={
                            "source": image_path,
                            "type": "docling_image_ocr",
                            "preprocessing": "docling",
                        },
                    )
                ]

            print("⚠️  Docling image OCR returned non-meaningful text. Falling back to EasyOCR pipeline.")
        except Exception as exc:
            print(f"⚠️  Docling image OCR unavailable or failed: {exc}. Falling back to EasyOCR pipeline.")

        return self.process_image_ocr(image_path, progress_callback=progress_callback)

    def _clean_ocr_text(self, text: str) -> str:
        """Normalize OCR output by removing layout-only placeholders and extra whitespace."""
        cleaned = re.sub(r"<!--.*?-->", " ", str(text or ""), flags=re.DOTALL)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _is_meaningful_ocr_text(self, text: str) -> bool:
        """Reject placeholder-only OCR output so image uploads can fallback to stronger OCR."""
        cleaned = self._clean_ocr_text(text)
        if not cleaned:
            return False

        alnum_count = sum(1 for ch in cleaned if ch.isalnum())
        return alnum_count >= 12
    
    def process_image_ocr(
        self,
        image_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Document]:
        """
        Extract text from image using OCR
        From: tutorial-3-mongodb/simple_ocr.py
        
        Use for:
        - Phone photos of documents
        - Screenshots with text
        - Any image containing text
        """
        try:
            print(f"Processing image with OCR: {image_path}")
            
            # Check file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")

            with Image.open(image_path) as loaded_image:
                base_image = ImageOps.exif_transpose(loaded_image).convert("RGB")

            # Keep orientation probing lightweight to avoid very long OCR on huge images.
            orientation_candidates = [0, 90, 270]
            best_result: Dict[str, Any] = {
                "text": "",
                "avg_confidence": 0.0,
                "line_count": 0,
                "score": -1.0,
                "rotation": 0,
            }

            for angle in orientation_candidates:
                if progress_callback:
                    progress_callback(f"EasyOCR pass (rotation {angle}°)")
                candidate = base_image if angle == 0 else base_image.rotate(angle, expand=True)
                preprocessed = self._preprocess_image_for_ocr(candidate)
                attempt = self._ocr_image_candidate(preprocessed)

                if attempt["score"] > best_result["score"]:
                    best_result = {**attempt, "rotation": angle}

            text = str(best_result.get("text") or "").strip()

            if not text:
                # Last resort: direct OCR on source image.
                if progress_callback:
                    progress_callback("EasyOCR final pass on original image")
                direct_result = self._readtext_safe(np.array(base_image))
                text = " ".join([(item[1] or "").strip() for item in direct_result if (item[1] or "").strip()]).strip()

            if not text:
                raise ValueError(
                    "No readable text found in uploaded image. Try a clearer scan/photo or upload a PDF."
                )

            print(
                "✅ Extracted "
                f"{len(text)} characters (rotation={best_result.get('rotation', 0)} deg, "
                f"confidence={float(best_result.get('avg_confidence', 0.0)):.2f})"
            )

            document_metadata = {
                "source": image_path,
                "type": "ocr",
                "preprocessing": "auto_rotate_denoise_contrast",
                "rotation_applied": int(best_result.get("rotation", 0) or 0),
                "ocr_confidence": float(best_result.get("avg_confidence", 0.0) or 0.0),
                "ocr_lines": int(best_result.get("line_count", 0) or 0),
            }
            
            # Create document
            document = Document(
                text=text,
                metadata=document_metadata,
            )
            
            return [document]
            
        except Exception as e:
            print(f"❌ Error processing image: {e}")
            raise
    
    def create_vector_index(
        self,
        documents: List[Document],
        collection_name: str = "documents"
    ):
        """
        Create MongoDB vector index from documents
        From: tutorial-3-mongodb/pdf_rag_simple.py
        """
        try:
            print("Creating MongoDB vector index...")
            
            collection = self.db[collection_name]
            
            # Create vector store (EXACT code from tutorial-3)
            vector_store = MongoDBAtlasVectorSearch(
                mongo_client=self.mongo_client,
                db_name=settings.MONGODB_DATABASE,
                collection_name=collection_name,
                vector_index_name="vector_index",
                embedding_key="embedding",
                text_key="text"
            )
            
            # Build index
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                embed_model=self.embed_model,
                show_progress=True
            )
            
            print("✅ Vector index created in MongoDB!")
            
            return index
            
        except Exception as e:
            print(f"❌ Error creating vector index: {e}")
            raise
    
    def search_documents(
        self,
        query: str,
        collection_name: str = "documents",
        limit: int = 3,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search documents using vector search
        From: tutorial-3-mongodb/demo_retrieval_methods.py
        """
        try:
            print(f"Searching for: {query}")
            
            collection = self.db[collection_name]
            
            # Create query embedding
            query_embedding = self.embed_model.get_query_embedding(query)

            vector_stage: Dict[str, Any] = {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": max(limit * 20, 120),
                "limit": limit,
            }
            if document_id:
                vector_stage["filter"] = self._document_match_filter(document_id)

            pipeline = [
                {"$vectorSearch": vector_stage},
                {
                    "$project": {
                        "text": 1,
                        "metadata": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]

            try:
                results = list(collection.aggregate(pipeline))
            except Exception:
                # Compatibility fallback for Mongo versions that do not support vectorSearch.filter.
                fallback_pipeline = [
                    {
                        "$vectorSearch": {
                            "index": "vector_index",
                            "path": "embedding",
                            "queryVector": query_embedding,
                            "numCandidates": max(limit * 20, 120),
                            "limit": max(limit * 5, 30),
                        }
                    },
                ]

                if document_id:
                    fallback_pipeline.append({"$match": self._document_match_filter(document_id)})

                fallback_pipeline.append(
                    {
                        "$project": {
                            "text": 1,
                            "metadata": 1,
                            "score": {"$meta": "vectorSearchScore"},
                        }
                    }
                )

                results = list(collection.aggregate(fallback_pipeline))

            # Normalize chunk text in case top-level "text" is empty but metadata has _node_content.
            for result in results:
                recovered_text = self.extract_text_from_record(result)
                result["text"] = recovered_text
            
            print(f"✅ Found {len(results)} results")
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching documents: {e}")
            return []

    def get_document_chunks(
        self,
        document_id: str,
        collection_name: str = "documents",
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Get all chunks for a specific uploaded document from MongoDB."""
        try:
            collection = self.db[collection_name]
            cursor = collection.find(
                self._document_match_filter(document_id),
                {"text": 1, "metadata": 1},
            ).limit(limit)

            chunks: List[Dict[str, Any]] = []
            for record in cursor:
                text = self.extract_text_from_record(record)
                if not text:
                    continue

                chunks.append(
                    {
                        "text": text,
                        "metadata": record.get("metadata", {}) or {},
                        "score": 0.35,
                    }
                )

            # Keep natural page order when page labels are available.
            chunks.sort(
                key=lambda c: int(c["metadata"].get("page_label", "999999"))
                if str(c["metadata"].get("page_label", "")).isdigit()
                else 999999
            )

            print(f"✅ Loaded {len(chunks)} chunk(s) for document_id={document_id}")
            return chunks
        except Exception as e:
            print(f"❌ Error loading document chunks: {e}")
            return []
    
    def save_document_metadata(self, doc_info: Dict[str, Any]) -> str:
        """Save document metadata to MongoDB"""
        try:
            result = self.collection.insert_one(doc_info)
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error saving document metadata: {e}")
            raise
    
    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        try:
            documents = list(self.collection.find({"user_id": user_id}))
            for doc in documents:
                doc["_id"] = str(doc["_id"])
            return documents
        except Exception as e:
            print(f"❌ Error getting user documents: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        try:
            result = self.collection.delete_one({"_id": document_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return False


# Singleton instance
document_service = DocumentService()
