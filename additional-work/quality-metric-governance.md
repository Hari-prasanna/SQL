# Quality Metric Governance

This page summarizes a quality-audit intelligence dashboard that consolidates
several distinct inbound, stock, and outbound audit processes into a single
governance view. Where the other pages in this portfolio focus on individual
scheduled data pipelines, this one is included because it shows a different
skill: turning several independently-run audit processes into one comparable,
weighted metric that non-technical stakeholders can act on in a recurring
meeting, without having to reconcile source-by-source numbers themselves.

## Quality audit intelligence dashboard

The dashboard aggregates six-plus separate quality-audit sources — spanning
inbound receiving, stock accuracy, and outbound processes — into a single
normalized "quality databank," then scores each sub-process against a
defects-per-million-items (DPMI) threshold. A sub-process only "passes" if it
clears its own DPMI bar; the headline score reported at the daily steering
meeting is simply the share of sub-processes that passed (for example, meeting 2
of 3 targets produces a 66.7% overall score). Drill-down pages let a viewer trace
a failing overall score back to the specific audit category driving it — e.g.
telling apart a sorter-audit failure from a pack-audit failure — rather than
leaving "quality dropped" as an unexplained top-line number.

The engineering technique worth noting is the **normalize-then-threshold
pattern**: rather than trying to compare raw audit output across sources with
different units, error definitions, and sampling methods, the pipeline maps every
source into a common pass/fail signal against its own defined threshold first,
and only aggregates *after* that normalization step. That's what makes a single
comparable score possible across audit processes that otherwise have nothing in
common structurally. The project is also paired with a written reference manual
that defines every metric (including the distinction between "critical" and
"major" DPMI) precisely enough that new team members can look a term up rather
than ask, so the dashboard doesn't function as an unexplained black box.

**Sanitization notes:** this project's three dashboard screenshots (a pipeline
diagram, a newsletter-style dashboard view, and a page from the metric reference
manual) are excluded per the portfolio's no-screenshots decision — the
above description substitutes prose for what those images showed. No source code
is copied into this page; the source project is a linear ETL plus scoring layer
with no public code presence in this repo, consistent with the "prose only" rule
for additional-work pages. No quantified before/after impact number is reported
here because the source README does not state one — only the qualitative
governance value (a single comparable score, traceable drill-downs, a written
metric reference) is described.

## Note on a related directory

While reviewing this project's parent README, no other content needed
sanitization changes beyond what's already covered above; see the final report
for a note on one reference to a sibling directory that is being handled by a
parallel migration and was deliberately left untouched here rather than guessed at.
