# Invalid Terraform - Missing Required Fields
# This file is intentionally incomplete to test error handling

# EC2 instance without instance_type
resource "aws_instance" "missing_type" {
  # instance_type is MISSING - should fail
  ami = "ami-0c55b159cbfafe1f0"
}

# RDS instance without instance_class
resource "aws_db_instance" "missing_class" {
  # instance_class is MISSING - should fail
  allocated_storage = 20
  engine            = "postgres"
}
