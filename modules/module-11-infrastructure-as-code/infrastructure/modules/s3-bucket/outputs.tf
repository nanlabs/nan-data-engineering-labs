output "id" {
  description = "ID (nombre) del bucket"
  value       = aws_s3_bucket.this.id
}

output "arn" {
  description = "ARN del bucket"
  value       = aws_s3_bucket.this.arn
}

output "domain_name" {
  description = "Domain name del bucket"
  value       = aws_s3_bucket.this.bucket_domain_name
}

output "region" {
  description = "Región del bucket"
  value       = aws_s3_bucket.this.region
}
