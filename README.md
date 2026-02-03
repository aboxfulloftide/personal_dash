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
