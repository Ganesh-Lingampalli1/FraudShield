-- ====================================================================
-- FraudShield: Fraud Transaction Detection & Risk Scoring System
-- File: 08_analysis_queries.sql
-- Description: Advanced SQL Demonstration Queries for Trainers and Evaluators
-- Topics: Window Functions, CTEs, Correlated Subqueries, HAVING, Joins
-- Compatible: MySQL 8.0+ / MySQL Workbench
-- ====================================================================

USE fraudshield;

-- ====================================================================
-- Query 1: CTE + Window Function (LAG)
-- Detect consecutive transactions on the same account within 10 minutes
-- Demonstrates: CTE, LAG(), TIMESTAMPDIFF, Window Functions
-- ====================================================================
WITH OrderedTransactions AS (
    SELECT 
        t.transaction_id,
        t.account_id,
        c.full_name AS customer_name,
        t.amount,
        t.transaction_timestamp,
        LAG(t.transaction_timestamp, 1) OVER (
            PARTITION BY t.account_id 
            ORDER BY t.transaction_timestamp
        ) AS prev_timestamp,
        LAG(t.amount, 1) OVER (
            PARTITION BY t.account_id 
            ORDER BY t.transaction_timestamp
        ) AS prev_amount
    FROM transactions t
    JOIN accounts a ON t.account_id = a.account_id
    JOIN customers c ON a.customer_id = c.customer_id
)
SELECT 
    transaction_id,
    account_id,
    customer_name,
    amount,
    transaction_timestamp,
    prev_timestamp,
    TIMESTAMPDIFF(MINUTE, prev_timestamp, transaction_timestamp) AS minutes_since_prev
FROM OrderedTransactions
WHERE prev_timestamp IS NOT NULL 
  AND TIMESTAMPDIFF(MINUTE, prev_timestamp, transaction_timestamp) <= 10
ORDER BY minutes_since_prev ASC;

-- ====================================================================
-- Query 2: Correlated Subquery + Historical Anomaly Detection
-- Identify transactions where amount exceeds 3x the customer's prior average
-- Demonstrates: Correlated Subquery, Aggregation, Date filtering
-- ====================================================================
SELECT 
    t.transaction_id,
    c.customer_id,
    c.full_name,
    t.amount,
    t.transaction_timestamp,
    ROUND((
        SELECT AVG(t_prev.amount)
        FROM transactions t_prev
        JOIN accounts a_prev ON t_prev.account_id = a_prev.account_id
        WHERE a_prev.customer_id = c.customer_id
          AND t_prev.transaction_id != t.transaction_id
          AND t_prev.transaction_timestamp < t.transaction_timestamp
          AND t_prev.transaction_status = 'Completed'
    ), 2) AS prior_historical_average,
    ROUND(
        t.amount / NULLIF((
            SELECT AVG(t_prev.amount)
            FROM transactions t_prev
            JOIN accounts a_prev ON t_prev.account_id = a_prev.account_id
            WHERE a_prev.customer_id = c.customer_id
              AND t_prev.transaction_id != t.transaction_id
              AND t_prev.transaction_timestamp < t.transaction_timestamp
              AND t_prev.transaction_status = 'Completed'
        ), 0), 2
    ) AS spike_ratio
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
JOIN customers c ON a.customer_id = c.customer_id
WHERE t.amount >= 15000
  AND t.amount >= 3.0 * (
      SELECT COALESCE(AVG(t_prev.amount), 0)
      FROM transactions t_prev
      JOIN accounts a_prev ON t_prev.account_id = a_prev.account_id
      WHERE a_prev.customer_id = c.customer_id
        AND t_prev.transaction_id != t.transaction_id
        AND t_prev.transaction_timestamp < t.transaction_timestamp
        AND t_prev.transaction_status = 'Completed'
  )
ORDER BY spike_ratio DESC;

-- ====================================================================
-- Query 3: Multi-Level Aggregation with GROUP BY, HAVING, and CASE
-- Identifies accounts with high velocity or elevated fraud rate
-- Demonstrates: GROUP BY, HAVING, SUM with CASE, Filtered Metrics
-- ====================================================================
SELECT 
    a.account_number,
    c.full_name AS customer_name,
    c.city,
    COUNT(t.transaction_id) AS total_transactions,
    ROUND(SUM(t.amount), 2) AS total_spent,
    SUM(CASE WHEN t.risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
    SUM(CASE WHEN t.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_count,
    ROUND(AVG(t.risk_score), 1) AS avg_risk_score,
    MAX(t.risk_score) AS max_risk_score
FROM accounts a
JOIN customers c ON a.customer_id = c.customer_id
JOIN transactions t ON a.account_id = t.account_id
GROUP BY a.account_number, c.full_name, c.city
HAVING high_risk_count > 0 OR avg_risk_score >= 25.0
ORDER BY high_risk_count DESC, avg_risk_score DESC;

-- ====================================================================
-- Query 4: Hourly Distribution & Peak Fraud Exposure
-- Identifies hour-by-hour vulnerability to fraud
-- Demonstrates: Date/Time extraction (HOUR), Conditional Aggregation
-- ====================================================================
SELECT 
    HOUR(transaction_timestamp) AS hour_of_day,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_tx,
    SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_tx,
    ROUND(
        SUM(CASE WHEN risk_level IN ('HIGH', 'MEDIUM') THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) AS suspicious_percentage,
    ROUND(SUM(amount), 2) AS total_volume
FROM transactions
GROUP BY HOUR(transaction_timestamp)
ORDER BY hour_of_day ASC;

-- ====================================================================
-- Query 5: Window Function (ROW_NUMBER & PARTITION BY)
-- Find the top 3 highest-risk transactions for every customer
-- Demonstrates: ROW_NUMBER(), PARTITION BY, CTE
-- ====================================================================
WITH RankedCustomerTx AS (
    SELECT 
        c.customer_id,
        c.full_name,
        t.transaction_id,
        t.amount,
        t.risk_score,
        t.risk_level,
        t.transaction_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_id 
            ORDER BY t.risk_score DESC, t.amount DESC
        ) AS rank_num
    FROM customers c
    JOIN accounts a ON c.customer_id = a.customer_id
    JOIN transactions t ON a.account_id = t.account_id
)
SELECT 
    customer_id,
    full_name,
    transaction_id,
    amount,
    risk_score,
    risk_level,
    transaction_timestamp
FROM RankedCustomerTx
WHERE rank_num <= 3 AND risk_score > 0
ORDER BY risk_score DESC, customer_id ASC;
