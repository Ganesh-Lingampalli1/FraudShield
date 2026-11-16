-- ====================================================================
-- FraudShield: Fraud Transaction Detection & Risk Scoring System
-- File: 04_procedures.sql
-- Description: MySQL Stored Procedures for transaction risk analysis,
--              alert management, and customer profiling
-- Compatible: MySQL 8.0+ / MySQL Workbench
-- ====================================================================

USE fraudshield;

DROP PROCEDURE IF EXISTS analyze_transaction;
DROP PROCEDURE IF EXISTS analyze_all_transactions;
DROP PROCEDURE IF EXISTS update_alert_status;
DROP PROCEDURE IF EXISTS customer_risk_summary;

DELIMITER $$

-- ====================================================================
-- Procedure 1: analyze_transaction
-- Evaluates all active fraud rules for a specific transaction,
-- persists rule matches, calculates risk score/level, updates the
-- transaction record, and creates or updates fraud alerts.
-- Safe to re-run (idempotent).
-- ====================================================================
CREATE PROCEDURE analyze_transaction(IN p_transaction_id INT)
proc_body: BEGIN
    DECLARE v_account_id INT;
    DECLARE v_customer_id INT;
    DECLARE v_amount DECIMAL(12, 2);
    DECLARE v_tx_timestamp DATETIME;
    DECLARE v_location_id INT;
    DECLARE v_device_id INT;
    DECLARE v_tx_status VARCHAR(20);
    DECLARE v_device_name VARCHAR(100);
    DECLARE v_device_status VARCHAR(20);
    DECLARE v_device_first_used DATETIME;
    DECLARE v_city VARCHAR(50);
    
    DECLARE v_historical_avg DECIMAL(12, 2) DEFAULT 0.00;
    DECLARE v_prior_tx_count INT DEFAULT 0;
    DECLARE v_rapid_count INT DEFAULT 0;
    DECLARE v_failed_count INT DEFAULT 0;
    DECLARE v_is_unusual_loc TINYINT DEFAULT 0;
    
    DECLARE v_total_score INT DEFAULT 0;
    DECLARE v_risk_level VARCHAR(10) DEFAULT 'LOW';
    DECLARE v_alert_reason TEXT DEFAULT '';
    
    -- Variables for active rule IDs and risk points
    DECLARE v_rule_high_amt_id INT;
    DECLARE v_rule_high_amt_pts INT;
    DECLARE v_rule_new_dev_id INT;
    DECLARE v_rule_new_dev_pts INT;
    DECLARE v_rule_unusual_loc_id INT;
    DECLARE v_rule_unusual_loc_pts INT;
    DECLARE v_rule_rapid_tx_id INT;
    DECLARE v_rule_rapid_tx_pts INT;
    DECLARE v_rule_late_night_id INT;
    DECLARE v_rule_late_night_pts INT;
    DECLARE v_rule_failed_tx_id INT;
    DECLARE v_rule_failed_tx_pts INT;

    -- 1. Fetch transaction and customer context
    SELECT 
        t.account_id,
        a.customer_id,
        t.amount,
        t.transaction_timestamp,
        t.location_id,
        t.device_id,
        t.transaction_status,
        d.device_name,
        d.trusted_status,
        d.first_used,
        l.city
    INTO 
        v_account_id,
        v_customer_id,
        v_amount,
        v_tx_timestamp,
        v_location_id,
        v_device_id,
        v_tx_status,
        v_device_name,
        v_device_status,
        v_device_first_used,
        v_city
    FROM transactions t
    JOIN accounts a ON t.account_id = a.account_id
    JOIN locations l ON t.location_id = l.location_id
    LEFT JOIN devices d ON t.device_id = d.device_id
    WHERE t.transaction_id = p_transaction_id;

    -- If transaction does not exist, exit
    IF v_account_id IS NULL THEN
        LEAVE proc_body;
    END IF;

    -- 2. Clear prior rule matches for idempotency
    DELETE FROM transaction_rule_matches WHERE transaction_id = p_transaction_id;

    -- 3. Cache active rules and their points from fraud_rules table
    SELECT rule_id, risk_points INTO v_rule_high_amt_id, v_rule_high_amt_pts 
    FROM fraud_rules WHERE rule_code = 'HIGH_AMOUNT' AND active_status = TRUE LIMIT 1;

    SELECT rule_id, risk_points INTO v_rule_new_dev_id, v_rule_new_dev_pts 
    FROM fraud_rules WHERE rule_code = 'NEW_DEVICE' AND active_status = TRUE LIMIT 1;

    SELECT rule_id, risk_points INTO v_rule_unusual_loc_id, v_rule_unusual_loc_pts 
    FROM fraud_rules WHERE rule_code = 'UNUSUAL_LOCATION' AND active_status = TRUE LIMIT 1;

    SELECT rule_id, risk_points INTO v_rule_rapid_tx_id, v_rule_rapid_tx_pts 
    FROM fraud_rules WHERE rule_code = 'RAPID_TRANSACTIONS' AND active_status = TRUE LIMIT 1;

    SELECT rule_id, risk_points INTO v_rule_late_night_id, v_rule_late_night_pts 
    FROM fraud_rules WHERE rule_code = 'LATE_NIGHT_TRANSACTION' AND active_status = TRUE LIMIT 1;

    SELECT rule_id, risk_points INTO v_rule_failed_tx_id, v_rule_failed_tx_pts 
    FROM fraud_rules WHERE rule_code = 'MULTIPLE_FAILED_TRANSACTIONS' AND active_status = TRUE LIMIT 1;

    -- ================================================================
    -- RULE 1: Unusually High Transaction Amount
    -- Compared to customer's historical average (excluding current transaction)
    -- ================================================================
    IF v_rule_high_amt_id IS NOT NULL THEN
        SET v_historical_avg = get_customer_historical_avg(v_customer_id, v_tx_timestamp, p_transaction_id);
        
        SELECT COUNT(*) INTO v_prior_tx_count
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE a.customer_id = v_customer_id
          AND t.transaction_timestamp < v_tx_timestamp
          AND t.transaction_status = 'Completed';

        -- Trigger if amount is 3x the baseline (and >= 15,000) OR high-value anomaly without baseline
        IF (v_prior_tx_count >= 2 AND v_historical_avg > 0 AND v_amount >= (3.0 * v_historical_avg) AND v_amount >= 15000.00) THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (
                p_transaction_id, 
                v_rule_high_amt_id, 
                v_rule_high_amt_pts, 
                CONCAT('Amount ₹', FORMAT(v_amount, 2), ' exceeds 3x customer average ₹', FORMAT(v_historical_avg, 2))
            );
        ELSEIF (v_prior_tx_count < 2 AND v_amount >= 80000.00) THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (
                p_transaction_id, 
                v_rule_high_amt_id, 
                v_rule_high_amt_pts, 
                CONCAT('Large transaction ₹', FORMAT(v_amount, 2), ' without established customer baseline')
            );
        END IF;
    END IF;

    -- ================================================================
    -- RULE 2: New or Untrusted Device
    -- ================================================================
    IF v_rule_new_dev_id IS NOT NULL THEN
        IF v_device_id IS NULL THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (p_transaction_id, v_rule_new_dev_id, v_rule_new_dev_pts, 'Transaction performed without recognized device');
        ELSEIF v_device_status IN ('Untrusted', 'Suspicious') THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (p_transaction_id, v_rule_new_dev_id, v_rule_new_dev_pts, CONCAT('Untrusted or flagged device: ', COALESCE(v_device_name, 'Unknown')));
        ELSEIF v_device_first_used >= DATE_SUB(v_tx_timestamp, INTERVAL 2 HOUR) THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (p_transaction_id, v_rule_new_dev_id, v_rule_new_dev_pts, CONCAT('Newly registered device: ', COALESCE(v_device_name, 'Unknown')));
        END IF;
    END IF;

    -- ================================================================
    -- RULE 3: Unusual Location
    -- Customer transacting in a location never previously recorded
    -- ================================================================
    IF v_rule_unusual_loc_id IS NOT NULL THEN
        SET v_is_unusual_loc = is_location_unusual(v_customer_id, v_location_id, v_tx_timestamp);
        IF v_is_unusual_loc = 1 THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (p_transaction_id, v_rule_unusual_loc_id, v_rule_unusual_loc_pts, CONCAT('Unusual location: ', v_city, ' (never transacted here previously)'));
        END IF;
    END IF;

    -- ================================================================
    -- RULE 4: Rapid Transactions (Velocity Spike)
    -- Multiple transactions on same account within 10 minutes
    -- ================================================================
    IF v_rule_rapid_tx_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_rapid_count
        FROM transactions
        WHERE account_id = v_account_id
          AND transaction_id != p_transaction_id
          AND transaction_timestamp BETWEEN DATE_SUB(v_tx_timestamp, INTERVAL 10 MINUTE) AND v_tx_timestamp;

        IF v_rapid_count >= 2 THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (
                p_transaction_id, 
                v_rule_rapid_tx_id, 
                v_rule_rapid_tx_pts, 
                CONCAT('High frequency: ', (v_rapid_count + 1), ' transactions detected within 10-minute window')
            );
        END IF;
    END IF;

    -- ================================================================
    -- RULE 5: Late-Night Transaction
    -- Transactions initiated between 12:00 AM (00:00:00) and 04:00:00 AM
    -- ================================================================
    IF v_rule_late_night_id IS NOT NULL THEN
        IF TIME(v_tx_timestamp) >= '00:00:00' AND TIME(v_tx_timestamp) <= '04:00:00' THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (
                p_transaction_id, 
                v_rule_late_night_id, 
                v_rule_late_night_pts, 
                CONCAT('Late-night transaction executed at ', TIME_FORMAT(v_tx_timestamp, '%H:%i:%s'))
            );
        END IF;
    END IF;

    -- ================================================================
    -- RULE 6: Multiple Failed Transactions
    -- Two or more failed transactions on the account within preceding 2 hours
    -- ================================================================
    IF v_rule_failed_tx_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_failed_count
        FROM transactions
        WHERE account_id = v_account_id
          AND transaction_id != p_transaction_id
          AND transaction_status IN ('Failed', 'Declined')
          AND transaction_timestamp BETWEEN DATE_SUB(v_tx_timestamp, INTERVAL 2 HOUR) AND v_tx_timestamp;

        IF v_failed_count >= 2 THEN
            INSERT INTO transaction_rule_matches (transaction_id, rule_id, points_awarded, match_reason)
            VALUES (
                p_transaction_id, 
                v_rule_failed_tx_id, 
                v_rule_failed_tx_pts, 
                CONCAT('Preceded by ', v_failed_count, ' failed/declined transactions within 2 hours')
            );
        END IF;
    END IF;

    -- 4. Calculate total score from junction table
    SELECT COALESCE(SUM(points_awarded), 0)
    INTO v_total_score
    FROM transaction_rule_matches
    WHERE transaction_id = p_transaction_id;

    -- 5. Determine risk level via MySQL function
    SET v_risk_level = get_risk_level(v_total_score);

    -- 6. Update the transaction record
    UPDATE transactions
    SET risk_score = v_total_score,
        risk_level = v_risk_level,
        analyzed_at = NOW()
    WHERE transaction_id = p_transaction_id;

    -- 7. Manage Fraud Alert
    IF v_risk_level IN ('MEDIUM', 'HIGH') THEN
        -- Construct consolidated alert reason
        SELECT GROUP_CONCAT(CONCAT(fr.rule_name, ' (', trm.match_reason, ')') SEPARATOR '; ')
        INTO v_alert_reason
        FROM transaction_rule_matches trm
        JOIN fraud_rules fr ON trm.rule_id = fr.rule_id
        WHERE trm.transaction_id = p_transaction_id;

        IF v_alert_reason IS NULL OR v_alert_reason = '' THEN
            SET v_alert_reason = CONCAT('Elevated risk level: ', v_risk_level, ' (Score: ', v_total_score, ')');
        END IF;

        -- Upsert into fraud_alerts
        INSERT INTO fraud_alerts (transaction_id, risk_score, risk_level, alert_reason, alert_status, created_at)
        VALUES (p_transaction_id, v_total_score, v_risk_level, v_alert_reason, 'Pending', NOW())
        ON DUPLICATE KEY UPDATE
            risk_score = VALUES(risk_score),
            risk_level = VALUES(risk_level),
            alert_reason = VALUES(alert_reason);
    ELSE
        -- If score was lowered back to LOW on re-evaluation and was still Pending, remove alert
        DELETE FROM fraud_alerts 
        WHERE transaction_id = p_transaction_id AND alert_status = 'Pending';
    END IF;

END proc_body$$

-- ====================================================================
-- Procedure 2: analyze_all_transactions
-- Iterates through all transactions and runs analyze_transaction on each
-- ====================================================================
CREATE PROCEDURE analyze_all_transactions()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_cur_tx_id INT;
    DECLARE v_count INT DEFAULT 0;
    
    DECLARE tx_cursor CURSOR FOR 
        SELECT transaction_id FROM transactions ORDER BY transaction_timestamp ASC, transaction_id ASC;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN tx_cursor;
    read_loop: LOOP
        FETCH tx_cursor INTO v_cur_tx_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        CALL analyze_transaction(v_cur_tx_id);
        SET v_count = v_count + 1;
    END LOOP;
    CLOSE tx_cursor;

    SELECT CONCAT('Successfully analyzed ', v_count, ' transactions.') AS result;
END$$

-- ====================================================================
-- Procedure 3: update_alert_status
-- Transitions alert status (Pending -> Investigating -> Resolved / False Positive)
-- Automatically records audit entry and sets resolved_at
-- ====================================================================
CREATE PROCEDURE update_alert_status(
    IN p_alert_id INT,
    IN p_new_status VARCHAR(20),
    IN p_notes TEXT
)
BEGIN
    DECLARE v_old_status VARCHAR(20);
    DECLARE v_resolved_time DATETIME DEFAULT NULL;

    -- Validate new status
    IF p_new_status NOT IN ('Pending', 'Investigating', 'Resolved', 'False Positive') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid alert status. Must be: Pending, Investigating, Resolved, or False Positive.';
    END IF;

    -- Fetch current status
    SELECT alert_status INTO v_old_status
    FROM fraud_alerts
    WHERE alert_id = p_alert_id;

    IF v_old_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Alert not found.';
    END IF;

    -- If final status, set resolved_at
    IF p_new_status IN ('Resolved', 'False Positive') THEN
        SET v_resolved_time = NOW();
    END IF;

    -- Update alert
    UPDATE fraud_alerts
    SET alert_status = p_new_status,
        notes = COALESCE(p_notes, notes),
        resolved_at = v_resolved_time
    WHERE alert_id = p_alert_id;

    -- Insert into audit log
    INSERT INTO fraud_audit_log (alert_id, old_status, new_status, changed_by, notes)
    VALUES (p_alert_id, v_old_status, p_new_status, 'Investigator', p_notes);

    SELECT p_alert_id AS alert_id, v_old_status AS old_status, p_new_status AS new_status, 'Updated successfully' AS status;
END$$

-- ====================================================================
-- Procedure 4: customer_risk_summary
-- Generates a 360-degree risk profile for a specific customer
-- ====================================================================
CREATE PROCEDURE customer_risk_summary(IN p_customer_id INT)
BEGIN
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
        COALESCE(SUM(t.amount), 0.00) AS total_spent,
        COALESCE(AVG(t.amount), 0.00) AS avg_transaction_amount,
        COALESCE(MAX(t.amount), 0.00) AS max_transaction_amount,
        SUM(CASE WHEN t.risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_transactions,
        SUM(CASE WHEN t.risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_transactions,
        SUM(CASE WHEN t.risk_level = 'LOW' THEN 1 ELSE 0 END) AS low_risk_transactions,
        COUNT(fa.alert_id) AS total_fraud_alerts,
        COALESCE(MAX(t.risk_score), 0) AS peak_risk_score,
        COALESCE(ROUND(AVG(t.risk_score), 1), 0.0) AS avg_risk_score,
        MAX(t.transaction_timestamp) AS last_transaction_date
    FROM customers c
    LEFT JOIN accounts a ON c.customer_id = a.customer_id
    LEFT JOIN devices d ON c.customer_id = d.customer_id
    LEFT JOIN transactions t ON a.account_id = t.account_id
    LEFT JOIN fraud_alerts fa ON t.transaction_id = fa.transaction_id
    WHERE c.customer_id = p_customer_id
    GROUP BY c.customer_id, c.full_name, c.email, c.phone, c.city, c.state, c.customer_status;
END$$

DELIMITER ;
