-- STOCK_BALANCE is a generic alias for the real production stock-balance view —
-- see ../../../docs/sanitization-policy.md. "Category" is bound as a query
-- parameter (e.g. "Beauty") rather than hardcoded, so the same query serves every
-- product category the job is run for. The BEZ exclusions drop two internal
-- carrier/description prefixes ("T%", "BSF_T%") that mark non-sellable or transit
-- handling units out of the dangerous-goods stock view.
SELECT *
FROM STOCK_BALANCE sb
WHERE
    sb."Category" = :category
    AND sb.BEZ NOT LIKE 'T%' AND sb.BEZ NOT LIKE 'BSF_T%'