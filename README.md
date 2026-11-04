# 🛡️ Nightwatch — Autonomous AI On-Call Engineer

> **Nightwatch** is an autonomous AI on-call Site Reliability Engineer (SRE) that watches a startup's production services around the clock, discovers the root cause of an incident, and fixes or escalates it with human-in-the-loop approval gates.

---

## 📁 Monorepo Architecture

```
nightwatch/
├── backend/            # FastAPI, Python 3.12+, Pydantic v2, SQLite/Firestore
│   ├── app/
│   │   ├── api/        # Typed FastAPI route endpoints (Services, Incidents, Settings)
│   │   ├── core/       # Pydantic Settings config & Bearer/Tick authentication
│   │   ├── models/     # Domain Pydantic schemas and enums matching SRS data model
│   │   ├── storage/    # Abstract BaseRepository, SQLite engine & Firestore stub
│   │   ├── detectors/  # Health & log sweep detector stubs (Phase 2)
│   │   ├── agent/      # Gemini reasoning & diagnostic loop stubs (Phase 3)
│   │   ├── tools/      # Log, commit, rollback & GitHub tool stubs (Phase 3)
│   │   └── notifiers/  # Telegram and email alert stubs (Phase 3)
│   ├── tests/          # Pytest suite covering auth, services CRUD, incidents, kill switch
│   └── seed.py         # Database seeding script for sample services and incidents
├── frontend/           # React 18, Vite, TypeScript, React Router, Lucide Icons
│   ├── src/
│   │   ├── api/        # Typed API client with Bearer session auth
│   │   ├── context/    # Auth context managing dashboard session state
│   │   ├── components/ # Calm UI badges, status indicators, and Navbar
│   │   └── pages/      # Overview, War-Room with event timeline, Services CRUD, Login
├── sample-app/         # Target Cloud Run service placeholder (Next task)
├── scripts/
│   └── check_setup.py  # Environment credentials & connectivity tester (make check)
├── docs/               # Software Requirements Specification (SRS)
├── Makefile            # Development, test, and check automation targets
├── .env.example        # Environment variable template
└── .gitignore          # Repository exclusions (DB, node_modules, secrets, envs)
```

---

## ⚡ Quickstart

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 18+** & **npm**

### 2. Configure Environment Variables
Copy the template into `.env` at the repository root:
```bash
cp .env.example .env
```
Default configuration keys:
| Key | Description | Default |
| --- | --- | --- |
| `GEMINI_API_KEY` | Google AI Studio free API key | `(optional for check)` |
| `GEMINI_MODEL` | Gemini LLM model | `gemini-2.5-flash` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (repo scope) | `(optional for check)` |
| `GITHUB_REPO` | Monitored repository (`owner/repo`) | `(optional for check)` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token from `@BotFather` | `(optional for check)` |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for emergency alerts | `(optional for check)` |
| `DASHBOARD_PASSWORD` | Bearer token protecting dashboard API | `nightwatch-dev-secret` |
| `TICK_SECRET` | Secret protecting `/internal/tick` | `nightwatch-scheduler-tick-secret` |
| `STORAGE_BACKEND` | Storage persistence provider | `sqlite` |

---

## 🛠️ Commands & Automation

| Target | Command | Description |
| --- | --- | --- |
| **Setup Check** | `make check` | Runs `scripts/check_setup.py` verifying credentials |
| **Run Tests** | `make test` | Runs backend pytest suite (21 unit & API tests) |
| **Start Dev** | `make dev` | Starts backend on `:8000` and frontend on `:5173` |
| **Seed Database** | `make seed` | Populates SQLite with 2 services & 3 sample incidents |
| **Build Frontend**| `make build` | Typechecks and creates production frontend bundle |

> **Note for Windows users without `make`:**
> - Setup check: `python scripts/check_setup.py`
> - Run tests: `python -m pytest backend/tests -v`
> - Seed database: `python backend/seed.py`
> - Run backend: `python -m uvicorn app.main:app --app-dir backend --reload --port 8000`
> - Run frontend: `cd frontend && npm run dev`

---

## 🔍 Setup Check Script (`scripts/check_setup.py`)

Run the setup check at any time:
```bash
make check
# or
python scripts/check_setup.py
```
The script validates each configured service without ever printing cleartext secrets:
- **Gemini**: Generates a prompt token to confirm quota and API connectivity.
- **GitHub**: Verifies repository metadata and issue reading capabilities.
- **Telegram**: Validates bot token via `getMe` and verifies alerting channel.
- **Storage**: Verifies write and read-back functionality in SQLite.

---

## 🧪 Testing Suite

The pytest suite tests all core foundation behaviors:
1. **Authentication**: Enforces `Authorization: Bearer <DASHBOARD_PASSWORD>` on dashboard routes; validates `X-Tick-Secret` on `/internal/tick`.
2. **Services CRUD**: Full lifecycle tests for service registration, updates, pausing, and deletion.
3. **Incident Operations**: Tests incident filtering by severity (`P1`-`P3`), status, and timeline event retrieval.
4. **Kill Switch**: Verifies immediate activation and deactivation of the emergency global agent kill switch.

```bash
make test
```

---

## 🖥️ Frontend Dashboard

The frontend is a calm, responsive single-page application built with React, Vite, and TypeScript:
- **Overview (`/`)**: High-level health banner (green when healthy), monitored service cards, and active incident list.
- **War-Room (`/incidents/:id`)**: Detailed root cause analysis view, confidence metric, evidence viewer, action approval gate, and live event reasoning trace.
- **Services (`/services`)**: Registry to add, pause, or configure services and their autonomy level.
- **Emergency Kill Switch**: Global toggle in the top navbar to instantly halt all automated agent actions.

---

## 🔒 Security & Safety Controls
- **Human-in-the-Loop Approval**: High-risk actions (rollbacks, deployments) require manual approval via the war-room or Telegram.
- **Autonomy Ladder**: Services default to `Observe` or `Suggest` before being granted higher autonomy.
- **Constant-Time Auth**: Dashboard and tick secrets are verified using constant-time string comparisons.
- **Secret Masking**: All logs and diagnostics mask credential tokens.
