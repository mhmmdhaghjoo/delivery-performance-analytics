# Delivery Performance Analytics

[![ci](https://github.com/mhmmdhaghjoo/delivery-performance-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/mhmmdhaghjoo/delivery-performance-analytics/actions/workflows/ci.yml)

> Status: work in progress. Milestones M1–M3 (data, validation, model, Python KPIs) are done; the Power BI dashboard (M4–M5) and the decision memo (M6) are next. Numbers below come from the current pipeline run and are provisional until the memo.

**Business question:** an online marketplace promises every customer a delivery date at checkout. Is the promise kept, where and when is it broken, what does a broken promise cost in customer satisfaction, and how should the promise be recalibrated?

**Audience:** Head of Logistics / Fulfilment.

## Provisional findings

- **The promise is long, but still broken.** Of 96,470 delivered orders, 6.8 % arrived after the promised date. The median promise is 24 days for a median actual delivery time of 10 days: the average order has two weeks of slack, and the problem is in the tail.
- **Lateness is concentrated.** It ranges from about 3 % in several northern states to 21 % in Alagoas. Rio de Janeiro has 12,350 orders and a 12 % late rate. The single lane with the most excess late orders is São Paulo → Rio de Janeiro (8,048 orders, 14.3 % late, 95 % interval 13.5 % to 15.0 %), about 600 more late orders than the overall rate would predict.
- **Late deliveries are punished in reviews.** On-time orders average 4.3 stars and late orders 2.3. The share of one-star reviews rises from 7 % on time to 25 % at 1–3 days late and 59 % at 4–7 days late. (Association; some reviews are written before delivery.)
- **Peaks break the promise.** The late rate reached 12 % for November 2017 orders (Black Friday) and 14 % and 19 % for February and March 2018, against 3–5 % in normal months.
- **Calibration.** 20 of 27 states miss a 95 % on-time target with today's promise. A few northern states meet it with days to spare.

## How it works

```
9 Olist CSV files ─▶ load + de-identify ─▶ 13 data-quality checks ─▶ order-level fact table + dimensions ─▶ KPI tables ─▶ Power BI
```

| Module | Responsibility |
|---|---|
| `delivery/ingest.py` | Reads only the columns needed; customer unique IDs, zip prefixes, cities and review texts are never loaded |
| `delivery/validate.py` | Counts violations per check and stops the run on blocking ones (`reports/data_quality.csv`) |
| `delivery/model.py` | One row per order: promise, lead time, delay, lane, value, latest review; state and date dimensions |
| `delivery/kpis.py` | Late rates with Wilson intervals by month, state and lane; review impact by delay band; promise calibration |
| `delivery/pipeline.py`, `cli.py` | `delivery run` writes every table to `reports/` |

### Definitions

- **Late:** delivered on a calendar day after the estimated delivery date. Delivery on the promised day counts as on time.
- **Lane:** seller state → customer state, for orders shipped by a single seller (98.7 % of orders). Lanes with fewer than 100 delivered orders are not ranked.
- **Review score:** the most recently answered review per order.
- **Calibration verdict:** a state misses the target when its late rate is above 5 %. The gap between the median promise and the 95th-percentile delivery time is shown as guidance only, because promises vary per order.

## Data

*Brazilian E-Commerce Public Dataset by Olist*, Kaggle (olistbr/brazilian-ecommerce), licensed **CC BY-NC-SA 4.0**. Real, anonymised orders from 2016 to 2018. The raw files are not included; download them from Kaggle into `data/olist/`.

The KPI tables in `reports/` are derived from this data and are shared under the same licence.

An earlier candidate dataset (DataCo Smart Supply Chain) was rejected after an audit showed its delivery times follow a fixed rule per shipping mode: see [`DATA_AUDIT_DATACO.md`](DATA_AUDIT_DATACO.md).

## Run it

Requires Python 3.10 or later.

```bash
pip install -e ".[dev]"
delivery run --data data/olist --out reports
pytest -q        # 17 tests on a synthetic fixture, no download needed
```

## Limitations

- No carrier, warehouse or cost data: the analysis shows where and when the promise fails, not why.
- The effect of a shorter or longer promise on conversion cannot be measured here.
- Data ends in 2018 and covers one marketplace.

## Related projects

- [Employee Turnover Analytics](https://github.com/mhmmdhaghjoo/employee-turnover-analytics): people analytics with survival analysis, out-of-time risk models and a fairness audit
- [Checkout A/B Test (R)](https://github.com/mhmmdhaghjoo/checkout-ab-test-r): an A/B test from power analysis to a Bayesian rollout recommendation
- Online shop case series: [SQL warehouse](https://github.com/mhmmdhaghjoo/online-retail-sql-warehouse), [churn pipeline](https://github.com/mhmmdhaghjoo/customer-churn-ml-pipeline), [text-to-SQL assistant](https://github.com/mhmmdhaghjoo/text-to-sql-assistant)

More about me: [mhmmdhaghjoo.github.io](https://mhmmdhaghjoo.github.io)

## Licence

Code: MIT. Data and derived tables: CC BY-NC-SA 4.0 (Olist).
