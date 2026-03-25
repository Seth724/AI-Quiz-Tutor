# AI Quiz Tutor 📚

Production-ready AI learning assistant that generates quizzes from uploaded documents using advanced document processing, RAG pipelines, and LLM-powered content generation.

## 🎯 Core Features

- ✅ **Smart Document Processing**: Auto-detect PDF/image type and select optimal extraction method
  - Docling for tables and structured content
  - OCR (EasyOCR) for scanned documents with memory optimization
  - Automatic fallback chain on low-resource servers
- ✅ **RAG-Powered Q&A**: Vector search over document content via MongoDB Atlas
- ✅ **Quiz Generation**: LLM-based (Groq) quiz creation from document chunks
- ✅ **Real-time Chat**: Chat with AI tutor about uploaded documents
- ✅ **Progress Tracking**: Elapsed time indicators, processing status, weak areas
- ✅ **Mobile PWA**: Progressive Web App for offline access and mobile install
- ✅ **Vision Model Integration**: Claude vision for image understanding

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Frontend (Next.js 16 PWA - Vercel)                  │
│  - Clerk Auth | TailwindCSS | Service Worker (PWA)          │
│  - Real-time Status | Chat Interface | Quiz Taking         │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTPS
                 ▼
┌─────────────────────────────────────────────────────────────┐
│         Backend (FastAPI - VPS Docker)                      │
│  ├─ Smart PDF Processor (Docling + EasyOCR)                │
│  ├─ RAG Pipeline (LlamaIndex + MongoDB Atlas)              │
│  ├─ LLM Integration (Groq)                                 │
│  └─ Background Job Processor                                │
└──┬──────────────────────────────────┬──────────────────────┘
   │                                  │
   ▼                                  ▼
┌──────────────────┐        ┌─────────────────────┐
│ MongoDB Atlas    │        │ Supabase Storage    │
│ - Vector Search  │        │ - Document Files    │
│ - Metadata       │        │ - Backups           │
└──────────────────┘        └─────────────────────┘
```

## 📁 Project Structure

```
quiz-tutor/
├── apps/
│   ├── backend/               # FastAPI + ML/RAG
│   │   ├── src/
│   │   │   ├── main.py       # FastAPI app entry
│   │   │   ├── config.py     # Centralized settings
│   │   │   ├── api/
│   │   │   │   ├── routes.py # REST endpoints
│   │   │   │   └── schemas.py
│   │   │   └── services/
│   │   │       ├── document_service.py  # Smart PDF/OCR processing
│   │   │       ├── quiz_service.py      # Quiz generation
│   │   │       └── background_processor.py  # Async jobs
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── SETUP.md          # Production deployment guide
│   │
│   └── frontend/              # Next.js 16 PWA
│       ├── src/components/    # Reusable UI
│       ├── src/pages/         # Routes
│       ├── src/services/      # API client
│       ├── package.json
│       └── next.config.ts
│
├── deploy/
│   ├── docker-compose.prod.yml  # VPS production setup
│   ├── nginx.conf               # Reverse proxy config
│   └── .env.example             # Production env template
│
├── docs/
│   ├── PRODUCTION_READINESS.md
│   └── PWA_TESTING.md
│
└── README.md (this file)
```

## 🚀 Quick Start (Local Development)

### Backend Setup (5 minutes)

```bash
cd apps/backend
python -m venv venv
venv\Scripts\activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env  # Windows: use copy; Mac/Linux: use cp
```

**Edit `.env` with your API keys** (get them free):
```env
GROQ_API_KEY=gsk_...           # From https://console.groq.com/keys
HF_TOKEN=hf_...                 # From https://huggingface.co/settings/tokens
MONGODB_URI=mongodb+srv://...   # From https://cloud.mongodb.com
```

```bash
# Test backend (validates all connections)
python test_backend.py

# Start server
python src/main.py
```

**API Docs:** http://localhost:8000/docs

### Frontend Setup (3 minutes)

```bash
cd apps/frontend
npm install
npm run dev
```

**Frontend:** http://localhost:3000

### Test the Full Flow

1. Open http://localhost:3000
2. Sign in with Clerk (dev keys pre-configured)
3. Upload a PDF → Watch processing status
4. Generate quiz → Take quiz
5. Chat about the document

## 🛠️ Tech Stack

### Backend Services
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API** | FastAPI + Uvicorn + Gunicorn | REST endpoints, async processing |
| **Document Processing** | Docling + EasyOCR + PyMuPDF | PDF extraction with smart fallback |
| **RAG Pipeline** | LlamaIndex + MongoDB Atlas | Vector search over document content |
| **LLM** | Groq (free tier) | Fast quiz/chat generation |
| **Embeddings** | HuggingFace API | Text vectorization (no local model) |
| **Storage** | Supabase/S3-compatible | Document file storage |

### Frontend Stack
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Next.js 16 (App Router) | React meta-framework |
| **Styling** | TailwindCSS | Utility-first CSS |
| **Auth** | Clerk | User authentication & management |
| **PWA** | Service Worker + Manifest | Offline support & mobile install |
| **Language** | TypeScript | Type safety |

### Infrastructure
| Service | Tier | Cost | Capacity |
|---------|------|------|----------|
| **VPS** (Backend) | DigitalOcean $12/mo | $12/mo | 1.5GB RAM, 25GB disk |
| **Database** | MongoDB Atlas M0 (free) | Free | 512MB storage |
| **File Storage** | Supabase (free) | Free | 1GB bandwidth/mo |
| **Frontend** | Vercel (free) | Free | Up to 100GB bandwidth |
| **LLM** | Groq (free) | Free | High rate limits |
| **Embeddings** | HuggingFace (free) | Free | Rate-limited |
| **Auth** | Clerk (free) | Free | 10K MAU included |

**Total Startup Cost: $12/mo** (VPS only) 🚀

## 📊 Document Processing Flow

```
PDF/Image Upload
│
├─ Quick Analysis (page count, text density, image ratio)
│
├─ Processing Mode Selection
│  ├─ simple_text: Text-only PDFs → Direct PyMuPDF extraction
│  ├─ docling_batch: Complex PDFs → Docling (preserves tables/structure)
│  ├─ ocr_hybrid: Text-heavy with some OCR → Docling + EasyOCR fallback
│  └─ ocr_full: Scanned images → EasyOCR only
│
├─ Extraction Phase (with progress tracking)
│  ├─ Try primary method (Docling with 180s timeout + heartbeat)
│  ├─ On timeout/error → Auto-fallback to OCR
│  └─ Memory-aware preprocessing (DPI: 150-170, max dims: 1400-1800)
│
├─ Vectorization Phase
│  └─ Split chunks → Embed with HuggingFace → Store in MongoDB
│
└─ Ready State
   └─ Document available for chat, quiz generation, search
```

## 🔒 Production Features

- ✅ HTTPS with Let's Encrypt auto-renewal
- ✅ CORS restricted to frontend origins
- ✅ Service worker caching optimized for offline fallback
- ✅ Auto-timeout for stuck processing jobs (20-minute reconciliation)
- ✅ Memory-aware OCR tuning (works on 1.5GB VPS)
- ✅ Watchdog timeout for Docling (prevents infinite hangs)
- ✅ Incremental progress tracking (elapsed time UI indicators)
- ✅ Graceful degradation when Docling unavailable

## 📚 Setup Guides

### For Local Development
- [Backend Quick Start](apps/backend/QUICK_START.md) - Get backend running in 5 minutes
- [Backend Full Setup](apps/backend/SETUP.md) - Complete explanation with troubleshooting

### For Production Deployment
- [Backend VPS Deployment](apps/backend/SETUP.md#production-deployment-vps) - Deploy on DigitalOcean $12/mo
- [Frontend Vercel Deployment](apps/frontend/README.md#deployment) - Deploy on Vercel (free)
- [Production Readiness Checklist](docs/PRODUCTION_READINESS.md) - Pre-launch validation

### Testing
- [PWA Testing Guide](docs/PWA_TESTING.md) - Test offline support and mobile install

## 🐛 Troubleshooting

### Backend

**Q: "Worker was sent SIGKILL" in logs**
- A: Out of memory on VPS. Solution: Add swap (see [Backend SETUP](apps/backend/SETUP.md#memory-tuning))

**Q: PDF stuck on "processing" for 20+ minutes**
- A: Status timeout kicks in after 20 min. Check logs: `docker logs -f quiz-tutor-backend`

**Q: Docling not found error**
- A: Backend image missing Docling. Rebuild: `docker build -t quiz-tutor-backend apps/backend`

**Q: "Connection refused" to MongoDB**
- A: Check MongoDB URI in `.env`. Verify IP whitelist in MongoDB Atlas → Network Access.

### Frontend

**Q: Cannot login (redirect loop)**
- A: Fixed in latest version. Update service worker: `npm run build`

**Q: "Processing" badge stuck**
- A: UI caches status. Hard refresh browser (Ctrl+Shift+R) or wait for next poll.

**Q: Photo upload works, PDF times out**
- A: Docling extraction takes time. Check backend logs for processing updates.

### General

**Q: "mongodb not found" error**
- A: MongoDB URI missing or incorrect. Get connection string from MongoDB Atlas → Connect.

**Q: Groq API returning error 401**
- A: Check `GROQ_API_KEY` in `.env`. Regenerate key at https://console.groq.com/keys if needed.

## 🚀 Deployment Summary

### Option 1: Local + Public

```bash
# Backend on your machine, Frontend on Vercel
npm run build    # Build frontend locally
vercel deploy --prod
# Share public URL
```

### Option 2: Full Production (VPS + Vercel)

1. **Backend**: Deploy on DigitalOcean/Linode VPS ($12/mo)
   - See [Backend SETUP → Production](apps/backend/SETUP.md#production-deployment-vps)

2. **Frontend**: Deploy on Vercel (free)
   - Push to GitHub → Vercel auto-deploys

3. **Domain**: Point DNS to both services
   - Backend: `api.yourdomain.com` → VPS
   - Frontend: `yourdomain.com` → Vercel DNS

See [Production Readiness Checklist](docs/PRODUCTION_READINESS.md) for full validation.

- Large PDFs can take several minutes while Docling + embedding jobs complete.
- Chat now blocks non-ready documents and returns a clear status message instead of partial answers.
- Page counts are now derived from page metadata (not chunk count), so chunk-heavy documents no longer show inflated page totals.
- Document list polling is throttled to reduce repetitive `200 OK` log noise.

## 🧪 Testing

### Test Backend

```bash
cd apps/backend
python test_backend.py
```

Tests:
- ✅ Configuration
- ✅ MongoDB connection
- ✅ HuggingFace embeddings
- ✅ Groq LLM
- ✅ Quiz generation

### Test API

Open http://localhost:8000/docs and try endpoints interactively.

## 🎓 Learning Path

This project builds on concepts from `tutorial-3-mongodb`:

1. **PDF Processing** - Uses `pdf_rag_simple.py` approach
2. **MongoDB Vector Search** - From `demo_retrieval_methods.py`
3. **RAG Pipeline** - LlamaIndex + Groq
4. **Quiz Generation** - LLM prompting

## 📝 API Endpoints

### Documents
- `POST /api/documents/upload` - Upload PDF
- `GET /api/documents` - List documents
- `DELETE /api/documents/{id}` - Delete document

### Quizzes
- `POST /api/quizzes/generate` - Generate quiz
- `GET /api/quizzes/{id}` - Get quiz
- `POST /api/quizzes/{id}/submit` - Submit answers
- `GET /api/quizzes/{id}/results` - Get results

### Progress
- `GET /api/progress` - User progress
- `GET /api/progress/weak-areas` - Weak areas
- `POST /api/reminders` - Schedule reminder

### Chat
- `POST /api/chat` - Chat with AI tutor (RAG)

## 🔧 Configuration

See `apps/backend/.env.example` for all configuration options.

Required:
- `GROQ_API_KEY` - LLM for quiz generation
- `HF_TOKEN` - HuggingFace embeddings
- `MONGODB_URI` - MongoDB Atlas connection

Optional:
- `CLERK_*` - Authentication

## 🚀 Deployment

### Backend (Railway/Render)

1. Push to GitHub
2. Connect Railway/Render
3. Add environment variables
4. Deploy!

### Frontend (Vercel)

1. Push to GitHub
2. Import to Vercel
3. Add environment variables
4. Deploy!

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit PR

## 📄 License

MIT

## 🙏 Acknowledgments

Built using working code from:
- `tutorial-3-mongodb/pdf_rag_simple.py`
- `tutorial-3-mongodb/demo_retrieval_methods.py`
- LlamaIndex, MongoDB, Groq, HuggingFace

---

**Ready to build the future of AI-powered learning!** 🎯
