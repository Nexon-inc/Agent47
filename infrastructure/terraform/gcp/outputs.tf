# GCP-specific outputs for Agent47

# GKE Cluster
output "cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.main.name
}

output "cluster_endpoint" {
  description = "Endpoint of the GKE cluster"
  value       = google_container_cluster.main.endpoint
}

output "cluster_ca_certificate" {
  description = "CA certificate of the GKE cluster"
  value       = google_container_cluster.main.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "Location of the GKE cluster"
  value       = google_container_cluster.main.location
}

# VPC and Networking
output "vpc_id" {
  description = "ID of the VPC"
  value       = google_compute_network.main.id
}

output "vpc_name" {
  description = "Name of the VPC"
  value       = google_compute_network.main.name
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = google_compute_subnetwork.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = google_compute_subnetwork.private[*].id
}

output "public_subnet_names" {
  description = "Names of the public subnets"
  value       = google_compute_subnetwork.public[*].name
}

output "private_subnet_names" {
  description = "Names of the private subnets"
  value       = google_compute_subnetwork.private[*].name
}

# Load Balancer
output "load_balancer_ip" {
  description = "IP address of the load balancer"
  value       = google_compute_global_address.main.address
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = google_compute_global_address.main.address
}

# Cloud Storage
output "storage_bucket_name" {
  description = "Name of the Cloud Storage bucket"
  value       = google_storage_bucket.main.name
}

output "storage_bucket_url" {
  description = "URL of the Cloud Storage bucket"
  value       = google_storage_bucket.main.url
}

# Supabase Integration
output "supabase_project_id" {
  description = "Supabase project ID"
  value       = var.supabase_project_id
}

output "supabase_api_url" {
  description = "Supabase API URL"
  value       = var.supabase_api_url
}

# Service Accounts
output "gke_service_account_email" {
  description = "Email of the GKE service account"
  value       = google_service_account.gke.email
}

# SSL Certificate
output "ssl_certificate_name" {
  description = "Name of the SSL certificate"
  value       = google_compute_managed_ssl_certificate.main.name
}

# Connection Information
output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.main.name} --region ${var.gcp_region} --project ${var.gcp_project_id}"
}

output "helm_install_command" {
  description = "Helm install command for Agent47"
  value       = "helm install agent47 ./helm-charts/agent47 --namespace agent47 --create-namespace"
}

# Application URLs
output "application_url" {
  description = "URL of the application"
  value       = "https://${google_compute_global_address.main.address}"
}

output "api_url" {
  description = "URL of the API"
  value       = "https://api.${var.domain_name}"
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "region" {
  description = "GCP region"
  value       = var.gcp_region
}

output "project_id" {
  description = "GCP Project ID"
  value       = var.gcp_project_id
}

# Cost Information
output "estimated_monthly_cost" {
  description = "Estimated monthly cost in USD (approximate)"
  value       = "~$150-400/month depending on usage and instance types (GCP + Supabase)"
}

# Monitoring
output "monitoring_dashboard_url" {
  description = "URL of the monitoring dashboard"
  value       = "https://console.cloud.google.com/monitoring/dashboards?project=${var.gcp_project_id}"
}

output "logging_url" {
  description = "URL of the logging dashboard"
  value       = "https://console.cloud.google.com/logs?project=${var.gcp_project_id}"
}

# Supabase Dashboard
output "supabase_dashboard_url" {
  description = "URL of the Supabase dashboard"
  value       = "https://supabase.com/dashboard/project/${var.supabase_project_id}"
}
