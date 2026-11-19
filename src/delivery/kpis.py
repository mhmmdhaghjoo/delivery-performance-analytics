"""KPIs calculated independently of Power BI, used for the memo and for reconciliation."""

from __future__ import annotations

import numpy as np
import pandas as pd

MIN_LANE_ORDERS = 100
Z = 1.959964


def wilson(successes: pd.Series | int, n: pd.Series | int) -> tuple:
    """Wilson 95 % interval for a proportion."""
    successes = np.asarray(successes, dtype=float)
    n = np.asarray(n, dtype=float)
    p = np.divide(successes, n, out=np.zeros_like(n), where=n > 0)
    denom = 1 + Z**2 / n
    centre = (p + Z**2 / (2 * n)) / denom
    half = Z * np.sqrt(p * (1 - p) / n + Z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def _late_table(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    g = df.groupby(by, observed=True)
    t = g.agg(
        orders=("is_late", "size"),
        late_orders=("is_late", "sum"),
        median_lead_time_days=("lead_time_days", "median"),
        median_promised_days=("promised_days", "median"),
        avg_review=("review_score", "mean"),
    ).reset_index()
    t["late_rate"] = t["late_orders"] / t["orders"]
    t["late_rate_low"], t["late_rate_high"] = wilson(t["late_orders"], t["orders"])
    return t


def delivered(fact: pd.DataFrame) -> pd.DataFrame:
    return fact[fact["is_delivered"]]


def headline(fact: pd.DataFrame) -> pd.DataFrame:
    d = delivered(fact)
    late = d["is_late"]
    rows = {
        "orders_total": len(fact),
        "orders_delivered": len(d),
        "on_time_rate": 1 - late.mean(),
        "late_rate": late.mean(),
        "median_lead_time_days": d["lead_time_days"].median(),
        "median_promised_days": d["promised_days"].median(),
        "avg_delay_days_late_orders": d.loc[late, "delay_days"].mean(),
        "avg_review_on_time": d.loc[~late, "review_score"].mean(),
        "avg_review_late": d.loc[late, "review_score"].mean(),
    }
    return pd.DataFrame({"kpi": list(rows), "value": list(rows.values())})


def by_month(fact: pd.DataFrame) -> pd.DataFrame:
    return _late_table(delivered(fact), ["purchase_month"])


def by_customer_state(fact: pd.DataFrame) -> pd.DataFrame:
    return _late_table(delivered(fact), ["customer_region", "customer_state"]).sort_values("late_rate")


def by_lane(fact: pd.DataFrame, min_orders: int = MIN_LANE_ORDERS) -> pd.DataFrame:
    """Lanes with enough orders, flagged when the whole interval lies above the overall late rate."""
    d = delivered(fact).dropna(subset=["lane"])
    t = _late_table(d, ["lane", "seller_state", "customer_state"])
    t = t[t["orders"] >= min_orders].copy()
    overall = delivered(fact)["is_late"].mean()
    t["above_baseline"] = t["late_rate_low"] > overall
    t["excess_late_orders"] = t["late_orders"] - t["orders"] * overall
    return t.sort_values("excess_late_orders", ascending=False).reset_index(drop=True)


def review_impact(fact: pd.DataFrame) -> pd.DataFrame:
    """Review score by delay band (association only)."""
    d = delivered(fact).dropna(subset=["review_score"]).copy()
    bands = pd.cut(
        d["delay_days"],
        bins=[-np.inf, 0, 3, 7, 14, np.inf],
        labels=["on time", "1-3 days late", "4-7 days late", "8-14 days late", "15+ days late"],
    )
    d["delay_band"] = bands
    t = d.groupby("delay_band", observed=True).agg(
        orders=("review_score", "size"),
        avg_review=("review_score", "mean"),
        one_star_share=("review_score", lambda s: (s == 1).mean()),
    )
    return t.reset_index()


def promise_calibration(fact: pd.DataFrame, quantile: float = 0.95) -> pd.DataFrame:
    """Per customer state: current median promise vs the lead time that covers ``quantile`` of orders."""
    d = delivered(fact)
    t = d.groupby(["customer_region", "customer_state"]).agg(
        orders=("lead_time_days", "size"),
        median_promised_days=("promised_days", "median"),
        p95_lead_time_days=("lead_time_days", lambda s: np.ceil(s.quantile(quantile))),
        late_rate=("is_late", "mean"),
    ).reset_index()
    needed = f"p{round(quantile * 100)}_lead_time_days"
    t = t.rename(columns={"p95_lead_time_days": needed})
    # Indicative only: promises vary per order, so the verdict uses the late rate itself.
    t["gap_days"] = t["median_promised_days"] - t[needed]
    target = f"{round(quantile * 100)} % on-time target"
    t["assessment"] = np.select(
        [t["late_rate"] > 1 - quantile, t["gap_days"] > 7],
        [f"misses {target}", f"meets {target} with > 7 days spare"],
        default=f"meets {target}",
    )
    t["small_sample"] = t["orders"] < MIN_LANE_ORDERS
    return t.sort_values("gap_days").reset_index(drop=True)
