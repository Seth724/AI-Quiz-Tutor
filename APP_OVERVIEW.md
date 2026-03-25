# AI Quiz Tutor - App Overview

## What It Does

An AI-powered study companion that:

1. **Upload PDFs & Documents** → Intelligent processing with smart format detection
   - Auto-detects simple text vs. complex vs. scanned documents
   - Uses Docling for structured content (preserves tables/formatting)
   - Falls back to OCR (EasyOCR) when needed
   - Processes in ~30-180 seconds depending on file size

2. **Generate Quizzes** → LLM-powered question creation
   - Creates multiple-choice questions from document content
   - Adjustable difficulty and question count
   - Instant feedback and scoring

3. **Chat About Documents** → RAG-powered answers with sources
   - Ask questions about your PDFs
   - Gets answers from document content with cited passages
   - Only enabled when document is fully processed

4. **Track Progress** → Learning analytics
   - Quiz scores and weak areas
   - Performance trends over time
   - Study session history

5. **Mobile Ready** → Progressive Web App (PWA)
   - Works offline (cached content)
   - Installable as app on iPhone/Android
   - Responsive design for all screen sizes

---

## Tech Stack

### Frontend (`apps/frontend/`)
- **Next.js 16** (App Router) — React meta-framework
- **TypeScript** — Type-safe development
- **TailwindCSS** — Utility-first styling
- **Clerk** — User authentication & management
- **Service Worker** — PWA support (offline + caching)
- **Responsive Design** — Mobile-optimized UI

### Backend (`apps/backend/`)
- **FastAPI** — Python web framework
- **Gunicorn + Uvicorn** — Production-grade server (single worker = low memory)
- **Docling** — Advanced PDF parsing (tables, structure preservation)
- **EasyOCR** — Optical character recognition fallback
- **PyMuPDF** — PDF text extraction
- **LlamaIndex** — RAG pipeline orchestration
- **MongoDB Atlas** — Vector database (512MB free tier)
- **HuggingFace API** — Text embeddings (no local models needed)
- **Groq** — Fast LLM inference (free tier, no rate limits)
- **Supabase** — File storage (optional)

### Infrastructure & Deployment

| Component | Platform | Cost/Tier | Why |
|-----------|----------|-----------|-----|
| **Frontend** | Vercel | Free | Optimized for Next.js, auto-deploys from GitHub |
| **Backend** | VPS (DigitalOcean/Linode) | $12/mo | Full control, Docker support, memory tuning |
| **Database** | MongoDB Atlas M0 | Free | Vector search, no setup needed, auto-backups |
| **Storage** | Supabase/S3 | Free tier | CDN-backed file storage |
| **SSL/HTTPS** | Let's Encrypt | Free | Auto-renews, no expiration worries |
| **LLM** | Groq | Free tier | Fast inference, generous rate limits |

**Total Cost:** $12/month (minimum, backend only) | Can serve 100-200 concurrent users

---

## Document Processing Pipeline

```
Upload File (PDF or Image)
        ↓
    [Analyze]
    - Page count
    - Text density
    - Image ratio
        ↓
  [Auto-Select Mode]
  ├─ simple_text: Text-only PDFs → Direct extraction
  ├─ docling_batch: Complex PDFs → Docling (180s timeout)
  ├─ ocr_hybrid: Mixed content → Docling + OCR fallback
  └─ ocr_full: Scanned images → EasyOCR only
        ↓
  [Extract with Progress]
  • Show elapsed time during processing
  • Heartbeat updates every 15 seconds
  • Auto-timeout after 20 minutes (mark failed)
        ↓
  [Vectorize & Store]
  • Split into chunks (300-500 tokens)
  • Embed with HuggingFace
  • Store in MongoDB with metadata
        ↓
  Status: processing → ready
```

---

## Key Architectural Decisions

### 🎯 Smart Document Processing
- **Why Docling?** Preserves tables, structure, formatting (not just text)
- **Why Fallback to OCR?** If Docling times out or errors (resource constraints)
- **Why Memory Tuning?** $12 VPS has only 1.5GB; must optimize:
  - Lower OCR DPI (170 → 150)
  - Limit image dimensions (1800 → 1400)
  - Single Gunicorn worker (prevents model duplication)

### 🔒 Production Safety
- **Docling Timeout:** Prevents infinite hangs; falls back to OCR
- **Stale Job Cleanup:** Auto-marks jobs failed after 20 minutes
- **UTC Timezone Handling:** Fixed browser display bugs
- **Service Worker Auth Bypass:** Prevents Clerk redirect loops
- **CORS Restricted:** Only frontend origin can hit backend

### 📱 Mobile-First
- **PWA Support:** Installable on iPhone/Android home screen
- **Offline Capable:** Service worker caches essential assets
- **Responsive Design:** Works on phones, tablets, desktops
- **Dark Mode Ready:** TailwindCSS supports theming

---

## User Flow

### 1. Getting Started
- Sign up with email (Clerk handles auth)
- Redirected to documents page
- See existing documents or upload new

### 2. Upload & Processing
```
Click "Upload PDF"
    ↓
Select file from device
    ↓
Backend starts processing (shows elapsed time)
    ↓
Every 15 seconds: UI updates progress
    ↓
When ready: Status changes from "Processing" to "Ready"
    ↓
Now can: Chat, generate quiz, or download
```

### 3. Generate Quiz
```
Click "Generate Quiz"
    ↓
Select difficulty + # of questions
    ↓
Backend extracts content → Groq generates MCQs
    ↓
Quiz appears with interactive answering
    ↓
Submit answers → Get score + weak areas
```

### 4. Chat with PDF
```
Click "Ask AI" in document card
    ↓
Chat window opens (only if document is ready)
    ↓
Type question about document
    ↓
Backend: Find relevant chunks → Generate answer with Groq
    ↓
Response shows answer + source passages
```

### 5. Progress Tracking
- View all quizzes and scores
- See weak areas (topics with low scores)
- View study history
- Download certificates (optional)

---

## Data Flow

```
Frontend (Vercel)
      ↓ HTTPS
Backend (VPS)
      ├─ Document Processing
      │  └─→ MongoDB Atlas (store vectors)
      │
      ├─ Quiz Generation
      │  └─→ Groq API (free LLM)
      │
      ├─ Chat RAG
      │  ├─→ MongoDB (retrieve vectors)
      │  └─→ Groq API (generate response)
      │
      └─ File Storage
         └─→ Supabase (optional, for backups)
```

---

## Environment Variables

### Backend (`.env.backend`)
```env
# Required
GROQ_API_KEY=gsk_...              # Free from https://console.groq.com/keys
HF_TOKEN=hf_...                    # Free from https://huggingface.co/settings/tokens
MONGODB_URI=mongodb+srv://...      # Free from https://cloud.mongodb.com

# Recommended
FRONTEND_ORIGINS=https://yourdomain.com
ENVIRONMENT=production

# Memory Tuning (for VPS)
OCR_PDF_DPI=150
OCR_MAX_IMAGE_DIM=1400
```

### Frontend (`.env.local` or Vercel)
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
```

---

## What Was Fixed (Production Deployment)

### Issue 1: PDF Hangs on VPS
- **Root Cause:** Out of memory (OOM) during OCR fallback
- **Fix:** Added Docling watchdog (180s timeout), memory tuning (DPI/dims), swap file

### Issue 2: Auth Redirect Loops
- **Root Cause:** Service worker caching Clerk auth responses
- **Fix:** v3 service worker with auth route bypass

### Issue 3: Timezone Display Bug
- **Root Cause:** API sends naive UTC; browser parsed as local time
- **Fix:** `parseApiDate()` explicitly treats as UTC before formatting

### Issue 4: Stale Processing Jobs Never Finish
- **Root Cause:** No timeout enforcement
- **Fix:** Auto-mark failed after 20 minutes + time display

### Issue 5: Large PDF Processing Very Slow
- **Root Cause:** High OCR DPI (220) + large image dims (2400)
- **Fix:** Reduced to DPI 150, dims 1400 (30% RAM savings each)

---

## Performance Targets

### Local (Your Machine)
- PDF upload: 10-50MB
- Processing: 30-120 seconds
- Quiz generation: 5-15 seconds
- Chat response: 2-10 seconds

### Production (VPS $12/mo)
- Concurrent uploads: 1 (sequential)
- Max PDF size: 100-150MB
- Processing time: 30-180 seconds
- Storage: 512MB (MongoDB free)
- Bandwidth: 100GB/mo (Vercel free)

---

## Next Steps for Users

### Try Locally (5 min)
```bash
# Backend
cd apps/backend
pip install -r requirements.txt
python src/main.py

# Frontend (new terminal)
cd apps/frontend
npm install
npm run dev
```

### Deploy to Production
1. **Backend:** See [Backend SETUP.md](apps/backend/SETUP.md#production-deployment-vps)
2. **Frontend:** See [Frontend README - Deployment](apps/frontend/README.md#-production-deployment-vercel)
3. **Validation:** See [Production Readiness](docs/PRODUCTION_READINESS.md)

---

## Documentation Index

| Topic | File |
|-------|------|
| **Quick Start** | [SETUP_SUMMARY.md](SETUP_SUMMARY.md) |
| **Backend Local** | [apps/backend/QUICK_START.md](apps/backend/QUICK_START.md) |
| **Backend Production** | [apps/backend/SETUP.md](apps/backend/SETUP.md) |
| **Frontend** | [apps/frontend/README.md](apps/frontend/README.md) |
| **Production Checklist** | [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) |
| **PWA Testing** | [docs/PWA_TESTING.md](docs/PWA_TESTING.md) |
| **API Docs** | http://localhost:8000/docs (when backend running) |
