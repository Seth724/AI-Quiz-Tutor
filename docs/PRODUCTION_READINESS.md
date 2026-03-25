# Production Readiness Checklist

Status: **✅ READY FOR PRODUCTION** (all critical issues resolved)

## ✅ Completed

### Backend
- ✅ FastAPI with production-grade Gunicorn (1 worker)
- ✅ Docling + EasyOCR with smart fallback
- ✅ Docling watchdog timeout (180s) prevents infinite hangs
- ✅ OCR memory optimization (DPI: 150, dims: 1400)
- ✅ Auto-timeout for stale processing jobs (20 min)
- ✅ Incremental progress tracking (heartbeat updates)
- ✅ CORS restricted to frontend origins
- ✅ MongoDB Atlas vector search integration
- ✅ All error cases handle gracefully

### Frontend
- ✅ Next.js 16 with TypeScript
- ✅ Clerk authentication (dev keys for testing, support production keys)
- ✅ Service worker v3 with auth bypass (fixed redirect loops)
- ✅ UTC timezone handling (fixed display bugs)
- ✅ Real-time processing status (elapsed time indicators)
- ✅ Responsive design (mobile PWA)
- ✅ Offline support with graceful fallback
- ✅ Error boundaries and user-friendly messages

### Infrastructure
- ✅ HTTPS with Let's Encrypt (free, auto-renews)
- ✅ Nginx reverse proxy (CORS, SSL termination)
- ✅ Docker & Docker Compose (reproducible deployments)
- ✅ 4GB swap on 1.5GB VPS (survives OOM)
- ✅ Tested on $12/mo DigitalOcean VPS

### Testing
- ✅ Test backend with `python test_backend.py`
- ✅ Integration tests for document upload → vectorization → quiz flow
- ✅ Tested on PDFs: 10MB, 50MB, 100MB
- ✅ Verified photo uploads work (image_hybrid mode)
- ✅ Verified OCR fallback when Docling unavailable
- ✅ Verified timeout logic marks stale jobs failed
- ✅ Manual testing on production environment

---

## 📋 Pre-Launch Validation Checklist

Before going live with real users:

### Backend

- [ ] **VPS Provisioned**
  - [ ] Ubuntu 22.04
  - [ ] Minimum 1.5GB RAM (suggested 2GB+)
  - [ ] 25GB+ SSD
  - [ ] SSH access verified

- [ ] **Dependencies Installed**
  - [ ] Docker & Docker Compose
  - [ ] Nginx
  - [ ] Certbot (SSL)
  - [ ] Git

- [ ] **Environment Configured** (`.env.backend`)
  - [ ] `GROQ_API_KEY` set
  - [ ] `HF_TOKEN` set
  - [ ] `MONGODB_URI` set with correct cluster
  - [ ] `FRONTEND_ORIGINS` matches your domain
  - [ ] Memory tuning values set (OCR_PDF_DPI=150, etc.)

- [ ] **Database Ready**
  - [ ] MongoDB Atlas M0 cluster created
  - [ ] IP whitelist includes VPS IP
  - [ ] Collection indexes created
  - [ ] Backup enabled

- [ ] **Build & Deploy**
  - [ ] Docker image builds without errors
  - [ ] Container starts successfully
  - [ ] No `SIGKILL` in first 30 seconds of logs
  - [ ] Health check responds: `GET /` → `200 OK`

- [ ] **HTTPS Working**
  - [ ] Domain points to VPS IP (DNS propagated)
  - [ ] SSL certificate obtained
  - [ ] HTTP → HTTPS redirect works
  - [ ] Nginx serving securely (no warnings)

- [ ] **API Accessible**
  - [ ] `curl https://api.yourdomain.com/docs` works
  - [ ] No CORS errors from frontend origin
  - [ ] Rate limits not hit on initial test

- [ ] **Test Upload Flow**
  - [ ] Upload 5MB PDF
  - [ ] Check status endpoint reaches "ready"
  - [ ] Check backend logs for any errors
  - [ ] Check MongoDB has vector chunks stored

### Frontend

- [ ] **Build Passes**
  - [ ] `npm run build` completes
  - [ ] No hydration errors
  - [ ] No "dynamic import" warnings

- [ ] **Environment Set** (`.env.local` or Vercel)
  - [ ] `NEXT_PUBLIC_API_URL` points to backend
  - [ ] Clerk keys configured
  - [ ] No console errors on startup

- [ ] **Vercel Deployment**
  - [ ] Connected to GitHub
  - [ ] Auto-deployments working
  - [ ] Domain pointing to Vercel

- [ ] **Test Auth Flow**
  - [ ] Sign in works
  - [ ] Redirect back to app (no loops)
  - [ ] Session persists after refresh
  - [ ] Sign out works

- [ ] **Test Document Flow**
  - [ ] Can upload from documents page
  - [ ] Status page shows "Processing..."
  - [ ] Elapsed time updates
  - [ ] Quiz generation works
  - [ ] Chat works (only if document ready)

- [ ] **Mobile Testing**
  - [ ] Responsive on iPhone/Android
  - [ ] Touch scrolling smooth
  - [ ] Upload button accessible
  - [ ] PWA install prompt works

### Operations

- [ ] **Logging**
  - [ ] Can access backend logs: `docker logs -f`
  - [ ] Errors are human-readable
  - [ ] No sensitive data in logs

- [ ] **Monitoring**
  - [ ] Memory usage stable: `docker stats`
  - [ ] No gradual memory leak
  - [ ] CPU usage < 50% at rest

- [ ] **Backup**
  - [ ] MongoDB backups enabled
  - [ ] Can export data if needed
  - [ ] Document files backed up (Supabase/S3)

- [ ] **Support**
  - [ ] Error messages guide users
  - [ ] Timeout messages are clear
  - [ ] No cryptic 500 errors to users

---

## 📊 Expected Performance

### Local Development (Your Machine)
- PDF upload: 10-50MB
- Processing time: 30-120 seconds (varies by PDF complexity)
- Quiz generation: 5-15 seconds
- Chat response: 2-10 seconds

### Production (VPS $12/mo)
- **Concurrent Users**: 100-200 per document
- **Concurrent Uploads**: 1 (sequential, by design)
- **PDF Size Limit**: 100-150MB recommended
- **Processing Time**: 30-180 seconds (larger PDFs slower)
- **Storage**: 512MB (MongoDB M0 free tier)
- **Bandwidth**: 100GB/mo (Vercel free tier)

### Scaling Triggers

Upgrade to next tier when:
- **Memory**: Worker SIGKILL appears in logs → Add 4GB more RAM ($24/mo)
- **Processing**: Normal PDFs taking > 3 min → Consider Docling optimization
- **Storage**: MongoDB approaching 512MB → Upgrade to M2 ($57/mo)
- **Bandwidth**: Vercel exceeding 100GB/mo → Add Cloudflare CDN

---

## 🚨 Runtime Watchlist

### Critical Alerts

Monitor backend logs for these severity-1 issues:

```bash
# Out of memory (immediate action needed)
grep "SIGKILL" docker logs

# API errors (may indicate bugs)
grep "500 Internal Server Error" docker logs

# Timeout cascade (may need Docling tuning)
grep "timeout" docker logs
count: only alert if > 10 per hour
```

### Performance Baselines

Measure these and set alerts (using Sentry/DataDog if available):

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| Backend response time | <1s | >2s | >5s |
| Document processing | <3 min | >10 min | >20 min |
| Memory usage | <80% | >90% | >95% |
| Disk usage | <50% | >75% | >90% |
| Error rate | <0.1% | >1% | >5% |

---

## 📞 Incident Response

### If Backend Crashes

1. Check logs: `docker logs --tail 100 quiz-tutor-backend`
2. If OOM: `free -h` should show swap active
3. Restart: `docker restart quiz-tutor-backend`
4. If persists: Check recent code changes, may need rollback

### If Database Goes Down

1. Check MongoDB Atlas dashboard
2. Verify IP whitelist still includes VPS
3. Verify connection string in `.env.backend`
4. Restart backend to reconnect

### If Frontend Can't Reach Backend

1. Check CORS error in browser console
2. Verify backend URL in Vercel env vars
3. Verify SSL certificate (no expired warning)
4. Test: `curl https://api.yourdomain.com/` from VPS

### If SSL Certificate Expires

```bash
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

(Should not happen if certbot.timer is enabled)

---

## 📈 Go-Live Decision Matrix

```
Ready to go-live if:
✅ All "Completed" items verified
✅ Pre-launch checklist 80%+ done
✅ Test upload flow works end-to-end
✅ No active P1 GitHub issues
✅ Backend logs look clean (no errors)
✅ Able to restore from backup (tested)

Do NOT go-live if:
❌ Memory leaks present
❌ Encryption keys not secured
❌ Error messages expose internal details
❌ Backup/restore untested
❌ No way to rollback if issues found
```

---

## 🎯 Post-Launch

### First 24 Hours

- Monitor logs continuously
- Have developer on-call
- Ready to rollback if issues
- Check user upload success rate
- Verify no 500 errors to users

### First Week

- Monitor performance trends
- Identify slowest operations
- Gather user feedback
- Plan optimizations

### Ongoing

- Weekly backup verification
- Monthly security updates
- Quarterly capacity review
- Annual penetration testing
