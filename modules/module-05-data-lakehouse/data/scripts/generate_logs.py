#!/usr/bin/env python3
"""
Generate synthetic application log data with intentional quality issues.

This script generates realistic application logs for practicing data lakehouse
patterns and log analytics.

Quality issues included (10-15%):
- Missing required fields
- Invalid log levels
- Malformed timestamps
- Duplicate log_ids
- Invalid HTTP status codes
- Empty messages
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from faker import Faker

# Initialize Faker
fake = Faker()
Faker.seed(44)  # Different seed for variety
random.seed(44)

# Constants
NUM_RECORDS = 100000  # 100K log entries
QUALITY_ISSUE_RATE = 0.13  # 13% of records have issues
OUTPUT_DIR = Path(__file__).parent.parent / "raw"
OUTPUT_FILE = OUTPUT_DIR / "logs.jsonl"

# Log configuration
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
SERVICES = ["api-gateway", "auth-service", "payment-service", "inventory-service", 
            "notification-service", "analytics-service", "user-service"]
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
ENVIRONMENTS = ["development", "staging", "production"]

# Error codes
ERROR_CODES = {
    "ERR5001": "Database connection timeout",
    "ERR5002": "Invalid authentication token",
    "ERR5003": "Payment processing failed",
    "ERR5004": "Resource not found",
    "ERR5005": "Rate limit exceeded",
    "ERR4001": "Validation error",
    "ERR4002": "Missing required parameter",
    "ERR4003": "Invalid request format",
    "WRN2001": "Slow query detected",
    "WRN2002": "Cache miss",
    "WRN2003": "Deprecated API usage"
}

# API endpoints by service
ENDPOINTS = {
    "api-gateway": ["/health", "/metrics", "/api/v1/users", "/api/v1/products", "/api/v1/orders"],
    "auth-service": ["/auth/login", "/auth/logout", "/auth/refresh", "/auth/verify"],
    "payment-service": ["/payments/process", "/payments/refund", "/payments/verify"],
    "inventory-service": ["/inventory/check", "/inventory/reserve", "/inventory/release"],
    "notification-service": ["/notifications/email", "/notifications/sms", "/notifications/push"],
    "analytics-service": ["/analytics/events", "/analytics/reports", "/analytics/dashboards"],
    "user-service": ["/users", "/users/{id}", "/users/{id}/profile", "/users/{id}/preferences"]
}


def generate_stack_trace() -> str:
    """Generate realistic stack trace for errors."""
    traces = [
        """Traceback (most recent call last):
  File "/app/payment_service.py", line 142, in process_payment
    result = payment_gateway.charge(amount, card_token)
  File "/app/lib/gateway.py", line 78, in charge
    response = requests.post(url, json=payload, timeout=10)
requests.exceptions.Timeout: HTTPConnectionPool(host='payment.api.com', port=443): Read timed out.""",
        
        """java.lang.NullPointerException: Cannot invoke "User.getEmail()" because "user" is null
    at com.example.service.UserService.sendNotification(UserService.java:245)
    at com.example.controller.NotificationController.notify(NotificationController.java:89)
    at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)""",
        
        """Error: ECONNREFUSED connect ECONNREFUSED 127.0.0.1:5432
    at TCPConnectWrap.afterConnect [as oncomplete] (node:net:1495:16)
    at Database.connect (/app/node_modules/pg/lib/client.js:132:10)
    at async queryDatabase (/app/services/database.js:45:3)"""
    ]
    return random.choice(traces)


def generate_log_message(level: str, service: str) -> str:
    """Generate realistic log message based on level and service."""
    if level == "DEBUG":
        messages = [
            f"Entering function: {fake.word()}()",
            f"Query parameters: {{page: {random.randint(1, 100)}, limit: {random.choice([10, 20, 50])}}}",
            f"Cache lookup: key={fake.uuid4()}, hit={random.choice(['true', 'false'])}",
            f"Processing request from IP: {fake.ipv4()}"
        ]
    elif level == "INFO":
        messages = [
            f"Request processed successfully in {random.randint(10, 500)}ms",
            f"User {fake.user_name()} logged in from {fake.city()}",
            f"Payment processed: order_id={fake.uuid4()}, amount=${random.randint(10, 500)}",
            f"Inventory updated: product_id=P{random.randint(10000, 99999)}, quantity={random.randint(1, 100)}"
        ]
    elif level == "WARNING":
        messages = [
            f"Slow query detected: {random.randint(1000, 5000)}ms",
            f"Cache miss rate high: {random.randint(40, 80)}%",
            f"API rate limit approaching: {random.randint(800, 950)}/1000 requests",
            f"Deprecated endpoint used: {random.choice(list(ENDPOINTS.values())[0])}"
        ]
    elif level == "ERROR":
        messages = [
            "Database connection timeout after 30s",
            f"Payment gateway returned 502 Bad Gateway",
            f"Invalid authentication token provided",
            f"Failed to send notification: recipient email invalid"
        ]
    else:  # CRITICAL
        messages = [
            "Database connection pool exhausted",
            "Payment service completely unavailable",
            "Disk space critical: 95% full",
            "Memory usage critical: 98% of heap"
        ]
    
    return random.choice(messages)


def generate_clean_log() -> Dict:
    """Generate a clean, valid log record."""
    service = random.choice(SERVICES)
    level = random.choice(LOG_LEVELS)
    
    # Generate timestamp within last 7 days
    days_ago = random.randint(0, 7)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    microseconds = random.randint(0, 999999)
    timestamp = datetime.now() - timedelta(days=days_ago, hours=hours, minutes=minutes, 
                                          seconds=seconds, microseconds=microseconds)
    
    log = {
        "log_id": str(uuid.uuid4()),
        "timestamp": timestamp.isoformat() + "Z",
        "level": level,
        "service": service,
        "host": f"{service}-{random.randint(1, 5)}.prod.internal",
        "process_id": random.randint(1000, 65535),
        "thread_id": random.randint(1, 1000),
        "message": generate_log_message(level, service),
        "environment": random.choice(ENVIRONMENTS)
    }
    
    # Add error-specific fields
    if level in ["ERROR", "CRITICAL"]:
        if random.random() > 0.3:
            error_code = random.choice(list(ERROR_CODES.keys()))
            log["error_code"] = error_code
        if random.random() > 0.5:
            log["stack_trace"] = generate_stack_trace()
    
    # Add HTTP-related fields for some logs
    if random.random() > 0.4:
        method = random.choice(HTTP_METHODS)
        endpoint = random.choice(ENDPOINTS.get(service, ["/health"]))
        
        log["method"] = method
        log["endpoint"] = endpoint
        log["http_status"] = random.choices(
            [200, 201, 204, 400, 401, 403, 404, 500, 502, 503],
            weights=[40, 10, 5, 5, 3, 2, 5, 3, 2, 1]
        )[0]
        log["duration_ms"] = round(random.uniform(5, 3000), 2)
        log["ip_address"] = fake.ipv4()
    
    # Add user context for some logs
    if random.random() > 0.6:
        log["user_id"] = f"U{random.randint(0, 9999999999):010d}"
        log["request_id"] = str(uuid.uuid4())
    
    return log


def inject_quality_issue(log: Dict, issue_type: str) -> Dict:
    """Inject a specific quality issue into a log."""
    
    if issue_type == "missing_required":
        # Remove required field
        required = ["level", "service", "message"]
        field = random.choice(required)
        log[field] = None
        
    elif issue_type == "invalid_level":
        # Invalid log level (lowercase or typo)
        log["level"] = random.choice(["debug", "info", "warn", "err", "UNKNOWN", "FATAL"])
        
    elif issue_type == "invalid_timestamp":
        # Future date or malformed
        if random.choice([True, False]):
            future = datetime.now() + timedelta(days=random.randint(1, 365))
            log["timestamp"] = future.isoformat() + "Z"
        else:
            log["timestamp"] = "2024-99-99T99:99:99Z"
            
    elif issue_type == "invalid_http_status":
        # Invalid HTTP status code
        log["http_status"] = random.choice([0, 999, -200, 1000])
        
    elif issue_type == "negative_duration":
        # Negative duration
        log["duration_ms"] = -random.uniform(10, 1000)
        
    elif issue_type == "empty_message":
        # Empty message
        log["message"] = ""
        
    elif issue_type == "missing_stack_trace":
        # ERROR/CRITICAL without stack trace when expected
        if log["level"] in ["ERROR", "CRITICAL"]:
            log.pop("stack_trace", None)
            log.pop("error_code", None)
            
    elif issue_type == "truncated_message":
        # Truncated message (incomplete)
        if len(log["message"]) > 20:
            log["message"] = log["message"][:20] + "..."
    
    elif issue_type == "inconsistent_service":
        # Service name doesn't match host
        log["service"] = random.choice(SERVICES)
        # But keep original host (inconsistent)
    
    return log


def generate_all_logs() -> List[Dict]:
    """Generate all logs with quality issues."""
    print(f"📝 Generating {NUM_RECORDS:,} log entries...")
    
    logs = []
    issue_types = [
        "missing_required",
        "invalid_level",
        "invalid_timestamp",
        "invalid_http_status",
        "negative_duration",
        "empty_message",
        "missing_stack_trace",
        "truncated_message",
        "inconsistent_service"
    ]
    
    # Generate clean records
    num_clean = int(NUM_RECORDS * (1 - QUALITY_ISSUE_RATE))
    num_issues = NUM_RECORDS - num_clean
    
    print(f"  ✅ Clean records: {num_clean:,} ({(1-QUALITY_ISSUE_RATE)*100:.1f}%)")
    print(f"  ⚠️  Records with issues: {num_issues:,} ({QUALITY_ISSUE_RATE*100:.1f}%)")
    
    # Generate clean logs
    for i in range(num_clean):
        logs.append(generate_clean_log())
        if (i + 1) % 15000 == 0:
            print(f"     Generated {i + 1:,} clean records...")
    
    # Generate logs with issues
    for i in range(num_issues):
        log = generate_clean_log()
        issue_type = random.choice(issue_types)
        log = inject_quality_issue(log, issue_type)
        logs.append(log)
        if (i + 1) % 2000 == 0:
            print(f"     Generated {i + 1:,} records with issues...")
    
    # Add duplicates (1.5% of records)
    num_duplicates = int(NUM_RECORDS * 0.015)
    print(f"  🔁 Adding {num_duplicates:,} duplicate records...")
    for _ in range(num_duplicates):
        duplicate = random.choice(logs).copy()
        logs.append(duplicate)
    
    # Shuffle
    random.shuffle(logs)
    
    # Sort by timestamp (logs usually come in chronological order)
    logs.sort(key=lambda x: x.get("timestamp", ""))
    
    return logs


def save_logs(logs: List[Dict]):
    """Save logs to JSON Lines file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')
    
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"✅ Saved {len(logs):,} logs ({file_size_mb:.2f} MB)")


def print_summary(logs: List[Dict]):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("📊 SUMMARY STATISTICS")
    print("=" * 60)
    
    # Count by level
    level_counts = {}
    for log in logs:
        level = log.get("level", "unknown")
        level_counts[level] = level_counts.get(level, 0) + 1
    
    print("\nRecords by log level:")
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        count = level_counts.get(level, 0)
        pct = (count / len(logs)) * 100 if count > 0 else 0
        print(f"  {level:10s}: {count:8,} ({pct:5.2f}%)")
    
    # Other levels (invalid)
    other_count = sum(v for k, v in level_counts.items() 
                     if k not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    if other_count > 0:
        pct = (other_count / len(logs)) * 100
        print(f"  {'Other':10s}: {other_count:8,} ({pct:5.2f}%) ⚠️  Invalid levels")
    
    # Count by service
    service_counts = {}
    for log in logs:
        service = log.get("service", "unknown")
        service_counts[service] = service_counts.get(service, 0) + 1
    
    print("\nRecords by service:")
    for service, count in sorted(service_counts.items(), key=lambda x: -x[1])[:5]:
        pct = (count / len(logs)) * 100
        print(f"  {service:25s}: {count:8,} ({pct:5.2f}%)")
    
    # Count nulls
    null_count = sum(1 for log in logs if any(v is None for v in log.values()))
    print(f"\nRecords with null values: {null_count:,} ({null_count/len(logs)*100:.2f}%)")
    
    # Count duplicates
    log_ids = [log.get("log_id") for log in logs if log.get("log_id")]
    duplicate_count = len(log_ids) - len(set(log_ids))
    print(f"Duplicate log_ids: {duplicate_count:,}")
    
    print("\n" + "=" * 60)


def main():
    """Main execution."""
    print("=" * 60)
    print("📝 APPLICATION LOGS DATA GENERATOR")
    print("=" * 60)
    print(f"\nTarget records: {NUM_RECORDS:,}")
    print(f"Quality issue rate: {QUALITY_ISSUE_RATE*100:.1f}%")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Generate logs
    logs = generate_all_logs()
    
    # Save to file
    save_logs(logs)
    
    # Print summary
    print_summary(logs)
    
    print("\n✅ Log data generation complete!")
    print("\n💡 Next steps:")
    print("   1. Inspect the data: head -n 5 data/raw/logs.jsonl")
    print("   2. Parse and analyze error patterns")
    print("   3. Build log aggregation pipelines")


if __name__ == "__main__":
    main()
