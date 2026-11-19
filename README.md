# 🩺 RepoDoctor AI

An AI-powered GitHub repository health analyzer. Paste a GitHub URL, get a comprehensive health report with scored issues, security findings, and fix suggestions.

## Features

- 🔍 **Code Quality Analysis** — Detects anti-patterns, missing error handling, code smells
- 🔒 **Security Scanning** — Finds hardcoded secrets, API keys, vulnerable patterns
- 📦 **Dependency Analysis** — Checks for outdated packages and known vulnerabilities
- 🧪 **Test Coverage Assessment** — Evaluates test file coverage and patterns
- 📖 **Documentation Review** — Analyzes README completeness and inline docs
- 🏗️ **Architecture Review** — Evaluates folder structure and separation of concerns
- 📊 **Health Score** — Overall repository health score (0–100)

## Architecture

```
React Frontend (Vite + TypeScript + Tailwind)
         │
         ▼
    FastAPI Backend
         │
    ┌────┴────┐
    │         │
GitHub     AI Service
Service    (Gemini API)
    │         │
    ▼         ▼
 Clone &   Multi-pass
 Scan      Analysis
    │         │
    └────┬────┘
         ▼
    PostgreSQL
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| AI | Google Gemini API |
| Database | PostgreSQL |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Git
- Gemini API Key ([Get one free](https://aistudio.google.com))

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key and database URL
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `backend/.env`:

```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/repodoctor
REPOS_DIR=./temp_repos
```

## Usage

1. Open http://localhost:5173
2. Paste a public GitHub repository URL
3. Click "Analyze Repository"
4. View your health report with categorized issues

## License

MIT
