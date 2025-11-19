# Variables
variable "name" {
    description = "Project name for resource naming"
    type        = string
}

# S3 Assets Bucket for Sentinel
resource "aws_s3_bucket" "assets" {
    bucket = "${var.name}-assets-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
    byte_length = 4
}

resource "aws_s3_bucket_public_access_block" "assets" {
    bucket = aws_s3_bucket.assets.id
    
    block_public_acls       = false
    block_public_policy     = false
    ignore_public_acls      = false
    restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "assets_public_read" {
    bucket = aws_s3_bucket.assets.id
    
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Principal = "*"
                Action = "s3:GetObject"
                Resource = "${aws_s3_bucket.assets.arn}/*"
            }
        ]
    })
    
    depends_on = [aws_s3_bucket_public_access_block.assets]
}

# Upload Sentinel logo that doubles as our tracking image
resource "aws_s3_object" "sentinel_logo" {
    bucket       = aws_s3_bucket.assets.id
    key          = "images/sentinel-logo.png"
    content_type = "image/png"
    
    # Small Sentinel logo (24x24 with "S" branding) - real PNG image  
    content_base64 = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJQSURBVEiJtZU9aBRBFMd/s7t3l0QSCxsLwcJCG1sLG0uxsLGwsLBQsLCwsLBQsLCwsLGwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLCwsLBQsLBQ"
    
    cache_control = "public, max-age=31536000"  # 1 year cache
    
    tags = {
        Name        = "Sentinel Logo"
        Purpose     = "Email Tracking & Branding"  
        Environment = var.name
    }
}

# Outputs
output "bucket_name" {
    description = "S3 assets bucket name"
    value       = aws_s3_bucket.assets.bucket
}

output "bucket_arn" {
    description = "S3 assets bucket ARN"
    value       = aws_s3_bucket.assets.arn
}

output "bucket_domain_name" {
    description = "S3 assets bucket domain name"
    value       = aws_s3_bucket.assets.bucket_domain_name
}

output "sentinel_logo_url" {
    description = "URL for the Sentinel logo (used for tracking)"
    value       = "https://${aws_s3_bucket.assets.bucket_domain_name}/images/sentinel-logo.png"
}