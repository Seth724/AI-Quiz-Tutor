"""
Configuration settings for the backend

Loads environment variables from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set cache directories to D: drive (from tutorial-3)
os.environ["HF_HOME"] = os.getenv("HF_HOME", "D:\\hf_cache")
os.environ["HF_HUB_CACHE"] = os.getenv("HF_HUB_CACHE", "D:\\hf_cache\\hub")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.getenv("SENTENCE_TRANSFORMERS_HOME", "D:\\hf_cache")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Create cache directories
for path in [os.environ["HF_HOME"], os.environ["HF_HUB_CACHE"], os.environ["SENTENCE_TRANSFORMERS_HOME"]]:
    os.makedirs(path, exist_ok=True)


class Settings:
    """Application settings"""
    
    # ===========================================
    # API Keys
    # ===========================================
    
    # Groq API Key
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Anthropic Claude (optional, for vision models)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # HuggingFace Token
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    
    # ===========================================
    # MongoDB Atlas
    # ===========================================
    
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "quiz_tutor")
    
    # ===========================================
    # Clerk
    # ===========================================
    
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_PUBLISHABLE_KEY: str = os.getenv("CLERK_PUBLISHABLE_KEY", "")
    
    # ===========================================
    # App Configuration
    # ===========================================
    
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    FRONTEND_ORIGINS: str = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:3001")
    FRONTEND_ORIGIN_REGEX: str = os.getenv("FRONTEND_ORIGIN_REGEX", "https://.*\\.vercel\\.app")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CHATBOT_API_URL: str = os.getenv("CHATBOT_API_URL", "https://fitness-chatbot-y6yn.onrender.com")
    CHATBOT_API_TIMEOUT_SECONDS: int = int(os.getenv("CHATBOT_API_TIMEOUT_SECONDS", "20"))

    # ===========================================
    # Optional: Supabase Storage (production)
    # ===========================================

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_SERVICE_KEY", ""))
    SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "documents")
    SUPABASE_PUBLIC_URL_BASE: str = os.getenv("SUPABASE_PUBLIC_URL_BASE", "")

    # ===========================================
    # Email Notifications (optional)
    # ===========================================

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}
    
    # ===========================================
    # LLM Configuration
    # ===========================================
    
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.7
    
    # Vision Model Configuration
    VISION_MODEL: str = "claude-3-5-sonnet-20241022"  # Claude vision model (if ANTHROPIC_API_KEY set)
    VISION_USE_LOCAL_FALLBACK: bool = True  # Use local BLIP if Claude unavailable
    
    # Embedding Model
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # ===========================================
    # Document Processing Controls
    # ===========================================

    # Optional override: simple_text | ocr_hybrid | ocr_full | docling_batch
    FORCE_PROCESSING_MODE: str = os.getenv("FORCE_PROCESSING_MODE", "").strip().lower()
    # Per-batch watchdog for Docling conversion on low-resource servers.
    DOCLING_BATCH_TIMEOUT_SECONDS: int = int(os.getenv("DOCLING_BATCH_TIMEOUT_SECONDS", "180"))
    DOCLING_PROGRESS_HEARTBEAT_SECONDS: int = int(os.getenv("DOCLING_PROGRESS_HEARTBEAT_SECONDS", "15"))
    # OCR memory tuning for low-resource VPS deployments.
    OCR_PDF_DPI: int = int(os.getenv("OCR_PDF_DPI", "170"))
    OCR_MAX_IMAGE_DIM: int = int(os.getenv("OCR_MAX_IMAGE_DIM", "1800"))
    
    def validate(self):
        """Validate required settings"""
        errors = []
        
        if not self.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required")
        
        if not self.HF_TOKEN:
            errors.append("HF_TOKEN is required")
        
        if not self.MONGODB_URI:
            errors.append("MONGODB_URI is required")
        
        if errors:
            raise ValueError("\n".join(errors))
        
        return True


# Create settings instance
settings = Settings()

# Validate on import (will raise error if missing)
try:
    settings.validate()
    print("✅ Settings loaded successfully")
except ValueError as e:
    print(f"⚠️  Configuration warning: {e}")
    print("\nGet your API keys:")
    print("  - GROQ: https://console.groq.com/keys")
    print("  - HuggingFace: https://huggingface.co/settings/tokens")
    print("  - MongoDB: https://cloud.mongodb.com/ → Connect → Drivers")
