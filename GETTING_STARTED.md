# Getting Started with AI Quiz Tutor

Welcome! This guide will get you from zero to running the full app in minutes (local) or hours (production).

## 🚀 Super Quick Start (10 minutes)

### What You Need
- Python 3.11+
- Node.js 18+
- 3 free API keys (all no-credit-card required)

### Step 1: Get Free API Keys (2 min)

1. **Groq** → https://console.groq.com/keys → Copy key
2. **HuggingFace** → https://huggingface.co/settings/tokens → Create token
3. **MongoDB** → https://cloud.mongodb.com → Create free cluster → Copy URL

### Step 2: Backend (4 min)

```bash
cd apps/backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
copy .env.example .env
notepad .env  # Paste your 3 API keys
python test_backend.py  # Verify setup
python src/main.py      # Start backend
```

Visit: http://localhost:8000/docs (API documentation)

### Step 3: Frontend (2 min)

Open **new terminal**, from project root:

```bash
cd apps/frontend
npm install
npm run dev
```

Visit: http://localhost:3000

### Step 4: Test It (2 min)

1. Sign in with Clerk (dev account)
2. Upload a PDF
3. Watch it process
4. Generate a quiz
5. Take quiz or chat about the PDF

**Done!** 🎉 You have the full stack running.

---

## 📚 Complete Setup Guides

Depending on what you want to do:

### I Want to Understand the Project
- **[APP_OVERVIEW.md](APP_OVERVIEW.md)** — Architecture, tech stack, what each component does

### I Want to Run Locally
- **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** — Complete local setup with troubleshooting
- **[Backend QUICK_START](apps/backend/QUICK_START.md)** — Fastest backend setup
- **[Frontend README](apps/frontend/README.md)** — Frontend setup & features

### I Want to Deploy to Production
- **[Backend SETUP → Production](apps/backend/SETUP.md#production-deployment-vps)** — VPS deployment (Nginx, Docker, SSL)
- **[Frontend README → Deployment](apps/frontend/README.md#-production-deployment-vercel)** — Vercel deployment (1-click)
- **[Production Readiness](docs/PRODUCTION_READINESS.md)** — Pre-launch checklist

### I Want to Troubleshoot
Check the "Troubleshooting" section in:
- **[README.md](README.md#-troubleshooting)** — Common issues
- **[Backend SETUP](apps/backend/SETUP.md#-troubleshooting)** — Backend-specific
- **[Production Readiness](docs/PRODUCTION_READINESS.md#-incident-response)** — Production issues

---

## 🏗️ Project Structure

```
quiz-tutor/
├── README.md                 ← Start here (project overview)
├── SETUP_SUMMARY.md         ← Local + production setup
├── APP_OVERVIEW.md          ← Architecture & tech stack
│
├── apps/backend/
│   ├── QUICK_START.md       ← 5-min backend setup
│   ├── SETUP.md             ← Full setup + production deploy
│   ├── README.md            ← Backend architecture
│   ├── requirements.txt      ← Python dependencies
│   ├── Dockerfile           ← Production image
│   └── src/
│       ├── main.py          ← FastAPI app
│       ├── config.py        ← Settings
│       ├── services/        ← Business logic
│       └── api/             ← REST endpoints
│
├── apps/frontend/
│   ├── README.md            ← Frontend setup + Vercel deploy
│   ├── package.json         ← npm dependencies
│   ├── next.config.ts       ← Next.js config
│   └── src/
│       ├── components/      ← Reusable UI
│       ├── pages/           ← Routes
│       ├── services/        ← API client
│       └── utils/           ← Helpers
│
├── deploy/
│   ├── docker-compose.prod.yml  ← Production services
│   ├── nginx.conf               ← Reverse proxy
│   └── .env.example             ← Production env template
│
└── docs/
    ├── PRODUCTION_READINESS.md  ← Pre-launch checklist
    └── PWA_TESTING.md           ← Mobile PWA testing
```

---

## 🎯 What Each Component Does

### Frontend (http://localhost:3000)
- User interface (Next.js + React)
- Document upload
- Quiz taking
- Chat with AI
- Mobile PWA support

### Backend (http://localhost:8000)
- REST API endpoints
- Smart document processing
  - Detects PDF type (text vs. scanned)
  - Uses Docling for tables, EasyOCR for scanned content
  - Auto-fallback if extraction fails
- RAG pipeline (find relevant content for questions)
- LLM integration (Groq for quiz/chat generation)
- MongoDB vector search

### Database (MongoDB Cloud)
- Stores vector embeddings
- Stores document metadata
- Stores quiz attempts
- Free tier: 512MB storage

---

## 🚀 One-Command Quick Test

After completing "Super Quick Start" steps 1-2:

```bash
cd apps/backend
python test_backend.py
```

Expected output:
```
✅ Configuration: OK
✅ MongoDB: Connected
✅ HuggingFace Embeddings: Working
✅ Groq LLM: Working
✅ Quiz Generation: Working
✅ All systems working!
```

If you see ❌ anywhere, check [SETUP_SUMMARY.md](SETUP_SUMMARY.md#-troubleshooting).

---

## 💾 Environment Variables

### Backend (`.env` file in `apps/backend/`)
```env
GROQ_API_KEY=gsk_...
HF_TOKEN=hf_...
MONGODB_URI=mongodb+srv://...
```

Get these from:
- **Groq**: https://console.groq.com/keys
- **HuggingFace**: https://huggingface.co/settings/tokens
- **MongoDB**: https://cloud.mongodb.com → Connect → Drivers

### Frontend (in `apps/frontend/.env.local`)
Usually auto-configured, but if needed:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🌍 Deployment Paths

### Path 1: Just Try It Locally
→ Follow "Super Quick Start" above

### Path 2: Deploy Full Stack (Production)

**Backend on VPS:**
1. Get a VPS ($12/mo, e.g., DigitalOcean)
2. Follow: [Backend SETUP → Production](apps/backend/SETUP.md#production-deployment-vps)
3. ~45 minutes, includes: Docker, Nginx, SSL, memory tuning

**Frontend on Vercel:**
1. Push code to GitHub
2. Follow: [Frontend README → Deployment](apps/frontend/README.md#-production-deployment-vercel)
3. ~5 minutes, auto-deploys future updates

**Costs:**
- Backend VPS: $12/mo
- Everything else (database, embeddings, LLM, frontend): Free tier
- **Total: $12/mo**

---

## 🏃 Next Steps

1. **Just started?** → Run "Super Quick Start" above
2. **Got it working locally?** → Check [APP_OVERVIEW.md](APP_OVERVIEW.md) to understand architecture
3. **Ready to deploy?** → Go to [SETUP_SUMMARY.md](SETUP_SUMMARY.md#-production-deployment-vps--vercel)
4. **Hit an issue?** → Check troubleshooting in [README.md](README.md#-troubleshooting)

---

## ❓ FAQ

### Q: Do I need to pay for anything?
A: No! All services have free tiers. Only VPS ($12/mo) if you want production.

### Q: Can I use this on my phone?
A: Yes! It's a Progressive Web App (PWA). Click "Install" in browser.

### Q: How long does PDF processing take?
A: 30-180 seconds depending on file size and complexity. You'll see progress in real-time.

### Q: Can I modify the code?
A: Absolutely! It's open-source. See [License](LICENSE) for details.

### Q: Where's my data stored?
A: MongoDB Atlas cloud, Supabase (optional), your database. Never sold.

### Q: How many people can use it?
A: Locally: unlimited (your machine). Production VPS: ~100-200 concurrent users.

### Q: Is it secure?
A: Yes! HTTPS, API key management, CORS protection, input validation. See [Production Readiness](docs/PRODUCTION_READINESS.md).

---

## 📞 Need Help?

1. **Error messages?** → Search [README.md](README.md#-troubleshooting)
2. **Setup stuck?** → Check [SETUP_SUMMARY.md](SETUP_SUMMARY.md#-troubleshooting)
3. **Want to understand code?** → See [APP_OVERVIEW.md](APP_OVERVIEW.md)
4. **Want to deploy?** → Follow step-by-step in [Backend SETUP](apps/backend/SETUP.md) or [Frontend README](apps/frontend/README.md)

---

## 🎓 Learning Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/) — Backend framework
- [Next.js Docs](https://nextjs.org/docs) — Frontend framework
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) — Database
- [LlamaIndex](https://docs.llamaindex.ai/) — RAG pipeline
- [Groq Developer Docs](https://console.groq.com/docs) — LLM API

---

**Ready?** Start with the "Super Quick Start" section above! 🚀
