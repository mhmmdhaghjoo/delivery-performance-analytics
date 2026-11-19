"""A tiny synthetic data set in the Olist file format, with known answers.

Personal columns (unique IDs, zip prefixes, cities, review texts) are included
on purpose so the tests can prove they never reach any output.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ORDERS = [
    # order_id, customer, status, purchase, delivered_customer, estimated
    ("o1", "c1", "delivered", "2017-03-01 10:00", "2017-03-10 18:00", "2017-03-10"),  # on the promised day -> on time
    ("o2", "c2", "delivered", "2017-03-02 09:00", "2017-03-12 08:00", "2017-03-11"),  # 1 day late
    ("o3", "c3", "delivered", "2017-03-03 12:00", "2017-03-05 12:00", "2017-03-20"),  # early
    ("o4", "c4", "delivered", "2017-03-04 12:00", "2017-03-02 12:00", "2017-03-15"),  # delivered before purchase -> invalid
    ("o5", "c5", "canceled", "2017-03-05 12:00", None, "2017-03-15"),                  # not delivered
    ("o6", "c6", "delivered", "2017-04-01 12:00", "2017-04-30 12:00", "2017-04-20"),  # 10 days late, two sellers
]  # fmt: skip


def write_fixture(folder: Path, orphan_item: bool = False) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    orders = pd.DataFrame(
        [
            {
                "order_id": oid, "customer_id": cid, "order_status": status,
                "order_purchase_timestamp": purchase, "order_approved_at": purchase,
                "order_delivered_carrier_date": purchase,
                "order_delivered_customer_date": delivered, "order_estimated_delivery_date": estimated,
            }
            for oid, cid, status, purchase, delivered, estimated in ORDERS
        ]
    )  # fmt: skip
    customers = pd.DataFrame(
        {
            "customer_id": [f"c{i}" for i in range(1, 7)],
            "customer_unique_id": [f"person{i}" for i in range(1, 7)],
            "customer_zip_code_prefix": [1000 + i for i in range(6)],
            "customer_city": ["sao paulo", "rio", "recife", "salvador", "manaus", "rio"],
            "customer_state": ["SP", "RJ", "PE", "BA", "AM", "RJ"],
        }
    )
    sellers = pd.DataFrame(
        {
            "seller_id": ["s1", "s2"],
            "seller_zip_code_prefix": [2000, 2001],
            "seller_city": ["campinas", "curitiba"],
            "seller_state": ["SP", "PR"],
        }
    )
    item_rows = [
        ("o1", 1, "p1", "s1", 50.0, 10.0),
        ("o1", 2, "p1", "s1", 50.0, 10.0),
        ("o2", 1, "p2", "s1", 80.0, 15.0),
        ("o3", 1, "p1", "s2", 20.0, 5.0),
        ("o4", 1, "p2", "s1", 30.0, 5.0),
        ("o5", 1, "p1", "s1", 40.0, 8.0),
        ("o6", 1, "p1", "s1", 60.0, 12.0),
        ("o6", 2, "p2", "s2", 70.0, 14.0),
    ]
    if orphan_item:
        item_rows.append(("o_missing", 1, "p1", "s1", 10.0, 1.0))
    items = pd.DataFrame(
        item_rows, columns=["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"]
    )
    items["shipping_limit_date"] = "2017-03-01 00:00:00"
    reviews = pd.DataFrame(
        {
            "review_id": ["r1", "r2", "r2b", "r3", "r6"],
            "order_id": ["o1", "o2", "o2", "o3", "o6"],
            "review_score": [5, 4, 1, 5, 1],
            "review_comment_title": ["ok", "", "bad", "", "late"],
            "review_comment_message": ["Maria was great", "", "still waiting", "", "never again"],
            "review_creation_date": ["2017-03-11", "2017-03-05", "2017-03-13", "2017-03-06", "2017-05-01"],
            # r2b was answered later than r2, so order o2 must get score 1
            "review_answer_timestamp": ["2017-03-12", "2017-03-06", "2017-03-14", "2017-03-07", "2017-05-02"],
        }
    )
    products = pd.DataFrame({"product_id": ["p1", "p2"], "product_category_name": ["moveis", None]})
    categories = pd.DataFrame({"product_category_name": ["moveis"], "product_category_name_english": ["furniture"]})

    frames = {
        "olist_orders_dataset.csv": orders,
        "olist_order_items_dataset.csv": items,
        "olist_customers_dataset.csv": customers,
        "olist_sellers_dataset.csv": sellers,
        "olist_order_reviews_dataset.csv": reviews,
        "olist_products_dataset.csv": products,
        "product_category_name_translation.csv": categories,
    }
    for name, frame in frames.items():
        frame.to_csv(folder / name, index=False)
    return folder


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return write_fixture(tmp_path / "olist")
