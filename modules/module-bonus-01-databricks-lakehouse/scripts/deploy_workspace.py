#!/usr/bin/env python3
"""
Automated Databricks Workspace Deployment Script

This script automates the setup of a Databricks workspace for training:
- Creates folder structure
- Imports notebooks
- Creates sample cluster
- Sets up DBFS directories
- Uploads sample data

Prerequisites:
- Databricks CLI configured (run setup_databricks_cli.sh first)
- Sample data generated (run create_sample_data.py first)

Usage:
    python deploy_workspace.py --workspace-url https://your-workspace.cloud.databricks.com
"""

import argparse
import subprocess
import json
from pathlib import Path
import sys

class DatabricksDeployer:
    def __init__(self, workspace_url, verbose=False):
        self.workspace_url = workspace_url
        self.verbose = verbose
        self.base_path = "/Users"  # Will be updated with actual user

    def run_command(self, cmd, capture_output=True):
        """Run shell command and return result."""
        if self.verbose:
            print(f"  Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return result.stdout.strip() if capture_output else None
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(cmd)}")
            print(f"   Error: {e.stderr}")
            raise

    def check_connection(self):
        """Test connection to Databricks workspace."""
        print("\n🔍 Testing connection to Databricks...")
        try:
            self.run_command(["databricks", "workspace", "ls", "/"])
            print("✅ Successfully connected to Databricks")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            print("\nPlease configure Databricks CLI:")
            print("  databricks configure --token")
            return False

    def get_current_user(self):
        """Get current Databricks user email."""
        print("\n🔍 Getting current user...")
        try:
            # Get current user from API
            result = self.run_command(["databricks", "workspace", "ls", "/Users"])
            users = result.split('\n')
            if users:
                # Assuming first user directory is current user
                user_email = users[0].strip().split()[-1].rstrip('/')
                self.base_path = f"/Users/{user_email}"
                print(f"✅ Current user: {user_email}")
                return user_email
            else:
                raise Exception("No users found")
        except Exception as e:
            print(f"⚠️  Could not auto-detect user: {e}")
            print("   Using /Shared instead")
            self.base_path = "/Shared"
            return None

    def create_folder_structure(self):
        """Create training folder structure in workspace."""
        print("\n📁 Creating folder structure...")

        folders = [
            f"{self.base_path}/training",
            f"{self.base_path}/training/module-bonus-01-databricks",
            f"{self.base_path}/training/module-bonus-01-databricks/notebooks",
            f"{self.base_path}/training/module-bonus-01-databricks/solutions",
        ]

        for folder in folders:
            try:
                self.run_command(["databricks", "workspace", "mkdirs", folder])
                print(f"  ✅ Created: {folder}")
            except Exception:
                print(f"  ⚠️  {folder} (may already exist)")

    def import_notebooks(self, notebooks_dir="./notebooks"):
        """Import notebooks to workspace."""
        print(f"\n📓 Importing notebooks from {notebooks_dir}...")

        notebooks_path = Path(notebooks_dir)
        if not notebooks_path.exists():
            print(f"  ⚠️  Notebooks directory not found: {notebooks_dir}")
            return

        notebook_files = list(notebooks_path.glob("*.py"))
        if not notebook_files:
            print(f"  ⚠️  No notebook files found in {notebooks_dir}")
            return

        target_path = f"{self.base_path}/training/module-bonus-01-databricks/notebooks"

        for notebook_file in notebook_files:
            try:
                workspace_path = f"{target_path}/{notebook_file.stem}"
                self.run_command([
                    "databricks", "workspace", "import",
                    str(notebook_file),
                    workspace_path,
                    "--language", "PYTHON",
                    "--format", "SOURCE",
                    "--overwrite"
                ])
                print(f"  ✅ Imported: {notebook_file.name}")
            except Exception as e:
                print(f"  ❌ Failed to import {notebook_file.name}: {e}")

    def create_dbfs_directories(self):
        """Create DBFS directories for data."""
        print("\n📦 Creating DBFS directories...")

        dirs = [
            "dbfs:/FileStore/training",
            "dbfs:/FileStore/training/data",
            "dbfs:/FileStore/training/checkpoints",
        ]

        for directory in dirs:
            try:
                self.run_command(["databricks", "fs", "mkdirs", directory])
                print(f"  ✅ Created: {directory}")
            except Exception:
                print(f"  ⚠️  {directory} (may already exist)")

    def upload_sample_data(self, data_dir="./data/sample"):
        """Upload sample data to DBFS."""
        print(f"\n💾 Uploading sample data from {data_dir}...")

        data_path = Path(data_dir)
        if not data_path.exists():
            print(f"  ⚠️  Data directory not found: {data_dir}")
            print("  💡 Generate data first: python scripts/create_sample_data.py")
            return

        data_files = list(data_path.glob("*.*"))
        if not data_files:
            print(f"  ⚠️  No data files found in {data_dir}")
            return

        for data_file in data_files:
            try:
                dbfs_path = f"dbfs:/FileStore/training/data/{data_file.name}"
                self.run_command([
                    "databricks", "fs", "cp",
                    str(data_file),
                    dbfs_path,
                    "--overwrite"
                ])
                file_size = data_file.stat().st_size / 1024**2  # MB
                print(f"  ✅ Uploaded: {data_file.name} ({file_size:.2f} MB)")
            except Exception as e:
                print(f"  ❌ Failed to upload {data_file.name}: {e}")

    def create_cluster(self, cluster_name="training-cluster"):
        """Create a training cluster."""
        print(f"\n🖥️  Creating cluster '{cluster_name}'...")

        cluster_config = {
            "cluster_name": cluster_name,
            "spark_version": "14.3.x-scala2.12",
            "node_type_id": "m5.xlarge",  # AWS
            "driver_node_type_id": "m5.xlarge",
            "autoscale": {
                "min_workers": 2,
                "max_workers": 4
            },
            "auto_termination_minutes": 30,
            "spark_conf": {
                "spark.databricks.delta.preview.enabled": "true",
                "spark.sql.adaptive.enabled": "true"
            }
        }

        # Save config to temp file
        config_file = Path("/tmp/cluster_config.json")
        with open(config_file, "w") as f:
            json.dump(cluster_config, f, indent=2)

        try:
            # Check if cluster already exists
            result = self.run_command(["databricks", "clusters", "list", "--output", "JSON"])
            clusters = json.loads(result) if result else {"clusters": []}

            existing_cluster = None
            for cluster in clusters.get("clusters", []):
                if cluster.get("cluster_name") == cluster_name:
                    existing_cluster = cluster
                    break

            if existing_cluster:
                cluster_id = existing_cluster["cluster_id"]
                print(f"  ⚠️  Cluster '{cluster_name}' already exists (ID: {cluster_id})")
                print(f"  💡 To use it, start with: databricks clusters start --cluster-id {cluster_id}")
            else:
                # Create new cluster
                result = self.run_command([
                    "databricks", "clusters", "create",
                    "--json-file", str(config_file)
                ])
                cluster_info = json.loads(result)
                cluster_id = cluster_info.get("cluster_id")
                print(f"  ✅ Cluster created: {cluster_id}")
                print("  ⏳ Starting cluster (this takes 5-10 minutes)...")
                print(f"  💡 Check status: databricks clusters get --cluster-id {cluster_id}")
        except Exception as e:
            print(f"  ❌ Failed to create cluster: {e}")
            print("  💡 You can create it manually in the Databricks UI")

    def deploy(self, skip_cluster=False, skip_data=False):
        """Run full deployment."""
        print("="*60)
        print("Databricks Workspace Deployment")
        print("="*60)

        # Step 1: Check connection
        if not self.check_connection():
            return False

        # Step 2: Get current user
        self.get_current_user()

        # Step 3: Create folders
        self.create_folder_structure()

        # Step 4: Import notebooks
        self.import_notebooks()

        # Step 5: Create DBFS directories
        self.create_dbfs_directories()

        # Step 6: Upload data (optional)
        if not skip_data:
            self.upload_sample_data()

        # Step 7: Create cluster (optional)
        if not skip_cluster:
            self.create_cluster()

        # Summary
        print("\n" + "="*60)
        print("Deployment Complete!")
        print("="*60)
        print(f"\n📍 Workspace URL: {self.workspace_url}")
        print(f"📁 Training folder: {self.base_path}/training/module-bonus-01-databricks")
        print("💾 Data location: dbfs:/FileStore/training/data/")
        print("\nNext steps:")
        print("  1. Open Databricks workspace in browser")
        print(f"  2. Navigate to: {self.base_path}/training/module-bonus-01-databricks/notebooks")
        print("  3. Start with notebook: 01-delta-lake-basics")
        print("  4. Make sure cluster is running (check 'Compute' tab)")
        print("\n✅ Ready to start training!")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Databricks training workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full deployment
  python deploy_workspace.py --workspace-url https://your-workspace.cloud.databricks.com

  # Skip cluster creation (create manually in UI)
  python deploy_workspace.py --skip-cluster

  # Skip data upload (upload manually or use existing data)
  python deploy_workspace.py --skip-data
        """
    )

    parser.add_argument(
        "--workspace-url",
        help="Databricks workspace URL (e.g., https://your-workspace.cloud.databricks.com)"
    )
    parser.add_argument(
        "--skip-cluster",
        action="store_true",
        help="Skip cluster creation"
    )
    parser.add_argument(
        "--skip-data",
        action="store_true",
        help="Skip data upload"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Get workspace URL from CLI config if not provided
    workspace_url = args.workspace_url or "https://community.cloud.databricks.com"

    deployer = DatabricksDeployer(workspace_url, verbose=args.verbose)
    success = deployer.deploy(
        skip_cluster=args.skip_cluster,
        skip_data=args.skip_data
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
