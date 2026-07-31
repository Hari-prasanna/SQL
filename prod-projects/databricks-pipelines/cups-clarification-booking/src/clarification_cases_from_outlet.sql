WITH params AS (
    SELECT
        CASE
            WHEN :start_datetime IS NOT NULL
            THEN TO_DATE(:start_datetime, 'DD.MM.YYYY HH24:MI:SS')
        END AS start_dt,

        CASE
            WHEN :end_datetime IS NOT NULL
            THEN TO_DATE(:end_datetime, 'DD.MM.YYYY HH24:MI:SS')
        END AS end_dt
    FROM dual
),

/*
 * Only clarification transactions
 *
 * TYP_ID  = 102
 * TPARTNR = 402
 */
clarification_data AS (
    SELECT
        TRUNC(hv.CREATED) AS booking_date,

        CASE
            WHEN TO_CHAR(hv.CREATED, 'HH24:MI:SS')
                 BETWEEN '05:50:00' AND '14:44:59'
                THEN 1

            WHEN TO_CHAR(hv.CREATED, 'HH24:MI:SS')
                 BETWEEN '14:45:00' AND '23:59:00'
                THEN 2

            ELSE NULL
        END AS shift,

        /*
         * Keep LHM internally.
         * It is required by quality fallback tiers 3 and 4.
         */
        hv.LHMNR AS internal_lhm,

        hv.ARTNR AS ean,

        DECODE(
            JSON_VALUE(hv.CUST_DATA, '$.CATEGORYID_ART'),
            '1', 'Schuhe',
            '2', 'Textil',
            '3', 'ACC',
            '4', 'Home',
            '5', 'Beauty',
            'Unknown'
        ) AS category,

        JSON_VALUE(
            hv.CUST_DATA,
            '$.SORTINGCRITERIAID_ART'
        ) AS sort_id,

        ABS(hv.MENGE) AS quantity,

        /*
         * Quality fallback logic for clarification items
         */
        COALESCE(
            /*
             * Tier 1:
             * Quality directly available on the clarification row
             */
            DECODE(
                JSON_VALUE(hv.CUST_DATA, '$.QUALITYID_SEKTOR'),
                '1', 'A',
                '2', 'B',
                '3', 'C',
                '4', 'D'
            ),

            /*
             * Tier 2:
             * Quality recorded against KF_<ZIEL>
             */
            (
                SELECT DECODE(
                    JSON_VALUE(q.CUST_DATA, '$.QUALITYID_SEKTOR'),
                    '1', 'A',
                    '2', 'B',
                    '3', 'C',
                    '4', 'D'
                )
                FROM HISTORIE_V q
                WHERE q.ARTNR = hv.ARTNR
                  AND TRIM(q.LHMNR) = 'KF_' || TRIM(hv.ZIEL)
                  AND q.TYP_ID = 101
                  AND q.TPARTNR = 520
                  AND ROWNUM = 1
            ),

            /*
             * Tier 3:
             * Quality from stock for an item remaining on the LHM
             */
            (
                SELECT MAX(zb."Qualität")
                FROM ZAL_BESTAND zb
                WHERE (
                    zb."MainLhm" = hv.LHMNR
                    OR zb."SubLhm" = hv.LHMNR
                )
                  AND zb."Qualität" IS NOT NULL
            ),

            /*
             * Tier 4:
             * Any valid quality previously recorded for the LHM
             */
            (
                SELECT DECODE(
                    JSON_VALUE(q.CUST_DATA, '$.QUALITYID_SEKTOR'),
                    '1', 'A',
                    '2', 'B',
                    '3', 'C',
                    '4', 'D'
                )
                FROM HISTORIE_V q
                WHERE q.LHMNR = hv.LHMNR
                  AND JSON_VALUE(
                        q.CUST_DATA,
                        '$.QUALITYID_SEKTOR'
                      ) IN ('1', '2', '3', '4')
                  AND ROWNUM = 1
            ),

            'Unknown'
        ) AS quality

    FROM HISTORIE_V hv
    CROSS JOIN params p

    WHERE hv.TYP_ID = 102
      AND hv.TPARTNR = 402

      AND (
          hv.LHMNR LIKE '4%'
          OR hv.LHMNR LIKE '5%'
      )

      AND (
          p.start_dt IS NULL
          OR hv.CREATED >= p.start_dt
      )

      AND (
          p.end_dt IS NULL
          OR hv.CREATED <= p.end_dt
      )
)

SELECT
    TO_CHAR(booking_date, 'YYYY-MM-DD') AS "Date",
    shift                              AS "Shift",
    ean                                AS "EANs",
    category                           AS "Category",
    sort_id                            AS "Sort_ID",
    quality                            AS "Quality",
    SUM(quantity)                      AS "Items"

FROM clarification_data

GROUP BY
    booking_date,
    shift,
    ean,
    category,
    sort_id,
    quality

HAVING
    SUM(quantity) > 0

ORDER BY
    booking_date,
    shift,
    ean,
    sort_id