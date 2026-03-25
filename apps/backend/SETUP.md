# Backend Setup & Deployment Guide

Complete setup guide for local development and production deployment on VPS.

---

## 🏠 LOCAL DEVELOPMENT SETUP

### Prerequisites
- Python 3.11+
- Free API keys (see Step 3)

### Step 1: Create Virtual Environment

```bash
cd apps/backend
python -m venv venv
```

### Step 2: Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 3: Get Free API Keys

1. **Groq** (LLM)
   - https://console.groq.com/keys
   - Copy key (starts with `gsk_`)

2. **HuggingFace** (Embeddings)
   - https://huggingface.co/settings/tokens
   - Create token

3. **MongoDB** (Database)
   - https://cloud.mongodb.com
   - Create free cluster (M0)
   - Copy connection string

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Includes:
- FastAPI + Uvicorn (web server)
- MongoDB drivers
- LlamaIndex (RAG)
- Docling + EasyOCR (document processing)
- Groq (LLM)
- HuggingFace (embeddings)

### Step 5: Configure Environment

```bash
copy .env.example .env  # Windows
# or
cp .env.example .env  # macOS/Linux
```

**Edit `.env`:**

```env
# Required
GROQ_API_KEY=gsk_your_key_here
HF_TOKEN=hf_your_token
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/quiz_tutor?retryWrites=true&w=majority
MONGODB_DATABASE=quiz_tutor

# Optional
ENVIRONMENT=development
FRONTEND_ORIGINS=http://localhost:3000
```

### Step 6: Test Backend

```bash
python test_backend.py
```

Expected output:
```
============================================================
Testing AI Quiz Tutor Backend
============================================================

[Test 1] Checking configuration... ✅ OK
[Test 2] Testing MongoDB connection... ✅ OK
[Test 3] Testing HuggingFace embedding... ✅ OK
[Test 4] Testing Groq LLM... ✅ OK
[Test 5] Testing quiz generation... ✅ OK

============================================================
✅ All systems working!
```

### Step 7: Run Development Server

```bash
python src/main.py
```

Server runs at: `http://localhost:8000`

**Test in browser:**
- Health check: http://localhost:8000/
- API docs: http://localhost:8000/docs
- Try endpoints in Swagger UI

### Step 8: Test Full Flow

1. In API docs, try uploading a PDF:
   ```
   POST /api/documents/upload
   ```

2. Check status:
   ```
   GET /api/documents/{id}/status
   ```

3. Generate quiz:
   ```
   POST /api/quizzes/generate
   ```

4. Chat about document:
   ```
   POST /api/chat
   ```

---

## 🌍 PRODUCTION DEPLOYMENT (VPS)

### Target Environment

- **OS:** Ubuntu 22.04 (DigitalOcean / Linode)
- **Cost:** $12/month basic VPS
- **Specs:** 1 vCPU, 1.5GB RAM, 25GB SSD
- **Capacity:** ~100-200 concurrent users

### Architecture

```
├─ Your Domain (yourdomain.com)
│  └─ DNS A Record → VPS IP
│
├─ VPS (Ubuntu 22.04)
│  ├─ Docker Engine
│  ├─ Docker Compose
│  ├─ Nginx (reverse proxy + SSL)
│  │  ├─ Port 80 (HTTP → HTTPS redirect)
│  │  └─ Port 443 (HTTPS → backend:8000)
│  │
│  └─ Backend Container
│     ├─ FastAPI (Uvicorn)
│     ├─ Gunicorn (1 worker)
│     └─ Python services
│
├─ Database (MongoDB Atlas cloud)
├─ Storage (Supabase cloud, optional)
└─ SSL (Let's Encrypt, auto-renewed)
```

### Prerequisites

- VPS with root access (DigitalOcean / Linode)
- Domain name pointing to VPS IP
- GitHub repository with code pushed
- API keys (same as local)

### Part 1: VPS Setup (First Time Only)

Connect via SSH:
```bash
ssh root@YOUR_VPS_IP
```

**Update system packages:**
```bash
sudo apt update
sudo apt upgrade -y
```

**Install Docker:**
```bash
sudo apt install -y docker.io docker-compose git wget curl
sudo systemctl start docker
sudo systemctl enable docker
```

**Add user to docker group** (avoid typing `sudo`):
```bash
sudo usermod -aG docker $USER
exit  # Log out and back in for changes to take effect
ssh root@YOUR_VPS_IP
```

### Part 2: Clone Repository

```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/ai-quiz-tutor
cd ai-quiz-tutor
```

### Part 3: Create Production Environment File

```bash
cat > .env.backend << 'EOF'
# API Keys
GROQ_API_KEY=gsk_your_key_here
HF_TOKEN=hf_your_token
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/quiz_tutor?retryWrites=true&w=majority

# Settings
ENVIRONMENT=production
MONGODB_DATABASE=quiz_tutor
FRONTEND_ORIGINS=https://yourdomain.com

# OCR Memory Tuning (1.5GB RAM constraint)
OCR_PDF_DPI=150
OCR_MAX_IMAGE_DIM=1400

# Docling Settings
DOCLING_BATCH_TIMEOUT_SECONDS=120
DOCLING_PROGRESS_HEARTBEAT_SECONDS=10

# Processing
PROCESSING_TIMEOUT_MINUTES=20
EOF
```

### Part 4: Setup Swap (Prevents OOM)

Add 4GB swap to prevent "Worker SIGKILL":

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h  # Should show 4G swap
```

### Part 5: Build and Start Backend

```bash
# Build Docker image (takes 2-3 min, loads Docling + models)
docker build -t quiz-tutor-backend -f apps/backend/Dockerfile apps/backend

# Start with docker-compose
docker compose --env-file .env.backend -f deploy/docker-compose.prod.yml up -d

# Watch startup logs
docker logs -f quiz-tutor-backend
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Part 6: Setup HTTPS with Nginx

**Copy Nginx config:**
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/quiz-tutor
sudo ln -s /etc/nginx/sites-available/quiz-tutor /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

**Test Nginx:**
```bash
sudo nginx -t  # Should say "syntax is ok"
```

**Allow firewall ports:**
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**Get SSL certificate:**
```bash
# First, point your domain DNS A record to VPS IP
# Then run (replace yourdomain.com with your actual domain):
sudo certbot certonly --standalone -d api.yourdomain.com -d yourdomain.com

# Update Nginx config to use certificate
# (See deploy/nginx.conf for SSL paths)
```

**Start Nginx:**
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Part 7: Verify It Works

**Test backend directly:**
```bash
curl http://localhost:8000/  # From VPS
```

**Test via Nginx:**
```bash
curl http://YOUR_VPS_IP/    # HTTP (should redirect to HTTPS)
```

**Test from internet:**
```bash
# From your local machine:
curl -k https://api.yourdomain.com/  # Should see API response
```

**Visit in browser:**
```
https://api.yourdomain.com/docs
```

### Part 8: Setup Auto-Renewal

```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
sudo certbot renew --dry-run  # Test renewal
```

---

## 🔧 Memory Tuning (Important for 1.5GB VPS)

The default 1.5GB can run out of memory when processing large PDFs:

### Problem
```
[ERROR] Worker (pid:95) was sent SIGKILL! Perhaps out of memory?
```

### Root Cause
- Docling model: ~200MB
- EasyOCR model: ~300MB  
- PDF buffers: 400-500MB
- Total needed: 900MB-1GB
- Available: Only 1.5GB (OS takes ~300MB)

### Solution

**A. Add Swap** (already done above):
```bash
sudo swapon -s  # Verify swap is active
```

**B. Reduce OCR Memory Footprint:**

In `.env.backend`:
```env
OCR_PDF_DPI=150              # Was 170, saves ~30% RAM
OCR_MAX_IMAGE_DIM=1400       # Was 1800, saves ~30% RAM
DOCLING_BATCH_TIMEOUT_SECONDS=120  # Prevents hang
```

**C. Gunicorn Single Worker:**

Already set in Dockerfile:
```dockerfile
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", ...]
```

Only 1 worker = only 1 OCR model loaded at a time.

### Result

With all three tunings:
- Can process PDFs up to **100-150MB** without crashing
- Processing takes **30-120 seconds** per PDF (varies by size)
- Multiple concurrent uploads → Queued, one at a time

---

## 📊 Monitoring Production

### Check Backend is Running

```bash
# Is container running?
docker ps | grep quiz-tutor-backend

# View logs (last 50 lines)
docker logs quiz-tutor-backend | tail -50

# Stream logs (live)
docker logs -f quiz-tutor-backend

# Search for errors
docker logs quiz-tutor-backend 2>&1 | grep ERROR

# Monitor memory
docker stats quiz-tutor-backend
```

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `SIGKILL in logs` | Out of memory | Swap is working; PDF too large or slow uploads |
| `Connection refused` | Backend crashed | Check logs, restart: `docker restart quiz-tutor-backend` |
| `SSL certificate error` | Cert expired | Renew: `sudo certbot renew` |
| `502 Bad Gateway` | Backend slow | Check memory: `docker stats` |
| `Cannot connect at all` | DNS not updated | Check: `nslookup api.yourdomain.com` |

### Restart Backend

```bash
# Soft restart (keep data)
docker restart quiz-tutor-backend

# Full restart (rebuild)
docker-compose --env-file .env.backend -f deploy/docker-compose.prod.yml down
docker-compose --env-file .env.backend -f deploy/docker-compose.prod.yml up -d
```

### View Performance

```bash
# CPU and memory
docker stats quiz-tutor-backend --no-stream

# Network (if supported)
docker exec quiz-tutor-backend ps aux

# Disk usage
du -sh /opt/ai-quiz-tutor
```

---

## 🔐 Backup & Recovery

### Database Backup

MongoDB Atlas auto-backs up free tier (M0):
- Automatic daily snapshots
- 7-day retention
- Recoverable via Atlas dashboard

### Manual Backup

```bash
# Export collection
docker exec -it quiz-tutor-backend mongodump --uri="$MONGODB_URI" --out=/backup
```

### Logs Archive

```bash
# Save Docker logs
docker logs quiz-tutor-backend > backend_logs_$(date +%Y%m%d).txt

# View old logs
docker logs quiz-tutor-backend -n 1000  # Last 1000 lines
```

---

## 🚀 Scaling

### If VPS Hits Memory Limit

Option 1: **Resize VPS**
```bash
# Upgrade to $24/mo (4GB RAM) on DigitalOcean
# Re-deploy backend (no code changes needed)
```

Option 2: **Multiple VPS + Load Balancer**
```bash
# Deploy on 2+ backend instances
# API Gateway or HAProxy to distribute requests
# More complex but handles more users
```

### If Database Hits V Size Limit

Option 1: **Upgrade MongoDB**
```bash
# Atlas M0 → M2 tier ($57/mo)
# Or switch to: AWS DocumentDB / Azure Cosmos
```

Option 2: **Archive Old Data**
```bash
# Export vectors older than 6 months
# Keep recent data in Atlas
```

---

## ✅ Deployment Checklist

- [ ] VPS provisioned and accessible via SSH
- [ ] Docker and docker-compose installed
- [ ] Repository cloned to `/opt/ai-quiz-tutor`
- [ ] `.env.backend` created with API keys
- [ ] Swap partition created (4GB)
- [ ] Backend Docker image built
- [ ] Backend started with `docker-compose`
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate obtained via certbot
- [ ] Firewall rules allow ports 80, 443
- [ ] Domain DNS points to VPS
- [ ] API accessible at `https://api.yourdomain.com/docs`
- [ ] Test upload PDF → see processing → completion
- [ ] Frontend .env configured with backend API URL
- [ ] Frontend deployed to Vercel
- [ ] End-to-end test: Frontend → Backend → Database

---

## 📞 Support

For issues:
1. Check logs: `docker logs -f quiz-tutor-backend`
2. See troubleshooting sections above
3. Verify env vars: `docker exec quiz-tutor-backend env | grep GROQ`
4. Test connectivity: `curl https://api.yourdomain.com/`
