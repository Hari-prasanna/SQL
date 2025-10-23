
--Exploring tables for references

SELECT *
FROM fact_trips
LIMIT 10


SELECT *
FROM dim_city


SELECT *
FROM monthly_target_trips


SELECT *
FROM dim_repeat_trip_distribution


SELECT *
FROM monthly_target_new_passengers


SELECT *
FROM fact_passenger_summary



--Business Request - 1: City-Level Fare and Trip Summary Report

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



--Business Request - 2: Monthly City-Level Trips Target Performance Report

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


--Business Request - 3: City-Level Repeat Passenger Trip Frequency Report


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



--Business Request - 4: Identify Cities with Highest and Lowest Total New Passengers



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



--Business Request - 5: Identify Month with Highest Revenue for Each City


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



--Business Request - 6: Repeat Passenger Rate Analysis


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
