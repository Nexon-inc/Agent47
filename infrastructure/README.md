# 🏗️ Agent47 Infrastructure

This directory contains all infrastructure-related configurations, documentation, and deployment scripts for the Agent47 platform.

## 📁 Directory Structure

```
infrastructure/
├── README.md                 # This file
├── grok-llm/                 # Grok LLM service configuration
│   ├── Dockerfile           # Grok LLM container
│   ├── requirements.txt     # Python dependencies
│   ├── main.py             # Grok LLM service
│   ├── download_model.py   # Model download script
│   └── start.sh            # Startup script
├── kubernetes/              # Kubernetes manifests
│   ├── namespace.yaml      # Namespace configuration
│   ├── configmap.yaml      # Configuration maps
│   ├── secrets.yaml        # Secrets (encrypted)
│   ├── postgres.yaml       # PostgreSQL deployment
│   ├── redis.yaml          # Redis deployment
│   ├── kafka.yaml          # Kafka deployment
│   ├── chromadb.yaml       # ChromaDB deployment
│   ├── backend.yaml        # Backend API deployment
│   ├── frontend.yaml       # Frontend deployment
│   ├── agents/             # Individual agent deployments
│   └── monitoring/         # Monitoring stack
├── terraform/               # Infrastructure as Code
│   ├── main.tf             # Main Terraform configuration
│   ├── variables.tf        # Variable definitions
│   ├── outputs.tf          # Output definitions
│   ├── aws/                # AWS-specific configurations
│   ├── gcp/                # GCP-specific configurations
│   └── azure/              # Azure-specific configurations
├── monitoring/              # Monitoring configurations
│   ├── prometheus.yml      # Prometheus configuration
│   ├── grafana/            # Grafana dashboards
│   └── alerts/             # Alert rules
├── nginx/                   # Reverse proxy configuration
│   ├── nginx.conf          # Main Nginx configuration
│   ├── ssl/                # SSL certificates
│   └── templates/          # Configuration templates
└── scripts/                 # Deployment and utility scripts
    ├── deploy.sh           # Deployment script
    ├── backup.sh           # Backup script
    └── health-check.sh     # Health check script
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (for K8s deployment)
- Terraform (for cloud deployment)
- kubectl (for K8s management)

### Local Development

```bash
# Start all services locally
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]
```

### Kubernetes Deployment

```bash
# Apply all Kubernetes manifests
kubectl apply -f kubernetes/

# Check deployment status
kubectl get pods -n agent47

# Access services
kubectl port-forward svc/agent47-frontend 3000:3000 -n agent47
```

### Cloud Deployment

```bash
# Initialize Terraform
cd terraform/aws  # or gcp/azure
terraform init

# Plan deployment
terraform plan

# Apply configuration
terraform apply
```

## 🔧 Service Configuration

### Port Allocation

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js application |
| Backend API | 8000 | Main FastAPI backend |
| Grok LLM | 8001 | Fallback LLM service |
| Aria Agent | 8002 | Content creation agent |
| Clara Agent | 8003 | Customer support agent |
| Eric Agent | 8004 | Sales & CRM agent |
| Jackie Agent | 8005 | Marketing agent |
| Joe Agent | 8006 | Research agent |
| Purity Agent | 8007 | Business creation agent |
| Shakes Agent | 8008 | Content writing agent |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & sessions |
| Kafka | 9092 | Message broker |
| ChromaDB | 8000 | Vector database |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Monitoring dashboard |
| Nginx | 80/443 | Reverse proxy |

### Environment Variables

Key environment variables for each service:

#### Backend Services
```bash
# Database
DB_POSTGRES_HOST=postgres
DB_POSTGRES_PORT=5432
DB_POSTGRES_USER=agent47
DB_POSTGRES_PASSWORD=agent47_password
DB_POSTGRES_DB=agent47_db

# Cache
REDIS_HOST=redis
REDIS_PORT=6379

# Message Broker
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# AI Services
CHUTES_API_KEY=your_chutes_api_key
GROK_API_URL=http://grok-llm:8001
```

#### Agent Services
```bash
# Each agent has its own port and configuration
AGENT_NAME=aria
AGENT_PORT=8002
DB_POSTGRES_HOST=postgres
REDIS_HOST=redis
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

## 📊 Monitoring & Observability

### Prometheus Metrics

- **Application Metrics**: Request rates, response times, error rates
- **Agent Metrics**: Task completion rates, processing times
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: User activity, subscription usage

### Grafana Dashboards

- **System Overview**: Overall platform health
- **Agent Performance**: Individual agent metrics
- **User Analytics**: User behavior and usage patterns
- **Infrastructure**: System resource utilization

### Health Checks

All services include health check endpoints:

```bash
# Backend API
curl http://localhost:8000/health

# Individual agents
curl http://localhost:8002/aria/health
curl http://localhost:8003/clara/health
# ... etc

# Grok LLM
curl http://localhost:8001/health
```

## 🔒 Security

### Network Security

- **Internal Communication**: Services communicate via internal Docker network
- **External Access**: Only frontend and API exposed externally
- **SSL/TLS**: HTTPS termination at Nginx level

### Authentication

- **JWT Tokens**: Secure API authentication
- **OAuth2**: Third-party integrations
- **Role-based Access**: Granular permissions

### Secrets Management

- **Environment Variables**: Sensitive data in environment
- **Kubernetes Secrets**: Encrypted secrets in K8s
- **Cloud Secrets**: AWS Secrets Manager, GCP Secret Manager

## 🚀 Deployment Strategies

### Blue-Green Deployment

```bash
# Deploy new version alongside existing
kubectl apply -f kubernetes/green/

# Switch traffic to new version
kubectl patch service agent47-frontend -p '{"spec":{"selector":{"version":"green"}}}'

# Remove old version
kubectl delete -f kubernetes/blue/
```

### Rolling Updates

```bash
# Update deployment with rolling strategy
kubectl set image deployment/agent47-backend backend=agent47-backend:v2.0.0

# Monitor rollout
kubectl rollout status deployment/agent47-backend
```

### Canary Deployment

```bash
# Deploy canary version
kubectl apply -f kubernetes/canary/

# Gradually increase traffic
kubectl patch service agent47-frontend -p '{"spec":{"selector":{"version":"canary"}}}'
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale backend services
kubectl scale deployment agent47-backend --replicas=5

# Scale individual agents
kubectl scale deployment agent47-aria --replicas=3
```

### Auto-scaling

```yaml
# HPA configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent47-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent47-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🔄 Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -h postgres -U agent47 agent47_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
./scripts/backup.sh
```

### Disaster Recovery

- **Automated Backups**: Daily database backups
- **Multi-region**: Cross-region replication
- **Point-in-time Recovery**: Restore to specific timestamp

## 🛠️ Troubleshooting

### Common Issues

1. **Service Not Starting**
   ```bash
   # Check logs
   docker-compose logs [service-name]
   
   # Check health
   curl http://localhost:[port]/health
   ```

2. **Database Connection Issues**
   ```bash
   # Test connection
   psql -h postgres -U agent47 -d agent47_db
   
   # Check database status
   docker-compose exec postgres pg_isready
   ```

3. **Agent Communication Issues**
   ```bash
   # Check Kafka
   docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
   
   # Check Redis
   docker-compose exec redis redis-cli ping
   ```

### Performance Optimization

- **Database Indexing**: Optimize query performance
- **Caching Strategy**: Redis for frequently accessed data
- **Connection Pooling**: Efficient database connections
- **Load Balancing**: Distribute traffic across instances

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Terraform Documentation](https://www.terraform.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.
