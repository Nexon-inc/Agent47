# Ubuntu VM Setup Guide

This checklist walks through installing every dependency needed to run the full Agent47 platform (backend, frontend, admin panel, monitoring stack) on a fresh Ubuntu 22.04+ virtual machine. Follow each step in order; commands assume sudo privileges.

---

## 1. Base OS Preparation

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git curl wget ca-certificates \
    apt-transport-https gnupg lsb-release unzip software-properties-common
sudo apt install -y python3.11 python3.11-venv python3.11-dev pipx
python3.11 -m pip install --upgrade pip setuptools wheel
```

> **Optional:** If your VM ships with an older Python, enable the `deadsnakes` PPA first:  
> `sudo add-apt-repository ppa:deadsnakes/ppa -y`

---

## 2. Install Docker Engine + Compose Plugin

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# run docker as non-root
sudo usermod -aG docker $USER
newgrp docker

# verify
docker version
docker compose version
```

> If you still need the standalone `docker-compose` binary:  
> `sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.8/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose`

---

## 3. Install Node.js, npm, and pnpm

Use `nvm` for easy upgrades:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# corepack gives access to pnpm/yarn
corepack enable
npm install -g pnpm
```

Verify versions (`node -v`, `npm -v`, `pnpm -v`). The frontend currently targets Node 20, but Node 18+ works.

---

## 4. Clone Repository & Environment Files

```bash
mkdir -p ~/workspace && cd ~/workspace
git clone https://github.com/your-org/agent47.git
cd agent47

cp env.example .env
```

Fill `.env` with your Supabase, Groq, Redis, Kafka, and email credentials. Required keys (non-exhaustive):

- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DB_URL`, `SUPABASE_STORAGE_BUCKET`, `SUPABASE_STORAGE_URL`
- `GROQ_API_KEY`, `GROQ_TTS_MODEL`, `GROQ_STT_MODEL`
- `SECURITY_SECRET_KEY` (fallbacks to `JWT_SECRET_KEY`)
- `REDIS_HOST`, `KAFKA_BOOTSTRAP_SERVERS`
- `OLLAMA_*` only if running local models

When migrating from Windows, copy any secrets you stored there into the new `.env`.

---

## 5. Optional: Local Python Dev Environment

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install  # optional formatting hooks
```

Run backend locally (without Docker) using `uvicorn main:app --reload` or `python main.py`.

---

## 6. Optional: Local Node Dev Environment

```bash
cd frontend
npm install   # or pnpm install
npm run dev
```

Expose `NEXT_PUBLIC_*` variables in `.env.local` if needed for the Next.js dev server.

---

## 7. Start Full Platform with Docker Compose

```bash
cd ~/workspace/agent47
docker compose pull        # fetches latest images (first time)
docker compose up -d       # launches backend, frontend, agents, infra
docker compose ps          # verify services

# view logs
docker compose logs -f backend
docker compose logs -f frontend
```

Key local endpoints:

- Frontend UI: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Admin portal: `http://localhost:3000/admin`
- Grafana: `http://localhost:3001` (default `admin/admin`)
- Prometheus: `http://localhost:9090`

---

## 8. Post-Setup Checks

1. **Database connectivity** – run `python backend/verify_env_setup.py`
2. **Service health** – `scripts/verify-services.sh` (requires bash)
3. **Kafka & Zookeeper** – `docker compose logs kafka zookeeper`
4. **Redis** – `redis-cli -h localhost -p 6379 ping`
5. **Supabase** – ensure RLS + service role keys configured in Supabase dashboard

---

## 9. Troubleshooting Tips

- **Docker permissions** – ensure your user is in the `docker` group; run `newgrp docker`.
- **Missing kernels** – on some VM providers you may need `sudo apt install linux-headers-$(uname -r)`.
- **Low disk space** – prune unused data with `docker system prune -a`.
- **SSL cert errors** – check that `/etc/ssl/certs/ca-certificates.crt` exists and run `sudo update-ca-certificates`.
- **Kafka fails to start** – delete volumes `docker volume rm agent47_kafka_data agent47_redis_data` (data loss!) or reset Compose services.
- **Supabase RLS errors** – confirm `.env` includes `SUPABASE_SERVICE_ROLE_KEY` and backend logs show successful bypass.

---

## 10. Launch Checklist

- [ ] `.env` populated with production-ready secrets
- [ ] Docker Desktop **NOT** required (pure Linux Docker works)
- [ ] `docker compose ps` shows all services healthy
- [ ] Admin login works with super admin credentials
- [ ] Kafka topics verifying via `kafka-topics --bootstrap-server localhost:9092 --list`
- [ ] Redis cache accessible (`redis-cli ping`)
- [ ] Frontend + backend reachable from browser
- [ ] Monitoring dashboards loading (Grafana/Prometheus)
- [ ] Backups configured (Supabase or external)

Keep this file handy after migrating from Windows. It doubles as a disaster-recovery runbook for rebuilding the stack on any Ubuntu host.


