-- ====================================================================
-- FraudShield: Fraud Transaction Detection & Risk Scoring System
-- File: 01_schema.sql
-- Description: Database creation, table definitions, constraints & relationships
-- Compatible: MySQL 8.0+ / MySQL Workbench
-- ====================================================================

-- 1. Create and select the database
CREATE DATABASE IF NOT EXISTS fraudshield
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fraudshield;

-- 2. Drop existing tables in reverse order of foreign key dependencies
DROP TABLE IF EXISTS fraud_audit_log;
DROP TABLE IF EXISTS fraud_alerts;
DROP TABLE IF EXISTS transaction_rule_matches;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS fraud_rules;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS customers;

-- ====================================================================
-- Table 1: customers
-- Stores customer personal profile and baseline status
-- ====================================================================
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    date_of_birth DATE NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'India',
    customer_status ENUM('Active', 'Suspended', 'Under Review', 'Closed') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_customer_email CHECK (email LIKE '%@%.%'),
    CONSTRAINT chk_customer_dob CHECK (date_of_birth >= '1900-01-01')
) ENGINE=InnoDB;

-- ====================================================================
-- Table 2: accounts
-- Stores bank/payment accounts tied to customers
-- ====================================================================
CREATE TABLE accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_number VARCHAR(24) NOT NULL UNIQUE,
    account_type ENUM('Savings', 'Current', 'Credit Card', 'Salary') NOT NULL DEFAULT 'Savings',
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    account_status ENUM('Active', 'Dormant', 'Frozen', 'Closed') NOT NULL DEFAULT 'Active',
    opened_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_accounts_customer FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_account_balance CHECK (balance >= 0.00)
) ENGINE=InnoDB;

-- ====================================================================
-- Table 3: devices
-- Stores customer devices (mobile, laptop, POS, tablet) & trust status
-- ====================================================================
CREATE TABLE devices (
    device_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    device_name VARCHAR(100) NOT NULL,
    device_type ENUM('Mobile', 'Desktop', 'Tablet', 'POS Terminal') NOT NULL DEFAULT 'Mobile',
    operating_system VARCHAR(50) NOT NULL,
    first_used DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    trusted_status ENUM('Trusted', 'Untrusted', 'Suspicious') NOT NULL DEFAULT 'Trusted',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_devices_customer FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ====================================================================
-- Table 4: locations
-- Standard geographic registry for transactions
-- ====================================================================
CREATE TABLE locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'India',
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    CONSTRAINT uq_location UNIQUE (city, state, country)
) ENGINE=InnoDB;

-- ====================================================================
-- Table 5: fraud_rules
-- Configurable fraud detection rules with assignable risk points
-- ====================================================================
CREATE TABLE fraud_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_code VARCHAR(50) NOT NULL UNIQUE,
    rule_name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL,
    risk_points INT NOT NULL DEFAULT 10,
    active_status BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_risk_points CHECK (risk_points >= 0 AND risk_points <= 100)
) ENGINE=InnoDB;

-- ====================================================================
-- Table 6: transactions
-- Core ledger of financial transactions with computed risk scores
-- ====================================================================
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    transaction_type ENUM('Debit', 'Credit', 'Transfer', 'Payment', 'Withdrawal') NOT NULL DEFAULT 'Debit',
    transaction_method ENUM('UPI', 'Net Banking', 'Credit Card', 'Debit Card', 'ATM', 'Wire Transfer') NOT NULL,
    transaction_timestamp DATETIME NOT NULL,
    location_id INT NOT NULL,
    device_id INT NULL,
    transaction_status ENUM('Completed', 'Failed', 'Pending', 'Declined', 'Reversed') NOT NULL DEFAULT 'Completed',
    merchant_name VARCHAR(100) NULL,
    risk_score INT NOT NULL DEFAULT 0,
    risk_level ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL DEFAULT 'LOW',
    analyzed_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tx_account FOREIGN KEY (account_id) 
        REFERENCES accounts(account_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tx_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) 
        ON UPDATE CASCADE,
    CONSTRAINT fk_tx_device FOREIGN KEY (device_id) 
        REFERENCES devices(device_id) 
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_tx_amount CHECK (amount > 0.00),
    CONSTRAINT chk_tx_score CHECK (risk_score >= 0)
) ENGINE=InnoDB;

-- ====================================================================
-- Table 7: transaction_rule_matches
-- Explainability table: records exactly which rules triggered for each transaction
-- ====================================================================
CREATE TABLE transaction_rule_matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL,
    rule_id INT NOT NULL,
    points_awarded INT NOT NULL,
    match_reason VARCHAR(255) NULL,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_match_tx FOREIGN KEY (transaction_id) 
        REFERENCES transactions(transaction_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_match_rule FOREIGN KEY (rule_id) 
        REFERENCES fraud_rules(rule_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_tx_rule UNIQUE (transaction_id, rule_id)
) ENGINE=InnoDB;

-- ====================================================================
-- Table 8: fraud_alerts
-- Actionable alerts generated for suspicious transactions (Medium/High)
-- ====================================================================
CREATE TABLE fraud_alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL UNIQUE,
    risk_score INT NOT NULL,
    risk_level ENUM('MEDIUM', 'HIGH') NOT NULL,
    alert_reason TEXT NOT NULL,
    alert_status ENUM('Pending', 'Investigating', 'Resolved', 'False Positive') NOT NULL DEFAULT 'Pending',
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    CONSTRAINT fk_alert_tx FOREIGN KEY (transaction_id) 
        REFERENCES transactions(transaction_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ====================================================================
-- Table 9: fraud_audit_log
-- Audit log capturing investigations and status changes
-- ====================================================================
CREATE TABLE fraud_audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL,
    old_status VARCHAR(20) NULL,
    new_status VARCHAR(20) NOT NULL,
    changed_by VARCHAR(50) NOT NULL DEFAULT 'System / Investigator',
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT NULL,
    CONSTRAINT fk_audit_alert FOREIGN KEY (alert_id) 
        REFERENCES fraud_alerts(alert_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;
