# Task 001: Project Setup — COMPLETED

## Objective
Initialize the monorepo structure with frontend and backend scaffolding, development environment configuration, and basic tooling.

## Prerequisites
- Node.js 18+ installed
- Python 3.10+ installed
- MySQL 8.0 installed and running
- Git installed

## Deliverables

### 1. Repository Structure
Create the following directory structure:
```
personal-dash/
├── frontend/
├── backend/
├── agent/
├── docs/
│   └── tasks/
├── .gitignore
└── README.md
```

### 2. Backend Setup (FastAPI)

#### Initialize Python environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv pydantic-settings alembic
pip freeze > requirements.txt
```

#### Create basic structure:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── models/
│   │   └── __init__.py
│   └── schemas/
│       └── __init__.py
├── alembic/
├── tests/
│   └── __init__.py
├── requirements.txt
├── .env.example
└── alembic.ini
```

#### app/main.py:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="Personal Dash API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

#### app/core/config.py:
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Dash"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 28

    class Config:
        env_file = ".env"

settings = Settings()
```

#### app/api/v1/router.py:
```python
from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/")
def root():
    return {"message": "Personal Dash API v1"}
```

#### .env.example:
Check for .env file in the backend dir
```
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/personal_dash
SECRET_KEY=your-secret-key-here-change-in-production
CORS_ORIGINS=["http://localhost:5173"]
```

### 3. Frontend Setup (React + Vite)

#### Initialize React project:
```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install axios react-router-dom react-grid-layout tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### Create basic structure:
```
frontend/
├── src/
│   ├── components/
│   │   ├── common/
│   │   ├── layout/
│   │   ├── widgets/
│   │   └── auth/
│   ├── contexts/
│   ├── hooks/
│   ├── services/
│   │   └── api.js
│   ├── utils/
│   ├── styles/
│   │   └── index.css
│   ├── App.jsx
│   └── main.jsx
├── public/
├── package.json
├── vite.config.js
├── tailwind.config.js
└── .env.example
```

#### Configure Tailwind (tailwind.config.js):
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
}
```

#### src/styles/index.css:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

#### src/services/api.js:
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  withCredentials: true,
});

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token refresh (to be implemented in auth task)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    return Promise.reject(error);
  }
);

export default api;
```

#### src/App.jsx:
```jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Routes>
          <Route path="/" element={<div className="p-4 text-gray-900 dark:text-white">Personal Dash - Coming Soon</div>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
```

#### .env.example:
```
VITE_API_URL=http://localhost:8000/api/v1
```

### 4. Git Configuration

#### .gitignore (root level):
```
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.env
*.egg-info/
dist/
build/

# Node
node_modules/
frontend/dist/
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*

# Testing
.coverage
htmlcov/
.pytest_cache/

# Misc
*.bak
```

### 5. Database Setup

Create MySQL database:
```sql
CREATE DATABASE personal_dash CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'personaldash'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON personal_dash.* TO 'personaldash'@'localhost';
FLUSH PRIVILEGES;
```

Initialize Alembic:
```bash
cd backend
alembic init alembic
```

Update alembic/env.py to import your models and use the DATABASE_URL from config.

### 6. README.md (root level)
```markdown
# Personal Dash

A self-hosted, multi-user personal dashboard with customizable widgets.

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Documentation
See `/docs` for detailed documentation.
```

## Acceptance Criteria
- [ ] Backend starts with `uvicorn app.main:app --reload` on port 9000
- [ ] Frontend starts with `npm run dev` on port 5173
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] `/api/v1/` endpoint returns `{"message": "Personal Dash API v1"}`
- [ ] CORS allows frontend origin
- [ ] Tailwind CSS is working (test with a colored div)
- [ ] All files committed to git with proper .gitignore
- [ ] Alembic is initialized

## Estimated Time
2-3 hours

## Next Task
Task 002: Database Models & Migrations
