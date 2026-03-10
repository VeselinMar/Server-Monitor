# Deployment Guide

This guide sets up a shared reverse proxy routing multiple applications by path on a single server, reachable at `http://servermonitor` from any device on the local network.

```
http://servermonitor/servermonitor  → ServerMonitor
http://servermonitor/photos         → Immich (future)
http://servermonitor/music          → Navidrome (future)
http://servermonitor/files          → Nextcloud (future)
```

Each app has its own `docker-compose.yml`. A single standalone proxy container sits in front of all of them and is the only thing bound to port 80 on the host.

---

## Prerequisites

- Ubuntu Server
- Docker and Docker Compose installed
- Server IP known and stable (assign a static IP via DHCP reservation on your router)

Install Docker if not already present:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

---

## Step 1 — Create the shared Docker network

All containers that need to talk to the proxy must join a shared network. Create it once — it persists across restarts and rebuilds:

```bash
docker network create proxy-network
```

---

## Step 2 — Set up the standalone proxy

The proxy is independent of all apps. It is the only container that binds port 80.

```bash
mkdir -p ~/proxy
```

Create `~/proxy/nginx.conf`:

```nginx
server {
    listen 80;
    server_name servermonitor;

    # ServerMonitor
    location /servermonitor/ {
        proxy_pass         http://servermonitor-frontend:80/;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /servermonitor/network/ {
        proxy_pass         http://servermonitor-backend:8000/network/;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering    off;
        proxy_read_timeout 120s;
    }

    # Add future apps here — one location block per app
}
```

Create `~/proxy/docker-compose.yml`:

```yaml
services:
  proxy:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - proxy-network

networks:
  proxy-network:
    external: true
```

Start the proxy:

```bash
cd ~/proxy
sudo docker compose up -d
sudo docker compose ps
```

---

## Step 3 — DNS resolution

The ZTE MC889 router does not support local DNS host records. Resolution is handled per-device via `/etc/hosts`.

**On each Linux machine:**

```bash
echo "192.168.254.150  servermonitor" | sudo tee -a /etc/hosts
```

**On mobile devices and smart TVs:** install AdGuard Home on the server (future — see planned additions below) and point devices to the server as their DNS server.

To find the server's IP:

```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

---

## Step 4 — Deploy ServerMonitor

Clone the repository:

```bash
cd ~
git clone https://github.com/VeselinMar/Server-Monitor.git
cd Server-Monitor/docker
```

Ensure the data directory exists and is writable:

```bash
ls -lh /mnt/media/monitoring/data/
```

The backend expects:
- `/mnt/media/monitoring/data/speedtest.csv` — written by `speedtest_monitor.sh`
- `/mnt/media/monitoring/data/connectivity.csv` — written by `connectivity_check.sh`
- `/mnt/media/monitoring/data/monitoring.db` — created automatically by Alembic on first start

Build and start:

```bash
sudo docker compose up -d --build
sudo docker logs servermonitor-backend --tail 15
```

The backend logs should show Alembic running the initial migration and uvicorn starting cleanly. If the DB file is owned by root and not writable by the container, fix permissions:

```bash
sudo chown $USER:$USER /mnt/media/monitoring/data/monitoring.db
```

Trigger the initial ingest to populate the database from existing CSV logs:

```bash
curl -s -X POST http://servermonitor/servermonitor/network/speedtest/ingest
curl -s -X POST http://servermonitor/servermonitor/network/connectivity/ingest
curl -s http://servermonitor/servermonitor/network/speedtest/count
curl -s http://servermonitor/servermonitor/network/connectivity/count
```

Verify the dashboard at `http://servermonitor/servermonitor`.

---

## Step 5 — First-time settings

Open the dashboard and click the ⚙ gear icon. Configure:

- Subscriber details (used in PDF reports)
- Contracted download speed — used to auto-derive performance thresholds

After saving thresholds, reclassify existing records:

```bash
curl -s -X POST http://servermonitor/servermonitor/network/speedtest/reclassify
```

---

## Ongoing Operations

### Ingest new data

Ingest is triggered manually via the "Ingest Logs" button in the dashboard header, or via curl:

```bash
curl -s -X POST http://servermonitor/servermonitor/network/speedtest/ingest
curl -s -X POST http://servermonitor/servermonitor/network/connectivity/ingest
```

### Rebuild after code changes

```bash
cd ~/Server-Monitor
git pull
cd docker
sudo docker compose up -d --build
sudo docker image prune -f
```

### Rebuild a single container

```bash
sudo docker compose up -d --build backend
sudo docker compose up -d --build frontend
```

### View logs

```bash
# Backend
sudo docker logs servermonitor-backend -f

# Frontend
sudo docker logs servermonitor-frontend -f

# Proxy
sudo docker logs proxy-proxy-1 -f
```

### Update proxy config (add a new app)

Edit `~/proxy/nginx.conf` to add a new `location` block, then reload without downtime:

```bash
cd ~/proxy
sudo docker compose exec proxy nginx -s reload
```

### Clean up old images after rebuild

```bash
sudo docker image prune -f
```

---

## Troubleshooting

**Backend keeps restarting — Alembic migration fails**

Check if a leftover `_new` table is blocking the migration:

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/mnt/media/monitoring/data/monitoring.db')
print(conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())
conn.close()
"
```

Drop any `*_new` tables then restart.

**Alembic runs but tables aren't created**

Check that `alembic/env.py` reads `DATABASE_URL` from the environment, not from `alembic.ini`. The `alembic.ini` default (`sqlite:///./monitoring.db`) resolves to `/app/monitoring.db` inside the container, not `/data/monitoring.db`.

**Ingest returns Internal Server Error**

Check backend logs — most likely the CSV file doesn't exist at the expected path, or the volume mount isn't working:

```bash
sudo docker exec servermonitor-backend ls /data/
```

**502 from the proxy**

The target container isn't running or hasn't joined `proxy-network`. Check:

```bash
sudo docker ps
sudo docker network inspect proxy-network
```

---

## Directory Structure

```
~/
├── proxy/
│   ├── docker-compose.yml
│   └── nginx.conf
│
└── Server-Monitor/
    ├── backend/
    ├── frontend/
    ├── scripts/
    └── docker/
        ├── docker-compose.yml
        ├── backend.dockerfile
        └── frontend.dockerfile
```

---

## Planned Additions

The following will be added to the server stack and this guide updated accordingly:

- **AdGuard Home** — local DNS resolver, enables `servermonitor` to resolve on mobile and TV without per-device `/etc/hosts` entries
- **Immich** — photo and image management (`http://servermonitor/photos`)
- **Navidrome** — music server (`http://servermonitor/music`)
- **Nextcloud** — documents and file storage (`http://servermonitor/files`)