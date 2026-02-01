# 📊 SQL & Data Analysis Portfolio

Welcome to my portfolio! This repository highlights my expertise in **Advanced SQL**, **Data Reconciliation**, and **Operational Analytics**. I specialize in solving complex business problems—from fixing critical inventory "data drift" to generating high-level executive insights.

## 📂 SQL Projects

### 1. [Overstock Inventory Reconciliation](./overstock-inventory-reconciliation)
* **Context:** The "Overstock" department faced a critical data integrity issue where the main reporting tool failed to track specific transaction types ("dummy items"), leading to discrepancies between physical and digital stock.
* **The SQL Solution:** Built a complex query using **CTEs** and **JSON Parsing** to reverse-engineer the transaction logs. The logic stitches together disjointed "book-out" and "book-in" events to capture the complete lifecycle of an item.
* **Impact:** Restored **100% accuracy** to the booking log and was adopted by the technical team as the primary source of truth.
* **Key Concepts:** `CTEs`, `JSON_VALUE`, `Self-Joins`, `Data Cleaning`.

### 2. [Manual Sorting Deduplication Algorithm](./manual-sorting-reconciliation)
* **Context:** The manual sorting line produced rapid, duplicate scans that inflated inventory numbers. Legacy reporting could not distinguish between a double-scan and a legitimate new transaction.
* **The SQL Solution:** Designed a strict sequencing algorithm using **Window Functions** (`ROW_NUMBER`). The query assigns a unique index to every step of a transaction, ensuring strictly 1:1 matching between scan-out and scan-in events.
* **Impact:** Eliminated "phantom" inventory records and provided the operations team with accurate throughput metrics.
* **Key Concepts:** `Window Functions`, `PARTITION BY`, `Performance Tuning (Materialize Hints)`, `Complex Logic`.

### 3. [Goodcabs Operational Analytics](./goodcabs-analytics)
* **Context:** Goodcabs, a Tier-2 city cab service, needed an urgent assessment of their 2024 performance targets. The Chief of Operations required insights into trip volume, passenger satisfaction, and repeat passenger rates across 10 cities.
* **The SQL Solution:** Developed a suite of ad-hoc SQL reports to answer critical business questions:
    * **Fare Efficiency:** Calculated average fare per km and trip contribution per city.
    * **Target Variance:** Created a "Target vs. Actual" performance report, calculating monthly percentage gaps and categorizing cities as "Above/Below Target."
* **Impact:** Delivered actionable insights on pricing efficiency and city-level performance gaps directly to the Chief of Operations.
* **Key Concepts:** `Aggregations`, `CASE Statements`, `Variance Analysis`, `Reporting`.

---

### 🛠️ Technical Skills

| Category | Skills |
|----------|--------|
| **Core SQL** | Joins, Aggregations, Subqueries, Unions |
| **Advanced SQL** | Window Functions (`ROW_NUMBER`, `RANK`), CTEs (Common Table Expressions) |
| **Data Handling** | JSON Parsing (`JSON_VALUE`), Regex (`REGEXP_LIKE`), Date Manipulation |
| **Performance** | Query Optimization, Materialized Views/Hints, Execution Plans |
