# Production Infrastructure

# Web Servers
resource "aws_instance" "web1" {
  instance_type = "t3.large"
}

resource "aws_instance" "web2" {
  instance_type = "t3.large"
}

# Database
resource "aws_db_instance" "prod_db" {
  instance_class    = "db.t3.large"
  allocated_storage = 200
}

# Storage
resource "aws_s3_bucket" "data" {
}

# Load Balancer
resource "aws_lb" "main" {
}

# NAT Gateway
resource "aws_nat_gateway" "main" {
}
