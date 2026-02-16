# HoloLearn Frontend Context

## Project Description
HoloLearn is an AI-driven adaptive holographic learning assistant for personalized bilingual education.

## Features
- Chat interface with AI (sends to FastAPI backend at localhost:8000)
- Voice input using Web Speech API (with Wav2Vec2 backend fallback)
- Document upload (PDF, DOCX, images) for RAG-based learning
- 3D holographic avatar using Three.js that animates when speaking
- Bilingual support (English + Hindi and other Indian languages)
- Quiz generation and grading
- Student dashboard with performance charts
- Personalized recommendations

## Tech Stack
- React 19 with Vite
- Tailwind CSS v4 (using @tailwindcss/vite plugin)
- Three.js with @react-three/fiber and @react-three/drei
- Chart.js with react-chartjs-2
- Axios for API calls
- Lucide React for icons
- React Dropzone for file uploads
- React Markdown for rendering responses

## Design Style
- Dark futuristic theme (dark blues, purples)
- Glassmorphism effects (backdrop-blur, semi-transparent backgrounds)
- Holographic accents (cyan #00d4ff, purple #8b5cf6, pink #ec4899)
- Smooth animations and transitions
- Professional, modern UI with good spacing

## Backend API Endpoints (FastAPI at http://localhost:8000)
- POST /chat/send - Send message, get AI response
- POST /documents/upload - Upload document (multipart form)
- GET /documents/list/{student_id} - List documents
- DELETE /documents/{document_id} - Delete document
- POST /speech/transcribe - Transcribe audio
- GET /profile/{student_id} - Get student profile
- POST /profile/create - Create student
- PUT /profile/{student_id} - Update profile
- GET /profile/{student_id}/statistics - Get stats
- POST /quiz/generate - Generate quiz
- GET /quiz/{quiz_id} - Get quiz
- POST /quiz/submit - Submit quiz answers
- GET /quiz/history/{student_id} - Quiz history
- GET /dashboard/{student_id} - Dashboard data
- GET /dashboard/{student_id}/performance-chart - Chart data
