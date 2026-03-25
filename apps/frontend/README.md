# Quiz Tutor Frontend

Modern React-based frontend for the Quiz Tutor application. Built with **Next.js 16**, **TypeScript**, **Tailwind CSS**, and **Clerk authentication**.

## ✅ What's Fixed

Recent production fixes verified:

1. **Auth Redirect Loops** → Service worker now bypasses Clerk auth routes
2. **Timezone Display** → Fixed UTC parsing on API responses
3. **Processing Status** → Real-time elapsed time indicators
4. **PWA Offline** → Service worker v3 with proper fallback
5. **Mobile UI** → Responsive design for all screen sizes

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Alert.tsx       # Alert notifications
│   ├── Button.tsx      # Reusable button component
│   ├── Card.tsx        # Card layout wrapper
│   ├── FileUpload.tsx  # File upload with drag-drop
│   ├── Loading.tsx     # Loading spinner
│   ├── QuestionCard.tsx # Quiz question display
│   └── index.ts        # Component exports
├── pages/              # Next.js pages
│   ├── _app.tsx       # Next app wrapper
│   ├── _document.tsx  # HTML document
│   └── index.tsx      # Home page (main quiz interface)
├── services/           # API services
│   └── api.ts         # Backend API client
├── types/              # TypeScript types
│   └── api.ts         # API response types
├── utils/              # Utility functions
│   └── helpers.ts     # Helper functions
└── globals.css         # Global styles

```

## 🚀 Quick Start (Local)

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend running at http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Test Full Flow

1. Sign in with Clerk (dev keys pre-configured)
2. Upload a PDF from backend
3. Watch processing status update in real-time
4. Generate quiz from document
5. Take quiz
6. Chat about document

## 📋 Features

- Document-aware chat that only sends PDF questions when the selected document is `ready`
- Document cards showing pages, estimated tables, and chunks
- Lower-noise polling cadence for processing status updates

### Components

1. **Button** - Variant support (primary, secondary, success, error, warning), sizes, loading states
2. **Alert** - Success, error, warning, and info alerts with dismissable option
3. **FileUpload** - Drag-and-drop PDF file upload with validation
4. **Card** - Flexible container with optional title and subtitle
5. **QuestionCard** - Interactive multiple-choice question display with answer tracking
6. **Loading** - Animated loading spinner with message

### Pages

- **Home (/)** - Main interface for uploading documents and taking quizzes
  - Upload PDF documents
  - Generate quizzes with customizable parameters
  - Interactive quiz taking with instant feedback
  - Score calculation and performance display

### Services

- **API Service** - Handles all communication with the backend
  - Document upload
  - Quiz generation
  - Error handling and response parsing

## � Production Deployment (Vercel)

AI Quiz Tutor frontend is optimized for deployment on **Vercel** (free tier).

### Prerequisites

- GitHub account with repository pushed
- Vercel account (free signup at https://vercel.com)
- Backend deployed and accessible at a public URL (e.g., `https://api.yourdomain.com`)

### Deployment Steps

1. **Ensure code is pushed to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to: https://vercel.com
   - Sign in with GitHub
   - Click "Add New" → "Project"
   - Select `ai-quiz-tutor` repository

3. **Configure Project**
   - Root Directory: `apps/frontend` ✓ (Vercel auto-detects)
   - Framework: `Next.js` (auto-selected)
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

4. **Set Environment Variables**
   
   In Vercel dashboard, go to Settings → Environment Variables:
   
   ```
   NEXT_PUBLIC_API_URL = https://api.yourdomain.com
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = [your_clerk_key]
   ```

   (Get these from your `.env.local`)

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (~3 min)
   - Get your Vercel URL: `https://your-project.vercel.app`

### Custom Domain

1. **Point DNS to Vercel**
   - In Vercel Dashboard → Domains
   - Add your domain (e.g., `yourdomain.com`)
   - Follow DNS setup instructions
   - Usually: Create `CNAME` record or update `A` record

2. **Optional: WWW Subdomain**
   - Vercel auto-configures `www.yourdomain.com` → `yourdomain.com`

### Environment Variables for Production

Update in Vercel Dashboard (Settings → Environment Variables):

```env
# Backend API (must be HTTPS in production)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Clerk (usually same as local, but can use production keys)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
```

### Verify It Works

1. Visit your Vercel URL
2. Sign in with Clerk
3. Check backend connectivity in browser console (no CORS errors)
4. Upload a document
5. Verify it appears in document list

### CI/CD (Automatic Deployments)

Enabled by default:
- **Push to main** → Auto-triggers build on Vercel
- **Pull Requests** → Preview deployment (temporary URL)
- **Rollback**: Vercel keeps 5 previous deployments

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `CORS error` (browser console) | Backend URL wrong | Check `NEXT_PUBLIC_API_URL` in Vercel env vars |
| `Cannot sign in` | Clerk keys wrong | Verify Clerk publishable key in Vercel env vars |
| `404 on pages` | Build failed | Check Vercel build logs for errors |
| `Slow page load` | API slow | Check backend performance; may need async optimization |
| `Static export error` | Dynamic route issue | Ensure routes are properly configured |

### Performance Tips

- Images: Vercel auto-compresses
- CSS: TailwindCSS already optimized
- JavaScript: Next.js auto-code-splits
- Caching: Vercel auto-caches static assets

### Monitoring

In Vercel Dashboard:
- **Deployments** → See all versions
- **Logs** → Real-time logs
- **Analytics** → Performance metrics
- **Settings** → Update env vars anytime

### Redeploy Without Code Changes

In Vercel Dashboard:
1. Go to Deployments
2. Click "..." on recent deployment
3. Select "Redeploy"

(Useful if you only changed backend API)

## 📦 Dependencies

- **next**: ^16.0.0
- **react**: ^18.3.1
- **react-dom**: ^18.3.1
- **axios**: ^1.6.0
- **tailwindcss**: ^3.4.0
- **typescript**: ^5.3.0

## 🎨 Styling

Uses **Tailwind CSS** for styling. Configured in `tailwind.config.ts` with custom color palette:
- Primary: Blue (#3b82f6)
- Secondary: Purple (#8b5cf6)
- Success: Green (#10b981)
- Warning: Yellow (#f59e0b)
- Error: Red (#ef4444)

## 📝 API Integration

The app communicates with the backend API at `http://localhost:8000`:

### Endpoints

- `POST /api/documents/upload` - Upload PDF document
- `POST /api/quizzes/generate` - Generate quiz from document
- `GET /api/documents` - List uploaded documents

See `src/services/api.ts` for detailed API client implementation.

## 🧪 Development

### Code Organization

- **Components**: Keep components small and focused on a single responsibility
- **Services**: All API calls go through the API service
- **Types**: Use TypeScript types for all data structures
- **Utils**: Pure utility functions with no side effects

### Type Safety

All API responses are typed using TypeScript interfaces defined in `src/types/api.ts`.

## 🚢 Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🔗 Related Projects

- Backend: `../backend` - FastAPI server with Groq LLM integration
- Docker setup: `../../docker-compose.yml`

## 📄 License

MIT License
