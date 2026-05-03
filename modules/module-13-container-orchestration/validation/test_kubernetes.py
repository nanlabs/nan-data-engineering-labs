"""
Kubernetes manifest validation tests
"""
import pytest
import yaml


@pytest.mark.kubernetes
class TestKubernetesManifests:
    """Test Kubernetes manifest validations"""

    def test_deployment_manifest(self):
        """Test Deployment manifest structure"""
        deployment = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-api
  namespace: data-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-api
  template:
    metadata:
      labels:
        app: data-api
    spec:
      containers:
      - name: api
        image: data-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        """

        manifest = yaml.safe_load(deployment)

        assert manifest['apiVersion'] == 'apps/v1'
        assert manifest['kind'] == 'Deployment'
        assert 'spec' in manifest
        assert 'replicas' in manifest['spec']
        assert manifest['spec']['replicas'] >= 1

    def test_service_manifest(self):
        """Test Service manifest structure"""
        service = """
apiVersion: v1
kind: Service
metadata:
  name: data-api
  namespace: data-pipeline
spec:
  selector:
    app: data-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
        """

        manifest = yaml.safe_load(service)

        assert manifest['apiVersion'] == 'v1'
        assert manifest['kind'] == 'Service'
        assert 'spec' in manifest
        assert 'selector' in manifest['spec']
        assert len(manifest['spec']['ports']) > 0

    def test_resources_defined(self):
        """Test container has resource requests and limits"""
        container = {
            "name": "api",
            "image": "api:latest",
            "resources": {
                "requests": {
                    "cpu": "250m",
                    "memory": "256Mi"
                },
                "limits": {
                    "cpu": "500m",
                    "memory": "512Mi"
                }
            }
        }

        assert 'resources' in container
        assert 'requests' in container['resources']
        assert 'limits' in container['resources']
        assert 'cpu' in container['resources']['requests']
        assert 'memory' in container['resources']['requests']

    def test_health_probes(self):
        """Test container has liveness and readiness probes"""
        container = {
            "name": "api",
            "image": "api:latest",
            "livenessProbe": {
                "httpGet": {
                    "path": "/health",
                    "port": 8000
                },
                "initialDelaySeconds": 30,
                "periodSeconds": 10
            },
            "readinessProbe": {
                "httpGet": {
                    "path": "/health",
                    "port": 8000
                },
                "initialDelaySeconds": 10,
                "periodSeconds": 5
            }
        }

        assert 'livenessProbe' in container
        assert 'readinessProbe' in container
        assert 'httpGet' in container['livenessProbe']


@pytest.mark.kubernetes
class TestKubernetesStatefulSet:
    """Test StatefulSet configurations"""

    def test_statefulset_manifest(self):
        """Test StatefulSet structure"""
        statefulset = """
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
        """

        manifest = yaml.safe_load(statefulset)

        assert manifest['kind'] == 'StatefulSet'
        assert 'serviceName' in manifest['spec']
        assert 'volumeClaimTemplates' in manifest['spec']

    def test_pvc_storage_class(self):
        """Test PVC uses proper storage class"""
        pvc = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": "data-pvc"},
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "storageClassName": "gp3",
                "resources": {
                    "requests": {
                        "storage": "10Gi"
                    }
                }
            }
        }

        assert 'storageClassName' in pvc['spec']
        assert pvc['spec']['storageClassName'] in ['gp2', 'gp3', 'ebs-gp3']


@pytest.mark.kubernetes
class TestKubernetesIngress:
    """Test Ingress configurations"""

    def test_ingress_alb_annotations(self):
        """Test Ingress has proper ALB annotations"""
        ingress = """
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  ingressClassName: alb
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
        """

        manifest = yaml.safe_load(ingress)

        assert 'annotations' in manifest['metadata']
        annotations = manifest['metadata']['annotations']
        assert 'alb.ingress.kubernetes.io/scheme' in annotations
        assert 'alb.ingress.kubernetes.io/target-type' in annotations


@pytest.mark.kubernetes
class TestKubernetesHPA:
    """Test HorizontalPodAutoscaler configurations"""

    def test_hpa_manifest(self):
        """Test HPA configuration"""
        hpa = """
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
        """

        manifest = yaml.safe_load(hpa)

        assert manifest['kind'] == 'HorizontalPodAutoscaler'
        assert 'minReplicas' in manifest['spec']
        assert 'maxReplicas' in manifest['spec']
        assert manifest['spec']['minReplicas'] < manifest['spec']['maxReplicas']
