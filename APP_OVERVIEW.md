# AI Quiz Tutor - App Overview

## What It Does

An AI-powered study platform that:

1. **Uploads PDFs/documents** → processes them with OCR support for scanned files
2. **Generates quizzes** from uploaded content using LLMs
3. **RAG-based chat** → ask questions about your PDFs with cited sources
4. **Memory-enabled assistant** → remembers your name, tracks progress, identifies weak areas
5. **Study planner** → set exam deadlines with reminder notifications
6. **Progress tracking** → quiz scores, weak area analysis, performance trends

---

## Tech Stack

### Frontend (`apps/frontend/`)
- **Next.js 16** (App Router + Pages hybrid)
- **React 18** + **TypeScript**
- **TailwindCSS** for styling
- **Framer Motion** for animations
- **Clerk** for authentication
- **PWA** support (mobile-ready) - can install as an app
- **Three.js** for 3D hero visuals

### Backend (`apps/backend/`)
- **FastAPI** (Python) with Uvicorn/Gunicorn
- **MongoDB Atlas** - vector search + backend data store
- **Supabase Storage** - for document storage
- **LlamaIndex** - RAG pipeline
- **Groq** - LLM inference (quiz generation, chat)
- **HuggingFace API** - embeddings (384-dim)
- **EasyOCR** + **PyMuPDF** - PDF text/image extraction
- **Docling** - complex PDFs with tables
- **Vision models** - BLIP for image understanding (optional)

### Infrastructure
- **Monorepo** structure (apps + packages)
- **Render** deployment - couldn't deploy due to insufficient memory
- **Vercel** for frontend deployment
- **Digital Ocean** for backend deployment
- **Docker** support (Dockerfiles + compose configs)
- **GitHub Actions** for CI/CD (CD not working yet)

---

## Key Features

| Feature          | Implementation                                                |
|------------------|---------------------------------------------------------------|
| PDF Processing   | Multi-mode: simple text, hybrid OCR, full OCR, Docling batch  |
| Vector Search    | MongoDB Atlas $vectorSearch with HuggingFace embeddings       |
| Quiz Generation  | Groq LLM with structured prompting for MCQs                   |
| Chat with Memory | Personalized context (user profile, quiz history, weak areas) |
| Study Planner    | MongoDB-based scheduling for study plans                      |
| Vision Analysis  | Claude API or local BLIP for image-heavy documents (optional as heavy) |

---

## User Flow

1. **Sign up** via Clerk → land on 3D hero homepage
2. **Upload PDF** → background processing (OCR if needed) → vector chunks stored in MongoDB vector DB
3. **Open Chat** → ask questions → RAG retrieves chunks → Groq generates answers with sources
4. **Generate Quiz** → LLM creates MCQs from document → submit answers → get results + weak area analysis
5. **Create Study Plan** → set target date → get reminders via notifications/in-app
