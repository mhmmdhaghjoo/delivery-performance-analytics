"""Data-quality checks. Each check counts violations and states the rule applied later."""

from __future__ import annotations

import pandas as pd

from .ingest import RawTables


def quality_report(raw: RawTables) -> pd.DataFrame:
    """Return one row per check: table, check, violating rows and the rule used in the model."""
    o, it, r = raw.orders, raw.items, raw.reviews
    delivered = o["order_status"].eq("delivered")
    rows = [
        ("orders", "duplicate order_id", o["order_id"].duplicated().sum(), "stop: must be 0"),
        ("orders", "delivered status without delivery date",
         (delivered & o["order_delivered_customer_date"].isna()).sum(),
         "excluded from delivery KPIs"),
        ("orders", "delivery date before purchase",
         (o["order_delivered_customer_date"] < o["order_purchase_timestamp"]).sum(),
         "excluded from delivery KPIs"),
        ("orders", "handed to carrier before approval",
         (o["order_delivered_carrier_date"] < o["order_approved_at"]).sum(),
         "kept; affects only the approval-to-carrier stage, which is not reported"),
        ("orders", "delivered to customer before handed to carrier",
         (o["order_delivered_customer_date"] < o["order_delivered_carrier_date"]).sum(),
         "kept for lead time (purchase to customer is unaffected)"),
        ("orders", "estimated date before purchase",
         (o["order_estimated_delivery_date"] < o["order_purchase_timestamp"].dt.normalize()).sum(),
         "excluded from delivery KPIs"),
        ("orders", "customer_id not in customers",
         (~o["customer_id"].isin(raw.customers["customer_id"])).sum(), "stop: must be 0"),
        ("items", "order_id not in orders", (~it["order_id"].isin(o["order_id"])).sum(), "stop: must be 0"),
        ("items", "seller_id not in sellers",
         (~it["seller_id"].isin(raw.sellers["seller_id"])).sum(), "stop: must be 0"),
        ("items", "negative price or freight",
         ((it["price"] < 0) | (it["freight_value"] < 0)).sum(), "stop: must be 0"),
        ("reviews", "orders with more than one review",
         int((r.groupby("order_id").size() > 1).sum()), "latest answered review is used"),
        ("reviews", "score outside 1-5", (~r["review_score"].between(1, 5)).sum(), "stop: must be 0"),
        ("products", "category missing",
         raw.products["product_category_name"].isna().sum(), "labelled 'unknown'"),
    ]  # fmt: skip
    report = pd.DataFrame(rows, columns=["table", "check", "rows", "rule"])
    report["rows"] = report["rows"].astype(int)
    return report


def assert_blocking_checks(report: pd.DataFrame) -> None:
    """Stop the run if any check marked 'stop' has violations."""
    failed = report[report["rule"].str.startswith("stop") & report["rows"].gt(0)]
    if not failed.empty:
        raise ValueError("blocking data-quality checks failed:\n" + failed.to_string(index=False))
