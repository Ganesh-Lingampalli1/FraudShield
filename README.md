# 🛡️ FraudShield – Fraud Transaction Detection & Risk Scoring System

**FraudShield** is an end-to-end, enterprise-styled financial transaction surveillance, fraud detection, and risk scoring system. 

The core philosophy of this project is **MySQL-First**: all critical business logic, baseline aggregations, fraud rule evaluations, explainable risk scoring, and alert lifecycle management are executed natively inside **MySQL 8.0** using stored procedures, stored functions, views, triggers, and indexed schema design. **Streamlit** serves as the interactive analytical and forensic dashboard interface.

---

## 📑 Table of Contents
1. [Project Overview](#-project-overview)
2. [Problem Statement](#-problem-statement)
3. [Technology Stack](#-technology-stack)
4. [System Architecture](#-system-architecture)
5. [Database Schema & ER Model](#-database-schema--er-model)
6. [Fraud Detection Rules & Risk Scoring](#-fraud-detection-rules--risk-scoring)
7. [MySQL Objects (Procedures, Functions, Views, Triggers)](#-mysql-objects)
8. [Installation & Setup Guide](#-installation--setup-guide)
9. [Application Pages & Capabilities](#-application-pages--capabilities)
10. [Trainer Demonstration Flow (Walkthrough Script)](#-trainer-demonstration-flow)

---

## 🎯 Project Overview

In electronic payment ecosystems, financial institutions process thousands of transactions per minute across web gateways, mobile apps, and point-of-sale terminals. Fraudsters exploit stolen credentials, SIM swap attacks, unauthorized devices, and automated bot scripts to drain accounts.

**FraudShield** implements an **explainable, rule-based fraud detection engine** directly inside relational database technology (MySQL). Rather than treating fraud scores as an opaque black box, every risk point awarded to a transaction is mapped directly to a triggered rule with forensic evidence preserved in junction history tables.

> ⚠️ **Educational Note**: This project is engineered for educational demonstration and relational database mastery; it should not be represented as an autonomous production banking fraud solution.

---

## ❓ Problem Statement

Modern data engineering and database administration courses often treat SQL as merely a passive storage query language. However, enterprise relational databases like MySQL offer robust procedural extensions (Stored Procedures, Stored Functions, CTEs, Window Functions, and Atomic Triggers) capable of running high-performance surveillance close to where the data resides.

FraudShield addresses:
1. **Explainability**: Why was a customer's ₹75,000 transaction flagged? (Answer: +30 High Amount +20 Untrusted Device +20 Unusual Location = 70 High Risk).
2. **Dynamic Configuration**: Allowing risk officers to tune point weights and toggle rules in MySQL tables without modifying or redeploying application code.
3. **Database-Driven Surveillance**: Eliminating application-level Python computation for core risk math so database administrators can inspect fraud directly via MySQL Workbench.

---

## 💻 Technology Stack

| Component | Technology | Role & Purpose |
|---|---|---|
| **Database Engine** | **MySQL 8.0+** | Stores all entities, enforces constraints, and executes all fraud scoring logic |
| **Database Development** | **MySQL Workbench / SQL Scripts** | Standardized, transactional DDL/DML scripts (01 through 08) |
| **Frontend Framework** | **Streamlit** | Analytical dashboard, investigation workbench, and filters |
| **Data Connector** | **mysql-connector-python** | Parameterized query execution, procedure calling, and pooling |
| **Data Processing** | **Pandas** | Tabular representation and DataFrame manipulation for UI components |
| **Styling** | **Custom CSS & HTML Badges** | Professional dark financial UI theme |

---

## 🏗️ System Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │             User / Fraud Investigator / Trainer         │
       └───────────────────────────┬────────────────────────────┘
                                   │ (Interactive UI)
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             Streamlit Web Application (app.py)          │
       │  ├─ Dashboard (pages/dashboard.py)                     │
       │  ├─ Transactions Ledger (pages/transactions.py)        │
       │  ├─ Alert Queue (pages/fraud_alerts.py)                │
       │  ├─ Investigation Lab (pages/investigation.py)         │
       │  ├─ Customer Dossier (pages/customers.py)              │
       │  ├─ Analytics Insights (pages/analytics.py)            │
       │  └─ Rules Console (pages/fraud_rules.py)               │
       └───────────────────────────┬────────────────────────────┘
                                   │ (Parameterized Queries & Procedures)
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │        MySQL Database Connector (db_connection.py)      │
       └───────────────────────────┬────────────────────────────┘
                                   │ (TCP Port 3306)
                                   ▼
 ╔════════════════════════════════════════════════════════════════════════╗
 ║                     MySQL DATABASE (fraudshield)                       ║
 ║                                                                        ║
 ║  ┌──────────────────────────────────────────────────────────────────┐  ║
 ║  │ Relational Tables                                                │  ║
 ║  │ • customers • accounts • devices • locations • transactions       │  ║
 ║  │ • fraud_rules • transaction_rule_matches • fraud_alerts • audit  │  ║
 ║  └─────────────────────────────────┬────────────────────────────────┘  ║
 ║                                    │                                   ║
 ║  ┌─────────────────────────────────▼────────────────────────────────┐  ║
 ║  │ Business Logic & Risk Engine Layer                              │  ║
 ║  │ • Stored Function:   get_risk_level(score)                       │  ║
 ║  │ • Stored Function:   get_customer_historical_avg()               │  ║
 ║  │ • Stored Function:   is_location_unusual()                       │  ║
 ║  │ • Stored Procedure:  analyze_transaction(tx_id)                  │  ║
 ║  │ • Stored Procedure:  analyze_all_transactions()                  │  ║
 ║  │ • Stored Procedure:  update_alert_status(alert_id, status, notes)│  ║
 ║  │ • Stored Procedure:  customer_risk_summary(cust_id)              │  ║
 ║  │ • Trigger:           trg_transactions_before_insert              │  ║
 ║  │ • Views:             vw_fraud_dashboard, vw_recent_alerts, etc.  │  ║
 ║  └──────────────────────────────────────────────────────────────────┘  ║
 ╚════════════════════════════════════════════════════════════════════════╝
```

---

## 🗄️ Database Schema & ER Model

The database contains 9 structured tables:

### 1. `customers`
Stores primary customer identities:
- `customer_id` (PK), `full_name`, `email` (UNIQUE), `phone` (UNIQUE), `date_of_birth`, `city`, `state`, `country`, `customer_status`, `created_at`.

### 2. `accounts`
Financial bank accounts tied to customers:
- `account_id` (PK), `customer_id` (FK -> customers), `account_number` (UNIQUE), `account_type` (Savings/Checking/Credit), `balance`, `account_status`, `opened_date`.

### 3. `devices`
Hardware footprint registered or used by customers:
- `device_id` (PK), `customer_id` (FK -> customers), `device_name`, `device_type` (Mobile/Desktop/Tablet), `operating_system`, `first_used`, `last_used`, `trusted_status` (Trusted/Untrusted/Suspicious).

### 4. `locations`
Geographic master table for physical and IP resolution:
- `location_id` (PK), `city`, `state`, `country`, `latitude`, `longitude`.

### 5. `transactions`
Core financial ledger storing every transaction event:
- `transaction_id` (PK), `account_id` (FK -> accounts), `amount`, `transaction_type` (Purchase/Transfer/Withdrawal), `transaction_method` (UPI/Credit Card/Debit Card/Net Banking/ATM), `transaction_timestamp`, `location_id` (FK -> locations), `device_id` (FK -> devices), `transaction_status` (Completed/Failed/Declined), `merchant_name`, `risk_score` (DEFAULT 0), `risk_level` (DEFAULT 'LOW'), `analyzed_at`.

### 6. `fraud_rules`
Configurable rules database defining score weights:
- `rule_id` (PK), `rule_code` (UNIQUE), `rule_name`, `description`, `risk_points`, `active_status` (T/F), `created_at`, `updated_at`.

### 7. `transaction_rule_matches`
Junction and forensic audit table recording which rules were triggered for each transaction:
- `match_id` (PK), `transaction_id` (FK -> transactions), `rule_id` (FK -> fraud_rules), `points_awarded`, `match_reason`, `detected_at`.

### 8. `fraud_alerts`
Active incident management queue for security officers:
- `alert_id` (PK), `transaction_id` (FK -> transactions, UNIQUE), `risk_score`, `risk_level`, `alert_reason`, `alert_status` (Pending/Investigating/Resolved/False Positive), `created_at`, `resolved_at`, `notes`.

### 9. `fraud_audit_log`
Chronological audit trail of investigation status transitions:
- `log_id` (PK), `alert_id` (FK -> fraud_alerts), `old_status`, `new_status`, `changed_by`, `changed_at`, `notes`.

---

## ⚡ Fraud Detection Rules & Risk Scoring

FraudShield implements 6 configurable detection rules:

| Rule Code | Rule Name | Points | SQL Detection Logic & Evidence |
|---|---|:---:|---|
| **`HIGH_AMOUNT`** | Unusually High Transaction | **+30** | Compares transaction amount with the customer's historical average spend (excluding the current transaction). Triggers if amount is $\ge 3\times$ baseline (and $\ge ₹15,000$). |
| **`NEW_DEVICE`** | New or Untrusted Device | **+20** | Triggers if the transaction is executed from an unrecognized device, a device with `trusted_status IN ('Untrusted', 'Suspicious')`, or a device first seen within the past 2 hours. |
| **`UNUSUAL_LOCATION`** | Unusual Transaction Location | **+20** | Uses MySQL function `is_location_unusual()` to verify if the customer has ever transacted from this location before. |
| **`RAPID_TRANSACTIONS`** | Rapid Velocity Spike | **+15** | Detects multiple transactions executed on the same account within a sliding 10-minute time window. |
| **`LATE_NIGHT_TRANSACTION`** | Late-Night Operation | **+10** | Flags transactions executed between midnight (**00:00:00**) and **04:00:00 AM**. |
| **`MULTIPLE_FAILED_TRANSACTIONS`**| Preceding Failed Attempts | **+15** | Identifies accounts having 2 or more failed or declined transactions within the preceding 2 hours. |

### Risk Classification Thresholds
- **0 – 29 Points**: `LOW` Risk (Standard legitimate traffic)
- **30 – 59 Points**: `MEDIUM` Risk (Surveillance alert raised)
- **60+ Points**: `HIGH` Risk (Critical fraud alert requiring immediate action)

---

## 🛠️ MySQL Objects

### Stored Functions
1. `get_risk_level(p_score INT)`: Returns 'LOW', 'MEDIUM', or 'HIGH' based on configurable point boundaries.
2. `get_customer_historical_avg(p_customer_id, p_tx_timestamp, p_current_tx_id)`: Calculates historical spending baseline without contaminating it with the current transaction.
3. `is_location_unusual(p_customer_id, p_location_id, p_tx_timestamp)`: Returns `1` if the customer has no prior transactions in this city.

### Stored Procedures
1. `analyze_transaction(IN p_transaction_id INT)`:
   - Evaluates active rules in `fraud_rules`.
   - Populates junction table `transaction_rule_matches`.
   - Computes total risk score and classifies risk level.
   - Upserts or resolves records in `fraud_alerts`.
   - Fully idempotent (safe to re-run).
2. `analyze_all_transactions()`: Cursor-based batch evaluation iterating through every ledger record.
3. `update_alert_status(IN p_alert_id INT, IN p_new_status VARCHAR(20), IN p_notes TEXT)`: Transitions alert state and records audit log.
4. `customer_risk_summary(IN p_customer_id INT)`: Returns 360-degree customer profile with aggregated risk metrics.

### Views
- `vw_fraud_dashboard`: High-level executive KPI metrics.
- `vw_high_risk_transactions`: Filtered view of all transactions with score $\ge 60$.
- `vw_recent_fraud_alerts`: Alert queue joined with customer and transaction metadata.
- `vw_customer_risk_summary`: Multi-table analytical aggregation per customer.
- `vw_fraud_reason_analysis`: Frequency and percentage share of triggered fraud rules.

---

## 🚀 Installation & Setup Guide

### 1. Prerequisites
- **Python 3.10+**
- **MySQL Server 8.0+** running locally (or remote server)

### 2. Configure MySQL Credentials
Edit or create `.streamlit/secrets.toml`:
```toml
[mysql]
host = "localhost"
port = 3306
user = "root"
password = "YOUR_MYSQL_PASSWORD"
database = "fraudshield"
```

### 3. Initialize the Database
Run the automated Python database setup script (which creates the database, schema, sample data, functions, procedures, triggers, views, and indexes):
```bash
python database/setup_database.py
```

*Alternatively, execute SQL files in MySQL Workbench in numerical order:*
1. `database/01_schema.sql`
2. `database/02_sample_data.sql`
3. `database/03_functions.sql`
4. `database/04_procedures.sql`
5. `database/05_triggers.sql`
6. `database/06_views.sql`
7. `database/07_indexes.sql`
8. `database/08_analysis_queries.sql`

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch FraudShield Streamlit Application
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## 🖥️ Application Pages & Capabilities

1. **🛡️ Dashboard (`pages/dashboard.py`)**:
   - Executive KPIs: Total Transactions, Total Volume, High-Risk Count, Medium-Risk Count, Active Alerts.
   - Real-time charts: Risk Classification Distribution and Top Triggered Rules.
2. **💳 Transactions Ledger (`pages/transactions.py`)**:
   - Multi-criteria parameterized search (Customer, Risk Level, Method, Status, Amount Slider).
   - Direct inspector with quick link to Investigation Lab.
3. **🚨 Fraud Alerts Queue (`pages/fraud_alerts.py`)**:
   - Incident queue with filters for Pending, Investigating, Resolved, and False Positive.
   - Status transition desk invoking `update_alert_status` stored procedure.
4. **🔍 Forensic Investigation Lab (`pages/investigation.py`)**:
   - The flagship page showing **explainable risk scoring breakdown** (+30 High Amount, +20 New Device, etc.).
   - Baseline multiplier comparison, device trust details, geolocation coordinates, and 3-hour velocity window.
   - Button to trigger live re-analysis via `CALL analyze_transaction()`.
5. **👤 Customer Surveillance (`pages/customers.py`)**:
   - 360-degree risk profile backed by `customer_risk_summary()` procedure.
   - Accounts, registered devices, location history, and recent ledger activity.
6. **📈 Analytics Insights (`pages/analytics.py`)**:
   - Temporal transaction volume vs fraud alerts over time.
   - Hourly distribution showing late-night spike patterns.
   - Geographic hotspots and payment method risk correlation.
7. **⚙️ Fraud Rules Configuration (`pages/fraud_rules.py`)**:
   - Interactive point tuning and rule active/inactive toggles.
   - Single-click batch re-evaluation button calling `CALL analyze_all_transactions()`.

---

## 🎓 Trainer Demonstration Flow

Follow this script to demonstrate the project:

1. **Demonstrate Database Architecture (Workbench or Terminal)**:
   - Show MySQL tables, functions, and procedures:
     ```sql
     USE fraudshield;
     SHOW TABLES;
     SHOW PROCEDURE STATUS WHERE Db = 'fraudshield';
     ```
2. **Open the Dashboard**:
   - Point out that all KPI cards and charts query MySQL views (`vw_fraud_dashboard` and `vw_fraud_reason_analysis`).
3. **Navigate to Forensic Investigation Lab**:
   - Click quick-select pill for a High-Risk transaction (e.g. Tx #105).
   - Highlight the **Explainable Scoring Engine**: explain how MySQL parsed the customer's historical average spend and device status, inserted records into `transaction_rule_matches`, and calculated the total score.
4. **Demonstrate Fraud Alert Resolution**:
   - Go to **Fraud Alerts**, select an open alert, change status to **Investigating** or **Resolved**, add notes, and click "Execute Status Transition".
   - Show that the update was performed by calling the stored procedure `update_alert_status`, updating the `fraud_audit_log` table.
5. **Demonstrate Dynamic Rule Weight Modification**:
   - Navigate to **Fraud Rules**.
   - Change `LATE_NIGHT_TRANSACTION` points from `10` to `25`.
   - Click **Save Rule to MySQL**.
   - Click **Run analyze_all_transactions()** and watch MySQL re-score all 596 transactions in ~1 second!
   - Return to the Dashboard to see the risk distribution dynamically update.

---
*Built with ❤️ for educational excellence in MySQL & Financial Analytics.*
