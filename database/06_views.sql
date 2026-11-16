-- ====================================================================
-- FraudShield: Fraud Transaction Detection & Risk Scoring System
-- File: 06_views.sql
-- Description: MySQL Database Views for reporting, dashboards & analytics
-- Compatible: MySQL 8.0+ / MySQL Workbench
-- ====================================================================

USE fraudshield;

DROP VIEW IF EXISTS vw_high_risk_transactions;
DROP VIEW IF EXISTS vw_customer_risk_summary;
DROP VIEW IF EXISTS vw_fraud_dashboard;
DROP VIEW IF EXISTS vw_recent_fraud_alerts;
DROP VIEW IF EXISTS vw_fraud_reason_analysis;

-- ====================================================================
-- View 1: vw_high_risk_transactions
-- Details all transactions classified as HIGH risk
-- ====================================================================
CREATE VIEW vw_high_risk_transactions AS
SELECT 
    t.transaction_id,
    c.customer_id,
    c.full_name AS customer_name,
    c.email AS customer_email,
    c.phone AS customer_phone,
    a.account_number,
    a.account_type,
    t.amount,
    t.transaction_type,
    t.transaction_method,
    t.transaction_timestamp,
    l.city,
    l.state,
    l.country,
    COALESCE(d.device_name, 'No Device / POS') AS device_name,
    COALESCE(d.trusted_status, 'Untrusted') AS device_status,
    t.transaction_status,
    t.risk_score,
    t.risk_level,
    fa.alert_id,
    fa.alert_status,
    fa.alert_reason
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
JOIN customers c ON a.customer_id = c.customer_id
JOIN locations l ON t.location_id = l.location_id
LEFT JOIN devices d ON t.device_id = d.device_id
LEFT JOIN fraud_alerts fa ON t.transaction_id = fa.transaction_id
WHERE t.risk_level = 'HIGH';

-- ====================================================================
-- View 2: vw_customer_risk_summary
-- Aggregated customer-level risk profile & transaction patterns
-- ====================================================================
CREATE VIEW vw_customer_risk_summary AS
SELECT 
    c.customer_id,
    c.full_name,
    c.email,
    c.phone,
    c.city,
    c.state,
    c.customer_status,
    COUNT(DISTINCT a.account_id) AS total_accounts,
    COUNT(DISTINCT d.device_id) AS registered_devices,
    COUNT(t.transaction_id) AS total_transactions,
    COALESCE(SUM(t.amount), 0.00) AS total_transaction_volume,
    COALESCE(ROUND(AVG(t.amount), 2), 0.00) AS avg_transaction_amount,
    SUM(CASE WHEN t.risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_transactions,
    SUM(CASE WHEN t.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_transactions,
    SUM(CASE WHEN t.risk_level = 'LOW' THEN 1 ELSE 0 END) AS low_risk_transactions,
    COUNT(DISTINCT fa.alert_id) AS total_fraud_alerts,
    COALESCE(MAX(t.risk_score), 0) AS max_risk_score,
    COALESCE(ROUND(AVG(t.risk_score), 1), 0.0) AS avg_risk_score,
    MAX(t.transaction_timestamp) AS last_transaction_date
FROM customers c
LEFT JOIN accounts a ON c.customer_id = a.customer_id
LEFT JOIN devices d ON c.customer_id = d.customer_id
LEFT JOIN transactions t ON a.account_id = t.account_id
LEFT JOIN fraud_alerts fa ON t.transaction_id = fa.transaction_id
GROUP BY 
    c.customer_id, 
    c.full_name, 
    c.email, 
    c.phone, 
    c.city, 
    c.state, 
    c.customer_status;

-- ====================================================================
-- View 3: vw_fraud_dashboard
-- System-wide Key Performance Indicators (KPIs)
-- ====================================================================
CREATE VIEW vw_fraud_dashboard AS
SELECT 
    COUNT(t.transaction_id) AS total_transactions,
    COALESCE(SUM(t.amount), 0.00) AS total_transaction_value,
    COALESCE(ROUND(AVG(t.amount), 2), 0.00) AS avg_transaction_value,
    SUM(CASE WHEN t.risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
    SUM(CASE WHEN t.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_count,
    SUM(CASE WHEN t.risk_level = 'LOW' THEN 1 ELSE 0 END) AS low_risk_count,
    COALESCE(SUM(CASE WHEN t.risk_level = 'HIGH' THEN t.amount ELSE 0.00 END), 0.00) AS high_risk_volume,
    (SELECT COUNT(*) FROM fraud_alerts) AS total_fraud_alerts,
    (SELECT COUNT(*) FROM fraud_alerts WHERE alert_status = 'Pending') AS pending_alerts,
    (SELECT COUNT(*) FROM fraud_alerts WHERE alert_status = 'Investigating') AS investigating_alerts,
    (SELECT COUNT(*) FROM fraud_alerts WHERE alert_status = 'Resolved') AS resolved_alerts,
    (SELECT COUNT(*) FROM fraud_alerts WHERE alert_status = 'False Positive') AS false_positive_alerts
FROM transactions t;

-- ====================================================================
-- View 4: vw_recent_fraud_alerts
-- Consolidated feed of fraud alerts with investigation context
-- ====================================================================
CREATE VIEW vw_recent_fraud_alerts AS
SELECT 
    fa.alert_id,
    fa.transaction_id,
    c.customer_id,
    c.full_name AS customer_name,
    c.phone AS customer_phone,
    a.account_number,
    t.amount,
    t.transaction_type,
    t.transaction_method,
    t.transaction_timestamp,
    l.city AS location_city,
    l.state AS location_state,
    COALESCE(d.device_name, 'No Device') AS device_name,
    fa.risk_score,
    fa.risk_level,
    fa.alert_reason,
    fa.alert_status,
    fa.created_at,
    fa.resolved_at,
    fa.notes
FROM fraud_alerts fa
JOIN transactions t ON fa.transaction_id = t.transaction_id
JOIN accounts a ON t.account_id = a.account_id
JOIN customers c ON a.customer_id = c.customer_id
JOIN locations l ON t.location_id = l.location_id
LEFT JOIN devices d ON t.device_id = d.device_id
ORDER BY fa.created_at DESC;

-- ====================================================================
-- View 5: vw_fraud_reason_analysis
-- Frequency analysis of triggered fraud rules across all transactions
-- ====================================================================
CREATE VIEW vw_fraud_reason_analysis AS
SELECT 
    fr.rule_id,
    fr.rule_code,
    fr.rule_name,
    fr.risk_points AS configured_points,
    fr.active_status,
    COUNT(trm.match_id) AS times_triggered,
    COALESCE(SUM(trm.points_awarded), 0) AS total_points_awarded,
    ROUND(
        COUNT(trm.match_id) * 100.0 / NULLIF((SELECT COUNT(*) FROM transaction_rule_matches), 0),
        1
    ) AS trigger_percentage
FROM fraud_rules fr
LEFT JOIN transaction_rule_matches trm ON fr.rule_id = trm.rule_id
GROUP BY fr.rule_id, fr.rule_code, fr.rule_name, fr.risk_points, fr.active_status
ORDER BY times_triggered DESC;
