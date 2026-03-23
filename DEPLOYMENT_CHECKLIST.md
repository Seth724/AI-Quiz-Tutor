# Quiz Tutor - Quick Deployment Checklist

## ✅ What We Fixed

### 1. Missing Dependencies (NOW ADDED TO requirements.txt)
- ✅ `numpy` - Critical for OCR/PIL operations
- ✅ `anthropic` - Claude vision models
- ✅ `torch` - PyTorch for local BLIP
- ✅ `transformers` - Hugging Face transformers for BLIP

❌ **If you deploy without these, features will break:**
- PDF uploads → Will crash
- Image analysis → Will fail
- Quiz generation → May timeout

### 2. PWA Fixes (Already Applied)
- ✅ Added `id: "/"` to manifest
- ✅ Added screenshot files for both desktop (wide) and mobile
- ✅ Added `display_override` for window controls overlay
- ✅ Added `protocol_handlers` for custom URL schemes
- ✅ Fixed time display to always use Asia/Colombo timezone

### 3. Timeout Issues (Already Fixed)
- ✅ Frontend no longer cancels long API calls at 120000ms
- ✅ Backend chat has 45-sec LLM timeout with grounded fallback
- ✅ Quiz generation no longer times out on clients

---

## 📋 Deployment Checklist

### Before You Deploy

- [ ] Verify requirements.txt has all 4 new packages:
  ```bash
  grep -E "numpy|torch|transformers|anthropic" apps/backend/requirements.txt
  ```
  Should show 4 matches ✓

- [ ] You have API keys ready:
  - [ ] GROQ_API_KEY (free at groq.com)
  - [ ] HF_TOKEN (free at huggingface.co)
  - [ ] MONGODB_URI (free tier at mongodb.com/cloud/atlas)
  - [ ] (Optional) ANTHROPIC_API_KEY for Claude vision

- [ ] GitHub repo is ready:
  ```bash
  # In root folder (d:\MetaruneLabs\ai-quiz-tutor\quiz-tutor)
  git remote -v  # Should show your GitHub repo
  ```

### Step-by-Step Deployment

#### 1️⃣ Deploy Backend to Render (5 min setup, 10 min deploy)
1. Read: `DEPLOYMENT_GUIDE.md` → Section B
2. Create Render account
3. Connect GitHub repo
4. Set Root Directory: `apps/backend`
5. Add environment variables (see `.env.example`)
6. Deploy
7. Copy Render URL: `https://quiz-tutor-backend.onrender.com`

#### 2️⃣ Deploy Frontend to Vercel (5 min setup, 5 min deploy)
1. Read: `DEPLOYMENT_GUIDE.md` → Section C
2. Create Vercel account
3. Import GitHub repo
4. Set Root Directory: `apps/frontend`
5. Add environment variables
6. Deploy
7. Copy Vercel URL: `https://your-app.vercel.app`

#### 3️⃣ Connect Backend ↔ Frontend (2 min)
1. Update Render environment: add Vercel URL to `FRONTEND_ORIGINS`
2. Render auto-redeploys
3. Test in browser: upload document, generate quiz

#### 4️⃣ Verify PWA Works in Production (5 min)
1. Open `https://your-app.vercel.app` in Chrome
2. Run Lighthouse PWA audit (F12 → Lighthouse)
3. Should show all checks passing
4. Click install button, app should install

---

## 🚀 After Deployment

### Monitor Backend (Render)
- Dashboard → Service Logs
- Look for: `Uvicorn running on 0.0.0.0:10000`
- If errors: check environment variables match `.env.example`

### Monitor Frontend (Vercel)
- Dashboard → Deployments → View Logs
- Look for: `Ready in X seconds`
- If CORS errors: check backend `FRONTEND_ORIGINS`

### Test Key Features
- [ ] Upload PDF → processes without timeout
- [ ] Generate quiz → completes (may take 30-60 sec first time)
- [ ] Ask from PDF → gets grounded response
- [ ] Chat history → timestamps show Asia/Colombo time
- [ ] PWA installs and works offline

---

## ⚠️ Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "Build failed" on Render | Check `requirements.txt` has all packages |
| "CORS error" in browser | Update backend `FRONTEND_ORIGINS` to include Vercel URL |
| "First request slow" | Render free tier spins down after 15 min inactivity (upgrade to Starter if needed) |
| "Time showing wrong timezone" | It's actually correct (Asia/Colombo). Browser's system timezone differs but we override it in code |
| "Install button not showing" | Run Lighthouse PWA audit. If it passes, clear browser cache and Unregister service worker |
| "Files disappear after redeploy" | Use Supabase storage for production (Render's filesystem is ephemeral) |

---

## 📞 Need Help?

1. **Render issues?** → https://render.com/docs
2. **Vercel issues?** → https://vercel.com/docs
3. **MongoDB issues?** → https://docs.atlas.mongodb.com
4. **Code issues?** → Check `PWA_VERIFICATION_GUIDE.md` and `DEPLOYMENT_GUIDE.md`

---

## 💾 File References

All guides are in the root folder:

- `DEPLOYMENT_GUIDE.md` - Full deployment walkthrough
- `PWA_VERIFICATION_GUIDE.md` - How to test PWA locally and on production
- `apps/backend/.env.example` - All environment variables explained
- `apps/backend/requirements.txt` - Now has all required packages

---

## 🎯 Timeline

- **Total setup time:** ~30 minutes
- **Deployment time:** ~30 minutes
- **Total:** About 1 hour to go from local → production

---

**You're ready to deploy! Start with `DEPLOYMENT_GUIDE.md` Section B.**

