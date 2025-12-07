# Agent47 Infrastructure as Code
# Main Terraform configuration

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

# Configure providers based on selected cloud
provider "aws" {
  region = var.aws_region
  profile = var.aws_profile
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "azurerm" {
  features {}
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

# Local values
locals {
  common_tags = {
    Project     = "Agent47"
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedBy   = "Agent47-Platform"
  }
  
  cluster_name = "${var.project_name}-${var.environment}"
  domain_name  = var.domain_name
}

# Data sources
data "aws_availability_zones" "available" {
  count = var.cloud_provider == "aws" ? 1 : 0
  state = "available"
}

data "google_client_config" "current" {
  count = var.cloud_provider == "gcp" ? 1 : 0
}

# VPC and Networking
module "networking" {
  source = "./modules/networking"
  
  cloud_provider = var.cloud_provider
  project_name   = var.project_name
  environment    = var.environment
  region         = var.aws_region
  availability_zones = var.cloud_provider == "aws" ? data.aws_availability_zones.available[0].names : []
  
  tags = local.common_tags
}

# Kubernetes Cluster
module "kubernetes" {
  source = "./modules/kubernetes"
  
  cloud_provider = var.cloud_provider
  project_name   = var.project_name
  environment    = var.environment
  cluster_name   = local.cluster_name
  
  # Networking
  vpc_id         = module.networking.vpc_id
  subnet_ids     = module.networking.private_subnet_ids
  public_subnet_ids = module.networking.public_subnet_ids
  
  # Node configuration
  node_instance_type = var.node_instance_type
  node_count         = var.node_count
  min_node_count     = var.min_node_count
  max_node_count     = var.max_node_count
  
  # Security
  ssh_key_name = var.ssh_key_name
  
  tags = local.common_tags
}

# Database
module "database" {
  source = "./modules/database"
  
  cloud_provider = var.cloud_provider
  project_name   = var.project_name
  environment    = var.environment
  
  # Networking
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids
  
  # Database configuration
  db_instance_class = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_engine_version = var.db_engine_version
  
  tags = local.common_tags
}

# Redis Cache
module "redis" {
  source = "./modules/redis"
  
  cloud_provider = var.cloud_provider
  project_name   = var.project_name
  environment    = var.environment
  
  # Networking
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids
  
  # Redis configuration
  redis_node_type = var.redis_node_type
  redis_num_cache_nodes = var.redis_num_cache_nodes
  
  tags = local.common_tags
}

# Storage
module "storage" {
  source = "./modules/storage"
  
  cloud_provider = var.cloud_provider
  project_name   = var.project_name
  environment    = var.environment
  
  tags = local.common_tags
}

# Load Balancer
module "load_balancer" {
  source = "./modules/load_balancer"
  
  cloud_provider = var.cloud_provider
  project_name   = var.project_name
  environment    = var.environment
  domain_name    = local.domain_name
  
  # Networking
  vpc_id         = module.networking.vpc_id
  subnet_ids     = module.networking.public_subnet_ids
  
  # SSL Certificate
  certificate_arn = var.certificate_arn
  
  tags = local.common_tags
}

# Monitoring
module "monitoring" {
  source = "./modules/monitoring"
  
  cloud_provider = var.cloud_provider
  project_name   = var.project_name
  environment    = var.environment
  
  tags = local.common_tags
}

# Security
module "security" {
  source = "./modules/security"
  
  cloud_provider = var.cloud_provider
  project_name   = var.project_name
  environment    = var.environment
  
  tags = local.common_tags
}
