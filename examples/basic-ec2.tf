# Basic EC2 Instance
resource "aws_instance" "app" {
  instance_type = "t3.small"
}
