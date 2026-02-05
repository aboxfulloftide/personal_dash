# Personal Dash

A self-hosted, multi-user personal dashboard that aggregates various data sources into customizable widgets. Built with a plugin architecture for easy widget additions.

## Features

- Multi-user support with JWT authentication
- Drag-and-drop customizable widget grid
- Dark mode support
- Mobile responsive design
- Plugin/widget architecture for extensibility
- Remote server monitoring agent

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | MySQL |
| Auth | JWT with refresh tokens |

## Project Structure

```
personal-dash/
├── frontend/       # React application
├── backend/        # FastAPI application
├── agent/          # Server monitoring agent (deploys to remote servers)
├── docs/           # Documentation and project plan
└── tests/          # Test suites
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/aboxfulloftide/personal_dash.git
cd personal_dash
```

### 2. Set up MySQL

Create the database:

```sql
CREATE DATABASE personal_dash CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dash_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON personal_dash.* TO 'dash_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
DATABASE_URL=mysql+pymysql://dash_user:your_password@localhost:3306/personal_dash
SECRET_KEY=generate-a-random-secret-key
CORS_ORIGINS=["http://localhost:5173"]
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Run database migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/api/v1/openapi.json`.

### 4. Frontend

```bash
cd frontend
npm install
```

Create your environment file:

```bash
cp .env.example .env
```

The default `VITE_API_URL=http://localhost:8000/api/v1` should work for local development.

Start the dev server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 5. Server Monitoring Agent (optional)

The monitoring agent is a standalone Python script that runs on remote servers to collect system and Docker metrics. See [agent/README.md](agent/README.md) for deployment instructions.

## Available Widgets

| Widget | Description | Status |
|---|---|---|
| Server Monitor | CPU, memory, disk, Docker stats | In progress |
| Package Tracker | USPS, UPS, FedEx, Amazon tracking | Planned |
| Stock Ticker | Real-time stock prices | Planned |
| Crypto Prices | Cryptocurrency tracking | Planned |
| Weather | Current conditions and forecast | Planned |
| Fitness Stats | Body weight tracking | Planned |
| Calendar | Google Calendar integration | Planned |
| News Headlines | RSS/News API aggregation | Planned |
| Smart Home | Home Assistant integration | Planned |
| GitHub Activity | Repository stats and activity | Planned |

## Development

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

### Build for Production

```bash
cd frontend
npm run build
```

Static files will be output to `frontend/dist/` for serving via Nginx.
