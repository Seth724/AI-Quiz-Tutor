# Verify App Works Locally BEFORE Deploying

Run these commands to ensure everything works on your machine first. This will catch any missing dependencies or configuration issues before you deploy to Render/Vercel.

---

## 1. Backend Verification (Python)

```bash
cd d:\MetaruneLabs\ai-quiz-tutor\quiz-tutor\apps\backend

# Check Python version
python --version
# Expected: Python 3.10+

# Check all dependencies installed
pip install -r requirements.txt

# Verify all imports work
python -c "
import fastapi
import pymongo
import groq
import llama_index
import easyocr
import numpy
import anthropic
import torch
import transformers
print('✅ All backend packages imported successfully!')
"

# Test backend starts
python -m uvicorn src.main:app --reload --port 8000
# Expected: "Uvicorn running on http://0.0.0.0:8000"
# Press Ctrl+C to stop
```

**✅ Success:** No import errors and Uvicorn starts

---

## 2. Frontend Verification (Node.js)

```bash
cd d:\MetaruneLabs\ai-quiz-tutor\quiz-tutor\apps\frontend

# Check Node version
node --version
npm --version
# Expected: Node 18+, npm 9+

# Install dependencies
npm install

# Check all packages
npm list --depth=0
# Should show: 
# - next@16.0.0
# - react@18.3.1
# - three@0.179.1
# - axios@1.6.0
# - @clerk/nextjs@6.22.0

# Verify PWA files exist
ls public/manifest.webmanifest
ls public/sw.js
ls public/icons/
echo "✅ PWA files present!"

# Test frontend builds
npm run build
# Expected: "Generated successfully in X sec"

# Start dev server (optional)
npm run dev
# Expected: "Ready in X seconds"
# Visit http://localhost:3001
```

**✅ Success:** Build completes and dev server starts

---

## 3. Verify .env File

```bash
# Backend
cat apps/backend/.env
# Should have at minimum:
# - GROQ_API_KEY=...
# - HF_TOKEN=...
# - MONGODB_URI=...

# If missing, copy from .env.example
cp apps/backend/.env.example apps/backend/.env
# Then edit with your actual values
```

**✅ Success:** `.env` exists and has required keys

---

## 4. Test Backend API

```bash
# In a new PowerShell terminal, with backend running (step 1):

# Test health check
curl http://localhost:8000/health
# Expected: 200 OK

# Test documents endpoint
curl -X GET "http://localhost:8000/api/documents?user_id=test-user"
# Expected: 200 OK with empty list or existing documents
```

**✅ Success:** API responds with 200 status

---

## 5. Test Full App Locally

**Terminal 1: Backend**
```bash
cd apps/backend
python -m uvicorn src.main:app --reload --port 8000
```

**Terminal 2: Frontend**
```bash
cd apps/frontend
npm run dev
```

**Terminal 3: Browser**
Open: `http://localhost:3001`

**Test these features:**
1. Click "Documents" → Upload a PDF
2. Wait for processing (may take 30-60 sec)
3. Click "Quiz" → Generate a quiz
4. Click "Chat" → Ask from PDF → "Summarize this document"
5. Check DevTools → Application → Service Workers → Should say "registered"
6. Check timestamps displayed → Should match Asia/Colombo time

**✅ Success:** All features work, no errors in console

---

## 6. Verify PWA Works Locally

```bash
# Backend and Frontend must both be running (from step 5)

# Open Chrome DevTools (F12)
Go to: Application → Manifest
Should show:
{
  "id": "/",
  "name": "Quiz Tutor",
  "screenshots": [
    { "form_factor": "wide", ... },
    { ... (no form_factor, mobile) }
  ]
}

# Go to: Application → Service Workers
Should show: "(registered)"

# Try installing:
Click chrome address bar install icon ⬇️
Click "Install Quiz Tutor"
App should open in standalone window
```

**✅ Success:** PWA installs and registers

---

## 7. Checklist Before Deployment

- [ ] `python --version` returns 3.10+
- [ ] All `pip install -r requirements.txt` packages install without errors
- [ ] Backend imports all packages successfully (step 2)
- [ ] `npm run build` completes without errors (step 2)
- [ ] No red X errors in browser console (step 5)
- [ ] Can upload document without "timeout" errors
- [ ] Can generate quiz successfully
- [ ] Can ask from PDF and get responses
- [ ] Service worker registers (step 6)
- [ ] PWA manifest is valid JSON (step 6)
- [ ] Install button appears in Chrome address bar (step 6)
- [ ] Timestamps display Asia/Colombo time

---

## 8. If Something Fails

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Try reinstalling requirements
pip uninstall -r requirements.txt -y
pip install --upgrade pip
pip install -r requirements.txt

# Check specific package
python -c "import torch"  # torch is the largest, often fails first
```

### Frontend won't build
```bash
# Clear cache
rm -r node_modules
rm package-lock.json

# Reinstall
npm install
npm run build
```

### MongoDB connection fails
- Check `MONGODB_URI` in `.env`
- Verify MongoDB Atlas cluster is running
- Check IP whitelist includes your machine's IP

### Service worker won't register
```bash
# Clear all site data
DevTools → Application → Storage → Clear site data
npm run dev  # Restart frontend
Hard refresh: Ctrl+Shift+R
Check DevTools again
```

---

## ✅ Ready to Deploy!

If all checks above pass, you're ready to deploy:

1. Push to GitHub
2. Follow `DEPLOYMENT_GUIDE.md`
3. Deploy backend to Render
4. Deploy frontend to Vercel
5. Connect them
6. Test on production

---

**Total local verification time: ~20 minutes**

###

