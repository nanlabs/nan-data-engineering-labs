# Module 02: Storage Basics - Infrastructure README

## Overview

LocalStack infrastructure for Module 02 exercises.

## Services Included

- **S3:** Object storage for data lakes
- **Glue:** Data catalog and crawlers
- **Athena:** SQL queries on S3
- **IAM:** Access management
- **CloudFormation:** Infrastructure as Code

## Usage

### Start Infrastructure

```bash
cd infrastructure
./init.sh
```

Or with docker-compose:
```bash
docker-compose up -d
```

### Check Status

```bash
docker-compose ps
docker-compose logs -f
```

### Stop Infrastructure

```bash
docker-compose down
```

### Clean All Data

```bash
docker-compose down -v
rm -rf localstack-data/
```

## Configuration

Set environment variables:

```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566
```

Or use with AWS CLI:
```bash
aws --endpoint-url=http://localhost:4566 s3 ls
```

## Data Persistence

Data is stored in `./localstack-data/` and persists across restarts.

## Troubleshooting

**Port conflict:**
```bash
lsof -i :4566
kill -9 <PID>
```

**Reset everything:**
```bash
docker-compose down -v
rm -rf localstack-data/
docker-compose up -d
```

For more help, see [docs/troubleshooting.md](../docs/troubleshooting.md)
