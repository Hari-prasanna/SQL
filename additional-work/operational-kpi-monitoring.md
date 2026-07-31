# Operational KPI Monitoring

These two projects share a pattern that shows up repeatedly across this portfolio:
take a metric that used to live in someone's head or a manually-refreshed
spreadsheet, and make it a scheduled pull straight from the operational database.
Neither one is architecturally novel on its own, but together they illustrate two
different points on the "how fresh does this number need to be" spectrum — a
5-minute floor-TV loop at one end, and a once-a-night batch KPI job at the other —
and the trade-offs each approach accepts to get there.

## Near-real-time floor dashboard

A Databricks job polls a set of operational queries against the source database
every 5 minutes and writes the results into a Google Sheet, which a self-hosted
Grafana instance reads and streams to TVs on the operations floor over
credential-less view tokens. It replaced a manual CSV reporting routine and
avoided standing up a dedicated vendor dashboard product, keeping the
Sheet-as-intermediary approach deliberately low-infrastructure.

The engineering technique worth calling out is the **convention-based KPI
folder**: the loop scans a directory of `.sql` files at runtime and executes every
query it finds, using the file name as the resulting Sheet column header. Adding a
new floor KPI is a matter of dropping in a new `.sql` file — no Python change, no
redeploy. The loop also runs a `while True` / `sleep(300)` cycle with a
timezone-aware cutoff that detects the end of the last operating shift and exits,
so the compute cluster isn't left running (and billing) overnight.

**Sanitization notes:** the source project's dashboard screenshot and internal
data-dictionary file are not carried forward (screenshots are excluded portfolio-wide
per the 2026-07-31 decision). No code is reproduced here — the convention-based
folder-scan pattern is described in prose only.

## Nightly units-per-hour KPI job

A simpler, once-a-night counterpart: a single parameterized query runs for the
day's shift window and appends one row of units-per-hour figures to a reporting
sheet. It's one of several jobs in this portfolio built on a shared internal
utilities module (covered separately in `shared/logistics_data_utils/`), so its
own code is mostly wiring — time-window resolution, an idempotent delete-then-load
write, and re-raising on failure so the scheduler marks the run correctly. The
value here isn't a novel technique; it's consistency — the same load/notify/timezone
conventions as the rest of the KPI job family, which is what makes them cheap to
maintain as a set rather than as one-offs.

**Sanitization notes:** no code copied; the shared-utilities dependency is
described narratively rather than by import path.

## Also present in source material (not detailed here)

A small set of supplementary volume-reporting SQL queries (sorter volume, inbound
receipt volume, and outlet/overstock receive volume) exists alongside the
inventory-reconciliation work covered in the technical deep dive, but is out of
scope for this page by an earlier scoping decision and is not summarized further.
