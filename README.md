# ServerMonitor

ServerMonitor is a self-hosted network and server health monitor built to document and report on ISP underperformance and host-system health. It runs automated speed and connectivity tests, collects server health metrics, visualises network results over time, and generates formatted PDF reports for ISP complaint submission. Built for the Drei Austria MyLife FIX Data 150 plan (contracted minimum 75 Mbps download).

## Screenshots

- **Download & Upload Speed** — performance zones and threshold lines
- **Incident Table** — grouped outage and degradation events with severity highlighting
- **Settings Modal** — subscriber details and service thresholds

## Architecture

```
[cron] → speedtest_monitor.sh   → speedtest.csv    ┐
[cron] → connectivity_check.sh → connectivity.csv  ┴→ FastAPI ingest → SQLite → REST API → React frontend
                                                        ↑
[systemd timer] → server_health_monitor.py ────────────┘
```

The monitoring scripts and server health collector run directly on the host. The backend and frontend run in Docker containers.

Network monitoring scripts write raw CSV data to `/mnt/media/monitoring/data/`. The backend container reads those files through a shared volume and persists the data into SQLite.

The server health collector runs as a host-level systemd oneshot service every minute. It collects host metrics using `psutil` and submits them to the backend through the authenticated `/server/health` API endpoint.

The server health API returns filesystem information together with the parent health sample. This allows each health snapshot to contain both host-wide metrics and per-filesystem capacity/inode information.

#### Collected Metrics

The collector currently reports:

- CPU utilisation, per-core utilisation, frequency, and load averages
- Memory and swap usage
- CPU package/core temperatures
- Disk I/O counters, IOPS, and utilisation
- Network traffic, errors, and drops
- System uptime
- Filesystem capacity and inode utilisation

Filesystem information is collected for each mounted filesystem and includes:

- Mount point
- Total capacity
- Used capacity
- Available capacity
- Capacity utilisation percentage
- Total inodes
- Used inodes
- Free inodes
- Inode utilisation percentage

Filesystem metrics are persisted in the `server_health_filesystems` table and associated with the parent `server_health` record.

Filesystem health evaluation is currently handled independently from metric collection. Capacity and inode utilisation use the following thresholds:

| Status | Usage |
|---|---|
| OK | < 80% |
| WARNING | ≥ 80% and < 90% |
| CRITICAL | ≥ 90% |

A missing percentage is treated as `OK`. This is particularly relevant for filesystems such as `/boot/efi` where inode statistics may not be available.

Capacity and inode health are evaluated independently. A filesystem can therefore have a different capacity status and inode status.


The server health collector uses a dedicated Python virtual environment at `/home/vesko/Server-Monitor/.venv/`. Its dependencies are intentionally kept outside the Docker containers because the collector monitors the host itself.

The Docker containers and the host collector communicate through the server's HTTP interface. The server health endpoint is protected by a shared API token.

For full deployment instructions see `DEPLOYMENT.md`.

## Prerequisites

**Host (monitoring scripts):**

- `speedtest-cli` installed at `/usr/bin/speedtest`
- `jq` for JSON parsing
- `awk`, `bash` (standard on most Linux systems)
- Python 3.12+ for the server health collector
- Python virtual environment with `psutil` installed for the server health collector
- `systemd` for scheduled server health collection

**Containers:**

- Docker and Docker Compose
- No other dependencies — everything else is installed inside the containers at build time

**Local development (backend):**

- Python 3.12+
- pip dependencies via `backend/requirements.txt`

**Local development (frontend):**

- Node.js 18+

## First-Time Setup

Before running any ingests, configure your subscriber details and service thresholds via the settings UI (⚙ gear icon in the top right). These values are used for performance classification and PDF report generation.

Settings you must configure:

- Subscriber name, address, account number, email, phone
- Provider name and plan name
- Contracted download speed — used to auto-derive thresholds (50% = degraded, 20% = critical)

Once saved, all subsequent ingests will classify results against your configured thresholds. Existing rows can be reclassified at any time via `POST /network/speedtest/reclassify`.

The server health collector additionally requires a shared API token. The token is stored on the host in:

```
/etc/servermonitor/server-health.env
```

Example:

```
SERVER_HEALTH_API_TOKEN=REPLACE_WITH_REAL_TOKEN
```

The same token must be provided to the backend container through the `SERVER_HEALTH_API_TOKEN` environment variable.

> **Note on the degraded flag in `speedtest_monitor.sh`:** The script uses a hardcoded threshold of 75 Mbps to set `/tmp/speedtest_degraded`, which triggers more frequent testing during poor performance. If you change the degraded threshold in the settings UI, update this value in the script manually — it is intentionally decoupled from the backend to keep the monitoring scripts self-contained and independent of the containers being up.

## Data Pipeline

### Speedtest Monitor

- **Script:** `scripts/speedtest_monitor.sh`
- **Install:** `/usr/local/bin/speedtest_monitor.sh`
- **Schedule:** Hourly — `0 * * * *`
- **Adaptive schedule:** Every 10 minutes when degraded flag exists — `*/10 * * * * [ -f /tmp/speedtest_degraded ] && /usr/local/bin/speedtest_monitor.sh`
- **Log:** `/mnt/media/monitoring/data/speedtest.csv`

Runs a speed test and appends the result to the CSV log. Attempts up to 3 times with a 10-second delay between retries, timing out after 180 seconds per attempt. Creates the log file on first run if it does not exist. After each successful test, sets or clears `/tmp/speedtest_degraded` depending on whether download falls below 75 Mbps — this flag triggers more frequent adaptive testing, providing denser data during poor performance periods for more accurate incident duration calculation.

> **Note:** The degraded flag threshold (75 Mbps) is hardcoded in the script and is independent of the degraded threshold configured in the settings UI. If you change `download_degraded_mbps` in the app, update the script manually to match.

Successful row:

```
2026-03-04 03:00:01,ONLINE,32.295,69.76,3.25,Vienna,51547,5.678609643115544
```

Failed row:

```
2026-03-04 02:00:01,FAILED,,,,,,"Cannot retrieve speedtest configuration"
```

Column order: `timestamp, status, ping, download_mbps, upload_mbps, server_name, server_id, distance[, failure_reason]`

### Connectivity Monitor

- **Script:** `scripts/connectivity_check.sh`
- **Install:** `/usr/local/bin/connectivity_check.sh`
- **Schedule:** Every 20 minutes — `*/20 * * * *`
- **Log:** `/mnt/media/monitoring/data/connectivity.csv`

Pings `8.8.8.8` twice with a 2-second timeout and records whether the connection is up, along with average round-trip latency. Creates the log file on first run if it does not exist.

Online row:

```
2026-03-05 13:04:17,ONLINE,34.690
```

Offline row:

```
2026-03-04 12:00:01,NO INTERNET,
```

Column order: `timestamp, status, latency_ms`

### Server Health Monitor

- **Script:** `scripts/server_health_monitor.py`
- **Python:** `/home/vesko/Server-Monitor/.venv/bin/python`
- **Schedule:** Every minute via systemd
- **Service:** `server-health-monitor.service`
- **Timer:** `server-health-monitor.timer`
- **Authentication:** `SERVER_HEALTH_API_TOKEN`
- **Endpoint:** `POST /server/health`

The server health collector runs directly on the host and reports host-level metrics to the ServerMonitor backend.

It uses `psutil` to collect system metrics without requiring Docker access or privileged container permissions. The collector is intentionally separate from the backend because the backend runs inside Docker while the metrics describe the physical/host server.

The service is configured as a `Type=oneshot` systemd service. The timer starts it once per minute:

```
server-health-monitor.timer
        ↓
server-health-monitor.service
        ↓
server_health_monitor.py
        ↓
POST /server/health
```

The service uses:

```
User=vesko
WorkingDirectory=/home/vesko/Server-Monitor
EnvironmentFile=/etc/servermonitor/server-health.env
ExecStart=/home/vesko/Server-Monitor/.venv/bin/python /home/vesko/Server-Monitor/scripts/server_health_monitor.py
```

The environment file is intentionally stored outside the repository because it contains the real API token:

```
/etc/servermonitor/server-health.env
```

The repository contains only the template:

```
systemd/server-health.env.example
```

Example:

```
SERVER_HEALTH_API_TOKEN=REPLACE_WITH_REAL_TOKEN
```

Install and enable the collector:

```bash
cd ~/Server-Monitor

python3 -m venv .venv
~/Server-Monitor/.venv/bin/pip install psutil

sudo mkdir -p /etc/servermonitor
sudo cp systemd/server-health.env.example /etc/servermonitor/server-health.env
sudo nano /etc/servermonitor/server-health.env

sudo cp systemd/server-health-monitor.service /etc/systemd/system/server-health-monitor.service
sudo cp systemd/server-health-monitor.timer /etc/systemd/system/server-health-monitor.timer

sudo systemctl daemon-reload
sudo systemctl enable --now server-health-monitor.timer
```

Verify the timer:

```bash
systemctl status server-health-monitor.timer --no-pager
systemctl list-timers --all | grep server-health
```

Run the collector manually:

```bash
sudo systemctl start server-health-monitor.service
```

Check the result:

```bash
systemctl status server-health-monitor.service --no-pager
journalctl -u server-health-monitor.service -n 20 --no-pager
```

A successful run should report:

```
Server health submitted successfully
```

The service is expected to become inactive (dead) after a successful run because it is a oneshot service. The timer remains active and starts it again at the next scheduled interval.

## Log Rotation

Logs are rotated monthly via `logrotate`, keeping 24 months of history. Rotated files are gzip-compressed and named `speedtest.csv.1.gz`, `connectivity.csv.1.gz` etc. The ingest service only reads the active CSV — compressed archives are not ingested automatically. Since raw records older than 7 days are aggregated and deleted, any data in a rotated archive that fell within the last 7 days of the previous month will not be captured. This is a known limitation.

## Cron Setup

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

Server health collection is not configured through cron. It is managed by the version-controlled systemd units in `systemd/`.

## Deployment

The backend and frontend are containerised and run behind a shared nginx reverse proxy. The proxy is the only service bound to port 80 — all apps on the server share it. See `DEPLOYMENT.md` for full step-by-step instructions covering:

- Setting up the shared Docker network and proxy
- Building and starting the ServerMonitor containers
- Configuring the authenticated server health API
- Installing the host-level systemd server health collector
- DNS configuration for local network access at `http://servermonitor/servermonitor`
- Ongoing operations — rebuilding, log viewing, adding future apps

### Container Structure

```
docker/
├── docker-compose.yml      # Backend + frontend services, joins proxy-network
├── backend.dockerfile      # Python 3.12-slim, installs deps, runs alembic + uvicorn
└── frontend.dockerfile     # Node 18 build stage → nginx:alpine serve stage
```

The backend runs Alembic migrations automatically on every container start before uvicorn starts. The database and CSV logs are shared with the host via a volume mount at `/mnt/media/monitoring/data/`.

The backend also exposes the authenticated server health endpoint used by the host collector.

Environment variables (backend):

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./monitoring.db` |
| `LOG_PATH_SPEEDTEST` | Path to speedtest CSV inside container | `/mnt/media/monitoring/data/speedtest.csv` |
| `LOG_PATH_CONNECTIVITY` | Path to connectivity CSV inside container | `/mnt/media/monitoring/data/connectivity.csv` |
| `SERVER_HEALTH_API_TOKEN` | Token required by the server health submission endpoint | Not set |

`SERVER_HEALTH_API_TOKEN` must be supplied by the deployment environment. The real token must not be committed to Git.

The Docker Compose configuration passes the token into the backend:

```yaml
environment:
  SERVER_HEALTH_API_TOKEN: ${SERVER_HEALTH_API_TOKEN}
```

The host collector obtains its token from:

```
/etc/servermonitor/server-health.env
```

## Backend

### Project Structure

```
backend/
├── main.py
├── alembic/                         # Database migrations
├── api/
│   ├── router.py
│   └── routes/
│       ├── speedtest.py
│       ├── connectivity.py
│       ├── summary.py
│       ├── report.py
│       ├── settings.py
│       └── server.py                # Host server health endpoint
├── core/
│   ├── config.py
│   └── database.py
├── models/
│   ├── speedtest.py                 # SpeedTestResult, SpeedTestFailure
│   ├── connectivity.py              # ConnectivityCheck
│   ├── daily_summary.py             # DailySummary
│   ├── settings.py                  # Setting (key-value store)
│   ├── server_health.py             # Server health data
│   └── server_health_filesystem.py  # Filesystem data
├── repositories/
│   ├── speedtest_repository.py
│   ├── connectivity_repository.py
│   ├── summary_repository.py
│   ├── settings_repository.py
│   └── server_health_repository.py
├── schemas/
│   ├── speedtest.py
│   ├── connectivity.py
│   └── server_health.py
├── services/
│   ├── speedtest_service.py
│   ├── connectivity_service.py
│   ├── summary_service.py
│   ├── ingest_speedtest.py
│   ├── ingest_connectivity.py
│   ├── aggregation_service.py
│   ├── report_service.py
│   ├── server_health_service.py
│   └── filesystem_health_service.py
└── tests/
    ├── conftest.py
    ├── test_ingest.py
    ├── test_settings.py
    ├── test_endpoints.py
    ├── test_summary.py
    └── test_report.py
```

### Local Development Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

API docs available at `http://localhost:8000/docs`.

### Running Tests

Tests use an in-memory SQLite database and a FastAPI test client. Each test gets a clean session that is rolled back after the test completes — no data bleeds between tests and no files are written to disk.

`pytest.ini` is in `backend/` and configures the test runner automatically. From the `backend/` directory:

```bash
pytest tests/
```

Use `--tb=line` for a compact summary:

```bash
pytest tests/ --tb=line
```

### Test files

**`conftest.py`** — shared fixtures and factory helpers. Provides the in-memory engine, a per-test db session with rollback, a client fixture that overrides each route's `get_db` dependency, and factory functions (`make_speedtest_result`, `make_connectivity_check`, etc.) for inserting test data with sensible defaults.

**`test_ingest.py`** — classification logic and CSV ingestion for both speedtest and connectivity services.

- `classify_speed` boundary conditions: exact threshold values, NORMAL/DEGRADED/CRITICAL transitions, custom threshold override, zero speeds
- `ingest_speedtest`: successful rows routed to `speedtest_results`, failed rows to `speedtest_failures`, mixed CSV split correctly, deduplication on re-ingest, classification persisted, custom thresholds read from settings at ingest time, empty CSV handled gracefully
- `reclassify_all`: existing rows updated when threshold changes, returns correct count, leaves already-correct rows untouched
- `ingest_connectivity`: online and offline checks stored correctly, null latency on offline rows, deduplication, mixed checks, empty CSV

**`test_settings.py`** — settings repository and API endpoints.

- Repository: defaults returned when DB is empty, stored values override defaults, unset keys still return defaults, single-key get, upsert insert and update, partial updates preserve other keys, numeric values stored as strings
- API: GET returns full dict with defaults, PUT persists and returns updated values, partial updates, threshold values round-trip correctly

**`test_endpoints.py`** — HTTP layer for speedtest and connectivity routes.

- `/latest`: returns null on empty DB, returns most recent result, returns failure if failure is most recent
- `/count`: zeros on empty DB, correct totals across results and failures
- `/history`: wide range returns all records, `from_dt` and `to_dt` filters, empty result outside range, missing params return 422
- `/incidents`: no incidents when all NORMAL, consecutive DEGRADED records grouped into one incident, type changes produce separate incidents, failures included, required fields present, missing params return 422
- Connectivity equivalents of the above

**`test_summary.py`** — daily summary endpoints and aggregation service.

- `/latest`: null on empty DB, returns most recent by date
- `/history`: date range filters, empty result outside range, required fields present
- Aggregation: creates DailySummary from raw records, idempotent on re-run, skips records within the 7-day cutoff window, counts failures correctly, computes outage minutes from consecutive offline checks, background task body verified by calling `aggregate_old_records` directly

**`test_report.py`** — PDF generation service and report endpoint.

- `generate_report`: returns bytes, valid PDF magic bytes, non-trivial file size, subscriber name/provider/plan from settings appear in extracted text, configured download guarantee threshold appears in text, below-guarantee day count correct
- Endpoint: 200 status, `application/pdf` content type, valid PDF bytes, Content-Disposition attachment header with `.pdf` filename, works with real DB data, missing date params return 422

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
        ├── SpeedChart.jsx            # Download/upload time series with performance zones
        ├── PingChart.jsx             # Ping latency time series
        ├── UptimeChart.jsx           # Donut charts for connectivity and speedtest uptime
        ├── IncidentTable.jsx         # Grouped incident log with severity highlighting
        ├── SummarySection.jsx        # Historical data section with range toggle and PDF export
        ├── SummaryChart.jsx           # Grouped bar + line chart over daily summaries
        ├── SummaryStats.jsx           # Five summary stat cards (outage time, avg speed, etc.)
        └── SettingsModal.jsx          # Gear icon modal for subscriber details and thresholds
```

### Component Overview

`App.jsx` is the single stateful root. It owns the selected time range, fetches all six data endpoints in parallel on range change, and passes data down to display components. The time range is stored as a preset (hours) or explicit from/to pair; the effective range is computed fresh on each fetch so preset ranges always use the current time.

`client.js` exports five typed objects (`speedtest`, `connectivity`, `summary`, `settings`, and the report URL helper) wrapping a shared axios instance. In production requests are relative to the current origin and routed through the proxy. In local development `VITE_API_URL=http://localhost:8000` in `frontend/.env.local` overrides the base URL.

`SpeedChart` renders a `ComposedChart` with coloured scatter dots per `performance_status` (green/amber/red), `ReferenceArea` background bands for the NORMAL/DEGRADED/CRITICAL zones, and threshold lines at the configured guarantee and critical values.

`UptimeChart` shows two side-by-side donut charts — one for connectivity uptime (online vs offline checks) and one for speedtest outcome (successful vs failed).

`IncidentTable` displays grouped incidents returned by `/network/speedtest/incidents`, with row colours indicating severity: red for NO INTERNET and CRITICAL, amber for DEGRADED and FAILURE.

`SummarySection` is self-contained — it fetches its own data from `/network/summary/history` based on a "Last 30 days / All time" toggle, renders `SummaryStats` and `SummaryChart`, and provides an "Export PDF Report" button that links directly to the `/network/report/pdf` endpoint for the active date range.

`SettingsModal` opens from the ⚙ gear button in the header. Two sections — Subscriber Details (used in the PDF report) and Service Thresholds (used for classification). An "Auto-derive from contracted speed" button computes degraded (50%) and critical (20%) thresholds automatically. Saving persists to the backend and closes the modal after a brief confirmation flash.

The server health API is currently backend-only. Host metrics are collected and persisted through the server health API, but they are not yet represented in the React frontend. A future frontend integration will expose these metrics through dedicated dashboard components.

### Local Development

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`. Requires the backend to be running separately.

## API Endpoints

### Speedtest — `/network/speedtest`

| Method | Path | Description |
|---|---|---|
| GET | `/latest` | Most recent record across results and failures |
| GET | `/count` | Record counts split by outcome |
| GET | `/history?from_dt=&to_dt=` | All records in time range |
| GET | `/incidents?from_dt=&to_dt=` | Grouped outage/degradation incidents |
| POST | `/ingest` | Parse CSV and persist new records |
| POST | `/reclassify` | Re-classify all stored results against current thresholds |

### Connectivity — `/network/connectivity`

| Method | Path | Description |
|---|---|---|
| GET | `/latest` | Most recent connectivity check |
| GET | `/count` | Record counts split by outcome |
| GET | `/history?from_dt=&to_dt=` | All checks in time range |
| POST | `/ingest` | Parse CSV and persist new records |

### Summary — `/network/summary`

| Method | Path | Description |
|---|---|---|
| GET | `/latest` | Most recent daily summary |
| GET | `/history?from_date=&to_date=` | Daily summaries in date range |
| POST | `/aggregate` | Manually trigger aggregation of records older than 7 days |

### Report — `/network/report`

| Method | Path | Description |
|---|---|---|
| GET | `/pdf?from_date=&to_date=` | Download PDF complaint report for date range |

### Settings — `/network/settings`

| Method | Path | Description |
|---|---|---|
| GET | `` | Get all settings (defaults filled in for unset keys) |
| PUT | `` | Save settings (partial updates supported) |

### Server Health — `/server`

| Method | Path | Description |
|---|---|---|
| POST | `/health` | Submit host server health metrics |
| GET | `/health/latest` | Return the most recent server health sample |
| GET | `/health/history?from_dt=&to_dt=` | Return server health samples within a time range |

The server health submission endpoint requires the Authorization header:

```text
Authorization: Bearer <SERVER_HEALTH_API_TOKEN>
```

A successful submission returns HTTP 201. Requests with a missing or invalid token return HTTP 401.

The latest and history endpoints return filesystem information nested inside each server health sample.

Example filesystem entry:
{
    "id": 1,
    "server_health_id": 7,
    "mountpoint": "/",
    "total_bytes": 502821715968,
    "used_bytes": 216513978368,
    "available_bytes": 260690714624,
    "percent": 45.4,
    "inode_total": 31252480,
    "inode_used": 1280044,
    "inode_free": 29972436,
    "inode_percent": 4.1
}

Filesystem entries are ordered by mount point. Health samples returned by the history endpoint are ordered chronologically.

The endpoint is intended for the host-level server_health_monitor.py collector and is not currently consumed by the frontend.

## Performance Classification

Incoming speedtest results are classified at ingest time based on thresholds stored in the settings table:

| Status | Condition |
|---|---|
| NORMAL | Download ≥ degraded threshold AND upload ≥ upload degraded threshold |
| DEGRADED | Either metric below the degraded threshold but above critical |
| CRITICAL | Either metric below the critical threshold |

Default thresholds for Drei MyLife FIX Data 150:

| Setting | Default | Derivation |
|---|---|---|
| `contracted_download_mbps` | 150.0 | Plan advertised speed |
| `download_degraded_mbps` | 75.0 | 50% of contracted |
| `download_critical_mbps` | 30.0 | 20% of contracted |
| `upload_degraded_mbps` | 5.0 | Based on observed baseline |
| `upload_critical_mbps` | 2.0 | Based on observed baseline |

After changing thresholds in the settings UI, call `POST /network/speedtest/reclassify` to update the classification of all existing stored records.

## Aggregation

Raw records older than 7 days are automatically aggregated into daily summaries after each ingest. Raw records are deleted after aggregation. Aggregation is idempotent — re-running it on already-aggregated days is safe.

Server health records are currently retained independently of the network aggregation process. They are collected at one-minute intervals and are not yet included in the daily network summaries.

## Data Models

### `speedtest_results`

| Column | Type | Description |
|---|---|---|
| `timestamp` | DateTime | Time of the test |
| `status` | String | Always `ONLINE` |
| `ping` | Float | Latency in ms |
| `download_mbps` | Float | Download speed in Mbps |
| `upload_mbps` | Float | Upload speed in Mbps |
| `server_name` | String | Name of the test server |
| `server_id` | Integer | ID of the test server |
| `distance` | Float | Distance to server in km |
| `performance_status` | String | `NORMAL`, `DEGRADED`, or `CRITICAL` |

### `speedtest_failures`

| Column | Type | Description |
|---|---|---|
| `timestamp` | DateTime | Time of the attempt |
| `status` | String | Always `FAILED` |
| `failure_reason` | String | Error message from the CLI. Nullable |

### `connectivity_checks`

| Column | Type | Description |
|---|---|---|
| `timestamp` | DateTime | Time of the check |
| `status` | String | `ONLINE` or `NO INTERNET` |
| `latency_ms` | Float | Average RTT in ms. Null when offline |

### `daily_summaries`

Aggregated per-day records covering both speedtest and connectivity metrics. Generated automatically from raw records older than 7 days.

### `server_health`

Point-in-time host-level metrics submitted by `server_health_monitor.py`.

The table stores:

- CPU utilisation, per-core utilisation, frequency, and load averages
- Memory and swap metrics
- CPU temperatures
- Disk I/O metrics
- Network traffic, errors, and drops
- System uptime

Filesystem metrics are intentionally stored in a separate table rather than as JSON inside `server_health`.

### `server_health_filesystems`

Per-filesystem capacity and inode metrics associated with a `server_health` sample.

| Column | Type | Description |
|---|---|---|
| `id` | Integer | Primary key |
| `server_health_id` | Integer | Foreign key to `server_health.id` |
| `mountpoint` | String | Filesystem mount point |
| `total_bytes` | BigInteger | Total filesystem capacity |
| `used_bytes` | BigInteger | Used filesystem capacity |
| `available_bytes` | BigInteger | Available filesystem capacity |
| `percent` | Float | Capacity utilisation percentage |
| `inode_total` | BigInteger | Total inodes, when available |
| `inode_used` | BigInteger | Used inodes, when available |
| `inode_free` | BigInteger | Free inodes, when available |
| `inode_percent` | Float | Inode utilisation percentage, when available |

Each health sample can have zero or more filesystem records.

For example, a host may report:

```text
server_health id=7
    ├── /           → 45.4% capacity, 4.1% inodes
    └── /boot/efi   → 6.5% capacity, inode metrics unavailable


### `settings`

Key-value store for subscriber details and service thresholds. Defaults are applied at read time for any key not yet stored in the database.

## Architecture Notes

- Scripts are dumb — they log raw numbers only. No quality judgements. The degraded flag threshold is the sole exception and is documented above.
- Backend is the single source of truth for thresholds, classification, and reporting.
- No silent discards — every CSV row is persisted. Failures go to `speedtest_failures`, ensuring uptime metrics are not positively skewed.
- Deduplication — ingest only inserts rows newer than the latest stored timestamp. Re-running ingest is always safe.
- Ingest is manual — there are no cron jobs triggering ingest. The "Ingest Logs" button in the dashboard header is the trigger. This is intentional — the server prioritises resource efficiency and ingest should happen on demand.
- Server health collection is scheduled independently — systemd runs the host collector every minute and submits metrics directly to the authenticated backend endpoint.
- Server health is host-level — the collector runs outside Docker so that it can observe the actual host system rather than the resource usage of an individual container.
- Server health authentication is token-based — the real token is stored outside the repository in `/etc/servermonitor/server-health.env` and is passed to the backend through Docker Compose.
- Systemd units are version-controlled — `systemd/server-health-monitor.service`, `systemd/server-health-monitor.timer`, and `systemd/server-health.env.example` are maintained in the repository. The real environment file is deliberately excluded from version control.
- Frontend server health integration is pending — the backend currently accepts, stores, and exposes host metrics through the server health API, but the React dashboard does not yet display them.
- Server health filesystem metrics are normalised into `server_health_filesystems` rather than stored inside the parent health record.
- Filesystem capacity and inode utilisation are evaluated independently using `OK`, `WARNING`, and `CRITICAL` status thresholds.
- Filesystem status evaluation is deliberately separate from metric collection. The collector records measurements; the backend service evaluates their health status.
- Layered backend — routes → services → repositories. Query logic lives in the repository layer only.
- Alembic owns the schema — `Base.metadata.create_all()` is not used. All schema changes go through versioned migrations in `backend/alembic/versions/`.