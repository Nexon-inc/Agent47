# Agent47 GCP Infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Data sources
data "google_client_config" "current" {}

# Local values
locals {
  name = "${var.project_name}-${var.environment}"
  common_labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${local.name}-vpc"
  auto_create_subnetworks = false
  mtu                     = 1460

  labels = local.common_labels
}

# Subnets
resource "google_compute_subnetwork" "public" {
  count = length(var.public_subnet_cidrs)

  name          = "${local.name}-public-subnet-${count.index + 1}"
  ip_cidr_range = var.public_subnet_cidrs[count.index]
  region        = var.gcp_region
  network       = google_compute_network.main.id

  private_ip_google_access = true

  labels = local.common_labels
}

resource "google_compute_subnetwork" "private" {
  count = length(var.private_subnet_cidrs)

  name          = "${local.name}-private-subnet-${count.index + 1}"
  ip_cidr_range = var.private_subnet_cidrs[count.index]
  region        = var.gcp_region
  network       = google_compute_network.main.id

  private_ip_google_access = true

  labels = local.common_labels
}

# Cloud NAT for private subnets
resource "google_compute_router" "main" {
  name    = "${local.name}-router"
  region  = var.gcp_region
  network = google_compute_network.main.id

  bgp {
    asn = 64514
  }
}

resource "google_compute_router_nat" "main" {
  name                               = "${local.name}-nat"
  router                            = google_compute_router.main.name
  region                            = var.gcp_region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# GKE Cluster
resource "google_container_cluster" "main" {
  name     = local.name
  location = var.gcp_region

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.private[0].name

  # Enable network policy
  network_policy {
    enabled = true
  }

  # Enable private nodes
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All"
    }
  }

  # Enable workload identity
  workload_identity_config {
    workload_pool = "${var.gcp_project_id}.svc.id.goog"
  }

  # Enable binary authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # Enable cost management
  cost_management_config {
    enabled = true
  }

  labels = local.common_labels
}

# Node Pool
resource "google_container_node_pool" "main" {
  name       = "${local.name}-nodes"
  location   = var.gcp_region
  cluster    = google_container_cluster.main.name
  node_count = var.node_count

  node_config {
    preemptible  = var.enable_spot_instances
    machine_type = var.node_instance_type
    disk_size_gb = 100
    disk_type    = "pd-standard"

    # Enable workload identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Enable secure boot
    shielded_instance_config {
      enable_secure_boot = true
    }

    # Enable integrity monitoring
    shielded_instance_config {
      enable_integrity_monitoring = true
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = local.common_labels

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "main" {
  name             = "${local.name}-database"
  database_version = "POSTGRES_15"
  region           = var.gcp_region

  settings {
    tier = var.db_instance_class

    disk_size = var.db_allocated_storage
    disk_type = "PD_SSD"

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      location                       = var.gcp_region
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
      require_ssl     = true
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  deletion_protection = var.environment == "prod"

  labels = local.common_labels
}

resource "google_sql_database" "main" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "main" {
  name     = var.db_username
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

# Memorystore Redis
resource "google_redis_instance" "main" {
  name           = "${local.name}-redis"
  tier           = "STANDARD_HA"
  memory_size_gb = 1
  region         = var.gcp_region

  authorized_network = google_compute_network.main.id

  redis_version     = "REDIS_7_0"
  display_name      = "Agent47 Redis Instance"
  reserved_ip_range = "10.0.0.0/29"

  labels = local.common_labels
}

# Cloud Storage Bucket
resource "google_storage_bucket" "main" {
  name          = "${local.name}-storage-${random_string.bucket_suffix.result}"
  location      = var.gcp_region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = local.common_labels
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Load Balancer
resource "google_compute_global_address" "main" {
  name = "${local.name}-ip"
}

resource "google_compute_global_forwarding_rule" "main" {
  name       = "${local.name}-forwarding-rule"
  target     = google_compute_target_https_proxy.main.id
  port_range = "443"
  ip_address = google_compute_global_address.main.address
}

resource "google_compute_target_https_proxy" "main" {
  name             = "${local.name}-https-proxy"
  url_map          = google_compute_url_map.main.id
  ssl_certificates = [google_compute_managed_ssl_certificate.main.id]
}

resource "google_compute_url_map" "main" {
  name            = "${local.name}-url-map"
  default_service = google_compute_backend_service.main.id
}

resource "google_compute_backend_service" "main" {
  name        = "${local.name}-backend"
  protocol    = "HTTP"
  port_name   = "http"
  timeout_sec = 30

  backend {
    group = google_container_node_pool.main.instance_group_urls[0]
  }

  health_checks = [google_compute_health_check.main.id]
}

resource "google_compute_health_check" "main" {
  name               = "${local.name}-health-check"
  check_interval_sec = 5
  timeout_sec        = 5
  healthy_threshold  = 2
  unhealthy_threshold = 3

  http_health_check {
    request_path = "/health"
    port         = "8000"
  }
}

resource "google_compute_managed_ssl_certificate" "main" {
  name = "${local.name}-ssl-cert"

  managed {
    domains = [var.domain_name, "*.${var.domain_name}"]
  }
}

# Cloud Monitoring
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notification Channel"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

resource "google_monitoring_alert_policy" "high_cpu" {
  display_name = "High CPU Usage"
  combiner     = "OR"

  conditions {
    display_name = "High CPU usage"

    condition_threshold {
      filter          = "resource.type=\"gke_container\" AND resource.labels.cluster_name=\"${google_container_cluster.main.name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.8

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"
  }
}

# IAM
resource "google_service_account" "gke" {
  account_id   = "${local.name}-gke"
  display_name = "GKE Service Account"
}

resource "google_project_iam_member" "gke_logging" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke.email}"
}

resource "google_project_iam_member" "gke_monitoring" {
  project = var.gcp_project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke.email}"
}

resource "google_project_iam_member" "gke_monitoring_viewer" {
  project = var.gcp_project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.gke.email}"
}

# Variables
variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
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

variable "alert_email" {
  description = "Email for alerts"
  type        = string
  default     = ""
}
