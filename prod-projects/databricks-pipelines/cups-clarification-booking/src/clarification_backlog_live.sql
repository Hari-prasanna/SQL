SELECT 'Outlet' AS "Abteilung", zb.BEZ AS "Arbeitsplatz", zb."MainLhm" AS "LHM", zb."Sortierziel ID" AS "Sort_ID", zb.ARTNR AS "EAN", zb.ANZ AS "Anzahl"
FROM ZAL_BESTAND zb 
WHERE (zb."Lager" = 'OL_APS' AND zb."MainLhmdef" = 'Federbodenwagen')
   OR (zb."MainLhm" LIKE 'KF_OL%')