# Development Environment

resource "aws_instance" "dev_server" {
  instance_type = "t3.micro"
}

resource "aws_db_instance" "dev_db" {
  instance_class    = "db.t3.micro"
  allocated_storage = 20
}

resource "aws_s3_bucket" "dev_assets" {
}
