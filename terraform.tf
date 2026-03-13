# Provider Configuration
provider "aws" {
  region = "us-east-1"
}

# --- Networking ---
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "dhaka-crime-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a"
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# --- Security Groups ---
resource "aws_security_group" "web_sg" {
  name   = "dhaka-crime-web-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # In production, restrict to your IP
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db_sg" {
  name   = "dhaka-crime-db-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id]
  }
}

# --- IAM Policy (Consolidated) ---
resource "aws_iam_policy" "dhaka_crime_service_policy" {
  name        = "dhaka_crime_service_policy"
  path        = "/"
  description = "Permissions for Dhaka Crime Index services"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
        Resource = ["arn:aws:s3:::dhaka-crime-raw-html-*", "arn:aws:s3:::dhaka-crime-raw-html-*/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.crime_queue.arn
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:GetParameters"]
        Resource = "arn:aws:ssm:us-east-1:*:parameter/dhaka-crime/*"
      }
    ]
  })
}

resource "aws_iam_role" "ec2_role" {
  name = "dhaka_crime_ec2_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.dhaka_crime_service_policy.arn
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "dhaka_crime_ec2_profile"
  role = aws_iam_role.ec2_role.name
}

# --- S3 & SQS ---
resource "aws_s3_bucket" "html_storage" {
  bucket = "dhaka-crime-raw-html-prod-${random_id.id.hex}"
}

resource "random_id" "id" {
  byte_length = 4
}

resource "aws_sqs_queue" "crime_queue" {
  name = "crime-extraction-queue"
}

# --- Secrets (SSM) ---
variable "database_master_password" {
  description = "The master password for the RDS database"
  type        = string
  sensitive   = true
}

resource "aws_ssm_parameter" "db_password" {
  name  = "/dhaka-crime/production/database/password/master"
  type  = "SecureString"
  value = var.database_master_password
}

# --- Database (RDS) ---
resource "aws_db_instance" "postgres" {
  identifier           = "dhaka-crime-db"
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "16"
  instance_class       = "db.t4g.micro"
  db_name              = "crimedb"
  username             = "crimeadmin"
  password             = var.database_master_password
  parameter_group_name = "default.postgres16"
  skip_final_snapshot  = true
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.db_subnet.name
}

resource "aws_db_subnet_group" "db_subnet" {
  name       = "dhaka-crime-db-subnet"
  subnet_ids = [aws_subnet.public.id, aws_subnet.secondary.id]
}

resource "aws_subnet" "secondary" { # RDS needs at least 2 AZs
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}

# --- Compute (EC2) ---
resource "aws_instance" "app_host" {
  ami                    = "ami-0c101f26f147fa7fd" # Amazon Linux 2023 (us-east-1)
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y docker
              service docker start
              usermod -a -G docker ec2-user
              # Install Docker Compose
              curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              EOF

  tags = { Name = "dhaka-crime-app-host" }
}

output "app_public_ip" {
  value = aws_instance.app_host.public_ip
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}