# Example Terraform Configuration
# Simple web application infrastructure

provider "aws" {
  region = "us-east-1"
}

# EC2 Instance for web server
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }
  
  tags = {
    Name = "web-server"
    Environment = "production"
  }
}

# RDS Database
resource "aws_db_instance" "database" {
  identifier           = "myapp-db"
  engine              = "postgres"
  engine_version      = "14.7"
  instance_class      = "db.t3.medium"
  allocated_storage   = 100
  storage_type        = "gp2"
  
  db_name  = "myapp"
  username = "admin"
  password = "changeme123"
  
  skip_final_snapshot = true
  
  tags = {
    Name = "myapp-database"
  }
}

# S3 Bucket for static assets
resource "aws_s3_bucket" "assets" {
  bucket = "myapp-assets-bucket"
  
  tags = {
    Name = "assets-bucket"
  }
}

# Application Load Balancer
resource "aws_lb" "app" {
  name               = "myapp-alb"
  internal           = false
  load_balancer_type = "application"
  
  tags = {
    Name = "myapp-alb"
  }
}
