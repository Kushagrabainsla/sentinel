############################################
# variables
############################################
variable "name" {
    type        = string
    description = "Base name/prefix for networking"
}

variable "vpc_cidr" {
    type        = string
    description = "CIDR block for the VPC"
    default     = "10.20.0.0/16"
}

variable "private_subnet_cidrs" {
    type        = list(string)
    description = "Two private subnet CIDRs (different AZs)"
    default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

############################################
# resources
############################################
data "aws_availability_zones" "available" {
    state = "available"
}

resource "aws_vpc" "this" {
    cidr_block           = var.vpc_cidr
    enable_dns_hostnames = true
    enable_dns_support   = true
    tags = { Name = "${var.name}-vpc" }
}

# Private route table (no IGW route = truly private)
resource "aws_route_table" "private" {
    vpc_id = aws_vpc.this.id
    tags   = { Name = "${var.name}-rt-private" }
}

resource "aws_subnet" "private_a" {
    vpc_id                  = aws_vpc.this.id
    cidr_block              = var.private_subnet_cidrs[0]
    availability_zone       = data.aws_availability_zones.available.names[0]
    map_public_ip_on_launch = false
    tags = { Name = "${var.name}-priv-a" }
}

resource "aws_subnet" "private_b" {
    vpc_id                  = aws_vpc.this.id
    cidr_block              = var.private_subnet_cidrs[1]
    availability_zone       = data.aws_availability_zones.available.names[1]
    map_public_ip_on_launch = false
    tags = { Name = "${var.name}-priv-b" }
}

resource "aws_route_table_association" "a" {
    subnet_id      = aws_subnet.private_a.id
    route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "b" {
    subnet_id      = aws_subnet.private_b.id
    route_table_id = aws_route_table.private.id
}

############################################
# outputs
############################################
output "vpc_id" {
    value = aws_vpc.this.id
}

output "private_subnet_ids" {
    value = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}
