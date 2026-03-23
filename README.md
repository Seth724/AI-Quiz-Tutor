# AI Quiz Tutor 📚

AI-powered learning assistant that generates quizzes from uploaded documents.

## 🎯 Features

- ✅ Upload PDFs and documents
- ✅ Automatic quiz generation
- ✅ OCR support (images, scanned PDFs)
- ✅ **Vision Model Analysis** (Claude or local BLIP) for image understanding
- ✅ Progress tracking
- ✅ Weak area identification
- ✅ Review reminders
- ✅ Chat with AI tutor
- ✅ Mobile-friendly PWA

## 📁 Monorepo Structure

```
quiz-tutor/
├── apps/
│   ├── backend/           # FastAPI (ML, RAG, Quiz generation)
│   └── frontend/          # Next.js 16 PWA
├── packages/
│   ├── shared/           # Shared types, utilities
│   └── config/           # Shared configurations
├── docs/
│   └── api/              # API documentation
└── .github/
    └── workflows/        # CI/CD
```

## 🚀 Quick Start

### Backend (ML Service)

```bash
cd apps/backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
copy .env.example .env
# Edit .env with your API keys
python test_backend.py  # Test setup
python src/main.py      # Run server
```

**API Docs:** http://localhost:8000/docs

### Frontend (Next.js 16)

```bash
cd apps/frontend
npm install
cp .env.example .env
npm run dev
```

**Frontend:** http://localhost:3000

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Python API framework
- **MongoDB Atlas** - Vector search + database (512MB free)
- **Groq** - Fast LLM inference (free tier)
- **HuggingFace API** - Embeddings (free)
- **LlamaIndex** - RAG pipeline (from tutorial-3)
- **Local File Storage** - Document files in backend data directory

### Frontend
- **Next.js 16** - React framework (App Router)
- **Clerk** - Authentication (10K users free)
- **TailwindCSS** - Styling
- **PWA** - Mobile app support

## 💰 Free Tier Services

All services have generous free tiers:

| Service | Free Tier | Paid When |
|---------|-----------|-----------|
| MongoDB Atlas | 512MB | ~500K vectors |
| Clerk | 10K MAU | 10,000+ users |
| Groq | Free tier | High usage |
| Vercel | Unlimited | 100GB bandwidth |
| HuggingFace | Free API | Rate limits |

**Can serve ~1,000 active users for FREE!** 🚀

## 📚 Documentation

- [Backend Setup](apps/backend/SETUP.md)
- [API Documentation](docs/api/README.md)
- [Frontend Setup](apps/frontend/README.md)
- [Production Readiness Checklist](docs/PRODUCTION_READINESS.md)
- [PWA Testing Guide](docs/PWA_TESTING.md)

## ⚠️ Processing And Chat Behavior

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
