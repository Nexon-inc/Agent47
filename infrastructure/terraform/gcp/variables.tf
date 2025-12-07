# GCP-specific variables for Agent47

# GCP Configuration
variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

# Kubernetes Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for GKE cluster"
  type        = string
  default     = "1.28"
}

variable "node_instance_type" {
  description = "Instance type for GKE nodes"
  type        = string
  default     = "e2-medium"
}

variable "node_count" {
  description = "Number of GKE nodes"
  type        = number
  default     = 3
}

variable "min_node_count" {
  description = "Minimum number of GKE nodes"
  type        = number
  default     = 2
}

variable "max_node_count" {
  description = "Maximum number of GKE nodes"
  type        = number
  default     = 10
}

# Supabase Configuration
variable "supabase_project_id" {
  description = "Supabase project ID"
  type        = string
}

variable "supabase_api_url" {
  description = "Supabase API URL"
  type        = string
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key"
  type        = string
  sensitive   = true
}

variable "supabase_service_role_key" {
  description = "Supabase service role key"
  type        = string
  sensitive   = true
}

# Database Configuration (for Supabase)
variable "db_name" {
  description = "Database name in Supabase"
  type        = string
  default     = "agent47_db"
}

# Redis Configuration (will use Supabase Edge Functions or external Redis)
variable "redis_enabled" {
  description = "Enable Redis (use external service or Supabase Edge Functions)"
  type        = bool
  default     = false
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable monitoring stack"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable logging stack"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email for alerts"
  type        = string
  default     = ""
}

# Security Configuration
variable "enable_private_nodes" {
  description = "Enable private GKE nodes"
  type        = bool
  default     = true
}

variable "enable_workload_identity" {
  description = "Enable workload identity"
  type        = bool
  default     = true
}

# Cost Optimization
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "enable_autoscaling" {
  description = "Enable auto-scaling"
  type        = bool
  default     = true
}

# General Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "agent47"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "agent47.com"
}

# Backup Configuration
variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

# Scaling Configuration
variable "cpu_threshold" {
  description = "CPU threshold for auto-scaling"
  type        = number
  default     = 70
}

variable "memory_threshold" {
  description = "Memory threshold for auto-scaling"
  type        = number
  default     = 80
}
