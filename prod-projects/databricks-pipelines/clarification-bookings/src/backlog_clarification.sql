SELECT SUM(zb.ANZ) AS "COMBINED_TOTAL"
FROM ZAL_BESTAND zb 
WHERE (zb."Lager" = 'OL_APS' AND zb."MainLhmdef" = 'Federbodenwagen')
   OR (zb."MainLhm" LIKE 'KF_OL%')