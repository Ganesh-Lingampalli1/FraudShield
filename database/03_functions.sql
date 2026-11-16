-- ====================================================================
-- FraudShield: Fraud Transaction Detection & Risk Scoring System
-- File: 03_functions.sql
-- Description: MySQL Stored Functions for risk classification & baselining
-- Compatible: MySQL 8.0+ / MySQL Workbench
-- ====================================================================

USE fraudshield;

DROP FUNCTION IF EXISTS get_risk_level;
DROP FUNCTION IF EXISTS get_customer_historical_avg;
DROP FUNCTION IF EXISTS is_location_unusual;

DELIMITER $$

-- ====================================================================
-- Function 1: get_risk_level
-- Classifies a numeric risk score into LOW, MEDIUM, or HIGH
-- Configurable boundaries:
--   0 - 29 : LOW
--  30 - 59 : MEDIUM
--  60+     : HIGH
-- ====================================================================
CREATE FUNCTION get_risk_level(p_score INT)
RETURNS VARCHAR(10)
DETERMINISTIC
CONTAINS SQL
BEGIN
    DECLARE v_level VARCHAR(10);
    
    IF p_score >= 60 THEN
        SET v_level = 'HIGH';
    ELSEIF p_score >= 30 THEN
        SET v_level = 'MEDIUM';
    ELSE
        SET v_level = 'LOW';
    END IF;
    
    RETURN v_level;
END$$

-- ====================================================================
-- Function 2: get_customer_historical_avg
-- Calculates a customer's average completed transaction amount PRIOR
-- to a given timestamp, strictly excluding the transaction under review
-- ====================================================================
CREATE FUNCTION get_customer_historical_avg(
    p_customer_id INT,
    p_tx_timestamp DATETIME,
    p_exclude_tx_id INT
)
RETURNS DECIMAL(12, 2)
READS SQL DATA
BEGIN
    DECLARE v_avg DECIMAL(12, 2) DEFAULT 0.00;
    
    SELECT COALESCE(AVG(t.amount), 0.00)
    INTO v_avg
    FROM transactions t
    JOIN accounts a ON t.account_id = a.account_id
    WHERE a.customer_id = p_customer_id
      AND t.transaction_id != p_exclude_tx_id
      AND t.transaction_timestamp < p_tx_timestamp
      AND t.transaction_status = 'Completed';
      
    RETURN v_avg;
END$$

-- ====================================================================
-- Function 3: is_location_unusual
-- Checks whether a transaction location has never been visited before
-- by the customer prior to this transaction (requires at least 2 historical tx)
-- ====================================================================
CREATE FUNCTION is_location_unusual(
    p_customer_id INT,
    p_location_id INT,
    p_tx_timestamp DATETIME
)
RETURNS TINYINT
READS SQL DATA
BEGIN
    DECLARE v_prev_total_tx INT DEFAULT 0;
    DECLARE v_prev_loc_tx INT DEFAULT 0;
    
    -- Count prior transactions in ANY location
    SELECT COUNT(*)
    INTO v_prev_total_tx
    FROM transactions t
    JOIN accounts a ON t.account_id = a.account_id
    WHERE a.customer_id = p_customer_id
      AND t.transaction_timestamp < p_tx_timestamp;
      
    -- If customer has fewer than 2 previous transactions, not enough baseline
    IF v_prev_total_tx < 2 THEN
        RETURN 0;
    END IF;
    
    -- Count prior transactions in THIS location
    SELECT COUNT(*)
    INTO v_prev_loc_tx
    FROM transactions t
    JOIN accounts a ON t.account_id = a.account_id
    WHERE a.customer_id = p_customer_id
      AND t.location_id = p_location_id
      AND t.transaction_timestamp < p_tx_timestamp;
      
    IF v_prev_loc_tx = 0 THEN
        RETURN 1; -- Unusual location!
    ELSE
        RETURN 0; -- Known location
    END IF;
END$$

DELIMITER ;
