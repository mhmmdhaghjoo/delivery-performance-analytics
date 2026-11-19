"""Run the whole analysis and write every artefact to the output folder."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from . import kpis, model, validate
from .ingest import load

logger = logging.getLogger(__name__)


def run(data_dir: Path, out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    (out_dir / "model").mkdir(parents=True, exist_ok=True)

    raw = load(Path(data_dir))
    report = validate.quality_report(raw)
    report.to_csv(out_dir / "data_quality.csv", index=False)
    validate.assert_blocking_checks(report)

    fact = model.fact_orders(raw)
    fact.to_csv(out_dir / "model" / "fact_orders.csv", index=False)
    model.dim_state().to_csv(out_dir / "model" / "dim_state.csv", index=False)
    model.dim_date(fact).to_csv(out_dir / "model" / "dim_date.csv", index=False)

    tables = {
        "kpi_headline": kpis.headline(fact),
        "kpi_by_month": kpis.by_month(fact),
        "kpi_by_customer_state": kpis.by_customer_state(fact),
        "kpi_by_lane": kpis.by_lane(fact),
        "kpi_review_impact": kpis.review_impact(fact),
        "kpi_promise_calibration": kpis.promise_calibration(fact),
    }
    for name, table in tables.items():
        table.to_csv(out_dir / f"{name}.csv", index=False)
        logger.info("wrote %s (%d rows)", name, len(table))

    summary = dict(zip(tables["kpi_headline"]["kpi"], tables["kpi_headline"]["value"].astype(float)))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary
