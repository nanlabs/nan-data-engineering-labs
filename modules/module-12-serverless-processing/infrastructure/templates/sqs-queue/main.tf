# Reusable SQS Queue Module with DLQ

variable "queue_name" {
  description = "Name of the SQS queue"
  type        = string
}

variable "is_fifo" {
  description = "Is this a FIFO queue?"
  type        = bool
  default     = false
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout"
  type        = number
  default     = 30
}

variable "message_retention_seconds" {
  description = "Message retention period"
  type        = number
  default     = 345600  # 4 days
}

variable "delay_seconds" {
  description = "Delay for message delivery"
  type        = number
  default     = 0
}

variable "max_receive_count" {
  description = "Max receives before moving to DLQ"
  type        = number
  default     = 3
}

variable "enable_dlq" {
  description = "Enable Dead Letter Queue"
  type        = bool
  default     = true
}

# Main Queue
resource "aws_sqs_queue" "this" {
  name                       = var.is_fifo ? "${var.queue_name}.fifo" : var.queue_name
  fifo_queue                 = var.is_fifo
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  delay_seconds              = var.delay_seconds

  content_based_deduplication = var.is_fifo ? true : null

  redrive_policy = var.enable_dlq ? jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq[0].arn
    maxReceiveCount     = var.max_receive_count
  }) : null
}

# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  count = var.enable_dlq ? 1 : 0

  name                       = var.is_fifo ? "${var.queue_name}-dlq.fifo" : "${var.queue_name}-dlq"
  fifo_queue                 = var.is_fifo
  message_retention_seconds  = 1209600  # 14 days

  content_based_deduplication = var.is_fifo ? true : null
}

# CloudWatch Alarms for DLQ
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  count               = var.enable_dlq ? 1 : 0
  alarm_name          = "${var.queue_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0

  dimensions = {
    QueueName = aws_sqs_queue.dlq[0].name
  }
}

# Outputs
output "queue_url" {
  value = aws_sqs_queue.this.url
}

output "queue_arn" {
  value = aws_sqs_queue.this.arn
}

output "dlq_url" {
  value = var.enable_dlq ? aws_sqs_queue.dlq[0].url : null
}

output "dlq_arn" {
  value = var.enable_dlq ? aws_sqs_queue.dlq[0].arn : null
}
