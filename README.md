# 📊 SQL & Data Analysis Portfolio

Welcome to my portfolio! This repository highlights my expertise in **Advanced SQL**, **Data Reconciliation**, and **Operational Analytics**. I specialize in solving complex business problems—from fixing critical inventory "data drift" to generating high-level executive insights.

## 📂 SQL Projects

### 1. [Overstock Inventory Reconciliation](./overstock-inventory-reconciliation)
* **The Challenge:** The "Overstock" department faced a critical data integrity issue where the main reporting tool failed to track "dummy items," causing a discrepancy between physical and digital stock.
* **The SQL Solution:** Built a complex query using **CTEs** and **JSON Parsing** to reverse-engineer transaction logs. The logic stitches together disjointed "book-out" and "book-in" events to capture the complete lifecycle of an item.
* **Impact:** Restored **100% accuracy** to the booking log and was adopted by the technical team as the primary source of truth.
* **Key Skills:** `CTEs`, `JSON_VALUE`, `Self-Joins`, `Data Cleaning`.

### 2. [Manual Sorting Deduplication Algorithm](./manual-sorting-deduplication)
* **The Challenge:** The manual sorting line produced rapid, duplicate scans that inflated inventory numbers. Legacy reporting could not distinguish between a double-scan and a legitimate new transaction.
* **The SQL Solution:** Designed a strict sequencing algorithm using **Window Functions** (`ROW_NUMBER`). The query assigns a unique index to every step of a transaction, ensuring strictly 1:1 matching between scan-out and scan-in events.
* **Impact:** Eliminated "phantom" inventory records and provided the operations team with accurate throughput metrics.
* **Key Skills:** `Window Functions`, `PARTITION BY`, `Performance Tuning`, `Complex Logic`.

### 3. [Goodcabs Transportation Analytics](./goodcabs-transportation-analytics)
* **The Challenge:** Goodcabs, a Tier-2 city cab service, needed an urgent assessment of their 2024 performance targets to support their growth strategy. The Chief of Operations required granular insights into trip volume, fare efficiency, and passenger satisfaction across 10 cities.
* **The SQL Solution:** Executed a series of ad-hoc SQL analyses to evaluate Key Performance Indicators (KPIs):
    * **Trip Efficiency:** Calculated city-level fare contributions (Average Fare/Km) to identify high-value locations.
    * **Target Variance:** Developed a "Target vs. Actual" performance report, calculating monthly percentage gaps and categorizing performance as "Above" or "Below" targets.
    * **Passenger Insights:** Analyzed new vs. repeat passenger rates to determine customer retention strength.
* **Impact:** Delivered a data-backed foundation for the 2024 strategic plan, identifying underperforming cities and pricing opportunities.
* **Key Skills:** `KPI Definition`, `Aggregations`, `Variance Analysis`, `Reporting`.
* **Source:** [Codebasics Resume Project Challenge](https://codebasics.io/challenges/resume-project-challenge)

---

### 🛠️ Technical Skills

| Category | Skills |
|----------|--------|
| **Core SQL** | Joins, Aggregations, Subqueries, Unions |
| **Advanced SQL** | Window Functions (`ROW_NUMBER`, `RANK`), CTEs (Common Table Expressions) |
| **Data Handling** | JSON Parsing (`JSON_VALUE`), Regex (`REGEXP_LIKE`), Date Manipulation |
| **Business Intelligence** | KPI Tracking, Variance Analysis, Ad-hoc Reporting |
