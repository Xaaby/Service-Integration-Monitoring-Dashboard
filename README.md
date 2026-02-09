## Service-Integration-Monitoring-Dashboard

A monitoring dashboard that helps **product, engineering, and SRE teams see the health of critical services at a glance**, so they can **spot customer‑impacting issues early and prioritize the right fixes**.

Instead of digging through raw logs or multiple vendor tools, this dashboard brings together **service availability, latency, errors, and throughput** in one place and ties them to **business‑meaningful services** (e.g., “Payments API”, “Orders API”) and **realistic incident timelines**.

Built with **PostgreSQL**, **FastAPI**, and **Streamlit**, and fully runnable via **Docker Compose**.

---

### Business Context & Real‑World Problem

Modern platforms are composed of dozens of services owned by different teams. When a release goes wrong or a customer reports slowness, teams often spend **hours correlating logs, metrics, and incident notes** across tools (APM, ticketing, chat, wikis).

This project is modeled after the kind of **internal “single pane of glass”** many organizations build for themselves. It is meant to answer questions like:

- **“Which services are currently at risk of breaching our SLOs?”**
- **“Did the latest release hurt checkout latency or error rates for the payments flow?”**
- **“Where did throughput drop off this morning, and which team owns that service?”**
- **“What were the last incidents for this service, and what was the root cause?”**

Out of the box, it simulates **30 days of realistic traffic patterns and incidents** so you can demo or practice:

- Running a **release review** or **production readiness review**.
- Walking through a **post‑incident analysis** with metrics and notes in one view.
- Helping a new engineer or SRE quickly understand **how the system behaves in production**.

---

### Architecture Overview

High-level architecture:

```text
                 +---------------------------+
                 |    Streamlit Dashboard    |
                 |   (dashboard container)   |
                 +-------------+-------------+
                               |
                               | HTTP (REST)
                               v
                 +---------------------------+
                 |       FastAPI API         |
                 |     (backend container)   |
                 +-------------+-------------+
                               |
                               | SQL (SQLAlchemy)
                               v
                 +---------------------------+
                 |        PostgreSQL         |
                 |       (db container)      |
                 +---------------------------+

                          ^
                          |
                +---------+----------+
                |  refresh_metrics   |
                |   (cron-capable)   |
                +--------------------+
```

---

### Project Structure

- **backend/**
  - `app/main.py` – FastAPI application factory and startup hooks.
  - `app/db.py` – SQLAlchemy engine/session, schema initialization, view loading, and auto-seed.
  - `app/models.py` – ORM models for `services`, `service_events`, and `incident_notes`.
  - `app/metrics.py` – Core metrics SQL queries and health score logic.
  - `app/routes/` – API routes:
    - `health.py` – `GET /health`.
    - `services.py` – `GET /services`, `GET /services/{id}/incidents`.
    - `metrics.py` – `GET /metrics/*` endpoints.
    - `seed.py` – `POST /seed` (dev-only reseed).
  - `tests/` – Pytest tests for metrics logic, API shape, and seed determinism.
  - `Dockerfile` – Backend container image.
- **dashboard/**
  - `app.py` – Main Streamlit app and shared selectors.
  - `pages/1_Overview.py` – Overview KPIs + incident notes.
  - `pages/2_Latency.py` – Latency charts and regression marker.
  - `pages/3_Errors.py` – Error codes and failures over time.
  - `pages/4_Throughput.py` – Throughput charts + heatmap-style view.
  - `Dockerfile` – Dashboard container image.
- **sql/**
  - `schema.sql` – Table definitions and enums.
  - `metrics_views.sql` – Aggregation view(s) (e.g., `service_event_daily_agg`).
- **data/**
  - `seed.py` – Deterministic seed generator and seeding routine.
- **jobs/**
  - `refresh_metrics.py` – Example cron-friendly job to verify DB connectivity / refresh views.
- **screenshots/**
  - Placeholder `README.txt` and expected screenshot filenames.
- `docker-compose.yml` – Orchestration of `db`, `api`, and `dashboard` services.

---

### How to Run (Docker Compose)

**Prerequisites**
- Docker and Docker Compose installed.

**Steps**

1. From the project root, build and run:

   ```bash
   docker compose up --build
   ```

2. Services:
   - **PostgreSQL** – `localhost:5433`
   - **FastAPI API** – `http://localhost:8000`
   - **Streamlit Dashboard** – `http://localhost:8501`

3. On startup:
   - The backend applies `sql/schema.sql` and `sql/metrics_views.sql`.
   - The backend auto-seeds 30 days of realistic sample data (`AUTO_SEED_ON_STARTUP=true`).

To stop:

```bash
docker compose down
```

---

### Data Model

**1) `services`**

- **id**: `uuid`, primary key.
- **name**: service name (e.g., `payments-api`).
- **owner_team**: team name (e.g., `payments`).
- **environment**: `prod` or `stage`.
- **created_at**: creation timestamp.

**2) `service_events`**

- **id**: `uuid`, primary key.
- **service_id**: FK → `services.id`.
- **ts**: event timestamp.
- **event_type**: enum: `request`, `job_run`.
- **status**: enum: `success`, `failure`.
- **latency_ms**: `int`, nullable (mainly for `request` events).
- **payload_size_bytes**: `int`, nullable.
- **error_code**: `text`, nullable.
- **correlation_id**: `text`.
- **build_version**: `text`.

**3) `incident_notes`**

- **id**: `uuid`, primary key.
- **service_id**: FK → `services.id`.
- **incident_date**: `date`.
- **summary**: short description.
- **root_cause**: text.
- **resolution**: text.
- **created_at**: timestamp.

---

### Seed Data

Located in `data/seed.py`:

- Uses a deterministic random seed (`SEED_VALUE = 42`) for repeatability.
- Generates **~30 days** of data for **6 services**:
  - `payments-api` (prod) – **intermittent failures**.
  - `user-service` (prod) – **latency regression** after halfway through the 30 days.
  - `orders-api` (prod) – **higher weekday throughput**.
  - `reporting-job` (stage) – low-frequency `job_run` events.
  - `notifications` (prod) – moderate, steady traffic.
  - `inventory-api` (stage) – moderate traffic.
- Adds 2 `incident_notes` per service with realistic descriptions.

Seeding is triggered automatically on backend startup (controlled via `AUTO_SEED_ON_STARTUP`).  
You can also call `POST /seed` (when `ENABLE_DEV_SEED=true`) to reseed on demand.

---

### Metrics Definitions

All metrics are computed over **time range + service + environment** filters.

- **success_rate**
  - Definition: `success_rate = success_count / total_events`
  - Counted from `service_events.status`.

- **p50_latency, p95_latency**
  - Only for events where `event_type = 'request'` and `latency_ms IS NOT NULL`.
  - Computed using `percentile_cont(0.5)` and `percentile_cont(0.95)` in PostgreSQL.

- **throughput_per_hour / throughput_per_day**
  - Throughput is `COUNT(*)` of `service_events` per hour or day bucket.
  - In the overview, `throughput_per_day` is `COUNT(*) / number_of_days_in_range`.

- **error_rate_per_1k**
  - `error_rate_per_1k = (failure_count * 1000) / total_events`
  - `failure_count` is `COUNT(*)` where `status = 'failure'`.

- **top_error_codes**
  - Top N error codes by count (limited to 10) from `service_events.error_code`
    where `status = 'failure'`.

- **health score (0–100)**
  - Implemented in `backend/app/metrics.py`.
  - Starts at **100** and subtracts points based on:
    - **Latency (p95)**:
      - > 1500 ms → -30
      - > 1000 ms → -20
      - > 700 ms → -10
    - **Error rate per 1k**:
      - > 50 → -40
      - > 20 → -25
      - > 5 → -10
  - Score is clamped between 0 and 100.

---

### API Endpoints (FastAPI)

- **`GET /health`**
  - Simple liveness check: `{ "status": "ok" }`.

- **`GET /services`**
  - Lists all services: `id`, `name`, `owner_team`, `environment`, `created_at`.

- **`GET /services/{service_id}/incidents`**
  - Incident notes for the specified service, sorted by `incident_date DESC`.

- **`GET /metrics/overview?service_id=&env=&from=&to=`**
  - Returns:
    - `success_rate`
    - `error_rate_per_1k`
    - `p95_latency`
    - `throughput_per_day`
    - `health_score`

- **`GET /metrics/latency?service_id=&env=&from=&to=&bucket=day|hour`**
  - Time series of:
    - `p50_latency`
    - `p95_latency`
  - Bucketed by day or hour.

- **`GET /metrics/errors?service_id=&env=&from=&to=`**
  - Returns:
    - `top_error_codes` (list of `{ error_code, count }`)
    - `failures_timeseries` (per-day failure counts).

- **`GET /metrics/throughput?service_id=&env=&from=&to=&bucket=day|hour`**
  - Time series of throughput counts.

- **`POST /seed`** (optional, dev-only)
  - Reseeds the database when `ENABLE_DEV_SEED=true`.

---

### Streamlit Dashboard

The dashboard talks to the FastAPI service via `API_BASE_URL` (default: `http://api:8000` in Docker).

#### 1) Overview Page

- Service selector (dropdown).
- Date range selector.
- Environment selector (`prod` / `stage`).
- KPI cards:
  - Success rate.
  - p95 latency.
  - Throughput/day.
  - Error rate per 1k.
- Health score indicator with a progress bar.
- Incident Notes section listing most recent incidents for the selected service.

#### 2) Latency Page

- Same filters as Overview.
- Line chart for `p50` and `p95` latency over time (bucketed by day).
- Simple regression marker:
  - Compares last 7 days of p95 vs earlier period.
  - Displays a warning when recent p95 > 120% of earlier p95.

#### 3) Errors Page

- Top error codes bar chart.
- Failures over time line chart.

#### 4) Throughput Page

- Throughput over time (line chart).
- Heatmap-style view:
  - Weekday (rows) x hour of day (columns).
  - Visualizes throughput concentration.

---

### Operational Refresh Job

File: `jobs/refresh_metrics.py`

- Connects to the PostgreSQL database using `DATABASE_URL`.
- Runs a lightweight `SELECT 1` to verify connectivity.
- Intended place to:
  - Refresh materialized views (if/when you introduce them).
  - Pre-compute heavy aggregates.

**Example cron entry (Linux)**

```cron
*/5 * * * * /usr/bin/env DATABASE_URL="postgresql+psycopg2://postgres:postgres@db:5432/monitoring" \
    python /app/jobs/refresh_metrics.py >> /var/log/refresh_metrics.log 2>&1
```

In containerized environments, you might instead:
- Use a separate “jobs” container that runs this script on a schedule.
- Or trigger it via a managed scheduler (e.g., GitHub Actions, Azure Functions, etc.).

---

### Tests

Located under `backend/tests/`:

- **`test_metrics.py`**
  - Verifies `calculate_health_score` decreases when latency or error rate increase.

- **`test_api_health.py`**
  - Uses FastAPI’s `TestClient` to assert the shape of the `GET /health` response.

- **`test_seed_determinism.py`**
  - Calls `generate_seed_events()` twice and asserts:
    - Same counts for services, events, and incidents.
    - Key attributes (such as timestamps and summaries) match, confirming determinism.

Run tests (inside the backend container or locally with dependencies installed):

```bash
pytest backend/tests
```

---

### Screenshots

Place screenshots under `screenshots/` with filenames like:

- `screenshots/overview.png`
- `screenshots/latency.png`
- `screenshots/errors.png`
- `screenshots/throughput.png`

Update this section with actual images as you capture them.

---

### Assumptions and Future Improvements

**Assumptions**
- Single PostgreSQL instance is sufficient for this demo.
- Time zone handling is simplified to UTC.
- Latency and error patterns are approximations for realistic but synthetic data.

**Potential future improvements**
- Integrate with **Azure Monitor** or similar:
  - Pull real metrics (App Insights, Log Analytics) into this schema.
  - Correlate custom events and traces with service_events.
  - Use Azure Alert rules to auto-create `incident_notes`.
- Add authentication/authorization for the dashboard.
- Implement materialized views for heavy aggregations and refresh them via `refresh_metrics.py`.
- Support multi-region deployments and environment-specific dashboards.

---

### Project Summary

This repository provides a **production-style monitoring and observability dashboard** for backend services, designed to feel like an internal tool used by real teams. With a single `docker compose up --build`, you get a **PostgreSQL + FastAPI + Streamlit stack** that surfaces service health, latency, errors, and throughput in business‑friendly views.
The system models services, per-request and job-run events, and incident notes, and seeds 30 days of realistic traffic patterns so the dashboard is immediately informative for demos, training, and interviews.  
FastAPI exposes health, services, and metrics endpoints that compute success rate, latency percentiles, throughput, error rates, and a rule-based health score, while Streamlit consumes those APIs to render overview KPIs, latency, error, and throughput views with interactive filters.  
The refresh job and automated tests complete the operational story, showing how this dashboard could underpin **operational readiness reviews, incident response, and ongoing reliability reporting** for engineering and business stakeholders.

