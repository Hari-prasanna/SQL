/*
 * Sanitized for public release — table/column names are generic aliases, not the
 * production schema. Partner codes and workstation codes below are illustrative
 * placeholders, not real production values. See ../docs/sanitization-report.md.
 *
 * Filter:
 * ZIEL IN ('WORKSTATION_1', 'WORKSTATION_2', 'WORKSTATION_3', 'WORKSTATION_4')
 */

WITH
    normal_goods_t1 AS (
        SELECT
            hv.LOCAL_TRANSACTION_ID,
            hv.ARTNR,
            hv.ZIEL,
            hv.CREATEDBY,
            hv.LHMNR,
            hv.CREATED,
            hv.MENGE,
            hv.CUST_DATA,
            JSON_VALUE(hv.CUST_DATA, '$.REFERENCENUMBER_LHM') AS Reference_LHM
        FROM
            TRANSACTION_HISTORY_V hv
        WHERE
            hv.TPARTNR = 1 -- NORMAL_GOODS_SOURCE (illustrative placeholder, not a real partner code)
            AND hv.MENGE < 0
            AND hv.LAGBEZ IN ('Overstock', 'SZROV')
            AND hv.ZIEL IN ('WORKSTATION_1', 'WORKSTATION_2', 'WORKSTATION_3', 'WORKSTATION_4')
    ),

    normal_goods_t2 AS (
        SELECT
            hv.LHMNR,
            hv.LOCAL_TRANSACTION_ID,
            hv.CUST_DATA
        FROM
            TRANSACTION_HISTORY_V hv
        WHERE
            hv.TPARTNR = 1 -- NORMAL_GOODS_SOURCE
            AND hv.LAGBEZ IN ('Overstock', 'SZROV')
            AND hv.MENGE = 1
            AND hv.LHMNR NOT LIKE '000%'
    ),

    dummy_goods_t1 AS (
        SELECT
            hv.LOCAL_TRANSACTION_ID,
            CASE
                WHEN hv.ARTNR NOT LIKE '2%' THEN JSON_VALUE(hv.CUST_DATA, '$.LASTEANGOTFROMMAUS_ZIEL')
                ELSE hv.ARTNR
            END AS ARTNR,
            hv.ZIEL,
            hv.CREATEDBY,
            hv.LHMNR,
            hv.CREATED,
            hv.MENGE,
            hv.CUST_DATA,
            JSON_VALUE(hv.CUST_DATA, '$.REFERENCENUMBER_LHM') AS Reference_LHM
        FROM
            TRANSACTION_HISTORY_V hv
        WHERE
            hv.TPARTNR = 2 -- DUMMY_GOODS_SOURCE_A (illustrative placeholder)
            AND hv.MENGE < 0
            AND hv.LAGBEZ IN ('Overstock', 'SZROV')
            AND hv.ZIEL IN ('WORKSTATION_1', 'WORKSTATION_2', 'WORKSTATION_3', 'WORKSTATION_4')
    ),

    dummy_goods_t2 AS (
        SELECT
            hv.LHMNR,
            hv.LOCAL_TRANSACTION_ID,
            hv.CUST_DATA
        FROM
            TRANSACTION_HISTORY_V hv
        WHERE
            hv.TPARTNR = 3 -- DUMMY_GOODS_SOURCE_B (illustrative placeholder)
            AND hv.LAGBEZ IN ('Overstock', 'SZROV')
            AND hv.MENGE = 1
            AND hv.ZIEL LIKE 'WORKSTATION_%'
    ),

    combined_transactions AS (
        SELECT
            t1.CREATED,
            t1.ARTNR,
            t1.ZIEL,
            t1.CREATEDBY,
            t1.LHMNR AS Source_LHM,
            t1.CUST_DATA AS t1_cust_data,
            t2.LHMNR AS ZIEL_LHM,
            t1.MENGE,
            t1.Reference_LHM,
            'NORMAL' AS good_type,
            t2.CUST_DATA AS t2_cust_data,
            CASE
                WHEN JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR') = '1'
                     AND LOWER(JSON_VALUE(t1.CUST_DATA, '$.SORTABLE_ART')) = 'false'
                    THEN 'B'
                WHEN JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR') = '1' THEN 'A'
                WHEN JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR') = '2' THEN 'B'
                WHEN JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR') = '3' THEN 'C'
                WHEN JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR') = '4' THEN 'D'
                ELSE 'Unknown'
            END AS Quality
        FROM normal_goods_t1 t1
        LEFT JOIN normal_goods_t2 t2
            ON t1.LOCAL_TRANSACTION_ID = t2.LOCAL_TRANSACTION_ID
        WHERE
            (
                :start_datetime IS NULL
                OR t1.CREATED BETWEEN TO_DATE(:start_datetime, 'DD.MM.YYYY HH24:MI:SS')
                                  AND TO_DATE(:end_datetime,   'DD.MM.YYYY HH24:MI:SS')
            )
            AND (
                :ref_lhm_filter IS NULL
                OR (INSTR(:ref_lhm_filter, '%') > 0
                    AND UPPER(t1.Reference_LHM) LIKE UPPER(:ref_lhm_filter))
                OR (INSTR(:ref_lhm_filter, ',') > 0
                    AND ',' || UPPER(:ref_lhm_filter) || ',' LIKE '%,' || UPPER(t1.Reference_LHM) || ',%')
                OR (INSTR(:ref_lhm_filter, '%') = 0
                    AND INSTR(:ref_lhm_filter, ',') = 0
                    AND UPPER(t1.Reference_LHM) = UPPER(:ref_lhm_filter))
            )

        UNION ALL

        SELECT
            t1.CREATED,
            t1.ARTNR,
            t1.ZIEL,
            t1.CREATEDBY,
            t1.LHMNR AS Source_LHM,
            t1.CUST_DATA AS t1_cust_data,
            t2.LHMNR AS ZIEL_LHM,
            t1.MENGE,
            t1.Reference_LHM,
            'DUMMY' AS good_type,
            t2.CUST_DATA AS t2_cust_data,
            CASE
                WHEN COALESCE(
                        JSON_VALUE(t2.CUST_DATA, '$.QUALITYID_ART'),
                        JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR')
                     ) = '1'
                     AND LOWER(
                        COALESCE(
                            JSON_VALUE(t2.CUST_DATA, '$.SORTABLE_ART'),
                            JSON_VALUE(t1.CUST_DATA, '$.SORTABLE_ART')
                        )
                     ) = 'false'
                    THEN 'B'
                WHEN COALESCE(JSON_VALUE(t2.CUST_DATA, '$.QUALITYID_ART'), JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR')) = '1' THEN 'A'
                WHEN COALESCE(JSON_VALUE(t2.CUST_DATA, '$.QUALITYID_ART'), JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR')) = '2' THEN 'B'
                WHEN COALESCE(JSON_VALUE(t2.CUST_DATA, '$.QUALITYID_ART'), JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR')) = '3' THEN 'C'
                WHEN COALESCE(JSON_VALUE(t2.CUST_DATA, '$.QUALITYID_ART'), JSON_VALUE(t1.CUST_DATA, '$.QUALITYID_SEKTOR')) = '4' THEN 'D'
                ELSE 'Unknown'
            END AS Quality
        FROM dummy_goods_t1 t1
        LEFT JOIN dummy_goods_t2 t2
            ON t1.LOCAL_TRANSACTION_ID = t2.LOCAL_TRANSACTION_ID
        WHERE
            (
                :start_datetime IS NULL
                OR t1.CREATED BETWEEN TO_DATE(:start_datetime, 'DD.MM.YYYY HH24:MI:SS')
                                  AND TO_DATE(:end_datetime,   'DD.MM.YYYY HH24:MI:SS')
            )
            AND t2.LHMNR NOT LIKE '000%'
            AND (
                :ref_lhm_filter IS NULL
                OR (INSTR(:ref_lhm_filter, '%') > 0
                    AND UPPER(t1.Reference_LHM) LIKE UPPER(:ref_lhm_filter))
                OR (INSTR(:ref_lhm_filter, ',') > 0
                    AND ',' || UPPER(:ref_lhm_filter) || ',' LIKE '%,' || UPPER(t1.Reference_LHM) || ',%')
                OR (INSTR(:ref_lhm_filter, '%') = 0
                    AND INSTR(:ref_lhm_filter, ',') = 0
                    AND UPPER(t1.Reference_LHM) = UPPER(:ref_lhm_filter))
            )
    ),

    processed_data AS (
        SELECT
            TRUNC(ag.CREATED) AS work_date,

            CASE
                WHEN TO_CHAR(ag.CREATED, 'HH24:MI:SS') BETWEEN '05:50:00' AND '14:44:59' THEN 1
                WHEN TO_CHAR(ag.CREATED, 'HH24:MI:SS') BETWEEN '14:45:00' AND '23:59:00' THEN 2
                ELSE NULL
            END AS shift,

            ag.CREATEDBY AS names,
            ag.ZIEL AS ziel,
            ag.Quality,
            ABS(ag.MENGE) AS quantity
        FROM
            combined_transactions ag
        WHERE
            NVL(ag.Source_LHM, 'value1') <> NVL(ag.ZIEL_LHM, 'value2')
            AND ag.ZIEL IN ('WORKSTATION_1', 'WORKSTATION_2', 'WORKSTATION_3', 'WORKSTATION_4')
    )

SELECT
    TO_CHAR(work_date, 'YYYY-MM-DD') AS "date",
    shift                            AS "shift",
    names                            AS "names",
    ziel                             AS "ziel",

    SUM(CASE WHEN Quality = 'A' THEN quantity ELSE 0 END) AS "A",
    SUM(CASE WHEN Quality = 'B' THEN quantity ELSE 0 END) AS "B",
    SUM(CASE WHEN Quality = 'C' THEN quantity ELSE 0 END) AS "C",
    SUM(CASE WHEN Quality = 'D' THEN quantity ELSE 0 END) AS "D"

FROM
    processed_data
GROUP BY
    work_date,
    shift,
    names,
    ziel
ORDER BY
    work_date ASC,
    shift ASC,
    ziel ASC,
    names ASC