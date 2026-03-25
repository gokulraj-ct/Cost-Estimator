# Microservices Architecture

# API Service
resource "aws_instance" "api" {
  instance_type = "t3.medium"
}

# Worker Service
resource "aws_instance" "worker" {
  instance_type = "t3.small"
}

# Cache
resource "aws_elasticache_cluster" "redis" {
  node_type = "cache.t3.micro"
  num_cache_nodes = 2
}

# Database
resource "aws_db_instance" "postgres" {
  instance_class    = "db.t3.medium"
  allocated_storage = 100
}

# Storage
resource "aws_s3_bucket" "uploads" {
}

# Load Balancer
resource "aws_lb" "api_lb" {
}
