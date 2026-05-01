#!/usr/bin/env python3
"""
Generate synthetic user event (clickstream) data with intentional quality issues.

This script generates realistic user behavior events for practicing data lakehouse
patterns and event stream processing.

Quality issues included (10-15%):
- Missing required fields
- Invalid timestamps
- Duplicate event_ids
- Inconsistent session tracking
- Invalid URLs
- Outlier screen resolutions
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from faker import Faker

# Initialize Faker
fake = Faker()
Faker.seed(43)  # Different seed for variety
random.seed(43)

# Constants
NUM_RECORDS = 200000  # 200K events
QUALITY_ISSUE_RATE = 0.12  # 12% of records have issues
OUTPUT_DIR = Path(__file__).parent.parent / "raw"
OUTPUT_FILE = OUTPUT_DIR / "events.json"

# Event configuration
EVENT_TYPES = ["page_view", "click", "search", "add_to_cart", "remove_from_cart", 
               "checkout", "purchase", "signup", "login", "logout"]
DEVICE_TYPES = ["desktop", "mobile", "tablet", "other"]
OS_TYPES = ["Windows", "macOS", "Linux", "iOS", "Android", "Other"]
BROWSERS = ["Chrome", "Firefox", "Safari", "Edge", "Opera", "Other"]

# Page URLs for e-commerce site
PAGE_URLS = [
    "/",
    "/products",
    "/products/electronics",
    "/products/clothing",
    "/products/home-garden",
    "/product/{product_id}",
    "/cart",
    "/checkout",
    "/account",
    "/account/orders",
    "/search",
    "/about",
    "/contact"
]


def generate_user_id() -> str:
    """Generate user ID in format U0000123456."""
    return f"U{random.randint(0, 9999999999):010d}"


def generate_session_id() -> str:
    """Generate session ID (UUID)."""
    return str(uuid.uuid4())


def generate_page_url() -> str:
    """Generate a page URL."""
    url_template = random.choice(PAGE_URLS)
    if "{product_id}" in url_template:
        product_id = f"P{random.randint(0, 99999999):08d}"
        url_template = url_template.replace("{product_id}", product_id)
    return f"https://ecommerce.example.com{url_template}"


def generate_user_agent(device: str, os: str, browser: str) -> str:
    """Generate realistic user agent string."""
    if device == "desktop":
        if os == "Windows":
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/120.0.0.0 Safari/537.36"
        elif os == "macOS":
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/120.0.0.0 Safari/537.36"
        else:  # Linux
            return f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/120.0.0.0 Safari/537.36"
    elif device == "mobile":
        if os == "iOS":
            return f"Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        else:  # Android
            return f"Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/120.0.6099.43 Mobile Safari/537.36"
    else:  # tablet
        return f"Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"


def generate_screen_resolution(device: str) -> tuple:
    """Generate realistic screen resolution based on device."""
    if device == "desktop":
        resolutions = [(1920, 1080), (2560, 1440), (1366, 768), (1440, 900), (3840, 2160)]
    elif device == "mobile":
        resolutions = [(390, 844), (428, 926), (375, 667), (414, 896), (360, 640)]
    else:  # tablet
        resolutions = [(768, 1024), (834, 1112), (810, 1080), (800, 1280)]
    
    return random.choice(resolutions)


def generate_event_data(event_type: str) -> Dict:
    """Generate event-specific data."""
    data = {}
    
    if event_type == "search":
        data["query"] = fake.word() + " " + fake.word()
        data["results_count"] = random.randint(0, 1000)
    elif event_type in ["add_to_cart", "remove_from_cart"]:
        data["product_id"] = f"P{random.randint(0, 99999999):08d}"
        data["quantity"] = random.randint(1, 10)
    elif event_type == "purchase":
        data["order_id"] = str(uuid.uuid4())
        data["total_amount"] = round(random.uniform(10.0, 500.0), 2)
    elif event_type == "click":
        data["element_id"] = fake.word() + "_" + str(random.randint(1, 100))
        data["element_type"] = random.choice(["button", "link", "image"])
    
    return data


def generate_clean_event() -> Dict:
    """Generate a clean, valid event record."""
    device = random.choice(DEVICE_TYPES)
    os = random.choice(OS_TYPES)
    browser = random.choice(BROWSERS)
    width, height = generate_screen_resolution(device)
    
    # Generate timestamp within last 30 days
    days_ago = random.randint(0, 30)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    microseconds = random.randint(0, 999999)
    timestamp = datetime.now() - timedelta(days=days_ago, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
    
    event_type = random.choice(EVENT_TYPES)
    
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": generate_user_id(),
        "session_id": generate_session_id(),
        "event_type": event_type,
        "page_url": generate_page_url(),
        "referrer_url": generate_page_url() if random.random() > 0.3 else None,
        "timestamp": timestamp.isoformat() + "Z",
        "user_agent": generate_user_agent(device, os, browser),
        "ip_address": fake.ipv4(),
        "country": fake.country_code(),
        "device_type": device,
        "os": os,
        "browser": browser,
        "screen_width": width,
        "screen_height": height,
        "event_data": generate_event_data(event_type)
    }


def inject_quality_issue(event: Dict, issue_type: str) -> Dict:
    """Inject a specific quality issue into an event."""
    
    if issue_type == "missing_required":
        # Remove required field
        required = ["user_id", "session_id", "event_type", "timestamp"]
        field = random.choice(required)
        event[field] = None
        
    elif issue_type == "invalid_timestamp":
        # Future date or malformed
        if random.choice([True, False]):
            future = datetime.now() + timedelta(days=random.randint(1, 365))
            event["timestamp"] = future.isoformat() + "Z"
        else:
            event["timestamp"] = "invalid-date-format"
            
    elif issue_type == "invalid_url":
        # Malformed URL
        event["page_url"] = "not-a-valid-url"
        
    elif issue_type == "inconsistent_session":
        # Same user, but event_type suggests new session
        if event["event_type"] == "logout":
            # But use same session_id as before (inconsistent)
            pass  # Session ID already set
            
    elif issue_type == "outlier_resolution":
        # Unrealistic screen resolution
        event["screen_width"] = random.randint(50000, 100000)
        event["screen_height"] = random.randint(50000, 100000)
        
    elif issue_type == "empty_string":
        # Empty strings
        string_fields = ["user_agent", "country", "browser"]
        field = random.choice(string_fields)
        event[field] = ""
        
    elif issue_type == "negative_dimensions":
        # Negative screen dimensions
        event["screen_width"] = -random.randint(100, 5000)
        event["screen_height"] = -random.randint(100, 5000)
    
    elif issue_type == "missing_event_data":
        # Missing event_data for events that should have it
        event["event_data"] = None
    
    return event


def generate_all_events() -> List[Dict]:
    """Generate all events with quality issues."""
    print(f"🌐 Generating {NUM_RECORDS:,} user events...")
    
    events = []
    issue_types = [
        "missing_required",
        "invalid_timestamp",
        "invalid_url",
        "inconsistent_session",
        "outlier_resolution",
        "empty_string",
        "negative_dimensions",
        "missing_event_data"
    ]
    
    # Generate clean records
    num_clean = int(NUM_RECORDS * (1 - QUALITY_ISSUE_RATE))
    num_issues = NUM_RECORDS - num_clean
    
    print(f"  ✅ Clean records: {num_clean:,} ({(1-QUALITY_ISSUE_RATE)*100:.1f}%)")
    print(f"  ⚠️  Records with issues: {num_issues:,} ({QUALITY_ISSUE_RATE*100:.1f}%)")
    
    # Generate clean events
    for i in range(num_clean):
        events.append(generate_clean_event())
        if (i + 1) % 30000 == 0:
            print(f"     Generated {i + 1:,} clean records...")
    
    # Generate events with issues
    for i in range(num_issues):
        event = generate_clean_event()
        issue_type = random.choice(issue_types)
        event = inject_quality_issue(event, issue_type)
        events.append(event)
        if (i + 1) % 5000 == 0:
            print(f"     Generated {i + 1:,} records with issues...")
    
    # Add duplicates (2% of records)
    num_duplicates = int(NUM_RECORDS * 0.02)
    print(f"  🔁 Adding {num_duplicates:,} duplicate records...")
    for _ in range(num_duplicates):
        duplicate = random.choice(events).copy()
        events.append(duplicate)
    
    # Shuffle
    random.shuffle(events)
    
    return events


def save_events(events: List[Dict]):
    """Save events to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')
    
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"✅ Saved {len(events):,} events ({file_size_mb:.2f} MB)")


def print_summary(events: List[Dict]):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("📊 SUMMARY STATISTICS")
    print("=" * 60)
    
    # Count by event type
    event_type_counts = {}
    for e in events:
        event_type = e.get("event_type", "unknown")
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
    
    print("\nRecords by event type:")
    for event_type, count in sorted(event_type_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(events)) * 100
        print(f"  {event_type:20s}: {count:8,} ({pct:5.2f}%)")
    
    # Count nulls
    null_count = sum(1 for e in events if any(v is None for v in e.values()))
    print(f"\nRecords with null values: {null_count:,} ({null_count/len(events)*100:.2f}%)")
    
    # Count duplicates
    event_ids = [e.get("event_id") for e in events if e.get("event_id")]
    duplicate_count = len(event_ids) - len(set(event_ids))
    print(f"Duplicate event_ids: {duplicate_count:,}")
    
    print("\n" + "=" * 60)


def main():
    """Main execution."""
    print("=" * 60)
    print("🌐 USER EVENTS DATA GENERATOR")
    print("=" * 60)
    print(f"\nTarget records: {NUM_RECORDS:,}")
    print(f"Quality issue rate: {QUALITY_ISSUE_RATE*100:.1f}%")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Generate events
    events = generate_all_events()
    
    # Save to file
    save_events(events)
    
    # Print summary
    print_summary(events)
    
    print("\n✅ Event data generation complete!")
    print("\n💡 Next steps:")
    print("   1. Inspect the data: head -n 5 data/raw/events.json")
    print("   2. Analyze event sequences by session")
    print("   3. Practice streaming ingestion patterns")


if __name__ == "__main__":
    main()
