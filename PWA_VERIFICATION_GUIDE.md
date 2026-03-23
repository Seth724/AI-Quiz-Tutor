# PWA Verification Checklist

## 1. Test PWA Locally (Before Deployment)

### Step 1: Run app locally
```bash
# Terminal 1: Backend
cd apps/backend
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd apps/frontend
npm run dev  # Should run on http://localhost:3000 or http://localhost:3001
```

### Step 2: Open Chrome DevTools (Lighthouse)
1. Open your app in **Chrome**: `http://localhost:3001`
2. Press `F12` to open DevTools
3. Click **Lighthouse** tab (or use `Ctrl+Shift+J` → Application)
4. Click **Analyze page load** → choose **PWA**
5. It should show:
   ✅ Installable badge
   ✅ Screenshots (both wide and mobile)
   ✅ App ID set to /
   ✅ Protocol handlers registered

### Step 3: Check Service Worker Registration
1. In DevTools, go to **Application** tab
2. Click **Service Workers** in left sidebar
3. Should show: `(registered)`
4. If grayed out or says "(activated, running)", that's perfect

### Step 4: Check Manifest
1. In DevTools Application tab, click **Manifest**
2. Verify you see:
   ```json
   {
     "id": "/",
     "name": "Quiz Tutor",
     "screenshots": [ { "form_factor": "wide", ... }, { ... (no form_factor, mobile) } ],
     "display_override": ["window-controls-overlay", "standalone"]
   }
   ```

### Step 5: Check Install Button
1. In Chrome address bar, you should see an **install icon▼** next to URL
2. Click it → should show "Install Quiz Tutor"
3. Click **Install** → app opens in standalone window (no browser UI)
4. Verify app is listed in Windows Start Menu

### Step 6: Test Offline Mode
1. In DevTools, go to **Network** tab
2. Check **Offline** checkbox
3. Reload page → should still load (cached assets)
4. Click to different pages → should work offline
5. Try clicking Quiz/Chat → will say "offline" for API calls (expected)

---

## 2. Quick Verification Commands

### Check manifest.json is valid JSON:
```powershell
$manifest = Get-Content "apps/frontend/public/manifest.webmanifest" | ConvertFrom-Json
Write-Host "✅ Manifest is valid JSON"
Write-Host "App ID: $($manifest.id)"
Write-Host "Screenshots: $($manifest.screenshots.Length)"
```

### Check service worker file exists:
```bash
ls -la apps/frontend/public/sw.js
```

### Check icons exist:
```bash
ls -la apps/frontend/public/icons/
```

---

## 3. Common PWA Issues & Fixes

### ❌ "Install button not showing"
- Clear browser cache (`Ctrl+Shift+Delete`)
- Unregister service worker (DevTools → Application → Service Workers → Unregister)
- Hard refresh (`Ctrl+Shift+R`)

### ❌ "Screenshots showing as blank"
- Verify screenshot files in `public/screenshots/` are not empty
- Check manifest `sizes` and `src` match actual file dimensions

### ❌ "Service worker not registering"
- Check `_document.tsx` or `_app.tsx` has service worker registration:
  ```tsx
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
    }
  }, [])
  ```

### ❌ "Manifest says id not specified"
- Verify manifest has `"id": "/"` (we added this)

---

## 4. Test After Deployment to Vercel

### Step 1: Deploy frontend first (see DEPLOYMENT_GUIDE.md)

### Step 2: Visit your Vercel URL in Chrome
```
https://your-app.vercel.app
```

### Step 3: Run Lighthouse again
- Should show all PWA criteria passing
- Install button should work in production

### Step 4: Test install & offline
- Click install → should appear on home screen
- Turn off internet → app still loads cached pages

### Step 5: Check manifest on production
```bash
curl https://your-app.vercel.app/manifest.webmanifest | jq '.'
```

Should show valid JSON with `id`, `screenshots`, `display_override`.

---

## 5. Time Zone Display Check (Fixed)

### Before: Time was showing in browser timezone
### After: All times now show in Asia/Colombo (Sri Lankan time)

**Test this:**
1. Open Chat page
2. Check timestamps on messages → should show Sri Lankan time
3. Open Quiz history → should show Sri Lankan time
4. Open Planner calendar → month header should use Sri Lankan timezone

If times still show wrong timezone after deployment, environment's system timezone may differ. Each browser will always convert to Asia/Colombo using `toLocaleString(..., { timeZone: 'Asia/Colombo' })`.

