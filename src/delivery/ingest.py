"""Load the Olist export files and drop everything the analysis does not need.

Only pseudonymous keys, states, timestamps, prices and review scores are kept.
Customer unique IDs, zip prefixes, cities and review texts never leave this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "categories": "product_category_name_translation.csv",
}

# Columns read from each file. Anything not listed is never loaded.
COLUMNS = {
    "orders": [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp",
        "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ],
    "items": ["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"],
    "customers": ["customer_id", "customer_state"],
    "sellers": ["seller_id", "seller_state"],
    "reviews": ["review_id", "order_id", "review_score", "review_creation_date", "review_answer_timestamp"],
    "products": ["product_id", "product_category_name"],
    "categories": ["product_category_name", "product_category_name_english"],
}  # fmt: skip

# Columns that identify people or places below state level. Tests assert that
# none of them appears in any output.
PERSONAL_COLUMNS = {
    "customer_unique_id", "customer_zip_code_prefix", "customer_city",
    "seller_zip_code_prefix", "seller_city", "review_comment_title", "review_comment_message",
}  # fmt: skip

DATE_COLUMNS = {
    "orders": COLUMNS["orders"][3:],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}


class DataError(ValueError):
    """An input file is missing or does not have the expected columns."""


@dataclass
class RawTables:
    orders: pd.DataFrame
    items: pd.DataFrame
    customers: pd.DataFrame
    sellers: pd.DataFrame
    reviews: pd.DataFrame
    products: pd.DataFrame
    categories: pd.DataFrame


def _read(folder: Path, name: str) -> pd.DataFrame:
    path = folder / FILES[name]
    if not path.exists():
        raise DataError(f"{path} not found. See the README for where to download the data.")
    header = pd.read_csv(path, nrows=0).columns
    missing = set(COLUMNS[name]) - set(header)
    if missing:
        raise DataError(f"{FILES[name]} is missing columns: {sorted(missing)}")
    frame = pd.read_csv(path, usecols=COLUMNS[name])
    for col in DATE_COLUMNS.get(name, []):
        frame[col] = pd.to_datetime(frame[col], errors="coerce")
    return frame


def load(folder: Path) -> RawTables:
    """Read all required files from ``folder``."""
    folder = Path(folder)
    return RawTables(**{name: _read(folder, name) for name in FILES})
