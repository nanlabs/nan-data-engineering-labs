"""
Schema Registry for Data Mesh

This module manages schema versioning and compatibility across domains.
Uses AWS Glue Schema Registry for centralized schema management.

Key Features:
1. Register schemas with versioning (v1, v2, v3...)
2. Check backward/forward compatibility
3. Validate schema evolution
4. Discover schemas across domains
5. Generate code from schemas (Avro → Python classes)

Author: Training Module 18
"""

import sys
import json
import logging
import argparse
from typing import Dict, List, Optional, Any

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchemaRegistry:
    """
    Manages schema registry for Data Mesh domains.

    Centralizes schema management while respecting domain ownership.
    """

    def __init__(
        self,
        registry_name: str = "data-mesh-schemas",
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Schema Registry.

        Args:
            registry_name: Glue Schema Registry name
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.registry_name = registry_name
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.glue = boto3.client('glue', region_name=region, endpoint_url=endpoint_url)

        logger.info(f"SchemaRegistry initialized: {registry_name}")

    def create_registry(self) -> str:
        """
        Create Glue Schema Registry.

        Returns:
            Registry ARN
        """
        logger.info(f"=== Creating Schema Registry: {self.registry_name} ===")

        try:
            response = self.glue.create_registry(
                RegistryName=self.registry_name,
                Description='Data Mesh centralized schema registry',
                Tags={
                    'Environment': 'production',
                    'Architecture': 'DataMesh'
                }
            )

            arn = response['RegistryArn']
            logger.info(f"✅ Created registry: {arn}")

            return arn

        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                logger.info(f"✅ Registry already exists: {self.registry_name}")

                # Get ARN
                response = self.glue.get_registry(RegistryId={'RegistryName': self.registry_name})
                return response['RegistryArn']
            else:
                raise

    def register_schema(
        self,
        domain: str,
        data_product: str,
        schema_content: Dict[str, Any],
        schema_type: str = 'AVRO',
        compatibility: str = 'BACKWARD'
    ) -> Dict[str, Any]:
        """
        Register schema for data product.

        Args:
            domain: Domain name (product, sales, customer)
            data_product: Data product name
            schema_content: Avro schema definition
            schema_type: AVRO or JSON
            compatibility: BACKWARD, FORWARD, FULL, NONE

        Returns:
            Dict with schema version info
        """
        schema_name = f"{domain}.{data_product}"

        logger.info(f"=== Registering Schema: {schema_name} ===")
        logger.info(f"   Type: {schema_type}")
        logger.info(f"   Compatibility: {compatibility}")

        # Ensure registry exists
        self.create_registry()

        try:
            # Register schema
            response = self.glue.register_schema_version(
                SchemaId={
                    'RegistryName': self.registry_name,
                    'SchemaName': schema_name
                },
                SchemaDefinition=json.dumps(schema_content)
            )

            version_info = {
                'schema_name': schema_name,
                'version_id': response['SchemaVersionId'],
                'version_number': response['VersionNumber'],
                'status': response['Status'],
                'schema_type': schema_type,
                'compatibility': compatibility
            }

            logger.info(f"✅ Registered: {schema_name} v{version_info['version_number']}")
            logger.info(f"   Version ID: {version_info['version_id']}")

            return version_info

        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                # Schema doesn't exist, create it first
                logger.info(f"   Creating schema: {schema_name}")

                self.glue.create_schema(
                    RegistryId={'RegistryName': self.registry_name},
                    SchemaName=schema_name,
                    DataFormat=schema_type,
                    Compatibility=compatibility,
                    SchemaDefinition=json.dumps(schema_content),
                    Tags={
                        'domain': domain,
                        'data_product': data_product
                    }
                )

                logger.info(f"✅ Created schema: {schema_name} v1")

                return {
                    'schema_name': schema_name,
                    'version_number': 1,
                    'status': 'AVAILABLE',
                    'schema_type': schema_type,
                    'compatibility': compatibility
                }
            else:
                raise

    def check_compatibility(
        self,
        domain: str,
        data_product: str,
        new_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if new schema is compatible with existing schema.

        Args:
            domain: Domain name
            data_product: Data product name
            new_schema: New schema definition

        Returns:
            Dict with compatibility check results
        """
        schema_name = f"{domain}.{data_product}"

        logger.info(f"=== Checking Compatibility: {schema_name} ===")

        try:
            # Get current schema
            response = self.glue.get_schema_version(
                SchemaId={
                    'RegistryName': self.registry_name,
                    'SchemaName': schema_name
                },
                SchemaVersionNumber={'LatestVersion': True}
            )

            current_schema = json.loads(response['SchemaDefinition'])
            current_version = response['VersionNumber']

            logger.info(f"   Current: v{current_version}")

            # Simple compatibility check
            # In production: use Avro compatibility libraries

            compatibility_result = self._check_avro_compatibility(
                current_schema,
                new_schema
            )

            result = {
                'schema_name': schema_name,
                'current_version': current_version,
                'compatible': compatibility_result['compatible'],
                'issues': compatibility_result.get('issues', []),
                'changes': compatibility_result.get('changes', [])
            }

            if result['compatible']:
                logger.info("✅ Schema is compatible")
            else:
                logger.error("❌ Schema incompatible")
                for issue in result['issues']:
                    logger.error(f"   • {issue}")

            return result

        except ClientError as e:
            logger.error(f"❌ Compatibility check failed: {e}")
            return {'compatible': False, 'error': str(e)}

    def _check_avro_compatibility(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check Avro schema compatibility (simplified).

        Real implementation would use avro.schema.SchemaCompatibility.
        """
        old_fields = {f['name']: f for f in old_schema.get('fields', [])}
        new_fields = {f['name']: f for f in new_schema.get('fields', [])}

        issues = []
        changes = []

        # Check for removed fields (backward incompatible)
        for field_name in old_fields:
            if field_name not in new_fields:
                issues.append(f"Field removed: {field_name} (breaks backward compatibility)")

        # Check for added fields
        for field_name in new_fields:
            if field_name not in old_fields:
                new_field = new_fields[field_name]

                # Check if has default value
                if 'default' not in new_field:
                    issues.append(f"Field added without default: {field_name} (breaks backward compatibility)")
                else:
                    changes.append(f"Field added: {field_name} (default: {new_field['default']})")

        # Check for type changes
        for field_name in old_fields:
            if field_name in new_fields:
                old_type = old_fields[field_name]['type']
                new_type = new_fields[field_name]['type']

                if old_type != new_type:
                    issues.append(f"Type changed: {field_name} ({old_type} → {new_type})")

        return {
            'compatible': len(issues) == 0,
            'issues': issues,
            'changes': changes
        }

    def list_schemas(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all schemas in registry.

        Args:
            domain: Filter by domain (optional)

        Returns:
            List of schema info dicts
        """
        logger.info("=== Listing Schemas ===")

        if domain:
            logger.info(f"   Domain: {domain}")

        try:
            response = self.glue.list_schemas(
                RegistryId={'RegistryName': self.registry_name},
                MaxResults=100
            )

            schemas = []

            for schema in response.get('Schemas', []):
                schema_name = schema['SchemaName']

                # Filter by domain
                if domain and not schema_name.startswith(f"{domain}."):
                    continue

                # Get latest version
                version_response = self.glue.get_schema_version(
                    SchemaId={
                        'RegistryName': self.registry_name,
                        'SchemaName': schema_name
                    },
                    SchemaVersionNumber={'LatestVersion': True}
                )

                schemas.append({
                    'schema_name': schema_name,
                    'domain': schema_name.split('.')[0],
                    'data_product': schema_name.split('.')[1] if '.' in schema_name else 'unknown',
                    'schema_arn': schema['SchemaArn'],
                    'latest_version': version_response['VersionNumber'],
                    'status': schema['SchemaStatus'],
                    'created_at': schema.get('CreatedTime')
                })

            # Print table
            print("\n" + "=" * 100)
            print("📋 DATA MESH SCHEMAS")
            print("=" * 100)
            print(f"\n{'Domain':<12} {'Data Product':<20} {'Version':<10} {'Status':<15} {'Created':<20}")
            print("-" * 100)

            for s in schemas:
                print(
                    f"{s['domain']:<12} "
                    f"{s['data_product']:<20} "
                    f"v{s['latest_version']:<9} "
                    f"{s['status']:<15} "
                    f"{s.get('created_at', 'N/A')}"
                )

            print("\n" + "=" * 100)
            logger.info(f"Found {len(schemas)} schemas")

            return schemas

        except ClientError as e:
            logger.error(f"❌ Failed to list schemas: {e}")
            return []


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Data Mesh - Schema Registry')

    parser.add_argument(
        '--mode',
        choices=['create-registry', 'register', 'check', 'list', 'get'],
        default='list',
        help='Operation mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment'
    )

    parser.add_argument(
        '--domain',
        type=str,
        help='Domain name (for filtering)'
    )

    parser.add_argument(
        '--data-product',
        type=str,
        help='Data product name'
    )

    parser.add_argument(
        '--schema-file',
        type=str,
        help='Path to Avro schema file (.avsc)'
    )

    args = parser.parse_args()

    # Initialize registry
    registry = SchemaRegistry(use_localstack=(args.env == 'localstack'))

    if args.mode == 'create-registry':
        arn = registry.create_registry()
        print(f"✅ Registry ARN: {arn}")

    elif args.mode == 'register':
        if not (args.domain and args.data_product and args.schema_file):
            logger.error("❌ --domain, --data-product, and --schema-file required")
            sys.exit(1)

        # Load schema
        with open(args.schema_file, 'r') as f:
            schema_content = json.load(f)

        version_info = registry.register_schema(
            domain=args.domain,
            data_product=args.data_product,
            schema_content=schema_content
        )

        print(json.dumps(version_info, indent=2, default=str))

    elif args.mode == 'check':
        if not (args.domain and args.data_product and args.schema_file):
            logger.error("❌ --domain, --data-product, and --schema-file required")
            sys.exit(1)

        # Load new schema
        with open(args.schema_file, 'r') as f:
            new_schema = json.load(f)

        result = registry.check_compatibility(
            domain=args.domain,
            data_product=args.data_product,
            new_schema=new_schema
        )

        print(json.dumps(result, indent=2, default=str))

    elif args.mode == 'list':
        registry.list_schemas(domain=args.domain)

    elif args.mode == 'get':
        if not (args.domain and args.data_product):
            logger.error("❌ --domain and --data-product required")
            sys.exit(1)

        schema_name = f"{args.domain}.{args.data_product}"

        try:
            response = registry.glue.get_schema_version(
                SchemaId={
                    'RegistryName': registry.registry_name,
                    'SchemaName': schema_name
                },
                SchemaVersionNumber={'LatestVersion': True}
            )

            schema_def = json.loads(response['SchemaDefinition'])

            print(json.dumps({
                'schema_name': schema_name,
                'version': response['VersionNumber'],
                'status': response['Status'],
                'schema': schema_def
            }, indent=2))

        except ClientError as e:
            logger.error(f"❌ Schema not found: {e}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
