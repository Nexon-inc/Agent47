# Agent47 Terraform Outputs

# Cluster Information
output "cluster_name" {
  description = "Name of the Kubernetes cluster"
  value       = module.kubernetes.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint of the Kubernetes cluster"
  value       = module.kubernetes.cluster_endpoint
}

output "cluster_ca_certificate" {
  description = "CA certificate of the Kubernetes cluster"
  value       = module.kubernetes.cluster_ca_certificate
  sensitive   = true
}

# Networking
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

# Database
output "database_endpoint" {
  description = "Endpoint of the database"
  value       = module.database.endpoint
}

output "database_port" {
  description = "Port of the database"
  value       = module.database.port
}

output "database_name" {
  description = "Name of the database"
  value       = module.database.name
}

# Redis
output "redis_endpoint" {
  description = "Endpoint of the Redis cluster"
  value       = module.redis.endpoint
}

output "redis_port" {
  description = "Port of the Redis cluster"
  value       = module.redis.port
}

# Load Balancer
output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = module.load_balancer.dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.load_balancer.zone_id
}

# Storage
output "storage_bucket_name" {
  description = "Name of the storage bucket"
  value       = module.storage.bucket_name
}

output "storage_bucket_arn" {
  description = "ARN of the storage bucket"
  value       = module.storage.bucket_arn
}

# Monitoring
output "monitoring_dashboard_url" {
  description = "URL of the monitoring dashboard"
  value       = module.monitoring.dashboard_url
}

output "prometheus_endpoint" {
  description = "Endpoint of Prometheus"
  value       = module.monitoring.prometheus_endpoint
}

output "grafana_endpoint" {
  description = "Endpoint of Grafana"
  value       = module.monitoring.grafana_endpoint
}

# Security
output "security_group_id" {
  description = "ID of the security group"
  value       = module.security.security_group_id
}

# Application URLs
output "application_url" {
  description = "URL of the application"
  value       = "https://${var.domain_name}"
}

output "api_url" {
  description = "URL of the API"
  value       = "https://api.${var.domain_name}"
}

output "admin_url" {
  description = "URL of the admin panel"
  value       = "https://admin.${var.domain_name}"
}

# Connection Information
output "kubectl_config" {
  description = "Kubectl configuration command"
  value       = module.kubernetes.kubectl_config_command
}

output "helm_install_command" {
  description = "Helm install command for Agent47"
  value       = "helm install agent47 ./helm-charts/agent47 --namespace agent47 --create-namespace"
}

# Cost Information
output "estimated_monthly_cost" {
  description = "Estimated monthly cost in USD"
  value       = module.kubernetes.estimated_cost
}

# Backup Information
output "backup_schedule" {
  description = "Backup schedule"
  value       = var.backup_schedule
}

output "backup_retention_days" {
  description = "Backup retention period in days"
  value       = var.backup_retention_days
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "cloud_provider" {
  description = "Cloud provider"
  value       = var.cloud_provider
}

output "region" {
  description = "Deployment region"
  value       = var.cloud_provider == "aws" ? var.aws_region : var.cloud_provider == "gcp" ? var.gcp_region : var.azure_location
}
