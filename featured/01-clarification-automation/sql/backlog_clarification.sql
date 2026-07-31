-- Sanitized for public release — table name is a generic alias, not the production schema.
SELECT SUM(zb.ANZ) AS "COMBINED_TOTAL"
FROM STOCK_BALANCE zb
WHERE (zb."Lager" = 'OL_APS' AND zb."MainLhmdef" = 'Federbodenwagen')
   OR (zb."MainLhm" LIKE 'KF_OL%')