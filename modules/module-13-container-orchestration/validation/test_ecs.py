"""
ECS infrastructure validation tests
"""
import pytest


@pytest.mark.ecs
class TestECSInfrastructure:
    """Test ECS infrastructure configurations"""

    def test_ecs_cluster_creation(self, ecs_client):
        """Test ECS cluster can be created"""
        cluster_name = 'test-cluster'

        response = ecs_client.create_cluster(
            clusterName=cluster_name,
            settings=[{
                'name': 'containerInsights',
                'value': 'enabled'
            }]
        )

        assert response['cluster']['clusterName'] == cluster_name
        assert response['cluster']['status'] == 'ACTIVE'

    def test_task_definition_validation(self):
        """Test task definition has required fields"""
        task_definition = {
            "family": "data-api",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "512",
            "memory": "1024",
            "containerDefinitions": [{
                "name": "api",
                "image": "data-api:latest",
                "portMappings": [{
                    "containerPort": 8080,
                    "protocol": "tcp"
                }]
            }]
        }

        # Validate required fields
        assert "family" in task_definition
        assert "networkMode" in task_definition
        assert "cpu" in task_definition
        assert "memory" in task_definition
        assert len(task_definition["containerDefinitions"]) > 0

    def test_task_definition_fargate_requirements(self):
        """Test Fargate task definition meets requirements"""
        fargate_cpu_memory_pairs = [
            ("256", "512"),
            ("256", "1024"),
            ("256", "2048"),
            ("512", "1024"),
            ("512", "2048"),
            ("512", "3072"),
            ("512", "4096"),
            ("1024", "2048"),
            ("1024", "3072"),
            ("1024", "4096"),
            ("1024", "5120"),
            ("1024", "6144"),
            ("1024", "7168"),
            ("1024", "8192")
        ]

        # Test valid combinations
        test_cpu = "512"
        test_memory = "1024"

        assert (test_cpu, test_memory) in fargate_cpu_memory_pairs

    def test_ecs_service_configuration(self):
        """Test ECS service configuration"""
        service_config = {
            "serviceName": "data-api",
            "taskDefinition": "data-api:1",
            "desiredCount": 2,
            "launchType": "FARGATE",
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": ["subnet-123", "subnet-456"],
                    "securityGroups": ["sg-123"],
                    "assignPublicIp": "DISABLED"
                }
            },
            "loadBalancers": [{
                "targetGroupArn": "arn:aws:...",
                "containerName": "api",
                "containerPort": 8080
            }]
        }

        assert service_config["desiredCount"] >= 1
        assert service_config["launchType"] == "FARGATE"
        assert "awsvpcConfiguration" in service_config["networkConfiguration"]
        assert len(service_config["networkConfiguration"]["awsvpcConfiguration"]["subnets"]) >= 2


@pytest.mark.ecs
class TestECSAutoScaling:
    """Test ECS auto scaling configurations"""

    def test_autoscaling_policy(self):
        """Test auto scaling policy configuration"""
        policy = {
            "policyName": "cpu-autoscaling",
            "policyType": "TargetTrackingScaling",
            "targetTrackingScalingPolicyConfiguration": {
                "predefinedMetricSpecification": {
                    "predefinedMetricType": "ECSServiceAverageCPUUtilization"
                },
                "targetValue": 70.0,
                "scaleInCooldown": 300,
                "scaleOutCooldown": 60
            }
        }

        assert policy["policyType"] == "TargetTrackingScaling"
        assert policy["targetTrackingScalingPolicyConfiguration"]["targetValue"] > 0
        assert policy["targetTrackingScalingPolicyConfiguration"]["targetValue"] <= 100

    def test_autoscaling_target_ranges(self):
        """Test auto scaling min/max validation"""
        min_capacity = 2
        max_capacity = 10

        assert min_capacity >= 1
        assert max_capacity > min_capacity
        assert max_capacity <= 100  # Reasonable limit


@pytest.mark.ecs
class TestECSEventBridge:
    """Test EventBridge scheduled tasks"""

    def test_cron_expression(self):
        """Test cron expression for scheduled tasks"""
        # Daily at 2 AM UTC
        cron_expression = "cron(0 2 * * ? *)"

        assert "cron(" in cron_expression
        assert cron_expression.endswith(")")

    def test_eventbridge_rule(self):
        """Test EventBridge rule configuration"""
        rule = {
            "Name": "daily-etl",
            "ScheduleExpression": "cron(0 2 * * ? *)",
            "State": "ENABLED",
            "Targets": [{
                "Arn": "arn:aws:ecs:us-east-1:123456789012:cluster/data-cluster",
                "RoleArn": "arn:aws:iam::123456789012:role/eventbridge-ecs-role",
                "EcsParameters": {
                    "TaskDefinitionArn": "arn:aws:ecs:us-east-1:123456789012:task-definition/etl:1",
                    "TaskCount": 1,
                    "LaunchType": "FARGATE"
                }
            }]
        }

        assert rule["State"] == "ENABLED"
        assert "ScheduleExpression" in rule
        assert len(rule["Targets"]) > 0
