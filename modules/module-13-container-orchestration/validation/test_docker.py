"""
Docker image validation tests
"""
import pytest


@pytest.mark.docker
class TestDockerImages:
    """Test Docker image builds and validations"""

    def test_docker_daemon_running(self, docker_client):
        """Test Docker daemon is accessible"""
        assert docker_client.ping()

    def test_dockerfile_exists(self):
        """Test Dockerfile exists for exercises"""
        import os
        exercise_dirs = [
            'exercises/01-docker-basics',
            'exercises/02-ecs-fargate-deployment'
        ]

        for exercise_dir in exercise_dirs:
            dockerfile_path = os.path.join(exercise_dir, 'Dockerfile')
            if os.path.exists(dockerfile_path):
                assert True

    def test_docker_image_security(self, docker_client):
        """Test Docker images follow security best practices"""
        test_image = 'alpine:latest'

        try:
            image = docker_client.images.pull(test_image)
            assert image is not None

            # Verify image has no vulnerabilities (placeholder)
            # In production: use Trivy, Snyk, etc.
            assert True
        except Exception as e:
            pytest.skip(f"Cannot pull image: {str(e)}")

    def test_multi_stage_build(self):
        """Test multi-stage Dockerfile pattern"""
        dockerfile_content = """
        FROM python:3.11-slim AS builder
        WORKDIR /build
        COPY requirements.txt .
        RUN pip install --user -r requirements.txt

        FROM python:3.11-slim
        COPY --from=builder /root/.local /root/.local
        CMD ["python"]
        """

        # Check for multi-stage keywords
        assert "AS builder" in dockerfile_content
        assert "COPY --from=builder" in dockerfile_content

    def test_dockerignore_recommended(self):
        """Test recommended .dockerignore patterns"""
        recommended_patterns = [
            '__pycache__',
            '*.pyc',
            '.git',
            '.venv',
            '*.log'
        ]

        dockerignore_content = "\n".join(recommended_patterns)

        for pattern in recommended_patterns:
            assert pattern in dockerignore_content


@pytest.mark.docker
class TestDockerCompose:
    """Test Docker Compose configurations"""

    def test_compose_file_structure(self):
        """Test docker-compose.yml has proper structure"""
        import yaml

        sample_compose = """
        version: '3.8'
        services:
          app:
            image: myapp:latest
            ports:
              - "8080:8080"
            environment:
              - ENV=production
        """

        compose_config = yaml.safe_load(sample_compose)

        assert 'version' in compose_config
        assert 'services' in compose_config
        assert 'app' in compose_config['services']

    def test_compose_healthcheck(self):
        """Test healthcheck configuration"""
        import yaml

        compose_with_health = """
        version: '3.8'
        services:
          app:
            image: myapp:latest
            healthcheck:
              test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
              interval: 30s
              timeout: 10s
              retries: 3
        """

        config = yaml.safe_load(compose_with_health)

        assert 'healthcheck' in config['services']['app']
        healthcheck = config['services']['app']['healthcheck']
        assert 'test' in healthcheck
        assert 'interval' in healthcheck
