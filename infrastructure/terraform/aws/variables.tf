# AWS-specific variables for Agent47

# AWS Configuration
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "aws_profile" {
  description = "AWS profile to use"
  type        = string
  default     = "default"
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

variable "public_access_cidrs" {
  description = "CIDR blocks allowed to access EKS cluster"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# Kubernetes Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "node_instance_type" {
  description = "Instance type for EKS nodes"
  type        = string
  default     = "t3.medium"
}

variable "node_count" {
  description = "Number of EKS nodes"
  type        = number
  default     = 3
}

variable "min_node_count" {
  description = "Minimum number of EKS nodes"
  type        = number
  default     = 2
}

variable "max_node_count" {
  description = "Maximum number of EKS nodes"
  type        = number
  default     = 10
}

# Database Configuration
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "agent47_db"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "agent47"
}

variable "db_password" {
  description = "Database password"
  type        = string
  default     = "agent47_password"
  sensitive   = true
}

variable "db_instance_class" {
  description = "Database instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Database allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Database maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_engine_version" {
  description = "Database engine version"
  type        = string
  default     = "15.4"
}

# Redis Configuration
variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

# Monitoring Configuration
variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 7
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

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}
