"""
FraudShield - Database Connection & Execution Layer
Handles MySQL connection pooling, credentials resolution, query execution,
and procedure invocation with parameterized safety.
"""

import os
import pathlib
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None
import mysql.connector
from mysql.connector import Error, errorcode
import pandas as pd

# Optional Streamlit import for secrets
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

def get_db_credentials():
    """
    Resolves MySQL connection parameters with fallback priority:
    1. streamlit.secrets['mysql'] (if available inside Streamlit runtime)
    2. .streamlit/secrets.toml directly (for CLI/scripts)
    3. Environment variables (MYSQL_HOST, MYSQL_PORT, etc.)
    4. Safe localhost defaults
    """
    creds = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "fraudshield"
    }

    # 1. Try Streamlit runtime secrets
    if HAS_STREAMLIT:
        try:
            if hasattr(st, "secrets") and "mysql" in st.secrets:
                mysql_sec = st.secrets["mysql"]
                for k in creds:
                    if k in mysql_sec:
                        creds[k] = mysql_sec[k]
                return creds
        except Exception:
            pass

    # 2. Try parsing .streamlit/secrets.toml manually
    secrets_path = pathlib.Path(__file__).parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import toml
            data = toml.load(str(secrets_path))
            if "mysql" in data:
                creds.update(data["mysql"])
                return creds
        except Exception:
            # Simple fallback line-by-line parser if toml not installed
            try:
                with open(secrets_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            k, v = line.split("=", 1)
                            k = k.strip().lower()
                            v = v.strip().strip('"').strip("'")
                            if k == "port":
                                creds[k] = int(v)
                            elif k in creds:
                                creds[k] = v
                return creds
            except Exception:
                pass

    # 3. Environment variables
    creds["host"] = os.getenv("MYSQL_HOST", creds["host"])
    creds["port"] = int(os.getenv("MYSQL_PORT", creds["port"]))
    creds["user"] = os.getenv("MYSQL_USER", creds["user"])
    creds["password"] = os.getenv("MYSQL_PASSWORD", creds["password"])
    creds["database"] = os.getenv("MYSQL_DATABASE", creds["database"])

    return creds

def get_connection(use_database=True):
    """
    Establishes and returns an active MySQL connection.
    Set use_database=False when initializing or creating the database itself.
    """
    creds = get_db_credentials()
    config = {
        "host": creds["host"],
        "port": creds["port"],
        "user": creds["user"],
        "password": creds["password"],
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False
    }
    if use_database and creds.get("database"):
        config["database"] = creds["database"]

    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        raise err

def test_connection():
    """
    Validates MySQL connection and returns (success: bool, info/error: str).
    """
    try:
        conn = get_connection(use_database=False)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, f"Connected to MySQL {version}"
    except Error as e:
        return False, str(e)

def query_df(query, params=None):
    """
    Executes a SELECT query with parameters and returns a clean pandas DataFrame
    directly from cursor results without triggering DBAPI2 warnings.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(rows)
    finally:
        conn.close()

def query_row(query, params=None):
    """
    Executes a query and returns the first row as a dictionary.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()

def query_scalar(query, params=None):
    """
    Executes a query and returns a single scalar value.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None
    finally:
        conn.close()

def query_all(query, params=None):
    """
    Executes a query and returns all rows as a list of dictionaries.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()

def execute_dml(query, params=None):
    """
    Executes an INSERT, UPDATE, or DELETE query and commits.
    Returns (rows_affected, last_insert_id).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        affected = cursor.rowcount
        last_id = cursor.lastrowid
        cursor.close()
        return affected, last_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def call_procedure(proc_name, args=()):
    """
    Calls a MySQL Stored Procedure safely.
    Returns list of result set DataFrames (if any).
    """
    conn = get_connection()
    dfs = []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(proc_name, args)
        conn.commit()
        for result in cursor.stored_results():
            rows = result.fetchall()
            if rows:
                dfs.append(pd.DataFrame(rows))
            else:
                dfs.append(pd.DataFrame())
        cursor.close()
        return dfs
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
