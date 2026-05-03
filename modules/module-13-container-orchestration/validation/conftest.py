"""
Pytest fixtures for Module 13 tests
"""
import pytest
import boto3
import docker
from kubernetes import client, config
from moto import mock_ecs, mock_s3

@pytest.fixture
def docker_client():
    """Docker client"""
    return docker.from_env()

@pytest.fixture
def aws_credentials():
    """Mock AWS credentials"""
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture
def ecs_client(aws_credentials):
    """ECS client with moto mock"""
    with mock_ecs():
        yield boto3.client('ecs', region_name='us-east-1')

@pytest.fixture
def s3_client(aws_credentials):
    """S3 client with moto mock"""
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')

@pytest.fixture
def k8s_client():
    """Kubernetes client"""
    try:
        config.load_kube_config()
        return client.CoreV1Api()
    except Exception:
        pytest.skip("Kubernetes cluster not available")
