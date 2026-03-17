# Dhurandar AI

A monorepo project with a **React + Vite + TypeScript** frontend and a **Python FastAPI** backend.

## Project Structure

```
dhurandar-ai/
├── frontend/          # React + Vite + TypeScript (Tailwind CSS, Anime.js, D3.js, Socket.IO)
├── backend/           # Python FastAPI (uvicorn, pandas, scikit-learn, langchain, InfluxDB)
├── docker-compose.yml
└── README.md
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- **OR** for local development:
  - Node.js 20+
  - Python 3.12+

## Quick Start (Docker)

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd dhurandar-ai
   ```

2. **Create the backend `.env` file**

   ```bash
   cp backend/.env.example backend/.env
   ```

   Edit `backend/.env` and fill in your actual values for:
   - `GEMINI_API_KEY`
   - `INFLUXDB_URL`
   - `INFLUXDB_TOKEN`

3. **Start both services**

   ```bash
   docker-compose up --build
   ```

4. **Access the apps**

   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then edit .env with real values

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on **http://localhost:3000** and proxies `/api` and `/ws` requests to the backend.

## Environment Variables

| Variable         | Description                        |
| ---------------- | ---------------------------------- |
| `GEMINI_API_KEY`  | Google Gemini API key              |
| `INFLUXDB_URL`    | InfluxDB connection URL            |
| `INFLUXDB_TOKEN`  | InfluxDB authentication token      |

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Anime.js (animations)
- D3.js (data visualization)
- Socket.IO Client (real-time communication)

### Backend
- FastAPI
- Uvicorn
- pandas & scikit-learn (data processing / ML)
- LangChain (LLM orchestration)
- InfluxDB Client (time-series data)
- python-socketio (WebSocket server)
