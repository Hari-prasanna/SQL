# Goodcabs Operational Analytics (Codebasics Challenge)

![SQL](https://img.shields.io/badge/Language-PostgreSQL-orange) ![Focus](https://img.shields.io/badge/Focus-Business_Intelligence-blue) ![Context](https://img.shields.io/badge/Context-Transportation_Sector-green)

## 🚖 Project Overview
**Goodcabs** is a cab service provider operating in ten Tier-2 cities in India. They are committed to supporting local drivers and providing excellent service. As part of their 2024 growth initiative, the management team aims to assess performance across key metrics: trip volume, passenger satisfaction, repeat passenger rates, and the balance between new vs. repeat customers.

**The Scenario:**
The Chief of Operations, Bruce Haryali, required immediate insights to answer critical business questions. Due to the unavailability of the primary manager, I stepped in as the Data Analyst to execute these ad-hoc requests using SQL.

*This project is based on the [Codebasics Resume Project Challenge #13](https://codebasics.io/challenges/resume-project-challenge).*

## Objectives

Check “ad-hoc-requests.pdf” - this document includes important business questions, requiring SQL-based report generation. 


## Schema

```sql
-- Table: fact_trips 
CREATE TABLE fact_trips (
    trip_id VARCHAR(25), 
    trip_date DATE,
    city_id VARCHAR (10), 
    passenger_type VARCHAR(20),
    distance_travelled_km NUMERIC,
    fare_amount INT,
    passenger_rating INT,
    driver_rating INT
);


-- Table: dim_repeat_trip_distribution
CREATE TABLE dim_repeat_trip_distribution (
    month DATE,
    city_id VARCHAR(10),
    trip_count INT,
    repeat_passenger_count INT
);

-- Table: city_target_passenger_rating
CREATE TABLE city_target_passenger_rating (
    city_id VARCHAR(10),
    target_avg_passenger_rating NUMERIC
);

-- Table: dim_city
CREATE TABLE dim_city (
    city_id VARCHAR(10),
    city_name VARCHAR(20)
);

-- Table: dim_date
CREATE TABLE dim_date (
    date DATE,
    start_of_month DATE,
    month_name VARCHAR(20),
    day_type VARCHAR(20)
);

-- Table: fact_passenger_summary
CREATE TABLE fact_passenger_summary (
    month DATE,
    city_id VARCHAR(10),
    new_passengers INT,
    repeat_passengers INT,
    total_passengers INT
);

-- Table: monthly_target_new_passengers
CREATE TABLE monthly_target_new_passengers (
    month DATE,
    city_id VARCHAR(10),
    target_new_passengers INT
);

-- Table: monthly_target_trips
CREATE TABLE monthly_target_trips (
    month DATE,
    city_id VARCHAR(10),
    total_target_trips INT
);


```

## Business Problems and Solutions

### 1. City-Level Fare and Trip Summary Report

**Objective:** Generate a report that displays the total trips, average fare per km, average fare per trip, and the percentage contribution of each city's trips to the overall trips. 

This report will help in assessing trip volume, pricing efficiency, and each city's contribution to the overall trip count


```sql
SELECT
    dc.city_name AS city_name,
    COUNT(*) AS total_trips,
    ROUND(SUM(fare_amount) / NULLIF(SUM(distance_travelled_km), 0), 2) AS avg_fare_per_km,
    ROUND(AVG(ft.fare_amount), 0) AS avg_fare_per_trip,
    ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM fact_trips)::NUMERIC * 100, 2) AS percentage_contribution_to_total_trips
FROM fact_trips AS ft
JOIN dim_city AS dc
     ON ft.city_id = dc.city_id
GROUP BY dc.city_name
ORDER BY total_trips DESC;
```

**### Business Request - 2: Monthly City-Level Trips Target Performance Report**

**Objective:** Generate a report that evaluates the target performance for trips at the monthly and city level. For each city and month, compare the actual total trips with the target trips and categorise the performance as follows:
    If actual trips are greater than target trips, mark it as "Above Target".
 	If actual trips are less than or equal to target trips, mark it as "Below Target".

Additionally, calculate the % difference between actual and target trips to quantify the performance gap.




```sql
WITH city_month AS (
    SELECT
        DATE_TRUNC('month', trip_date) AS month,
        ft.city_id,
        dc.city_name,
        COUNT(*) AS actual_trips
    FROM fact_trips AS ft
    JOIN dim_city AS dc
         ON ft.city_id = dc.city_id
    GROUP BY 1, 2, 3
)
SELECT 
    cm.city_name,
    TO_CHAR(cm.month, 'Month') AS month_name,
    SUM(cm.actual_trips) AS actual_trips,
    SUM(mt.total_target_trips) AS target_trips,
    CASE
        WHEN SUM(cm.actual_trips) > SUM(mt.total_target_trips) THEN 'Above Target'
        ELSE 'Below Target'
    END AS performance_status,
    ROUND(
        (SUM(cm.actual_trips) - SUM(mt.total_target_trips)) / NULLIF(SUM(mt.total_target_trips), 0) * 100,
        2
    ) AS percentage_difference
FROM city_month AS cm
JOIN monthly_target_trips AS mt 
     ON cm.city_id = mt.city_id
    AND cm.month = mt.month
GROUP BY cm.city_name, cm.month
ORDER BY cm.city_name, cm.month;
```



### Business Request - 3: City-Level Repeat Passenger Trip Frequency Report

**Objective:** 
Generate a report that shows the percentage distribution of repeat passengers by the number of trips they have taken in each city. Calculate the percentage of repeat passengers who took 2 trips, 3 trips, and so on, up to 10 trips.
Each column should represent a trip count category, displaying the percentage of repeat passengers who fall into that category out of the total repeat passengers for that city.

This report will help identify cities with high repeat trip frequency, which can indicate strong customer loyalty or frequent usage patterns.


```sql
WITH trip_count AS (
    SELECT 
        dc.city_name,
        td.city_id,
        SUM(CASE WHEN td.trip_count = '2-Trips' THEN td.repeat_passenger_count ELSE 0 END) AS trips_2,
        SUM(CASE WHEN td.trip_count = '3-Trips' THEN td.repeat_passenger_count ELSE 0 END) AS trips_3,
        SUM(CASE WHEN td.trip_count = '4-Trips' THEN td.repeat_passenger_count ELSE 0 END) AS trips_4,
        SUM(CASE WHEN td.trip_count = '5-Trips' THEN td.repeat_passenger_count ELSE 0 END) AS trips_5,
        SUM(CASE WHEN td.trip_count = '6-Trips' THEN td.repeat_passenger_count ELSE 0 END) AS trips_6,
        SUM(CASE WHEN td.trip_count = '7-Trips' THEN td.repeat_passenger_count ELSE 0 END) AS trips_7,
        SUM(CASE WHEN td.trip_count = '8-Trips' THEN td.repeat_passenger_count ELSE 0 END) AS trips_8,
        SUM(CASE WHEN td.trip_count = '9-Trips' THEN td.repeat_passenger_count ELSE 0 END) AS trips_9,
        SUM(CASE WHEN td.trip_count = '10-Trips'THEN td.repeat_passenger_count ELSE 0 END) AS trips_10
    FROM dim_repeat_trip_distribution AS td
    JOIN dim_city AS dc
        ON td.city_id = dc.city_id
    GROUP BY dc.city_name, td.city_id
),
total_passenger_count AS (
    SELECT 
        city_id,
        SUM(repeat_passenger_count) AS total_passengers
    FROM dim_repeat_trip_distribution
    GROUP BY city_id
)
SELECT
    t.city_name,
    ROUND(SUM(t.trips_2) / NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_2,
    ROUND(SUM(t.trips_3) / NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_3,
    ROUND(SUM(t.trips_4) / NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_4,
    ROUND(SUM(t.trips_5) / NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_5,
    ROUND(SUM(t.trips_6) / NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_6,
    ROUND(SUM(t.trips_7) / NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_7,
    ROUND(SUM(t.trips_8) / NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_8,
    ROUND(SUM(t.trips_9) / NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_9,
    ROUND(SUM(t.trips_10)/ NULLIF(SUM(tp.total_passengers), 0) * 100, 2) AS trips_10
FROM trip_count AS t
JOIN total_passenger_count AS tp
    ON t.city_id = tp.city_id
GROUP BY t.city_name;

```

### Business Request - 4: Identify Cities with Highest and Lowest Total New Passengers

**Objective:** 
Generate a report that calculates the total new passengers for each city and ranks them based on this value. 
Identify the top 3 cities with the highest number of new passengers as well as the bottom 3 cities with the lowest number of new passengers, categorising them as "Top 3" or "Bottom 3" accordingly.

```sql
WITH city_level AS (
    SELECT 
        dc.city_name,
        SUM(fs.new_passengers) AS total_new_passengers,
        rank () OVER (ORDER BY SUM(fs.new_passengers) DESC) AS rank
FROM fact_passenger_summary AS fs 
JOIN dim_city AS dc
    ON fs.city_id = dc.city_id
GROUP BY dc.city_name)


SELECT
    city_name,
    total_new_passengers,
    city_category
FROM
(SELECT
     *,
     CASE 
         WHEN rank BETWEEN 1 AND 3 THEN 'Top 3'
         WHEN rank BETWEEN 8 AND 10 THEN 'Bottom 3'
         ELSE 'Middle'
     END AS city_category
FROM city_level) AS rank
WHERE city_category = 'Top 3' OR city_category = 'Bottom 3'
```

### Business Request - 5: Identify Month with Highest Revenue for Each City

**Objective:** 
Generate a report that identifies the month with the highest revenue for each city. For each city, display the month_name, the revenue amount for that month, and the percentage contribution of that month's revenue to the city's total revenue.

```sql
WITH revenue AS (
    SELECT 
        dc.city_name,
        TO_CHAR(DATE_TRUNC('month', ft.trip_date), 'FMMonth') AS month,
        SUM(ft.fare_amount) AS revenue,
        RANK() OVER (PARTITION BY dc.city_name ORDER BY SUM(ft.fare_amount) DESC) AS revenue_rank
    FROM fact_trips AS ft
    JOIN dim_city AS dc
        ON ft.city_id = dc.city_id
    GROUP BY dc.city_name, DATE_TRUNC('month', ft.trip_date)
),
city_total AS (
    SELECT 
        dc.city_name,
        SUM(ft.fare_amount) AS total_fare_by_city
    FROM fact_trips AS ft
    JOIN dim_city AS dc
        ON ft.city_id = dc.city_id
    GROUP BY dc.city_name
)
SELECT 
    r.city_name,
    r.month AS highest_revenue_month,
    r.revenue,
    ROUND(r.revenue / ct.total_fare_by_city * 100, 2) AS percentage_contribution
FROM revenue AS r
JOIN city_total AS ct
    ON r.city_name = ct.city_name
WHERE r.revenue_rank = 1
ORDER BY r.city_name;
```


Business Request - 6: Repeat Passenger Rate Analysis

**Objective:** 
Generate a report that calculates two metrics:
1.	Monthly Repeat Passenger Rate: Calculate the repeat passenger rate for each city and month by comparing the number of repeat passengers to the total passengers.
2.	City-wide Repeat Passenger Rate: Calculate the overall repeat passenger rate for each city, considering all passengers across months.
   
These metrics will provide insights into monthly repeat trends as well as the overall repeat behaviour for each city.


```sql
WITH passenger_summary AS (
    SELECT 
        dc.city_name,
        DATE_TRUNC('month', ft.trip_date) AS month,
        COUNT(*) AS total_passengers,
        SUM(CASE WHEN ft.passenger_type = 'repeated' THEN 1 ELSE 0 END) AS repeat_passengers
    FROM fact_trips AS ft
    JOIN dim_city AS dc
        ON ft.city_id = dc.city_id
    GROUP BY 1, 2
),
city_summary AS (
    SELECT 
        city_name,
        SUM(total_passengers) AS total_city_passengers,
        SUM(repeat_passengers) AS total_repeat_passengers
    FROM passenger_summary
    GROUP BY 1
)
SELECT 
    ps.city_name,
    TO_CHAR(ps.month, 'Month') AS month,
    ps.total_passengers,
    ps.repeat_passengers,
    ROUND((ps.repeat_passengers::NUMERIC / ps.total_passengers) * 100, 2) AS monthly_repeat_passenger_rate,
    ROUND((cs.total_repeat_passengers::NUMERIC / cs.total_city_passengers) * 100, 2) AS city_repeat_passenger_rate
FROM passenger_summary AS ps
JOIN city_summary AS cs
    ON ps.city_name = cs.city_name
ORDER BY ps.city_name, ps.month;
```

