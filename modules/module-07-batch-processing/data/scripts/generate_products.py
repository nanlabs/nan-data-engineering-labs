#!/usr/bin/env python3
"""
Generate product catalog for batch processing exercises.

Creates realistic product data with:
- 100K products
- Different categories
- Price ranges
- Stock levels
"""

import argparse
import random
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from tqdm import tqdm


# Configuration
CATEGORIES = ["electronics", "clothing", "books", "home", "sports", "toys", "food", "beauty"]

# Sample product names by category
PRODUCT_NAMES = {
    "electronics": [
        "Laptop", "Smartphone", "Tablet", "Headphones", "Camera", "Monitor",
        "Keyboard", "Mouse", "Speaker", "Smartwatch", "Charger", "USB Cable"
    ],
    "clothing": [
        "T-Shirt", "Jeans", "Dress", "Jacket", "Shoes", "Sneakers",
        "Hoodie", "Sweater", "Pants", "Shorts", "Socks", "Hat"
    ],
    "books": [
        "Novel", "Textbook", "Cookbook", "Biography", "Self-Help", "Fiction",
        "Magazine", "Comic", "Dictionary", "Atlas", "Guide", "Manual"
    ],
    "home": [
        "Chair", "Table", "Lamp", "Rug", "Curtain", "Pillow",
        "Blanket", "Vase", "Clock", "Mirror", "Shelf", "Organizer"
    ],
    "sports": [
        "Ball", "Racket", "Weights", "Yoga Mat", "Bicycle", "Treadmill",
        "Gloves", "Helmet", "Water Bottle", "Bag", "Shoes", "Jersey"
    ],
    "toys": [
        "Action Figure", "Doll", "Puzzle", "Board Game", "LEGO Set", "RC Car",
        "Teddy Bear", "Building Blocks", "Card Game", "Truck", "Train Set"
    ],
    "food": [
        "Coffee", "Tea", "Chocolate", "Snack Bar", "Cereal", "Pasta",
        "Sauce", "Spices", "Oil", "Nuts", "Cookies", "Candy"
    ],
    "beauty": [
        "Shampoo", "Conditioner", "Lotion", "Perfume", "Lipstick", "Foundation",
        "Mascara", "Face Cream", "Body Wash", "Sunscreen", "Nail Polish"
    ]
}

BRANDS = {
    "electronics": ["Samsung", "Apple", "Sony", "LG", "Dell", "HP", "Lenovo", "Asus"],
    "clothing": ["Nike", "Adidas", "H&M", "Zara", "Gap", "Levi's", "Uniqlo", "Puma"],
    "books": ["Penguin", "HarperCollins", "Simon & Schuster", "Wiley", "McGraw-Hill"],
    "home": ["IKEA", "West Elm", "Pottery Barn", "Crate&Barrel", "HomeGoods"],
    "sports": ["Nike", "Adidas", "Under Armour", "Puma", "Reebok", "Wilson"],
    "toys": ["LEGO", "Mattel", "Hasbro", "Fisher-Price", "Nerf", "Hot Wheels"],
    "food": ["Nestlé", "General Mills", "Kellogg's", "Kraft", "Barilla"],
    "beauty": ["L'Oréal", "Estée Lauder", "Maybelline", "Nivea", "Neutrogena"]
}


def generate_product(product_id: int) -> Dict[str, Any]:
    """Generate a single product record."""

    # Category
    category = random.choice(CATEGORIES)

    # Name
    base_name = random.choice(PRODUCT_NAMES[category])
    brand = random.choice(BRANDS[category])

    # Add variation to name
    if category == "electronics":
        variant = random.choice(["Pro", "Plus", "Max", "Mini", "Ultra", "Lite", ""])
        model = f"{random.choice(['X', 'S', 'Z'])}{random.randint(1, 9)}"
        name = f"{brand} {base_name} {variant} {model}".strip()
    elif category == "clothing":
        size = random.choice(["XS", "S", "M", "L", "XL", "XXL"])
        color = random.choice(["Black", "White", "Blue", "Red", "Gray", "Navy"])
        name = f"{brand} {base_name} {size} {color}"
    else:
        name = f"{brand} {base_name}"

    # Price based on category
    price_ranges = {
        "electronics": (50, 3000),
        "clothing": (20, 300),
        "books": (10, 100),
        "home": (30, 1000),
        "sports": (25, 500),
        "toys": (10, 200),
        "food": (5, 50),
        "beauty": (10, 150)
    }
    min_price, max_price = price_ranges[category]
    price = round(random.uniform(min_price, max_price), 2)

    # Stock (higher for cheaper items)
    if price < 50:
        stock = random.randint(100, 10000)
    elif price < 200:
        stock = random.randint(50, 1000)
    else:
        stock = random.randint(10, 500)

    # Rating (normal distribution around 4.0)
    rating = random.normalvariate(4.0, 0.8)
    rating = max(1.0, min(5.0, rating))
    rating = round(rating, 1)

    # Reviews (correlated with rating and price)
    base_reviews = int(random.expovariate(1 / 50))
    if rating > 4.5:
        reviews_count = int(base_reviews * 1.5)
    elif rating < 3.0:
        reviews_count = int(base_reviews * 0.5)
    else:
        reviews_count = base_reviews

    # Availability (95% available)
    is_available = random.random() > 0.05 and stock > 0

    return {
        "product_id": f"PROD{product_id:05d}",
        "name": name,
        "category": category,
        "price": price,
        "stock": stock,
        "brand": brand,
        "rating": rating,
        "reviews_count": reviews_count,
        "is_available": is_available
    }


def main():
    parser = argparse.ArgumentParser(description="Generate product dataset")
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/raw/products.parquet",
        help="Output file path"
    )
    parser.add_argument(
        "--num-products",
        type=int,
        default=100_000,
        help="Number of products to generate"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["parquet", "csv", "json"],
        default="parquet",
        help="Output format"
    )

    args = parser.parse_args()

    # Setup
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.num_products:,} products")
    print(f"Output: {output_path}")
    print(f"Format: {args.format}")
    print()

    # Generate products
    products = []
    for product_id in tqdm(range(1, args.num_products + 1), desc="Generating products"):
        product = generate_product(product_id)
        products.append(product)

    # Create DataFrame
    df = pd.DataFrame(products)

    # Write data
    if args.format == "parquet":
        df.to_parquet(output_path, index=False, compression="snappy")
    elif args.format == "csv":
        df.to_csv(output_path, index=False)
    elif args.format == "json":
        df.to_json(output_path, orient="records", lines=True)

    # Summary
    size_mb = output_path.stat().st_size / (1024 * 1024)

    print()
    print("=" * 50)
    print("Generation Complete!")
    print("=" * 50)
    print(f"Total products: {len(df):,}")
    print(f"File size: {size_mb:.2f} MB")
    print()

    print("Category distribution:")
    print(df["category"].value_counts())
    print()

    print("Price statistics:")
    print(df["price"].describe())
    print()

    print("Sample data (first 5 products):")
    print(df.head())


if __name__ == "__main__":
    main()
