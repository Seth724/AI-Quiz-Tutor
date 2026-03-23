# Deployment Guide: Render + Vercel + Connect

This guide walks you through deploying Quiz Tutor backend on Render and frontend on Vercel, then connecting them.

---

## Prerequisites Before You Start

- [ ] GitHub account
- [ ] Render account (free tier OK)
- [ ] Vercel account (free tier OK)
- [ ] MongoDB Atlas account (free tier OK)
- [ ] Groq API key (free at groq.com)
- [ ] HuggingFace token (free at huggingface.co)
- [ ] (Optional) Anthropic API key for Claude vision
- [ ] (Optional) Supabase account for document storage

---

## A. MongoDB Atlas Setup (Required)

### 1. Create MongoDB Atlas Account
1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up (free)
3. Create a new project called "Quiz Tutor"

### 2. Create Cluster
1. Click "Build a Database"
2. Select **M0 (Free Tier)** → Continue
3. Select provider: AWS → Region: **ap-southeast-1** (Singapore, closest to Sri Lanka)
4. Cluster name: `quiz-tutor-cluster`
5. Click "Create"

### 3. Create Database User
1. Wait for cluster to initialize (5-10 min)
2. Click "Security" → "Database Access"
3. Click "Add New Database User"
4. Username: `quiz-tutor-admin`
5. Password: Generate secure password (copy it)
6. Built-in Role: `Atlas Admin`
7. Click "Add User"

### 4. Get Connection String
1. Click "Database" → Your cluster
2. Click "Connect" → "Drivers"
3. Copy connection string:
   ```
   mongodb+srv://quiz-tutor-admin:<password>@quiz-tutor-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   Replace `<password>` with your password
4. Add `&appName=quiztutor` at the end

### 5. Allow Outbound Traffic
1. Security → "Network Access"
2. Click "Add IP Address"
3. Select "Allow Access from Anywhere" (0.0.0.0/0)
4. Click "Confirm"

---

## B. Deploy Backend to Render

### 1. Push Backend to GitHub
```bash
cd d:\MetaruneLabs\ai-quiz-tutor\quiz-tutor
git init
git add -A
git commit -m "Initial commit: Quiz Tutor app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/quiz-tutor.git
git push -u origin main
```

### 2. Create Render Account & Connect GitHub
1. Go to https://render.com
2. Sign up / log in
3. Click "Dashboard"
4. Click "New" → "Web Service"
5. Click "Connect Account" → authorize GitHub
6. Select your `quiz-tutor` repo

### 3. Configure Render Service
**Basic Info:**
- Name: `quiz-tutor-backend`
- Repository: Your repo
- Branch: `main`
- Root Directory: `apps/backend` ⚠️ IMPORTANT

**Environment:**
- Runtime: `Python 3.11`
- Build Command: 
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt
  ```
- Start Command: 
  ```bash
   gunicorn -w 1 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:$PORT --timeout 120
  ```

**Pricing Plan:**
- Select `Free` tier (OK for development/testing)
- Production: upgrade to Starter ($7/month)

### 4. Add Environment Variables to Render
Click "Environment" and add:

```
GROQ_API_KEY=your_groq_api_key_here
HF_TOKEN=your_huggingface_token_here
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/quiz_tutor?retryWrites=true&w=majority
MONGODB_DATABASE=quiz_tutor
ENVIRONMENT=production
LOG_LEVEL=INFO

# Frontend URL (update after Vercel deployment)
FRONTEND_ORIGINS=http://localhost:3000,http://localhost:3001,https://your-app.vercel.app
FRONTEND_ORIGIN_REGEX=https://.*\.vercel\.app

# Optional: Supabase (skip if using local file storage)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
SUPABASE_BUCKET=documents

# Optional: Anthropic (for Claude vision)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: Email notifications
# Leave these empty unless you enable reminder emails
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
```

Notes:
- Do not commit real credentials to Git.
- `HF_HOME`, `HF_HUB_CACHE`, and `SENTENCE_TRANSFORMERS_HOME` are optional local cache paths. Set them only if you want custom cache directories on your host.

### 5. Deploy
1. Click "Deploy"
2. Wait for build to complete (5-10 minutes)
3. Once deployed, copy your Render URL:
   ```
   https://quiz-tutor-backend.onrender.com
   ```
   (Your URL will be different)

**⚠️ Important:** First request to free Render app can take 30-60 seconds (spins up). No problem for testing.

---

## C. Deploy Frontend to Vercel

### 1. Prepare Frontend for Deployment

**Update API URL** in `apps/frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=https://quiz-tutor-backend.onrender.com
```

### 2. Connect GitHub to Vercel
1. Go to https://vercel.com
2. Sign up / log in
3. Click "Add New" → "Project"
4. Import your GitHub repo
5. Select the `quiz-tutor` repository
6. Click "Import"

### 3. Configure Vercel Deployment
**Root Directory:** `apps/frontend`

**Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://quiz-tutor-backend.onrender.com

# If using Clerk authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key_here
CLERK_SECRET_KEY=your_clerk_secret_here
```

### 4. Deploy
1. Click "Deploy"
2. Wait for deployment (2-5 minutes)
3. Once done, get your Vercel URL:
   ```
   https://your-app.vercel.app
   ```

---

## D. Connect Frontend ↔ Backend

### 1. Update Render Backend with Vercel URL

1. Go to **Render Dashboard** → Your `quiz-tutor-backend` service
2. Click "Environment"
3. Update `FRONTEND_ORIGINS`:
   ```
   http://localhost:3000,http://localhost:3001,https://your-app.vercel.app
   ```
4. Click "Save"
5. Render will auto-redeploy

### 2. Test Connection

**In your browser**, go to your Vercel URL:
```
https://your-app.vercel.app
```

**Upload a document:**
1. Click "Documents" tab
2. Upload a PDF/image
3. Should see success message

**Check backend logs** on Render:
1. Render Dashboard → your service → "Logs"
2. Should see:
   ```
   POST /api/documents/upload HTTP/1.1" 200 OK
   ```

---

## E. Verify PWA on Production

### 1. Open Chrome
```
https://your-app.vercel.app
```

### 2. Check Install Button
1. Look for install icon ⬇️ in address bar
2. Click → "Install Quiz Tutor"
3. App should install to Start Menu

### 3. Run Lighthouse PWA Audit
1. Press `F12` → Lighthouse
2. Click "Analyze page load"
3. Should show:
   ✅ Installable
   ✅ Screenshots working
   ✅ Protocol handlers
   ✅ Display override

---

## F. Troubleshooting Deployment

### ❌ "Backend not responding"
1. Check Render logs for errors
2. Verify MONGODB_URI and API keys are correct
3. Check MongoDB Atlas whitelist includes Render IPs (0.0.0.0/0)

### ❌ "Build failed on python-bidi / easyocr"
Cause: Render used Python 3.14, but OCR dependencies are more stable on Python 3.11.

Fix:
1. In Render service settings, set environment variable:
   - `PYTHON_VERSION=3.11.11`
2. Confirm runtime is Python in Render.
3. Clear build cache and redeploy.

Note: This repository also pins `PYTHON_VERSION` in `render.yaml`.

### ❌ "CORS errors in browser"
1. Update backend `FRONTEND_ORIGINS` to include Vercel URL
2. Render will auto-redeploy
3. Try again

### ❌ "Quiz generation times out"
- Free Render instances have limited CPU
- Docling PDF processing is slow on free tier
- Solution: Upgrade to Starter ($7/month) or use Render Pro

### ❌ "Service Worker not registering on production"
1. Clear Vercel cache:
   - Vercel Dashboard → Project → Settings → Deployment → Redeploy
   - Click "Redeploy"
2. Hard refresh browser (`Ctrl+Shift+R`)

### ❌ "Images/PDFs not uploading"
- If using Supabase: verify bucket permissions
- If using local storage: Render ephemeral filesystem deletes data on redeploy
- Solution: **Use Supabase storage** for production

### ❌ "Time zone still showing wrong"
- All timestamps already use Asia/Colombo
- If still wrong: check browser's system timezone
- Not a deployment issue

---

## G. Post-Deployment Checklist

- [ ] Backend running on Render (check logs)
- [ ] Frontend running on Vercel
- [ ] No CORS errors in browser console
- [ ] Can upload documents on production
- [ ] Can generate quizzes on production
- [ ] Can ask from PDF
- [ ] PWA installs and works offline
- [ ] Service worker registered
- [ ] Manifest loads correctly
- [ ] MongoDB has data from quiz attempts
- [ ] Time displays in Asia/Colombo timezone

---

## H. Important Notes for Future Use

### Render Free Tier Limitations
- Auto-spins down after 15 min inactivity
- First request takes 30-60 sec
- 50-100 concurrent connections max

**If you need always-on:** Upgrade to Starter ($7/month)

### Vercel Free Tier Limitations
- Edge functions limited
- 50 concurrent deployments max
- Plenty for production use

### Database Backups
- MongoDB Atlas: automatic daily backups
- Render doesn't backup files (ephemeral storage)
- Use Supabase or S3 for persistent file storage

### Cost Estimate (Monthly)
- MongoDB Atlas M0: FREE
- Render Starter (backend): $7
- Vercel Free (frontend): FREE
- Supabase Free (storage): FREE
- **Total: ~$7/month** (or free during development)

---

## I. Next Steps

1. **Testing in Production:**
   - Share your Vercel URL with users
   - Gather feedback on quiz quality, chat responsiveness
   - Monitor Render logs for errors

2. **Monitoring & Logging:**
   - Render: Built-in logs (free)
   - Add Sentry/LogRocket for advanced analytics (optional)

3. **Custom Domain (Optional):**
   - Vercel: Settings → Domains → Connect custom domain
   - Render: Settings → Custom Domains
   - Use Cloudflare for DNS (free)

4. **Auto-Scaling:**
   - Render: Upgrade to enable auto-scaling
   - Vercel: Already scales automatically

---

## Still Need Help?

**Render Docs:** https://render.com/docs
**Vercel Docs:** https://vercel.com/docs
**MongoDB Docs:** https://docs.atlas.mongodb.com

