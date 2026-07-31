# Logistics Data & Automation Case Studies

Sanitized case studies based on operational logistics problems solved using SQL,
Python, Databricks, dashboards, and workflow automation.

All company names, internal identifiers, infrastructure details, credentials,
URLs, table names, and operational codes have been removed or replaced.
This repository demonstrates engineering decisions and validation methods;
it is not a deployable copy of an employer system.

## Featured Projects

| Project | Business problem | Solution | Measured impact | Primary hiring signal |
|---|---|---|---|---|
| [Clarification Case Automation](featured/01-clarification-automation/) | Employees double-logged inventory clarification work in both a WMS and a spreadsheet | Oracle/WMS made the source of truth; idempotent scheduled sync with a late-data recovery window | ~90% less manual entry (operator-reported, see project docs) | Designing idempotent, recoverable data pipelines around a system of record |
| [Dangerous-Goods Data Product](featured/02-dangerous-goods-data-product/) | A compliance-critical stock report was built by hand from a large manual export | Parameterized Oracle extract, automated cleaning/classification, scheduled refresh feeding a dashboard | ~100 minutes/day of manual work removed (operator-reported) | Turning a manual compliance report into a monitored data product |
| [Order-Flow Bottleneck Analysis](featured/03-order-flow-bottleneck-analysis/) | Suspected background transport traffic was slowing order fulfilment, with no data to confirm it | Joined 3 event sources to measure wait time, processing time, and concurrent transport load | Evidence used to justify a warehouse-control-system prioritisation change (correlational, not causal — see project docs) | Turning an operational hypothesis into a rigorous, honestly-scoped data analysis |

## Also in this repository

- [technical-deep-dives/inventory-event-reconciliation](technical-deep-dives/inventory-event-reconciliation/) —
  a closer look at the SQL techniques (transaction-lifecycle reconstruction,
  JSON extraction, sequence-matched deduplication) behind the inventory data used
  across the featured projects above.
- [additional-work/](additional-work/) — shorter write-ups of other automation and
  reporting work that didn't warrant a full case study.
- [shared/logistics_data_utils](shared/logistics_data_utils/) — the shared Python
  package the featured pipelines are built on.

See [docs/portfolio-scope.md](docs/portfolio-scope.md) for what is and isn't
covered here, and [docs/sanitization-policy.md](docs/sanitization-policy.md) for
exactly how identifying details were removed.

## License

MIT — see [LICENSE](LICENSE).
