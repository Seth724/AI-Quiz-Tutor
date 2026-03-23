# Quick Backend Setup

## Use Existing VENV from Root

Since you already have a working venv in the root with all packages installed, we can use it!

## Option 1: Use Root VENV (Recommended - Already Has Everything)

```bash
# From quiz-tutor/apps/backend directory
cd D:\MetaruneLabs\rag-llamaindex-docling

# Activate existing venv
venv\Scripts\activate

# Go to backend
cd quiz-tutor/apps/backend

# Copy environment file
copy .env.example .env

# Edit .env with your API keys
notepad .env

# Test backend
python test_backend.py

# Run server
python src\main.py
```

**✅ This uses your existing packages from tutorial-3!**

---

## Option 2: Create New VENV (If You Want Separate Environment)

```bash
cd quiz-tutor/apps/backend

# Create new venv
python -m venv venv
venv\Scripts\activate

# Install all packages
pip install -r requirements.txt

# This installs:
# - FastAPI (web framework)
# - MongoDB drivers
# - LlamaIndex (from tutorial-3)
# - Groq (LLM)
# - HuggingFace (embeddings)
# - EasyOCR (from simple_ocr.py)
# - And more...

# Copy environment
copy .env.example .env

# Edit .env
notepad .env

# Test
python test_backend.py

# Run
python src\main.py
```

---

## Required API Keys (.env)

Edit `quiz-tutor/apps/backend/.env`:

```env
# Required - Get from tutorial-3 or create new
GROQ_API_KEY=your_groq_key
HF_TOKEN=your_huggingface_token
MONGODB_URI=mongodb+srv://your_cluster
```

**Get API Keys:**
- **Groq:** https://console.groq.com/keys
- **HuggingFace:** https://huggingface.co/settings/tokens
- **MongoDB:** https://cloud.mongodb.com/ → Connect → Drivers

---

## Test Backend

```bash
# Activate venv
venv\Scripts\activate

# Go to backend
cd quiz-tutor/apps/backend

# Run test
python test_backend.py
```

**Expected Output:**
```
============================================================
Testing AI Quiz Tutor Backend
============================================================

Using working code from tutorial-3-mongodb:
  - pdf_rag_simple.py (PDF processing)
  - pdf_rag_complete.py (production features)
  - simple_ocr.py (OCR for images)
  - demo_retrieval_methods.py (vector search)

[Test 1] Checking configuration...
  GROQ_API_KEY: ✅ Set
  HF_TOKEN: ✅ Set
  MONGODB_URI: ✅ Set
  ✅ Configuration OK

[Test 2] Testing MongoDB connection...
  ✅ MongoDB connection successful

[Test 3] Testing HuggingFace embedding API...
  ✅ Embedding generated: 384 dimensions

[Test 4] Testing Groq LLM...
  ✅ Groq LLM response: Hello, I am working!

[Test 5] Testing PDF processing...
  ✅ PDF processed: 234 pages

[Test 7] Testing quiz generation...
  ✅ Generated 2 questions:
  ...

============================================================
Test Summary
============================================================
✅ All systems working!
```

---

## Run Server

```bash
python src\main.py
```

**Server starts at:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

---

## Packages Installed

From `requirements.txt`:

### Core (from tutorial-3)
- `llama-index-core` - RAG pipeline
- `llama-index-llms-groq` - Groq LLM
- `llama-index-embeddings-huggingface-api` - HuggingFace embeddings
- `llama-index-vector-stores-mongodb` - MongoDB vector search
- `llama-index-readers-file` - PDFReader (from pdf_rag_simple.py)

### OCR (from simple_ocr.py)
- `easyocr` - OCR engine
- `pillow` - Image processing

### Web Framework
- `fastapi` - API framework
- `uvicorn` - Server

### Database
- `pymongo` - MongoDB driver
- `motor` - Async MongoDB

### Storage
- Local filesystem under `apps/backend/src/data`

### Utilities
- `python-dotenv` - Environment variables
- `httpx` - HTTP client
- `aiofiles` - Async file I/O

---

## Troubleshooting

### "Module not found" Error

**If using root venv:**
```bash
# Make sure venv is activated
venv\Scripts\activate

# Check packages
pip list | findstr llama
```

**If using new venv:**
```bash
pip install -r requirements.txt
```

### MongoDB Connection Error

```
ServerSelectionTimeoutError
```

**Fix:**
1. Check MongoDB URI in `.env`
2. Whitelist IP in Atlas: Network Access → Add IP Address → `0.0.0.0/0` (allow all)

### API Key Error

```
AuthenticationError
```

**Fix:** Check API keys in `.env` - copy from your tutorial-3 `.env` file

---

## Next Steps

1. ✅ Test backend: `python test_backend.py`
2. ✅ Run server: `python src\main.py`
3. ✅ Test API: http://localhost:8000/docs
4. ⏭️ Create frontend (Next.js 16)

---

**Status: Ready to test!** 🚀
