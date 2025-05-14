provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "main_vpc" {
  cidr_block           = "10.0.0.0/20"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "MainVPC"
  }
}

# Subnet
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.10.0.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a"

  tags = {
    Name = "PublicSubnet"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main_vpc.id

  tags = {
    Name = "InternetGateway"
  }
}

# Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "PublicRouteTable"
  }
}

# Route Table Association
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# Security Group for Jump Server (Windows RDP)
resource "aws_security_group" "jump_sg" {
  name        = "JumpSG"
  description = "Allow RDP from Internet"
  vpc_id      = aws_vpc.main_vpc.id

  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "JumpServerSG"
  }
}

# Security Group for Web Server
resource "aws_security_group" "web_sg" {
  name        = "WebSG"
  description = "Allow HTTP from Internet and SSH from Jump"
  vpc_id      = aws_vpc.main_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.jump_sg.id]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "WebServerSG"
  }
}

# Jump Server Instance (Windows Server 2022)
resource "aws_instance" "jump_server" {
  ami                         = "ami-0c798d4b81e585f36" # Windows Server 2022 Base
  instance_type               = "t2.micro"
  subnet_id                   = aws_subnet.public_subnet.id
  vpc_security_group_ids      = [aws_security_group.jump_sg.id]
  key_name                    = "vockey"
  associate_public_ip_address = true

  tags = {
    Name = "JumpServer-Windows"
  }
}

# Web Server Instance (Linux)
resource "aws_instance" "web_server" {
  ami                         = "ami-084568db4383264d4"
  instance_type               = "t2.micro"
  subnet_id                   = aws_subnet.public_subnet.id
  vpc_security_group_ids      = [aws_security_group.web_sg.id]
  key_name                    = "vockey"
  associate_public_ip_address = true

  tags = {
    Name = "WebServer"
  }
}

# Outputs
output "jump_server_ip" {
  value = aws_instance.jump_server.public_ip
}

output "web_server_ip" {
  value = aws_instance.web_server.public_ip
}
