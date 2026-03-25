# Database Setup
resource "aws_db_instance" "main" {
  instance_class    = "db.t3.small"
  allocated_storage = 50
}
