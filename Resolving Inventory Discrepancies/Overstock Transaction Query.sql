/*
 * SCRIPT: overstock_transaction_query.sql
 * PURPOSE: Extracts and reconciles inventory transactions (both 'Normal' and 'Dummy' goods)
 * moving from Overstock locations to 'OV' destinations.
 * It matches the initial transaction (t1) with its completion (t2).
 *
 * PARAMETERS:
 * :start_datetime (VARCHAR2) - The start of the time window. Format: 'DD.MM.YYYY HH24:MI:SS'
 * :end_datetime (VARCHAR2)   - The end of the time window. Format: 'DD.MM.YYYY HH24:MI:SS'
 * :ref_lhm_filter (VARCHAR2) - A filter for the Reference_LHM. Supports:
 * 1. Single value (e.g., 'REF123')
 * 2. Comma-separated list (e.g., 'REF123,REF456')
 * 3. LIKE wildcard (e.g., 'REF%')
 */

WITH
    -- CTE 1: Captures the initial transaction for 'Normal Goods' leaving an Overstock location.
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
            HISTORIE_V hv
        WHERE
            hv.TPARTNR = 520
            AND hv.MENGE < 0
            AND hv.LAGBEZ IN ('Overstock', 'SZROV')
            AND hv.ZIEL LIKE 'OV%'
    ),

    -- CTE 2: Captures the corresponding completion transaction for 'Normal Goods'.
    normal_goods_t2 AS (
        SELECT
            hv.LHMNR,
            hv.LOCAL_TRANSACTION_ID,
            hv.CUST_DATA
        FROM
            HISTORIE_V hv
        WHERE
            hv.TPARTNR = 520
            AND hv.LAGBEZ IN ('Overstock', 'SZROV')
            AND hv.MENGE = 1
            AND hv.LHMNR NOT LIKE '000%'
    ),

    -- CTE 3: Captures the initial transaction for 'Dummy Goods' leaving an Overstock location.
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
            HISTORIE_V hv
        WHERE
            hv.TPARTNR = 614
            AND hv.MENGE < 0
            AND hv.LAGBEZ IN ('Overstock', 'SZROV')
            AND hv.ZIEL LIKE 'OV%'
    ),

    -- CTE 4: Captures the corresponding completion transaction for 'Dummy Goods'.
    dummy_goods_t2 AS (
        SELECT
            hv.LHMNR,
            hv.LOCAL_TRANSACTION_ID,
            hv.CUST_DATA
        FROM
            HISTORIE_V hv
        WHERE
            hv.TPARTNR = 207
            AND hv.LAGBEZ IN ('Overstock', 'SZROV')
            AND hv.MENGE = 1
            AND hv.ZIEL LIKE 'OV%'
    ),

    -- CTE 5: Combined Data (Replaces the nested subquery)
    -- Joins T1 and T2 for both Normal and Dummy goods and applies filters.
    combined_transactions AS (
        -- Part 1: Normal Goods
        SELECT
            t1.CREATED, t1.ARTNR, t1.ZIEL, t1.CREATEDBY, t1.LHMNR AS Source_LHM, 
            t1.CUST_DATA AS t1_cust_data, 
            t2.LHMNR AS ZIEL_LHM, t1.MENGE, t1.Reference_LHM,
            'NORMAL' AS good_type, 
            t2.CUST_DATA AS t2_cust_data
        FROM normal_goods_t1 t1
        LEFT JOIN normal_goods_t2 t2 ON t1.LOCAL_TRANSACTION_ID = t2.LOCAL_TRANSACTION_ID
        WHERE 
            (:start_datetime IS NULL OR t1.CREATED BETWEEN TO_DATE(:start_datetime, 'DD.MM.YYYY HH24:MI:SS') AND TO_DATE(:end_datetime, 'DD.MM.YYYY HH24:MI:SS'))
            AND (
                :ref_lhm_filter IS NULL
                OR (INSTR(:ref_lhm_filter, '%') > 0 AND UPPER(t1.Reference_LHM) LIKE UPPER(:ref_lhm_filter))
                OR (INSTR(:ref_lhm_filter, ',') > 0 AND ',' || UPPER(:ref_lhm_filter) || ',' LIKE '%,' || UPPER(t1.Reference_LHM) || ',%')
                OR (INSTR(:ref_lhm_filter, '%') = 0 AND INSTR(:ref_lhm_filter, ',') = 0 AND UPPER(t1.Reference_LHM) = UPPER(:ref_lhm_filter))
            )

        UNION ALL

        -- Part 2: Dummy Goods
        SELECT
            t1.CREATED, t1.ARTNR, t1.ZIEL, t1.CREATEDBY, t1.LHMNR AS Source_LHM, 
            t1.CUST_DATA AS t1_cust_data, 
            t2.LHMNR AS ZIEL_LHM, t1.MENGE, t1.Reference_LHM,
            'DUMMY' AS good_type, 
            t2.CUST_DATA AS t2_cust_data
        FROM dummy_goods_t1 t1
        LEFT JOIN dummy_goods_t2 t2 ON t1.LOCAL_TRANSACTION_ID = t2.LOCAL_TRANSACTION_ID
        WHERE 
            (:start_datetime IS NULL OR t1.CREATED BETWEEN TO_DATE(:start_datetime, 'DD.MM.YYYY HH24:MI:SS') AND TO_DATE(:end_datetime, 'DD.MM.YYYY HH24:MI:SS'))
            AND t2.LHMNR NOT LIKE '000%'
            AND (
                :ref_lhm_filter IS NULL
                OR (INSTR(:ref_lhm_filter, '%') > 0 AND UPPER(t1.Reference_LHM) LIKE UPPER(:ref_lhm_filter))
                OR (INSTR(:ref_lhm_filter, ',') > 0 AND ',' || UPPER(:ref_lhm_filter) || ',' LIKE '%,' || UPPER(t1.Reference_LHM) || ',%')
                OR (INSTR(:ref_lhm_filter, '%') = 0 AND INSTR(:ref_lhm_filter, ',') = 0 AND UPPER(t1.Reference_LHM) = UPPER(:ref_lhm_filter))
            )
    )

-- FINAL SELECT: Applies business logic to the combined dataset
SELECT
    TO_CHAR(ag.CREATED, 'DD.MM.YYYY HH24:MI:SS')       AS Timestamp,
    ag.ARTNR                                            AS EAN,
    ag.ZIEL                                             AS AP,
    ag.CREATEDBY                                        AS BENUTZER,
    ag.Source_LHM,
    ag.ZIEL_LHM,
    ABS(ag.MENGE)                                       AS Quantity,
    ag.Reference_LHM,
    
    -- Logic Update: Checks T2 data first, falls back to T1
    DECODE(
        COALESCE(
            JSON_VALUE(ag.t2_cust_data, '$.SOURCEID_SEKTOR'), 
            JSON_VALUE(ag.t1_cust_data, '$.SOURCEID_SEKTOR')
        ),
        '1', 'Zalando SE',
        '10', 'OSR',
        '11', 'OSR (OV)',
        'Unknown'
    ) AS Source_Channel,

    DECODE(
        JSON_VALUE(ag.t1_cust_data, '$.QUALITYID_SEKTOR'),
        '1', 'A',
        '2', 'B',
        '3', 'C',
        '4', 'D',
        'Unknown'
    ) AS Quality,

    DECODE(
        JSON_VALUE(ag.t1_cust_data, '$.CATEGORYID_ART'),
        '1', 'Schuhe',
        '2', 'Textil',
        '3', 'ACC',
        '4', 'Home',
        '5', 'Beauty',
        'Unknown'
    ) AS Category,

    -- Logic Update: Distribution Channel checks T2 first, then T1
    CASE
        WHEN ag.ZIEL_LHM LIKE '50%' THEN 'Overstock'
        WHEN JSON_VALUE(ag.t1_cust_data, '$.QUALITYID_SEKTOR') IN ('3', '4') THEN 'Overstock'
        WHEN COALESCE(JSON_VALUE(ag.t2_cust_data, '$.DISTRIBUTIONCHANNELID_ART'), JSON_VALUE(ag.t1_cust_data, '$.DISTRIBUTIONCHANNELID_ART')) = '4'  THEN 'Outlet'
        WHEN COALESCE(JSON_VALUE(ag.t2_cust_data, '$.DISTRIBUTIONCHANNELID_ART'), JSON_VALUE(ag.t1_cust_data, '$.DISTRIBUTIONCHANNELID_ART')) = '3'  THEN 'Overstock'
        WHEN COALESCE(JSON_VALUE(ag.t2_cust_data, '$.SOURCEID_SEKTOR'), JSON_VALUE(ag.t1_cust_data, '$.SOURCEID_SEKTOR')) = '11' THEN 'Overstock'
        ELSE 'Unknown'
    END AS Distribution_Channel,

    CASE
        WHEN ag.good_type = 'NORMAL' THEN JSON_VALUE(ag.t1_cust_data, '$.SKU_ART')
        WHEN ag.good_type = 'DUMMY'  THEN JSON_VALUE(ag.t2_cust_data, '$.SKU_ART')
    END AS SKU,

    CASE
        WHEN ag.good_type = 'NORMAL' THEN JSON_VALUE(ag.t1_cust_data, '$.SORTINGCRITERIAID_ART')
        WHEN ag.good_type = 'DUMMY'  THEN JSON_VALUE(ag.t2_cust_data, '$.SORTINGCRITERIAID_ART')
    END AS SORT_ID

FROM 
    combined_transactions ag
WHERE
    NVL(ag.Source_LHM, 'value1') <> NVL(ag.ZIEL_LHM, 'value2')
    AND REGEXP_LIKE(ag.ZIEL_LHM, '^[0-9]+$');
