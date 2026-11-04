# Demo-Shop: Monitored Sample Application

`demo-shop` is a lightweight e-commerce API built specifically as the target monitored service for **Nightwatch**, an AI on-call SRE engineer. It provides realistic product browsing, shopping cart checkout, in-memory structured JSON log streaming, background traffic generation, and admin chaos injection controls.

---

## Tech Stack & Architecture

- **Runtime:** Python 3.12+ / FastAPI / Uvicorn
- **State:** 100% in-memory (product catalog, runtime version, chaos state, 1,000-entry log ring buffer)
- **Port:** `8001` (default)
- **Container:** Dockerfile included (`python:3.12-slim`)

---

## Quickstart

### 1. Install Dependencies

```bash
cd sample-app
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example configuration:

```bash
cp .env.example .env
```

Configuration keys:
| Variable | Default | Purpose |
|---|---|---|
| `ADMIN_TOKEN` | `demo-admin-secret` | Required in `X-Admin-Token` header for `/admin/*` routes |
| `APP_VERSION` | `v1` | Initial version (`v1` or `v2`) |
| `CHAOS_MODE` | `none` | Initial chaos mode (`none`, `slow`, `down`) |
| `TRAFFIC_INTERVAL_SECONDS` | `1.5` | Interval between simulated background requests (0 to disable) |
| `TRAFFIC_ENABLED` | `true` | Toggle background traffic generator |
| `PORT` | `8001` | Service listening port |

### 3. Run Application

```bash
# From sample-app directory
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Or with Docker
docker build -t demo-shop .
docker run -p 8001:8001 demo-shop
```

### 4. Run Test Suite

```bash
pytest tests -v
```

---

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check returning status (`healthy`/`unhealthy`), current version, and uptime. Returns **HTTP 503** when chaos mode is `down`. |
| `GET` | `/products` | Catalog of 8 e-commerce products (Electronics, Accessories, Home Office). |
| `GET` | `/products/{id}` | Single product details (returns 404 if not found). |
| `POST` | `/checkout` | Process order. Body: `{"items": [{"product_id": 1, "quantity": 2}], "discount_code": "SAVE10"}`. |
| `GET` | `/logs` | Structured JSON log ring buffer. Query params: `level` (`INFO`/`WARN`/`ERROR`), `since` (ISO timestamp), `limit` (default 100, max 1000). |

### Admin Endpoints (Require `X-Admin-Token: <ADMIN_TOKEN>`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/state` | Inspect current version, chaos mode, and git commit label. |
| `POST` | `/admin/deploy` | Deploy version: `{"version": "v1" \| "v2"}`. |
| `POST` | `/admin/rollback` | Immediately rolls back to `v1`. |
| `POST` | `/admin/chaos` | Inject chaos: `{"mode": "none" \| "slow" \| "down"}`. |

---

## Demo Controls Table

These controls simulate on-call production incidents for Nightwatch:

| Action | Command / Payload | Simulated Incident Effect |
|---|---|---|
| **Deploy Bad Release** | `POST /admin/deploy`<br>`{"version": "v2"}` | Shifts app to `v2` ("Add discount codes to checkout"). Approximately 70% of checkouts fail with **HTTP 500 TypeError** when users apply unlisted or expired discount codes. Real tracebacks pointing to `app/checkout.py` and `apply_discount` appear in `/logs`. |
| **Simulate Slow Latency** | `POST /admin/chaos`<br>`{"mode": "slow"}` | Injects growing synthetic latency (from 0.5s up to ~6.0s) into non-admin endpoints, simulating memory leaks or thread starvation. |
| **Simulate Service Down** | `POST /admin/chaos`<br>`{"mode": "down"}` | `/health` immediately fails with **HTTP 503 Service Unavailable**, triggering Nightwatch P1/P2 outage sweeps. |
| **Rollback Release** | `POST /admin/rollback` | Restores app to `v1` ("Initial demo-shop API"). Checkouts immediately return to 100% success rate. |
| **Reset Chaos** | `POST /admin/chaos`<br>`{"mode": "none"}` | Clears all synthetic latency and restores `/health` to HTTP 200. |

---

## Background Traffic Simulator

A built-in background task runs on startup (configured by `TRAFFIC_INTERVAL_SECONDS`, default 1.5s):
- **Browsing (~65%):** Random `GET /products` and `GET /products/{id}` requests.
- **Health sweeps (~15%):** Periodic `GET /health` requests.
- **Checkouts (~20%):** Cart checkout requests:
  - In **v1**: standard checkouts without discount codes (100% success).
  - In **v2**: checkouts pick randomly from `SAMPLE_CODES` (7 unknown, 3 valid), producing a natural **~70% error spike** with real `TypeError` tracebacks logged to the ring buffer.

---

## Publishing to GitHub (`demo-shop`)

The demo script requires a realistic 3-commit history in the external repo:
1. `Initial demo-shop API`: v1 files without discounts or `/logs`.
2. `Add discount codes to checkout`: introduces `app/discounts.py` and the v2 checkout bug.
3. `Add /logs endpoint and README`: adds log ring buffer and documentation.

To publish these commits to GitHub:
```powershell
.\publish_to_demo_shop.ps1 -RepoUrl "https://github.com/yohanneszewde2556/demo-shop.git"
```
*(Requires git credentials with push rights to `demo-shop`.)*
