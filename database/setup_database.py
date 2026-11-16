"""
FraudShield - Automated Database Setup Script
Executes SQL scripts in proper dependency order, handles DELIMITER statements,
and analyzes all initial transactions directly in MySQL.
"""

import os
import sys
import re
import time
from pathlib import Path

# Ensure UTF-8 stdout encoding on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_connection import get_connection, get_db_credentials, call_procedure, query_df

def parse_sql_file(file_path):
    """
    Parses a SQL script file containing standard statements and DELIMITER blocks.
    Returns a list of executable SQL statement strings.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    statements = []
    current_delimiter = ";"
    buffer = []

    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()

        # Check for DELIMITER change
        if stripped.upper().startswith("DELIMITER"):
            parts = stripped.split()
            if len(parts) >= 2:
                current_delimiter = parts[1]
            continue

        # Skip comment-only lines if buffer is empty
        if not buffer and (stripped.startswith("--") or stripped.startswith("/*") or not stripped):
            continue

        buffer.append(line)

        # Check if line ends with current delimiter
        if stripped.endswith(current_delimiter):
            stmt = "\n".join(buffer)
            # Remove trailing delimiter
            if current_delimiter == ";":
                stmt = stmt.rstrip()
                if stmt.endswith(";"):
                    stmt = stmt[:-1]
            else:
                stmt = stmt.rstrip()
                if stmt.endswith(current_delimiter):
                    stmt = stmt[:-len(current_delimiter)]
            
            stmt = stmt.strip()
            if stmt:
                statements.append(stmt)
            buffer = []

    if buffer:
        stmt = "\n".join(buffer).strip()
        if stmt:
            statements.append(stmt)

    return statements

def execute_sql_file(conn, file_path):
    """
    Executes all statements in a parsed SQL file against the connection.
    """
    stmts = parse_sql_file(file_path)
    cursor = conn.cursor()
    success_count = 0
    for stmt in stmts:
        if not stmt.strip():
            continue
        try:
            cursor.execute(stmt)
            if cursor.with_rows:
                cursor.fetchall()
            success_count += 1
        except Exception as e:
            # Ignore harmless duplicate index or drop if not exists warnings
            err_msg = str(e)
            if "Duplicate key name" in err_msg or "Unknown table" in err_msg:
                continue
            print(f"Error executing statement in {file_path.name}:\n{stmt[:100]}...\nError: {e}")
            raise e
    conn.commit()
    cursor.close()
    return success_count

def run_database_setup():
    """
    Main orchestration function to initialize the entire database.
    """
    print("=" * 65)
    print("FraudShield: Initializing MySQL Database & Business Logic")
    print("=" * 65)

    base_dir = Path(__file__).resolve().parent

    sql_files = [
        base_dir / "01_schema.sql",
        base_dir / "02_sample_data.sql",
        base_dir / "03_functions.sql",
        base_dir / "04_procedures.sql",
        base_dir / "05_triggers.sql",
        base_dir / "06_views.sql",
        base_dir / "07_indexes.sql",
    ]

    # Step 1: Connect without specific DB to run 01_schema.sql (which creates the DB)
    print("\n[1/4] Connecting to MySQL server...")
    conn = get_connection(use_database=False)
    print("  [OK] Connected successfully.")

    # Step 2: Execute each SQL file in sequence
    print("\n[2/4] Executing SQL scripts in dependency order...")
    for sf in sql_files:
        if not sf.exists():
            print(f"  [X] Error: File not found: {sf}")
            return False
        print(f"  -> Running {sf.name}...")
        count = execute_sql_file(conn, sf)
        print(f"    [OK] {sf.name} completed ({count} statements).")

    conn.close()

    # Step 3: Run Procedure to Score and Classify All Transactions
    print("\n[3/4] Running MySQL Stored Procedure 'analyze_all_transactions()'...")
    start_time = time.time()
    call_procedure("analyze_all_transactions")
    elapsed = round(time.time() - start_time, 2)
    print(f"  [OK] Transaction analysis completed in {elapsed} seconds.")

    # Step 4: Verification and Summary
    print("\n[4/4] Verifying database records & risk distribution...")
    try:
        df_counts = query_df("""
            SELECT 
                (SELECT COUNT(*) FROM customers) AS customers,
                (SELECT COUNT(*) FROM accounts) AS accounts,
                (SELECT COUNT(*) FROM devices) AS devices,
                (SELECT COUNT(*) FROM locations) AS locations,
                (SELECT COUNT(*) FROM transactions) AS transactions,
                (SELECT COUNT(*) FROM fraud_rules) AS fraud_rules,
                (SELECT COUNT(*) FROM transaction_rule_matches) AS rule_matches,
                (SELECT COUNT(*) FROM fraud_alerts) AS fraud_alerts;
        """)
        counts = df_counts.iloc[0].to_dict()

        df_risk = query_df("""
            SELECT risk_level, COUNT(*) AS count, ROUND(SUM(amount), 2) AS total_amount
            FROM transactions
            GROUP BY risk_level
            ORDER BY FIELD(risk_level, 'LOW', 'MEDIUM', 'HIGH');
        """)

        print("\n--- DATABASE SUMMARY TABLE ---")
        for table, cnt in counts.items():
            print(f"  * {table.capitalize():<24}: {cnt}")

        print("\n--- TRANSACTION RISK DISTRIBUTION ---")
        print(df_risk.to_string(index=False))

        # Check conditions
        has_low = (df_risk['risk_level'] == 'LOW').any()
        has_med = (df_risk['risk_level'] == 'MEDIUM').any()
        has_high = (df_risk['risk_level'] == 'HIGH').any()

        if has_low and has_med and has_high and counts['fraud_alerts'] > 0:
            print("\n" + "=" * 65)
            print("[SUCCESS] FraudShield database is fully initialized and verified!")
            print("  All risk tiers (LOW, MEDIUM, HIGH) and alerts are operational.")
            print("=" * 65)
            return True
        else:
            print("\n[WARNING] Missing some risk categories or alerts.")
            return False

    except Exception as e:
        print(f"Error during verification: {e}")
        return False

if __name__ == "__main__":
    run_database_setup()
