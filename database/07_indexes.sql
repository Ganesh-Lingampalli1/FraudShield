-- ====================================================================
-- FraudShield: Fraud Transaction Detection & Risk Scoring System
-- File: 07_indexes.sql
-- Description: Composite and covering indexes for optimal query & procedure performance
-- Compatible: MySQL 8.0+ / MySQL Workbench
-- ====================================================================

USE fraudshield;

-- Transactions indexes
CREATE INDEX idx_tx_account_timestamp ON transactions(account_id, transaction_timestamp);
CREATE INDEX idx_tx_timestamp ON transactions(transaction_timestamp);
CREATE INDEX idx_tx_risk_level_score ON transactions(risk_level, risk_score);
CREATE INDEX idx_tx_status_timestamp ON transactions(transaction_status, transaction_timestamp);
CREATE INDEX idx_tx_location ON transactions(location_id);
CREATE INDEX idx_tx_device ON transactions(device_id);

-- Accounts indexes
CREATE INDEX idx_accounts_customer ON accounts(customer_id);
CREATE INDEX idx_accounts_status ON accounts(account_status);

-- Devices indexes
CREATE INDEX idx_devices_customer_status ON devices(customer_id, trusted_status);
CREATE INDEX idx_devices_first_used ON devices(first_used);

-- Fraud Alerts indexes
CREATE INDEX idx_alerts_status_created ON fraud_alerts(alert_status, created_at);
CREATE INDEX idx_alerts_risk_level ON fraud_alerts(risk_level);

-- Transaction Rule Matches indexes
CREATE INDEX idx_trm_tx ON transaction_rule_matches(transaction_id);
CREATE INDEX idx_trm_rule ON transaction_rule_matches(rule_id);
