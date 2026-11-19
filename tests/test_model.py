from __future__ import annotations

import math

import pandas as pd
import pytest

from delivery import kpis, model, validate
from delivery.ingest import PERSONAL_COLUMNS, load
from delivery.pipeline import run

from .conftest import write_fixture


@pytest.fixture
def fact(data_dir):
    return model.fact_orders(load(data_dir)).set_index("order_id")


def test_one_row_per_order(fact):
    assert fact.index.is_unique
    assert len(fact) == 6


def test_delivery_on_promised_day_is_on_time_regardless_of_clock_time(fact):
    assert not fact.loc["o1", "is_late"]
    assert fact.loc["o1", "delay_days"] == 0


def test_one_day_after_promise_is_late(fact):
    assert fact.loc["o2", "is_late"]
    assert fact.loc["o2", "delay_days"] == 1


def test_impossible_and_undelivered_orders_are_excluded(fact):
    assert not fact.loc["o4", "is_delivered"]  # delivered before purchase
    assert not fact.loc["o5", "is_delivered"]  # cancelled
    assert pd.isna(fact.loc["o4", "lead_time_days"])


def test_lane_only_for_single_seller_orders(fact):
    assert fact.loc["o1", "lane"] == "SP → SP"
    assert fact.loc["o3", "lane"] == "PR → PE"
    assert pd.isna(fact.loc["o6", "lane"])  # two sellers


def test_items_are_summed_per_order(fact):
    assert fact.loc["o1", "n_items"] == 2
    assert fact.loc["o1", "items_value"] == 100.0
    assert fact.loc["o1", "freight_value"] == 20.0


def test_latest_answered_review_is_used(fact):
    assert fact.loc["o2", "review_score"] == 1


def test_promised_days_counted_from_purchase_date(fact):
    assert fact.loc["o1", "promised_days"] == 9


def test_headline_late_rate(fact):
    head = kpis.headline(fact.reset_index()).set_index("kpi")["value"]
    # delivered and valid: o1 on time, o2 late, o3 early, o6 late
    assert head["orders_delivered"] == 4
    assert head["late_rate"] == pytest.approx(0.5)
    assert head["avg_delay_days_late_orders"] == pytest.approx((1 + 10) / 2)


def test_lane_threshold_hides_small_lanes(fact):
    assert kpis.by_lane(fact.reset_index(), min_orders=2).empty
    lanes = kpis.by_lane(fact.reset_index(), min_orders=1)
    assert set(lanes["lane"]) == {"SP → SP", "SP → RJ", "PR → PE"}


def test_wilson_interval_matches_known_value():
    low, high = kpis.wilson(10, 100)
    assert low == pytest.approx(0.0552, abs=1e-4)
    assert high == pytest.approx(0.1744, abs=1e-4)


def test_review_impact_bands(fact):
    impact = kpis.review_impact(fact.reset_index()).set_index("delay_band")
    assert impact.loc["on time", "avg_review"] == pytest.approx(5.0)  # o1 and o3
    assert impact.loc["1-3 days late", "one_star_share"] == pytest.approx(1.0)


def test_quality_report_counts_known_defects(data_dir):
    report = validate.quality_report(load(data_dir)).set_index("check")["rows"]
    assert report["delivery date before purchase"] == 1
    assert report["orders with more than one review"] == 1
    assert report["category missing"] == 1


def test_blocking_check_stops_on_orphan_item(tmp_path):
    folder = write_fixture(tmp_path / "bad", orphan_item=True)
    with pytest.raises(ValueError, match="order_id not in orders"):
        validate.assert_blocking_checks(validate.quality_report(load(folder)))


def test_no_personal_column_or_value_reaches_any_output(data_dir, tmp_path):
    out = tmp_path / "out"
    run(data_dir, out)
    for path in out.rglob("*.csv"):
        frame = pd.read_csv(path, dtype=str)
        assert not PERSONAL_COLUMNS & set(frame.columns), path.name
        text = frame.to_csv()
        for value in ["person1", "sao paulo", "Maria", "campinas"]:
            assert value not in text, f"{value} in {path.name}"


def test_pipeline_writes_all_tables(data_dir, tmp_path):
    summary = run(data_dir, tmp_path / "out")
    assert math.isclose(summary["late_rate"], 0.5)
    for name in ["kpi_by_month", "kpi_by_customer_state", "kpi_promise_calibration", "data_quality"]:
        assert (tmp_path / "out" / f"{name}.csv").exists()
    assert (tmp_path / "out" / "model" / "fact_orders.csv").exists()


def test_promise_calibration_compares_promise_with_actual_lead_time(fact):
    cal = kpis.promise_calibration(fact.reset_index(), quantile=0.95).set_index("customer_state")
    # RJ: o2 (promised 9 days, took ~9.96 days) and o6 (promised 19 days, took 29 days)
    rj = cal.loc["RJ"]
    assert rj["median_promised_days"] == pytest.approx(14.0)
    assert rj["p95_lead_time_days"] == pytest.approx(29.0)
    assert rj["gap_days"] == pytest.approx(-15.0)
    assert rj["assessment"].startswith("misses")
    # PE: o3 promised 17 days, delivered in 2 -> lots of spare time
    assert cal.loc["PE", "assessment"].endswith("> 7 days spare")
    assert cal["small_sample"].all()
