variable "bucket_name" {
  description = "Nombre base del bucket (sin sufijo de entorno)"
  type        = string

  validation {
    condition     = length(var.bucket_name) >= 3 && length(var.bucket_name) <= 50
    error_message = "Bucket name debe tener entre 3 y 50 caracteres."
  }
}

variable "environment" {
  description = "Entorno (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment debe ser: dev, staging o prod."
  }
}

variable "enable_versioning" {
  description = "Habilitar versionado del bucket"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Habilitar access logging"
  type        = bool
  default     = false
}

variable "logging_bucket" {
  description = "Bucket para almacenar logs (opcional)"
  type        = string
  default     = null
}

variable "kms_key_id" {
  description = "ARN de KMS key para cifrado (opcional, usa AES256 por defecto)"
  type        = string
  default     = null
}

variable "lifecycle_rules" {
  description = "Lista de lifecycle rules"
  type = list(object({
    id      = string
    enabled = bool
    prefix  = optional(string)
    transition = optional(list(object({
      days          = number
      storage_class = string
    })))
    expiration = optional(object({
      days = number
    }))
  }))
  default = []
}

variable "tags" {
  description = "Tags adicionales"
  type        = map(string)
  default     = {}
}
