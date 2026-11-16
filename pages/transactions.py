"""
FraudShield - Transactions Page
Comprehensive transaction browser with parameterized filtering, detailed inspector,
and live re-analysis via MySQL stored procedures.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from db_connection import query_df, call_procedure
from utils.helpers import format_currency, format_number, sanitize_dataframe, get_risk_badge

def render_transactions_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #F9FAFB;">
                💳 Transaction Ledger & Surveillance
            </h1>
            <p style="color: #9CA3AF; margin-top: 4px; font-size: 1rem;">
                Browse, search, and inspect financial transactions with granular multi-criteria filtering.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Fetch metadata for filter dropdowns
    customers_df = query_df("SELECT customer_id, full_name FROM customers ORDER BY full_name ASC;")
    cust_options = ["All Customers"] + [f"{row['customer_id']} - {row['full_name']}" for _, row in customers_df.iterrows()]

    methods_df = query_df("SELECT DISTINCT transaction_method FROM transactions ORDER BY transaction_method ASC;")
    method_options = ["All Methods"] + methods_df["transaction_method"].tolist()

    statuses_df = query_df("SELECT DISTINCT transaction_status FROM transactions ORDER BY transaction_status ASC;")
    status_options = ["All Statuses"] + statuses_df["transaction_status"].tolist()

    # 2. Filter Bar
    with st.expander("🔍 Filter & Search Transactions", expanded=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)

        with fcol1:
            search_tx_id = st.text_input("Transaction ID", placeholder="e.g. 105 or leave blank")
            selected_cust = st.selectbox("Customer", cust_options)

        with fcol2:
            selected_risk = st.selectbox("Risk Level", ["All Risk Levels", "HIGH", "MEDIUM", "LOW"])
            selected_method = st.selectbox("Payment Method", method_options)

        with fcol3:
            selected_status = st.selectbox("Status", status_options)
            search_account = st.text_input("Account Number", placeholder="e.g. SBIN or leave blank")

        with fcol4:
            amt_range = st.slider("Amount Range (₹)", 0, 500000, (0, 500000), step=5000)

    # 3. Build dynamic parameterized MySQL query
    where_clauses = ["1=1"]
    params = []

    if search_tx_id.strip():
        try:
            tx_id_num = int(search_tx_id.strip())
            where_clauses.append("t.transaction_id = %s")
            params.append(tx_id_num)
        except ValueError:
            st.error("Transaction ID must be numeric.")

    if selected_cust != "All Customers":
        cust_id = int(selected_cust.split(" - ")[0])
        where_clauses.append("a.customer_id = %s")
        params.append(cust_id)

    if selected_risk != "All Risk Levels":
        where_clauses.append("t.risk_level = %s")
        params.append(selected_risk)

    if selected_method != "All Methods":
        where_clauses.append("t.transaction_method = %s")
        params.append(selected_method)

    if selected_status != "All Statuses":
        where_clauses.append("t.transaction_status = %s")
        params.append(selected_status)

    if search_account.strip():
        where_clauses.append("a.account_number LIKE %s")
        params.append(f"%{search_account.strip()}%")

    if amt_range:
        where_clauses.append("t.amount BETWEEN %s AND %s")
        params.extend([amt_range[0], amt_range[1]])

    sql_query = f"""
        SELECT 
            t.transaction_id AS `ID`,
            c.full_name AS `Customer`,
            a.account_number AS `Account`,
            t.amount AS `Amount`,
            t.transaction_type AS `Type`,
            t.transaction_method AS `Method`,
            t.transaction_timestamp AS `Timestamp`,
            l.city AS `Location`,
            COALESCE(d.device_name, 'None / POS') AS `Device`,
            t.transaction_status AS `Status`,
            t.risk_score AS `Score`,
            t.risk_level AS `Risk Level`
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        JOIN customers c ON a.customer_id = c.customer_id
        JOIN locations l ON t.location_id = l.location_id
        LEFT JOIN devices d ON t.device_id = d.device_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY t.transaction_timestamp DESC
        LIMIT 300;
    """

    df_results = query_df(sql_query, tuple(params))

    # 4. Display Results Summary & Table
    st.markdown(f"**Found {len(df_results)} transactions matching criteria** (capped at 300)")

    if not df_results.empty:
        df_clean = sanitize_dataframe(df_results)
        st.dataframe(
            df_clean,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="₹%.2f"),
                "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d")
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # 5. Transaction Inspector
        st.markdown("### 🔎 Quick Transaction Inspector")
        inspect_col1, inspect_col2 = st.columns([1, 2])

        with inspect_col1:
            tx_ids = df_results["ID"].tolist()
            selected_tx = st.selectbox("Select Transaction ID to inspect", tx_ids)
            
            bcol_a, bcol_b = st.columns(2)
            with bcol_a:
                # Action button to trigger MySQL analyze_transaction procedure
                if st.button("🔄 Re-Analyze via MySQL", use_container_width=True):
                    try:
                        call_procedure("analyze_transaction", [int(selected_tx)])
                        st.success(f"Transaction #{selected_tx} re-evaluated successfully via MySQL!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error executing analyze_transaction: {e}")
            with bcol_b:
                if st.button("🔍 Open Investigation Lab", type="primary", use_container_width=True):
                    st.session_state["investigate_tx_id"] = int(selected_tx)
                    st.session_state["nav_selection"] = "🔍 Investigation"
                    st.rerun()

        with inspect_col2:
            if selected_tx:
                # Fetch detailed rule matches for selected transaction
                df_matches = query_df("""
                    SELECT 
                        fr.rule_name AS `Rule Triggered`,
                        trm.points_awarded AS `Points`,
                        trm.match_reason AS `Detection Reason`,
                        trm.detected_at AS `Detected At`
                    FROM transaction_rule_matches trm
                    JOIN fraud_rules fr ON trm.rule_id = fr.rule_id
                    WHERE trm.transaction_id = %s;
                """, (int(selected_tx),))

                if not df_matches.empty:
                    st.markdown(f"**Rules Triggered for Transaction #{selected_tx}:**")
                    st.dataframe(sanitize_dataframe(df_matches), hide_index=True, use_container_width=True)
                else:
                    st.info(f"Transaction #{selected_tx} has a clean record (Score: 0 - No fraud rules triggered).")

                # Link to investigation
                st.caption(f"For complete customer history, device details, and alert resolution, navigate to the **Investigation** page with ID #{selected_tx}.")
    else:
        st.info("No transactions found matching the selected filter criteria.")
