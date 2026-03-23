# Backend Setup Guide

## Step 1: Create Virtual Environment

```bash
cd apps/backend
python -m venv venv
```

## Step 2: Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- MongoDB drivers
- LlamaIndex (RAG pipeline from tutorial-3)
- Groq (LLM)
- HuggingFace (embeddings)
- Local file storage utilities

## Step 4: Set Up Environment Variables

```bash
copy .env.example .env  # Windows
# or
cp .env.example .env  # macOS/Linux
```

Edit `.env` and add your API keys:

```env
# Required
GROQ_API_KEY=gsk_your_key_here
HF_TOKEN=your_huggingface_token
MONGODB_URI=mongodb+srv://your_cluster

# Optional (for later)
CLERK_SECRET_KEY=your_key

# Optional (email reminders)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_USE_TLS=true
```

## Step 5: Test Backend

```bash
python test_backend.py
```

Expected output:
```
✅ Configuration: OK
✅ MongoDB: Connected
✅ HuggingFace Embeddings: Working
✅ Groq LLM: Working
✅ Quiz Generation: Working
```

## Step 6: Run the Server

```bash
python src/main.py
```

Server starts at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

## Step 7: Test API Endpoints

Open `http://localhost:8000/docs` and try:

1. **Health Check:**
   - `GET /`
   - Should return: `{"status": "ok"}`

2. **Generate Quiz:**
   - `POST /api/quizzes/generate`
   - Body:
   ```json
   {
     "document_id": "test-doc",
     "num_questions": 3,
     "difficulty": "easy"
   }
   ```

## Troubleshooting

### MongoDB Connection Error
```
pymongo.errors.ServerSelectionTimeoutError
```
**Fix:** Check your MongoDB URI in `.env`. Make sure your IP is whitelisted in Atlas.

### HuggingFace API Error
```
HTTPError: 401 Unauthorized
```
**Fix:** Check your HF_TOKEN in `.env`. Get one from https://huggingface.co/settings/tokens

### Groq API Error
```
AuthenticationError
```
**Fix:** Check your GROQ_API_KEY. Get one from https://console.groq.com/keys

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Fix:** Use a different port:
```bash
uvicorn src.main:app --reload --port 8001
```

## Next Steps

1. ✅ Backend is working
2. ⏭️ Test with your PDF files from tutorial-3
3. ⏭️ Create frontend (Next.js 16)
4. ⏭️ Integrate Clerk auth
5. ⏭️ Configure SMTP if you need email reminders

## Using Tutorial-3 Code

This backend uses your working code from `tutorial-3-mongodb`:

- **PDF Processing:** `services/document_service.py` uses `PDFReader` from `pdf_rag_simple.py`
- **MongoDB RAG:** `services/document_service.py` uses vector search from `demo_retrieval_methods.py`
- **Quiz Generation:** `services/quiz_service.py` uses Groq like your tutorials

To process a PDF:

```python
from services.document_service import document_service

# Load PDF (from tutorial-3)
documents = document_service.process_pdf_simple("../tutorial-3-mongodb/data/threejs_tutorial.pdf")

# Create vector index
index = document_service.create_vector_index(documents)

# Search
results = document_service.search_documents("What is Three.js?")
```

## Production Deployment

For deployment on Railway/Render:

1. Add environment variables in platform dashboard
2. Update `BACKEND_URL` in `.env`
3. Deploy!

The backend is production-ready! 🚀
