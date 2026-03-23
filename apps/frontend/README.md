# Quiz Tutor Frontend

Modern React-based frontend for the Quiz Tutor application. Built with **Next.js 16**, **TypeScript**, and **Tailwind CSS**.

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

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
# (Already configured in .env.local)

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

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

## 🔧 Configuration

### Environment Variables (`.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Update the API URL if your backend runs on a different port or host.

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
