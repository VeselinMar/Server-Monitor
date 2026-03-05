# ServerMonitor

A full-stack network health monitor. Bash scripts run scheduled connectivity and speed tests, appending results to CSV logs. A FastAPI backend ingests the logs and exposes the data via a REST API. A React frontend (in progress) will visualise the metrics as graphs.

---

## Architecture

```
[cron] → speedtest_monitor.sh   → speedtest.csv    ┐
[cron] → connectivity_check.sh → connectivity.csv  ┴→ FastAPI ingest → SQLite → REST API → React frontend
```

---

## Prerequisites

**System:**
- [`speedtest-cli`](https://www.speedtest.net/apps/cli) installed at `/usr/bin/speedtest`
- `jq` for JSON parsing in the speedtest script
- `bc` for float comparison in the speedtest script
- `awk`, `bash` (standard on most Linux systems)

**Backend:**
- Python 3.12+
- pip dependencies via `requirements.txt`

**Frontend:**
- Node.js (coming soon)

---

## Data Pipeline

### Speedtest Monitor

**Location:** `/usr/local/bin/speedtest_monitor.sh`  
**Schedule:** Every hour — `0 * * * *`  
**Log:** `/mnt/media/monitoring/data/speedtest.csv`

Runs a speed test and appends the result to the CSV log. Attempts the test up to 3 times with a 10 second delay between retries, timing out after 180 seconds per attempt.

**Successful row (8 columns):**
```
2026-03-04 03:00:01,ONLINE,32.295,69.76,3.25,Vienna,51547,5.678609643115544
```

**Failed row (9 columns):**
```
2026-03-04 02:00:01,FAILED,,,,,,"Cannot retrieve speedtest configuration"
```

Column order: `timestamp, status, ping, download_mbps, upload_mbps, server_name, server_id, distance[, failure_reason]`

---

### Connectivity Monitor

**Location:** `/usr/local/bin/connectivity_check.sh`  
**Schedule:** Every 20 minutes — `*/20 * * * *`  
**Log:** `/mnt/media/monitoring/data/connectivity.csv`

Pings `8.8.8.8` twice and records whether the connection is up, along with the average round-trip latency. Failed checks record `NO INTERNET` with a null latency.

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

### Cron Setup

Open the crontab on the server:

```bash
sudo crontab -e
```

Add the following lines:

```
0 * * * *    /usr/local/bin/speedtest_monitor.sh
*/20 * * * * /usr/local/bin/connectivity_check.sh
```

---

### Log File Location

All logs are written to:

```
/mnt/media/monitoring/data/
├── speedtest.csv
└── connectivity.csv
```

Ensure this directory exists and is writable before running the scripts:

```bash
mkdir -p /mnt/media/monitoring/data
```

---

### Copying Logs to Development Machine

Add the server's IP to `/etc/hosts` on your dev machine:

```bash
sudo nano /etc/hosts
```

Add:
```
192.168.x.x     home-ken-stein
```

Then copy the logs:

```bash
scp -r vesko@home-ken-stein:/mnt/media/monitoring/data/ /mnt/media/monitoring/data/
```

---

## Backend

### Project Structure

```
backend/
├── main.py                          # FastAPI app entry point
├── api/
│   ├── router.py                    # Top-level API router
│   └── routes/
│       ├── speedtest.py             # Speedtest HTTP endpoints
│       └── connectivity.py         # Connectivity HTTP endpoints
├── core/
│   ├── config.py                    # Environment configuration
│   └── database.py                  # SQLAlchemy engine, session, and base
├── models/
│   ├── speedtest.py                 # SpeedTestResult, SpeedTestFailure
│   └── connectivity.py             # ConnectivityCheck
├── repositories/
│   ├── speedtest_repository.py      # Speedtest query logic
│   └── connectivity_repository.py  # Connectivity query logic
├── schemas/
│   ├── speedtest.py                 # Speedtest response schemas
│   └── connectivity.py             # Connectivity response schemas
├── services/
│   ├── speedtest_service.py         # Speedtest service layer
│   ├── connectivity_service.py     # Connectivity service layer
│   ├── ingest_speedtest.py         # Speedtest CSV ingestion
│   └── ingest_connectivity.py     # Connectivity CSV ingestion
```

### Setup

```bash
cd backend
pip install -r requirements.txt
```

### Configuration

The database URL is configured via the `DATABASE_URL` environment variable. Defaults to a local SQLite file if not set:

```
sqlite:///./monitoring.db
```

To override:

```bash
export DATABASE_URL=postgresql://user:password@localhost/servermonitor
```

### Running

```bash
uvicorn main:app --reload
```

Interactive API docs available at `http://localhost:8000/docs`.

---

## API Endpoints

### Speedtest — `/network/speedtest`

| Method | Path | Description |
|---|---|---|
| `GET` | `/network/speedtest/latest` | Most recent record across results and failures |
| `GET` | `/network/speedtest/count` | Record counts split by outcome |
| `POST` | `/network/speedtest/ingest` | Parse CSV log and persist new records |

#### `GET /network/speedtest/count`
```json
{
  "successful": 120,
  "failed": 8,
  "total": 128
}
```

### Connectivity — `/network/connectivity`

| Method | Path | Description |
|---|---|---|
| `GET` | `/network/connectivity/latest` | Most recent connectivity check |
| `GET` | `/network/connectivity/count` | Record counts split by outcome |
| `POST` | `/network/connectivity/ingest` | Parse CSV log and persist new records |

#### `GET /network/connectivity/count`
```json
{
  "online": 210,
  "offline": 9,
  "total": 219
}
```

---

## Data Models

### `speedtest_results` — successful speed tests

| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| timestamp | DateTime | Time of the test |
| status | String | Always `ONLINE` |
| ping | Float | Latency in ms |
| download_mbps | Float | Download speed in Mbps |
| upload_mbps | Float | Upload speed in Mbps |
| server_name | String | Name of the test server |
| server_id | Integer | ID of the test server |
| distance | Float | Distance to server in km |

### `speedtest_failures` — failed speed tests

| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| timestamp | DateTime | Time of the test |
| status | String | e.g. `FAILED` |
| server_name | String | Nullable |
| server_id | Integer | Nullable |
| distance | Float | Nullable |
| failure_reason | String | Error message from the script |

### `connectivity_checks` — connectivity checks

| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| timestamp | DateTime | Time of the check |
| status | String | `ONLINE` or `NO INTERNET` |
| latency_ms | Float | Average RTT in ms. Null when offline |

---

## Frontend

Coming soon — a React app that will visualise network health metrics over time including download/upload trends, ping history, connectivity uptime, and outage events.

---

## Architecture Notes

- **No silent discards** — every speedtest CSV row is persisted. Failures go to `speedtest_failures`, ensuring uptime metrics are not positively skewed.
- **Deduplication** — ingest compares incoming timestamps against the latest stored record and only inserts new rows. Re-running ingest is safe.
- **Layered backend** — routes → services → repositories. Query logic lives exclusively in the repository layer.
- **Schema auto-creation** — tables are created automatically on startup via `Base.metadata.create_all()`.