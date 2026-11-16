-- ====================================================================
-- FraudShield: Fraud Transaction Detection & Risk Scoring System
-- File: 05_triggers.sql
-- Description: MySQL Database Triggers for automated timestamps & audit integrity
-- Compatible: MySQL 8.0+ / MySQL Workbench
-- ====================================================================

USE fraudshield;

DROP TRIGGER IF EXISTS trg_fraud_alerts_before_update;
DROP TRIGGER IF EXISTS trg_transactions_before_insert;

DELIMITER $$

-- ====================================================================
-- Trigger 1: trg_fraud_alerts_before_update
-- Automatically sets resolved_at timestamp when an alert is resolved
-- or marked False Positive, and clears it if reopened.
-- ====================================================================
CREATE TRIGGER trg_fraud_alerts_before_update
BEFORE UPDATE ON fraud_alerts
FOR EACH ROW
BEGIN
    -- If transitioning to Resolved or False Positive, ensure resolved_at is set
    IF NEW.alert_status IN ('Resolved', 'False Positive') AND OLD.alert_status NOT IN ('Resolved', 'False Positive') THEN
        IF NEW.resolved_at IS NULL THEN
            SET NEW.resolved_at = CURRENT_TIMESTAMP;
        END IF;
    END IF;

    -- If reopened from Resolved/False Positive to Pending or Investigating, clear resolved_at
    IF NEW.alert_status IN ('Pending', 'Investigating') AND OLD.alert_status IN ('Resolved', 'False Positive') THEN
        SET NEW.resolved_at = NULL;
    END IF;
END$$

-- ====================================================================
-- Trigger 2: trg_transactions_before_insert
-- Ensures risk_score defaults to 0 and risk_level matches get_risk_level()
-- upon creation before deep analysis
-- ====================================================================
CREATE TRIGGER trg_transactions_before_insert
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    IF NEW.risk_score IS NULL THEN
        SET NEW.risk_score = 0;
    END IF;
    
    IF NEW.risk_level IS NULL THEN
        SET NEW.risk_level = get_risk_level(NEW.risk_score);
    END IF;
END$$

DELIMITER ;
