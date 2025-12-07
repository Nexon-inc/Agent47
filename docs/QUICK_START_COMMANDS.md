# 🚀 Agent47 Quick Start Commands

## 📋 Essential Installation Commands

### 1. System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git build-essential

# Install Java (required for Kafka)
sudo apt install -y openjdk-11-jdk

# Install Python 3.9+
sudo apt install -y python3.9 python3.9-pip python3.9-venv python3.9-dev

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Clone and Setup
```bash
# Clone repository
git clone https://github.com/your-username/Agent47.git
cd Agent47

# Copy environment file
cp env.example .env

# Edit environment variables
nano .env
```

### 3. Quick Start (Docker)
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Manual Service Installation
```bash
# PostgreSQL
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Redis
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Kafka
cd /opt
sudo wget https://downloads.apache.org/kafka/2.13-3.6.0/kafka_2.13-3.6.0.tgz
sudo tar -xzf kafka_2.13-3.6.0.tgz
sudo mv kafka_2.13-3.6.0 kafka
sudo chown -R $USER:$USER /opt/kafka

# ChromaDB
pip3 install chromadb
```

## 🔧 Service Management

### Start/Stop Services
```bash
# Docker services
docker-compose up -d          # Start all
docker-compose down           # Stop all
docker-compose restart backend # Restart specific

# Manual services
sudo systemctl start postgresql
sudo systemctl start redis
sudo systemctl start kafka
sudo systemctl start zookeeper
```

### Health Checks
```bash
# Core services
curl http://localhost:8000/health
curl http://localhost:8009/api/v1/heartbeat
redis-cli ping
pg_isready -h localhost -p 5432

# Agents
curl http://localhost:8000/api/agents/aria/health
curl http://localhost:8000/api/agents/clara/health
curl http://localhost:8000/api/agents/eric/health
```

## 🛠️ Troubleshooting

### Common Issues
```bash
# Port conflicts
sudo netstat -tulpn | grep :8000
sudo kill -9 <PID>

# Docker issues
docker system prune -a
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Database issues
docker-compose logs postgres
sudo systemctl restart postgresql

# Memory issues
free -h
docker stats
```

### Logs
```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis

# System logs
sudo journalctl -u postgresql -f
sudo journalctl -u redis -f
sudo journalctl -u kafka -f
```

## 📱 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin
- **Health Check**: http://localhost:8000/health

### Agent Endpoints
- **Aria**: http://localhost:8000/api/agents/aria
- **Clara**: http://localhost:8000/api/agents/clara
- **Eric**: http://localhost:8000/api/agents/eric
- **Jackie**: http://localhost:8000/api/agents/jackie
- **Joe**: http://localhost:8000/api/agents/joe
- **Purity**: http://localhost:8000/api/agents/purity
- **Shakes**: http://localhost:8000/api/agents/shakes

## 🔑 Essential Environment Variables

```bash
# Required
CHUTES_API_KEY=your_chutes_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
DB_POSTGRES_PASSWORD=your_secure_password_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# Optional but recommended
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your_s3_bucket_name
FACEBOOK_APP_ID=your_facebook_app_id
TWITTER_API_KEY=your_twitter_api_key
```

## 🚀 One-Line Startup

```bash
# Complete setup and start
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $USER && sudo apt install -y openjdk-11-jdk python3.9 python3.9-pip nodejs git && git clone https://github.com/your-username/Agent47.git && cd Agent47 && cp env.example .env && docker-compose up -d
```

## 📊 Monitoring

```bash
# Check all services
docker-compose ps

# View resource usage
docker stats

# Check logs
docker-compose logs -f

# Health check
curl http://localhost:8000/health
```

## 🔄 Backup & Recovery

```bash
# Database backup
pg_dump -h localhost -U agent47 agent47_db > backup.sql

# Redis backup
redis-cli BGSAVE

# Configuration backup
tar -czf config_backup.tar.gz .env docker-compose.yml
```

---

**💡 Tip**: Use `./scripts/start.sh` for automated startup with verification!
