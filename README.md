# ServerMonitor

A full-stack network health monitor targeting the Drei Austria MyLife FIX Data 150 plan (guaranteed minimum 75 Mbps download). Bash scripts run scheduled connectivity and speed tests, appending results to CSV logs. A FastAPI backend ingests the logs, classifies performance against configurable thresholds, and exposes a REST API. A React frontend visualises the metrics and can generate PDF reports suitable for ISP complaint submission.

---

## Architecture

```
[cron] → speedtest_monitor.sh   → speedtest.csv    ┐
[cron] → connectivity_check.sh → connectivity.csv  ┴→ FastAPI ingest → SQLite → REST API → React frontend
```

The monitoring scripts run directly on the host. The backend runs in a container. Both share access to `/mnt/media/monitoring/data/` via a mounted volume — this is the only bridge between them.

---

## Prerequisites

**Host (monitoring scripts):**
- [`speedtest-cli`](https://www.speedtest.net/apps/cli) installed at `/usr/bin/speedtest`
- `jq` for JSON parsing
- `awk`, `bash` (standard on most Linux systems)

**Backend container:**
- Python 3.12+
- pip dependencies via `requirements.txt`
- `reportlab` for PDF generation
- `pypdf` for PDF tests

**Frontend:**
- Node.js 18+

---

## First-Time Setup

Before running any ingests, configure your subscriber details and service thresholds via the settings UI (⚙ gear icon in the top right). These values are used for performance classification and PDF report generation.

**Settings you must configure:**
- Subscriber name, address, account number, email, phone
- Provider name and plan name
- Contracted download speed — used to auto-derive thresholds (50% = degraded, 20% = critical)

Once saved, all subsequent ingests will classify results against your configured thresholds. Existing rows can be reclassified at any time via `POST /network/speedtest/reclassify`.

> **Note on the degraded flag in `speedtest_monitor.sh`:** The script uses a hardcoded threshold of `75` Mbps to set `/tmp/speedtest_degraded`, which triggers more frequent testing during poor performance. If you change the degraded threshold in the settings UI, update this value in the script manually — it is intentionally decoupled from the backend to keep the monitoring scripts self-contained and independent of the container being up.

---

## Data Pipeline

### Speedtest Monitor

**Script:** `scripts/speedtest_monitor.sh`
**Install:** `/usr/local/bin/speedtest_monitor.sh`
**Schedule:** Hourly — `0 * * * *`
**Adaptive schedule:** Every 10 minutes when degraded flag exists — `*/10 * * * * [ -f /tmp/speedtest_degraded ] && /usr/local/bin/speedtest_monitor.sh`
**Log:** `/mnt/media/monitoring/data/speedtest.csv`

Runs a speed test and appends the result to the CSV log. Attempts up to 3 times with a 10-second delay between retries, timing out after 180 seconds per attempt. Creates the log file on first run if it does not exist. After each successful test, sets or clears `/tmp/speedtest_degraded` depending on whether download falls below 75 Mbps — this flag triggers more frequent adaptive testing, providing denser data during poor performance periods for more accurate incident duration calculation.

> **Note:** The degraded flag threshold (75 Mbps) is hardcoded in the script and is independent of the degraded threshold configured in the settings UI. If you change `download_degraded_mbps` in the app, update the script manually to match.

**Successful row:**
```
2026-03-04 03:00:01,ONLINE,32.295,69.76,3.25,Vienna,51547,5.678609643115544
```

**Failed row:**
```
2026-03-04 02:00:01,FAILED,,,,,,"Cannot retrieve speedtest configuration"
```

Column order: `timestamp, status, ping, download_mbps, upload_mbps, server_name, server_id, distance[, failure_reason]`

---

### Connectivity Monitor

**Script:** `scripts/connectivity_check.sh`
**Install:** `/usr/local/bin/connectivity_check.sh`
**Schedule:** Every 20 minutes — `*/20 * * * *`
**Log:** `/mnt/media/monitoring/data/connectivity.csv`

Pings `8.8.8.8` twice with a 2-second timeout and records whether the connection is up, along with average round-trip latency. Creates the log file on first run if it does not exist.

**Online row:**
```
2026-03-05 13:04:17,ONLINE,34.690
```

**Offline row:**
```
2026-03-04 12:00:01,NO INTERNET,
```

Column order: `timestamp, status, latency_ms`

---

### Log Rotation

Logs are rotated monthly via logrotate, keeping 24 months of history. Rotated files are gzip-compressed and named `speedtest.csv.1.gz`, `connectivity.csv.1.gz` etc. The ingest service only reads the active CSV — compressed archives are not ingested automatically. Since raw records older than 7 days are aggregated and deleted, any data in a rotated archive that fell within the last 7 days of the previous month will not be captured. This is a known limitation.

---

### Cron Setup

Install the scripts from the repository:

```bash
sudo cp scripts/speedtest_monitor.sh /usr/local/bin/speedtest_monitor.sh
sudo cp scripts/connectivity_check.sh /usr/local/bin/connectivity_check.sh
sudo chmod +x /usr/local/bin/speedtest_monitor.sh
sudo chmod +x /usr/local/bin/connectivity_check.sh
```

Then add the cron entries:

```bash
sudo crontab -e
```

```
0 * * * *    /usr/local/bin/speedtest_monitor.sh
*/10 * * * * [ -f /tmp/speedtest_degraded ] && /usr/local/bin/speedtest_monitor.sh
*/20 * * * * /usr/local/bin/connectivity_check.sh
```

---

## Backend

### Project Structure

```
backend/
├── main.py
├── api/
│   ├── router.py
│   └── routes/
│       ├── speedtest.py
│       ├── connectivity.py
│       ├── summary.py
│       ├── report.py
│       └── settings.py
├── alembic/
├── core/
│   ├── config.py
│   └── database.py
├── models/
│   ├── speedtest.py                 # SpeedTestResult, SpeedTestFailure
│   ├── connectivity.py              # ConnectivityCheck
│   ├── daily_summary.py             # DailySummary
│   └── settings.py                  # Setting (key-value store)
├── repositories/
│   ├── speedtest_repository.py
│   ├── connectivity_repository.py
│   ├── summary_repository.py
│   └── settings_repository.py
├── schemas/
│   ├── speedtest.py
│   └── connectivity.py
├── services/
│   ├── speedtest_service.py
│   ├── connectivity_service.py
│   ├── summary_service.py
│   ├── ingest_speedtest.py
│   ├── ingest_connectivity.py
│   ├── aggregation_service.py
│   └── report_service.py
└── tests/
    ├── conftest.py
    ├── test_ingest.py
    ├── test_settings.py
    ├── test_endpoints.py
    ├── test_summary.py
    └── test_report.py
```

### Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### Configuration

Database URL via environment variable, defaults to local SQLite:

```bash
export DATABASE_URL=sqlite:///./monitoring.db
```

### Running

```bash
uvicorn main:app --reload
```

API docs: `http://localhost:8000/docs`

### Running Tests

Tests use an in-memory SQLite database and a FastAPI test client. Each test gets a clean session that is rolled back after the test completes — no data bleeds between tests and no files are written to disk.

`pytest.ini` is located in `backend/tests/` and configures the test runner automatically. From the `backend/` directory:

```bash
pytest tests/
```

No `PYTHONPATH` prefix needed — `pythonpath = .` in `pytest.ini` handles it. Use `--tb=line` for a compact summary:

```bash
pytest tests/ --tb=line
```

#### Test files

**`conftest.py`** — shared fixtures and factory helpers. Provides the in-memory engine, a per-test `db` session with rollback, a `client` fixture that overrides each route's `get_db` dependency, and factory functions (`make_speedtest_result`, `make_connectivity_check`, etc.) for inserting test data with sensible defaults.

**`test_ingest.py`** — classification logic and CSV ingestion for both speedtest and connectivity services.
- `classify_speed` boundary conditions: exact threshold values, NORMAL/DEGRADED/CRITICAL transitions, custom threshold override, zero speeds
- `ingest_speedtest`: successful rows routed to `speedtest_results`, failed rows to `speedtest_failures`, mixed CSV split correctly, deduplication on re-ingest, classification persisted, custom thresholds read from settings at ingest time, empty CSV handled gracefully
- `reclassify_all`: existing rows updated when threshold changes, returns correct count, leaves already-correct rows untouched
- `ingest_connectivity`: online and offline checks stored correctly, null latency on offline rows, deduplication, mixed checks, empty CSV

**`test_settings.py`** — settings repository and API endpoints.
- Repository: defaults returned when DB is empty, stored values override defaults, unset keys still return defaults, single-key `get`, upsert insert and update, partial updates preserve other keys, numeric values stored as strings
- API: `GET` returns full dict with defaults, `PUT` persists and returns updated values, partial updates, threshold values round-trip correctly

**`test_endpoints.py`** — HTTP layer for speedtest and connectivity routes.
- `/latest`: returns `null` on empty DB, returns most recent result, returns failure if failure is most recent
- `/count`: zeros on empty DB, correct totals across results and failures
- `/history`: wide range returns all records, `from_dt` and `to_dt` filters, empty result outside range, missing params return 422
- `/incidents`: no incidents when all NORMAL, consecutive DEGRADED records grouped into one incident, type changes produce separate incidents, failures included, required fields present, missing params return 422
- Connectivity equivalents of the above

**`test_summary.py`** — daily summary endpoints and aggregation service.
- `/latest`: null on empty DB, returns most recent by date
- `/history`: date range filters, empty result outside range, required fields present
- Aggregation: creates `DailySummary` from raw records, idempotent on re-run, skips records within the 7-day cutoff window, counts failures correctly, computes outage minutes from consecutive offline checks, background task body verified by calling `aggregate_old_records` directly

**`test_report.py`** — PDF generation service and report endpoint.
- `generate_report`: returns bytes, valid PDF magic bytes, non-trivial file size, subscriber name/provider/plan from settings appear in extracted text, configured download guarantee threshold appears in text, below-guarantee day count correct
- Endpoint: 200 status, `application/pdf` content type, valid PDF bytes, `Content-Disposition` attachment header with `.pdf` filename, works with real DB data, missing date params return 422

---

## Frontend

### Project Structure

```
frontend/
├── index.html
├── vite.config.js
└── src/
    ├── main.jsx                     # React entry point
    ├── App.jsx                      # Root component — state, data fetching, layout
    ├── index.css                    # Design system and all component styles
    ├── api/
    │   └── client.js                # Axios instance and typed API calls
    └── components/
        ├── StatCard.jsx             # Single metric display card
        ├── TimeRangeSelector.jsx    # Preset (24h / 7d) and custom range picker
        ├── SpeedChart.jsx           # Download/upload time series with performance zones
        ├── PingChart.jsx            # Ping latency time series
        ├── UptimeChart.jsx          # Donut charts for connectivity and speedtest uptime
        ├── IncidentTable.jsx        # Grouped incident log with severity highlighting
        ├── SummarySection.jsx       # Historical data section with range toggle and PDF export
        ├── SummaryChart.jsx         # Grouped bar + line chart over daily summaries
        ├── SummaryStats.jsx         # Five summary stat cards (outage time, avg speed, etc.)
        └── SettingsModal.jsx        # Gear icon modal for subscriber details and thresholds
```

### Component Overview

**`App.jsx`** is the single stateful root. It owns the selected time range, fetches all six data endpoints in parallel on range change, and passes data down to display components. The time range is stored as a preset (hours) or explicit `from`/`to` pair; the effective range is computed fresh on each fetch so preset ranges always use the current time.

**`client.js`** exports five typed objects (`speedtest`, `connectivity`, `summary`, `settings`, and the report URL helper) wrapping a shared axios instance pointed at `http://localhost:8000`.

**`SpeedChart`** renders a `ComposedChart` with coloured scatter dots per `performance_status` (green/amber/red), `ReferenceArea` background bands for the NORMAL/DEGRADED/CRITICAL zones, and threshold lines at the configured guarantee and critical values.

**`UptimeChart`** shows two side-by-side donut charts — one for connectivity uptime (online vs offline checks) and one for speedtest outcome (successful vs failed). A vertical divider separates them.

**`IncidentTable`** displays grouped incidents returned by `/network/speedtest/incidents`, with row colours indicating severity: red for `NO INTERNET` and `CRITICAL`, amber for `DEGRADED` and `FAILURE`.

**`SummarySection`** is self-contained — it fetches its own data from `/network/summary/history` based on a "Last 30 days / All time" toggle, renders `SummaryStats` and `SummaryChart`, and provides an "Export PDF Report" button that links directly to the `/network/report/pdf` endpoint for the active date range.

**`SettingsModal`** opens from the ⚙ gear button in the header. Two sections — Subscriber Details (used in the PDF report) and Service Thresholds (used for classification). An "Auto-derive from contracted speed" button computes degraded (50%) and critical (20%) thresholds automatically. Saving persists to the backend and closes the modal after a brief confirmation flash.

### Running

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`.

---

## API Endpoints

### Speedtest — `/network/speedtest`

| Method | Path | Description |
|---|---|---|
| `GET` | `/latest` | Most recent record across results and failures |
| `GET` | `/count` | Record counts split by outcome |
| `GET` | `/history?from_dt=&to_dt=` | All records in time range |
| `GET` | `/incidents?from_dt=&to_dt=` | Grouped outage/degradation incidents |
| `POST` | `/ingest` | Parse CSV and persist new records |
| `POST` | `/reclassify` | Re-classify all stored results against current thresholds |

### Connectivity — `/network/connectivity`

| Method | Path | Description |
|---|---|---|
| `GET` | `/latest` | Most recent connectivity check |
| `GET` | `/count` | Record counts split by outcome |
| `GET` | `/history?from_dt=&to_dt=` | All checks in time range |
| `POST` | `/ingest` | Parse CSV and persist new records |

### Summary — `/network/summary`

| Method | Path | Description |
|---|---|---|
| `GET` | `/latest` | Most recent daily summary |
| `GET` | `/history?from_date=&to_date=` | Daily summaries in date range |
| `POST` | `/aggregate` | Manually trigger aggregation of records older than 7 days |

### Report — `/network/report`

| Method | Path | Description |
|---|---|---|
| `GET` | `/pdf?from_date=&to_date=` | Download PDF complaint report for date range |

### Settings — `/network/settings`

| Method | Path | Description |
|---|---|---|
| `GET` | `` | Get all settings (defaults filled in for unset keys) |
| `PUT` | `` | Save settings (partial updates supported) |

---

## Performance Classification

Incoming speedtest results are classified at ingest time based on thresholds stored in the settings table:

| Status | Condition |
|---|---|
| `NORMAL` | Download ≥ degraded threshold AND upload ≥ upload degraded threshold |
| `DEGRADED` | Either metric below the degraded threshold but above critical |
| `CRITICAL` | Either metric below the critical threshold |

Default thresholds for Drei MyLife FIX Data 150:

| Setting | Default | Derivation |
|---|---|---|
| `contracted_download_mbps` | 150.0 | Plan advertised speed |
| `download_degraded_mbps` | 75.0 | 50% of contracted |
| `download_critical_mbps` | 30.0 | 20% of contracted |
| `upload_degraded_mbps` | 5.0 | Based on observed baseline |
| `upload_critical_mbps` | 2.0 | Based on observed baseline |

After changing thresholds in the settings UI, call `POST /network/speedtest/reclassify` to update the classification of all existing stored records.

---

## Aggregation

Raw records older than 7 days are automatically aggregated into daily summaries after each ingest. Raw records are deleted after aggregation. Aggregation is idempotent — re-running it on already-aggregated days is safe.

---

## Data Models

### `speedtest_results`

| Column | Type | Description |
|---|---|---|
| timestamp | DateTime | Time of the test |
| status | String | Always `ONLINE` |
| ping | Float | Latency in ms |
| download_mbps | Float | Download speed in Mbps |
| upload_mbps | Float | Upload speed in Mbps |
| server_name | String | Name of the test server |
| server_id | Integer | ID of the test server |
| distance | Float | Distance to server in km |
| performance_status | String | `NORMAL`, `DEGRADED`, or `CRITICAL` |

### `speedtest_failures`

| Column | Type | Description |
|---|---|---|
| timestamp | DateTime | Time of the attempt |
| status | String | Always `FAILED` |
| failure_reason | String | Error message from the CLI |

### `connectivity_checks`

| Column | Type | Description |
|---|---|---|
| timestamp | DateTime | Time of the check |
| status | String | `ONLINE` or `NO INTERNET` |
| latency_ms | Float | Average RTT in ms. Null when offline |

### `daily_summaries`

Aggregated per-day records covering both speedtest and connectivity metrics. Generated automatically from raw records older than 7 days.

### `settings`

Key-value store for subscriber details and service thresholds. Defaults are applied at read time for any key not yet stored in the database.

---

## Architecture Notes

- **Scripts are dumb** — they log raw numbers only. No quality judgements. The degraded flag threshold is the sole exception and is documented above.
- **Backend is the single source of truth** for thresholds, classification, and reporting.
- **No silent discards** — every CSV row is persisted. Failures go to `speedtest_failures`, ensuring uptime metrics are not positively skewed.
- **Deduplication** — ingest only inserts rows newer than the latest stored timestamp. Re-running ingest is always safe.
- **Layered backend** — routes → services → repositories. Query logic lives in the repository layer only.