"""Build the order-level fact table and small dimensions for Power BI."""

from __future__ import annotations

import pandas as pd

from .ingest import RawTables

REGIONS = {
    "North": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Northeast": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Center-West": ["DF", "GO", "MT", "MS"],
    "Southeast": ["ES", "MG", "RJ", "SP"],
    "South": ["PR", "RS", "SC"],
}
STATE_REGION = {state: region for region, states in REGIONS.items() for state in states}


def _latest_review(reviews: pd.DataFrame) -> pd.Series:
    """One score per order: the most recently answered review."""
    latest = reviews.sort_values(["order_id", "review_answer_timestamp"]).groupby("order_id").tail(1)
    return latest.set_index("order_id")["review_score"]


def fact_orders(raw: RawTables) -> pd.DataFrame:
    """One row per order with delivery timing, lane, value and review score."""
    o = raw.orders.merge(raw.customers, on="customer_id", how="left")

    items = raw.items.merge(raw.sellers, on="seller_id", how="left")
    per_order = items.groupby("order_id").agg(
        n_items=("order_item_id", "size"),
        n_sellers=("seller_id", "nunique"),
        seller_state=("seller_state", "first"),
        items_value=("price", "sum"),
        freight_value=("freight_value", "sum"),
    )
    o = o.join(per_order, on="order_id")
    # A lane is only defined when one seller ships the whole order.
    o.loc[o["n_sellers"].ne(1), "seller_state"] = pd.NA
    o["review_score"] = o["order_id"].map(_latest_review(raw.reviews))

    purchase_day = o["order_purchase_timestamp"].dt.normalize()
    delivered_day = o["order_delivered_customer_date"].dt.normalize()
    o["promised_days"] = (o["order_estimated_delivery_date"] - purchase_day).dt.days
    o["lead_time_days"] = (
        o["order_delivered_customer_date"] - o["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    o["delay_days"] = (delivered_day - o["order_estimated_delivery_date"]).dt.days

    o["is_delivered"] = (
        o["order_status"].eq("delivered")
        & o["order_delivered_customer_date"].notna()
        & o["lead_time_days"].ge(0)
        & o["promised_days"].ge(0)
    )
    o["is_late"] = o["is_delivered"] & o["delay_days"].gt(0)
    o.loc[~o["is_delivered"], ["lead_time_days", "delay_days"]] = pd.NA

    o["customer_region"] = o["customer_state"].map(STATE_REGION)
    o["lane"] = o["seller_state"].where(o["seller_state"].isna(), o["seller_state"] + " → " + o["customer_state"])
    o["purchase_date"] = purchase_day.dt.date
    o["purchase_month"] = o["order_purchase_timestamp"].dt.to_period("M").astype(str)

    columns = [
        "order_id", "order_status", "purchase_date", "purchase_month",
        "order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date",
        "customer_state", "customer_region", "seller_state", "lane", "n_items", "n_sellers",
        "items_value", "freight_value", "promised_days", "lead_time_days", "delay_days",
        "is_delivered", "is_late", "review_score",
    ]  # fmt: skip
    return o[columns].reset_index(drop=True)


def dim_state() -> pd.DataFrame:
    return pd.DataFrame(sorted(STATE_REGION.items()), columns=["state", "region"])


def dim_date(fact: pd.DataFrame) -> pd.DataFrame:
    start = pd.Timestamp(fact["order_purchase_timestamp"].min()).normalize()
    end = pd.Timestamp(fact["order_estimated_delivery_date"].max()).normalize()
    days = pd.date_range(start, end, freq="D")
    return pd.DataFrame(
        {
            "date": days.date,
            "year": days.year,
            "month": days.month,
            "year_month": days.to_period("M").astype(str),
            "quarter": "Q" + days.quarter.astype(str),
            "weekday": days.day_name(),
        }
    )
