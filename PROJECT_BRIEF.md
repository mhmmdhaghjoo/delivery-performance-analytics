# Project brief — Delivery Performance Analytics (Supply Chain · Power BI)

Version 2 (2026-11-19). Dataset switched from DataCo to Olist after a data audit (see `DATA_AUDIT_DATACO.md`; GATE 1 delta approved, D-8).
Repo name: `delivery-performance-analytics`

## 1. Business context
- **Organisation:** Olist, a Brazilian e-commerce marketplace connecting small sellers to customers across Brazil (2016–2018 order data).
- **Decision owner:** Head of Logistics / Fulfilment.
- **Secondary audience:** Customer Experience lead (reviews) and seller management (seller-side delays).

## 2. Business problem
Every order gets an estimated delivery date at purchase: the delivery promise. When the promise is broken, customers punish it in reviews. A promise that is too long is "safe" but may cost sales. Management needs to know where the promise is broken, what it costs in customer satisfaction, and where the promise should be longer or shorter.

## 3. Business questions
1. How often is the promise kept, overall, over time and by customer state / region?
2. Which seller-state → customer-state lanes break the promise most, beyond chance?
3. How much does a broken promise cost in review scores, and does the size of the delay matter?
4. Is the promise calibrated? By customer state, how does the promised lead time compare with the lead time actually needed to deliver 95 % of orders on time?
5. Which 3–5 lanes or periods should operations review first?

## 4. Decisions supported
(a) Recalibrate the delivery promise per customer state (longer where it is broken, shorter where it is heavily padded).
(b) Prioritise lanes and peak periods for an operational review.

## 5. KPIs
| KPI | Definition |
|---|---|
| On-time delivery rate (OTD) | Delivered orders with delivery date ≤ estimated date ÷ delivered orders. Calendar-day comparison. |
| Late rate | 1 − OTD |
| Delay of late orders | Days between estimated date and delivery date, late orders only |
| Lead time | Purchase timestamp → delivery to customer, in days |
| Promised lead time | Purchase date → estimated delivery date, in days |
| Promise buffer | Promised lead time − actual lead time |
| P95 lead time | 95th percentile of actual lead time in a segment |
| Average review score | Mean of the latest review per order (1–5) |
| 1-star share | Share of reviewed orders scored 1 |
| Lane | Seller state → customer state (single-seller orders only) |

Grain: one row per **order**. Multi-seller orders (~1.3 %) are kept in totals and excluded from lane metrics.

## 6. Dataset
- **Source:** Olist, *Brazilian E-Commerce Public Dataset by Olist*, Kaggle (olistbr/brazilian-ecommerce).
- **Licence:** **CC BY-NC-SA 4.0**, verified on the Kaggle dataset page on 2026-11-19. Non-commercial use with attribution; derived data shared under the same licence. Raw files are not committed.
- **Realism:** real, anonymised marketplace data (per the publisher). Store and partner names in review texts were replaced by the publisher.
- **Files used:** orders, order_items, customers, sellers, order_reviews, products, category translation. Payments and geolocation out of scope.

## 7. Privacy and ethics
- Pseudonymous IDs only. `customer_unique_id`, zip prefixes and cities are dropped at ingestion; review titles/texts are not loaded.
- All reported results are at state, lane or month level. Lanes with fewer than 100 orders are not ranked.

## 8. Methods
- Validation of timestamps (order of events, missing dates), statuses and joins, with documented rules.
- Rates with Wilson 95 % intervals; lanes compared with the overall late rate as baseline.
- Review impact: mean review score and 1-star share by on-time vs late and by delay band (association, not causation; reviews can be written before delivery).
- Promise calibration: per customer state, P95 actual lead time vs median promised lead time.
- No machine learning: the decision needs measurement and calibration, not prediction.

## 9. Tools
| Tool | Role |
|---|---|
| Python (pandas, pytest) | Ingestion, de-identification, validation, star-schema export, independent KPI calculation |
| Power Query M | Load and type the exports, date table |
| DAX | KPI measures |
| Power BI Desktop | Two-page dashboard for the Head of Logistics (built by the candidate) |

Audit: a reconciliation table compares every headline KPI from Python with the DAX result.

## 10. Outputs
`reports/` KPI tables, data-quality report and decision memo; `powerbi/` measures, queries, spec, `.pbix`, screenshots.
Dashboard pages: (1) Promise vs reality — OTD trend, OTD by state on a map or bar, review impact; (2) Lane and calibration review — lane matrix with intervals, promise vs P95 by state.

## 11. Milestones
| # | Milestone | Done when |
|---|---|---|
| M1 | Data obtained | 9 files present; licence verified ✔ (2026-11-19) |
| M2 | Ingestion + validation | De-identified order table; data-quality report; tests pass |
| M3 | Star schema + Python KPIs | Exports + KPI tables answer Q1–Q4; tests on KPI logic |
| M4 | Power BI model | M + DAX; reconciliation table matches Python to 0.1 pp |
| M5 | Dashboard | Two pages per spec; screenshots |
| M6 | Memo + README | Answers Q1–Q5; limitations stated |
| M7 | Mastery check | Candidate explains, without notes: grain, OTD definition, lane threshold, one DAX measure, one limitation |

## 12. Limitations (known)
- Data ends in 2018 and covers one marketplace; no carrier, warehouse or cost data, so the project shows where and when the promise fails, not why.
- The effect of a shorter promise on conversion cannot be measured with this data.
- Olist is a popular public dataset; the value is in the decision framing, calibration and reconciliation, not in novelty.

## 13. Overlap and effort
Logistics domain, no overlap with the HR or shop projects; the model is built in Python + Power Query, not SQL marts. Estimated 25–35 h.
