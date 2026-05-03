# Reusable EKS Add-ons Terraform Module
# Installs: AWS Load Balancer Controller, EBS CSI, EFS CSI, Cluster Autoscaler
# Use: module "eks_addons" { source = "../templates/eks-addons" }

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "cluster_oidc_issuer_url" {
  description = "OIDC issuer URL (from aws_eks_cluster.identity.oidc.issuer)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "install_alb_controller" {
  description = "Install AWS Load Balancer Controller"
  type        = bool
  default     = true
}

variable "install_efs_csi" {
  description = "Install EFS CSI driver"
  type        = bool
  default     = false
}

variable "install_cluster_autoscaler" {
  description = "Install Cluster Autoscaler"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}

# Get OIDC provider ARN
data "aws_iam_openid_connect_provider" "eks" {
  url = var.cluster_oidc_issuer_url
}

locals {
  oidc_provider_arn = data.aws_iam_openid_connect_provider.eks.arn
  oidc_provider     = replace(var.cluster_oidc_issuer_url, "https://", "")
}

# ==============================================
# AWS Load Balancer Controller
# ==============================================

# IAM Policy
resource "aws_iam_policy" "alb_controller" {
  count  = var.install_alb_controller ? 1 : 0
  name   = "${var.cluster_name}-alb-controller-policy"
  policy = file("${path.module}/policies/alb-controller-policy.json")
}

# IAM Role for Service Account (IRSA)
resource "aws_iam_role" "alb_controller" {
  count = var.install_alb_controller ? 1 : 0
  name  = "${var.cluster_name}-alb-controller-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = local.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_provider}:sub" = "system:serviceaccount:kube-system:aws-load-balancer-controller"
          "${local.oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "alb_controller" {
  count      = var.install_alb_controller ? 1 : 0
  policy_arn = aws_iam_policy.alb_controller[0].arn
  role       = aws_iam_role.alb_controller[0].name
}

# ==============================================
# EFS CSI Driver
# ==============================================

resource "aws_iam_policy" "efs_csi" {
  count = var.install_efs_csi ? 1 : 0
  name  = "${var.cluster_name}-efs-csi-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:DescribeAccessPoints",
          "elasticfilesystem:DescribeFileSystems",
          "elasticfilesystem:DescribeMountTargets",
          "elasticfilesystem:CreateAccessPoint",
          "elasticfilesystem:DeleteAccessPoint",
          "ec2:DescribeAvailabilityZones"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "efs_csi" {
  count = var.install_efs_csi ? 1 : 0
  name  = "${var.cluster_name}-efs-csi-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = local.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_provider}:sub" = "system:serviceaccount:kube-system:efs-csi-controller-sa"
          "${local.oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "efs_csi" {
  count      = var.install_efs_csi ? 1 : 0
  policy_arn = aws_iam_policy.efs_csi[0].arn
  role       = aws_iam_role.efs_csi[0].name
}

# ==============================================
# Cluster Autoscaler
# ==============================================

resource "aws_iam_policy" "cluster_autoscaler" {
  count = var.install_cluster_autoscaler ? 1 : 0
  name  = "${var.cluster_name}-cluster-autoscaler-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "autoscaling:DescribeTags",
          "ec2:DescribeImages",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:GetInstanceTypesFromInstanceRequirements",
          "eks:DescribeNodegroup"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "autoscaling:ResourceTag/k8s.io/cluster-autoscaler/${var.cluster_name}" = "owned"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role" "cluster_autoscaler" {
  count = var.install_cluster_autoscaler ? 1 : 0
  name  = "${var.cluster_name}-cluster-autoscaler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = local.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_provider}:sub" = "system:serviceaccount:kube-system:cluster-autoscaler"
          "${local.oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "cluster_autoscaler" {
  count      = var.install_cluster_autoscaler ? 1 : 0
  policy_arn = aws_iam_policy.cluster_autoscaler[0].arn
  role       = aws_iam_role.cluster_autoscaler[0].name
}

# Outputs
output "alb_controller_role_arn" {
  value = var.install_alb_controller ? aws_iam_role.alb_controller[0].arn : ""
}

output "efs_csi_role_arn" {
  value = var.install_efs_csi ? aws_iam_role.efs_csi[0].arn : ""
}

output "cluster_autoscaler_role_arn" {
  value = var.install_cluster_autoscaler ? aws_iam_role.cluster_autoscaler[0].arn : ""
}
