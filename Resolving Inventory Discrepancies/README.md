Overstock Transaction & Inventory Reconciliation Query

The Challenge 🎯

The Overstock department's main report for tracking booked items was inaccurate. This "data drift" made it impossible to trust our stock levels and led to discrepancies in our inventory. The root cause was unknown, but it was clear the system was failing to record certain types of transactions.

The Solution 🛠️

After investigating, I discovered the old report completely ignored "dummy item" barcodes. To fix this, I created this new SQL query from scratch.

The solution identifies both standard items and the missing dummy items by tracking their complete journey—from the moment they are booked out (MENGE < 0) to the moment they are booked in (MENGE = 1).

The Impact ✨

This new query immediately resolved the reporting errors and restored 100% accuracy to the booking log. The Overstock team now has a reliable tool they can trust, which has corrected inventory data from previous periods and ensures precise stock levels moving forward.

How It Works

Instead of one massive, complex query, the logic is broken into simple, understandable building blocks using Common Table Expressions (CTEs).

Find "Normal" Items:

normal_goods_t1: Finds "booking out" transactions.

TPARTNR = 520 AND MENGE < 0


normal_goods_t2: Finds "booking in" completions.

TPARTNR = 520 AND MENGE = 1


Find "Dummy" Items:

dummy_goods_t1: Finds the "dummy" item "booking out" transactions that were being missed.

TPARTNR = 614 AND MENGE < 0


dummy_goods_t2: Finds the dummy item completions.

TPARTNR = 207 AND MENGE = 1


Stitch Them Together:

The query uses a LEFT JOIN on the LOCAL_TRANSACTION_ID to match the "booking out" (t1) record with its "booking in" (t2) record for both normal and dummy flows.

Combine & Clean:

A UNION ALL merges the "normal" and "dummy" results into one complete list.

The final SELECT cleans up the data, translating internal codes from the CUST_DATA JSON into human-readable text.

-- Example of cleaning up JSON data
DECODE(JSON_VALUE(ag.CUST_DATA, '$.QUALITYID_SEKTOR'),
  '1', 'A',
  '2', 'B',
  'Unknown'
) AS Quality


Key Business Logic

SKU & SORT_ID Source: The logic for NORMAL vs. DUMMY goods is different:

For NORMAL goods, the SKU is pulled from the initial t1 record's JSON.

For DUMMY goods, the SKU is pulled from the completion t2 record's JSON.

CASE
  WHEN ag.good_type = 'NORMAL' THEN JSON_VALUE(ag.CUST_DATA, '$.SKU_ART')
  WHEN ag.good_type = 'DUMMY' THEN JSON_VALUE(ag.t2_cust_data, '$.SKU_ART')
END AS SKU


Final Filters: The query cleans the final list by:

Removing self-to-self transactions (where source and destination are the same).

Ensuring the final destination LHM is a valid number.

WHERE
  NVL(ag.Source_LHM, 'value1') <> NVL(ag.ZIEL_LHM, 'value2')
  AND REGEXP_LIKE(ag.ZIEL_LHM, '^[0-9]+$');
