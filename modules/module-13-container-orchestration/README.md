# Module 13: Container Orchestration

⏱️ **Estimated Time:** 25-30 hours

## Prerequisites

- ✅ Module 12 completed (Serverless Processing)
- Docker fundamentals knowledge
- AWS account with appropriate permissions
- kubectl, terraform, helm installed

## Module Overview

Master container orchestration with Docker, Amazon ECS, and Kubernetes. Build production-ready data platforms using containers, from simple Docker applications to complex Kubernetes deployments with Spark, Airflow, and Kafka.

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Create optimized Docker images with multi-stage builds
- ✅ Deploy serverless containers on AWS ECS/Fargate
- ✅ Orchestrate complex ETL pipelines with Step Functions + ECS
- ✅ Manage Kubernetes clusters on Amazon EKS
- ✅ Run Apache Spark jobs at scale on Kubernetes
- ✅ Build production data platforms with Airflow, Kafka, and monitoring

## Structure

- **theory/**: 3 comprehensive theory files (Docker, ECS, Kubernetes)
- **exercises/**: 6 progressive hands-on exercises (25+ hours)
- **infrastructure/**: Reusable Terraform modules (ECS, EKS, add-ons)
- **validation/**: pytest test suite for Docker, ECS, Kubernetes
- **scripts/**: Automation scripts (setup, deploy, cleanup)

## Getting Started

1. Run setup script: `./scripts/setup.sh`
2. Configure AWS: `aws configure`
3. Read theory files in order (01 → 02 → 03)
4. Complete exercises sequentially
5. Run tests: `pytest validation/ -v`
6. Clean up: `./scripts/cleanup.sh`

## Exercises

1. **Exercise 01**: Docker Basics - First container with ETL app (2-3h)
2. **Exercise 02**: ECS Fargate Deployment - Production infrastructure (3-4h)
3. **Exercise 03**: ECS Data Pipeline - Step Functions orchestration (3-4h)
4. **Exercise 04**: Kubernetes Basics - EKS cluster & workloads (3-4h)
5. **Exercise 05**: EKS Spark Jobs - Large-scale processing (4-5h)
6. **Exercise 06**: Production K8s - Airflow + Kafka + Monitoring (5-6h)

## Technology Stack

**Containers**: Docker, Docker Compose
**AWS**: ECS, Fargate, ECR, ALB, EventBridge
**Kubernetes**: EKS, kubectl, Helm, Operators
**Data**: Spark, Airflow, Kafka, PostgreSQL
**IaC**: Terraform, eksctl
**Monitoring**: Prometheus, Grafana, CloudWatch
**GitOps**: ArgoCD

## Resources

See `theory/resources.md` for:
- Official AWS documentation
- Video tutorials and workshops
- Community resources
- Certification mapping

## Validation

Run all validations:
```bash
bash scripts/validate.sh
```

Or use the global validation:
```bash
make validate MODULE=module-{module_id}-{module["name"]}
```

## Progress Checklist

- [ ] Read all theory documentation
- [ ] Completed Exercise 01
- [ ] Completed Exercise 02
- [ ] Completed Exercise 03
- [ ] Completed Exercise 04
- [ ] Completed Exercise 05
- [ ] Completed Exercise 06
- [ ] All validations passing
- [ ] Ready for next module

## Next Steps

After completing this module, you'll be ready for:
[List of modules that depend on this one]
