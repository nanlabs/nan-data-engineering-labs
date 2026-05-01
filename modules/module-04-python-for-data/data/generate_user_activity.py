#!/usr/bin/env python3
"""Generar dataset de actividad de usuarios en JSON"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

Path("data/raw").mkdir(parents=True, exist_ok=True)

random.seed(42)

event_types = [
    'page_view', 'click', 'search', 'add_to_cart', 'remove_from_cart',
    'checkout', 'purchase', 'login', 'logout', 'review', None
]
devices = ['desktop', 'mobile', 'tablet', None]
browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera', None]
os_list = ['Windows', 'MacOS', 'Linux', 'iOS', 'Android', None]

print("Generando user_activity.json...")

events = []

for i in range(1, 20001):
    if i % 5000 == 0:
        print(f"  {i}/20000 eventos generados...")
    
    days_ago = random.randint(1, 90)
    event_time = datetime.now() - timedelta(
        days=days_ago,
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    
    # Device nested
    device = {
        "type": random.choice(devices),
        "browser": random.choice(browsers),
        "os": random.choice(os_list),
        "screen_resolution": random.choice([
            "1920x1080", "1366x768", "1440x900", "2560x1440", None
        ])
    } if random.random() > 0.05 else None
    
    # Location nested
    location = {
        "country": random.choice(["México", "España", "Argentina", "Colombia", None]),
        "city": random.choice(["CDMX", "Madrid", "Buenos Aires", "Bogotá", None]),
        "ip_address": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    } if random.random() > 0.05 else None
    
    event = {
        "event_id": f"EVT-{i:06d}",
        "user_id": random.randint(1, 10000) if random.random() > 0.02 else None,
        "session_id": f"SES-{random.randint(1, 5000):06d}",
        "timestamp": event_time.isoformat() if random.random() > 0.03 
                     else str(int(event_time.timestamp())),
        "event_type": random.choice(event_types),
        "page_url": f"/page/{random.randint(1, 100)}" if random.random() > 0.05 else None,
        "referrer": random.choice([
            "https://google.com",
            "https://facebook.com",
            "direct",
            None,
            ""
        ]),
        "device": device,
        "location": location,
        "product_id": random.randint(1, 500) if random.random() > 0.3 else None,
        "search_query": random.choice([
            "laptop", "phone", "camera", "headphones", "watch", None, ""
        ]) if random.random() > 0.7 else None,
        "duration_seconds": random.randint(1, 600) if random.random() > 0.2 else None
    }
    
    events.append(event)

# Guardar en JSON
print("  Guardando archivo...")
with open('data/raw/user_activity.json', 'w', encoding='utf-8') as f:
    json.dump(events, f, indent=2, ensure_ascii=False)

print("✅ Creado user_activity.json con 20,000 eventos")
