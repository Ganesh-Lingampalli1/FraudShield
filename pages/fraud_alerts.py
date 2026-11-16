"""
FraudShield - Fraud Alerts Management Page
Surveillance queue for reviewing, filtering, and investigating generated fraud alerts.
Status transitions are executed directly via the MySQL stored procedure `update_alert_status`.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from db_connection import query_df, call_procedure
from utils.helpers import format_currency, format_number, sanitize_dataframe, get_risk_badge, get_status_badge, render_kpi

def render_fraud_alerts_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #F9FAFB;">
                🚨 Fraud Alert Center & Investigation Queue
            </h1>
            <p style="color: #9CA3AF; margin-top: 4px; font-size: 1rem;">
                Review flagged transactions, inspect risk justification, and update investigation statuses via MySQL procedures.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Fetch Alert Metrics for Top KPI Cards
    kpi_df = query_df("""
        SELECT 
            COUNT(*) AS total_alerts,
            SUM(CASE WHEN alert_status = 'Pending' THEN 1 ELSE 0 END) AS pending_alerts,
            SUM(CASE WHEN alert_status = 'Investigating' THEN 1 ELSE 0 END) AS investigating_alerts,
            SUM(CASE WHEN alert_status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_alerts,
            SUM(CASE WHEN alert_status = 'False Positive' THEN 1 ELSE 0 END) AS false_positive_alerts,
            SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_alerts
        FROM fraud_alerts;
    """)

    if not kpi_df.empty:
        k = kpi_df.iloc[0].to_dict()
        kcol1, kcol2, kcol3, kcol4, kcol5 = st.columns(5)
        with kcol1:
            render_kpi("Total Alerts", format_number(k.get("total_alerts")), "All flagged alerts", "#8B5CF6")
        with kcol2:
            render_kpi("Pending Action", format_number(k.get("pending_alerts")), "Awaiting review", "#EF4444")
        with kcol3:
            render_kpi("Under Investigation", format_number(k.get("investigating_alerts")), "Active case files", "#3B82F6")
        with kcol4:
            render_kpi("Resolved / Closed", format_number(k.get("resolved_alerts")), f"False Pos: {k.get('false_positive_alerts', 0)}", "#10B981")
        with kcol5:
            render_kpi("Critical High Risk", format_number(k.get("high_risk_alerts")), "Score >= 60", "#DC2626")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Filters Bar
    with st.expander("🔍 Filter Alert Queue", expanded=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            status_filter = st.selectbox("Alert Status", ["All Statuses", "Pending", "Investigating", "Resolved", "False Positive"])
        with fcol2:
            risk_filter = st.selectbox("Risk Level", ["All Risk Levels", "HIGH", "MEDIUM"])
        with fcol3:
            search_query = st.text_input("Search Alert ID / Tx ID / Customer", placeholder="e.g. 5 or Rahul")
        with fcol4:
            date_sort = st.selectbox("Sort By", ["Newest First", "Oldest First", "Highest Risk Score"])

    # 3. Build Parameterized Query
    where_clauses = ["1=1"]
    params = []

    if status_filter != "All Statuses":
        where_clauses.append("fa.alert_status = %s")
        params.append(status_filter)

    if risk_filter != "All Risk Levels":
        where_clauses.append("fa.risk_level = %s")
        params.append(risk_filter)

    if search_query.strip():
        q = f"%{search_query.strip()}%"
        where_clauses.append("(CAST(fa.alert_id AS CHAR) LIKE %s OR CAST(fa.transaction_id AS CHAR) LIKE %s OR c.full_name LIKE %s)")
        params.extend([q, q, q])

    order_clause = "ORDER BY fa.created_at DESC"
    if date_sort == "Oldest First":
        order_clause = "ORDER BY fa.created_at ASC"
    elif date_sort == "Highest Risk Score":
        order_clause = "ORDER BY fa.risk_score DESC, fa.created_at DESC"

    alerts_query = f"""
        SELECT 
            fa.alert_id AS `Alert ID`,
            fa.transaction_id AS `Tx ID`,
            c.full_name AS `Customer`,
            t.amount AS `Amount`,
            t.transaction_method AS `Method`,
            fa.risk_score AS `Score`,
            fa.risk_level AS `Risk Level`,
            fa.alert_reason AS `Reason`,
            fa.alert_status AS `Status`,
            fa.created_at AS `Created At`,
            fa.resolved_at AS `Resolved At`,
            fa.notes AS `Notes`
        FROM fraud_alerts fa
        JOIN transactions t ON fa.transaction_id = t.transaction_id
        JOIN accounts a ON t.account_id = a.account_id
        JOIN customers c ON a.customer_id = c.customer_id
        WHERE {' AND '.join(where_clauses)}
        {order_clause};
    """

    df_alerts = query_df(alerts_query, params)

    st.markdown(f"### 📋 Flagged Incidents Queue ({len(df_alerts)} records found)")

    if df_alerts.empty:
        st.info("No fraud alerts match the selected criteria.")
    else:
        # Display table
        df_display = df_alerts.copy()
        df_display["Amount"] = df_display["Amount"].apply(format_currency)
        df_display["Created At"] = pd.to_datetime(df_display["Created At"]).dt.strftime("%Y-%m-%d %H:%M")
        df_display["Resolved At"] = df_display["Resolved At"].apply(
            lambda x: pd.to_datetime(x).strftime("%Y-%m-%d %H:%M") if pd.notna(x) else "-"
        )

        st.dataframe(
            df_display[[
                "Alert ID", "Tx ID", "Customer", "Amount", "Method",
                "Score", "Risk Level", "Status", "Created At", "Resolved At", "Reason"
            ]],
            use_container_width=True,
            hide_index=True,
            height=320
        )

    st.markdown("---")

    # 4. Alert Investigation & Status Transition Panel
    st.markdown("### 🛠️ Alert Actions & Investigation Desk")
    st.caption("Change alert status by executing the MySQL stored procedure `update_alert_status(alert_id, new_status, notes)`.")

    alert_id_list = df_alerts["Alert ID"].tolist() if not df_alerts.empty else []
    
    # Also fetch all alert IDs if current filter is empty
    if not alert_id_list:
        all_ids_df = query_df("SELECT alert_id FROM fraud_alerts ORDER BY alert_id ASC;")
        alert_id_list = all_ids_df["alert_id"].tolist() if not all_ids_df.empty else []

    if alert_id_list:
        action_col1, action_col2 = st.columns([1, 1])

        with action_col1:
            selected_alert_id = st.selectbox(
                "Select Alert ID to Update / Inspect",
                alert_id_list,
                format_func=lambda x: f"Alert #{x}"
            )

            # Fetch details for the selected alert
            alert_detail = query_df("""
                SELECT 
                    fa.alert_id, fa.transaction_id, fa.risk_score, fa.risk_level, 
                    fa.alert_status, fa.alert_reason, fa.notes, fa.created_at, fa.resolved_at,
                    t.amount, c.full_name, a.account_number
                FROM fraud_alerts fa
                JOIN transactions t ON fa.transaction_id = t.transaction_id
                JOIN accounts a ON t.account_id = a.account_id
                JOIN customers c ON a.customer_id = c.customer_id
                WHERE fa.alert_id = %s;
            """, [selected_alert_id])

            if not alert_detail.empty:
                row = alert_detail.iloc[0].to_dict()
                st.markdown(f"""
                    <div style="background: #111827; padding: 16px; border-radius: 8px; border: 1px solid #1F2937; margin-top: 10px;">
                        <div style="font-weight: 600; font-size: 1.1rem; color: #F9FAFB;">
                            Alert #{row['alert_id']} &bull; Transaction #{row['transaction_id']}
                        </div>
                        <div style="color: #9CA3AF; font-size: 0.9rem; margin-top: 6px;">
                            <strong>Customer:</strong> {row['full_name']} &nbsp;|&nbsp;
                            <strong>Account:</strong> {row['account_number']}<br>
                            <strong>Amount:</strong> {format_currency(row['amount'])} &nbsp;|&nbsp;
                            <strong>Risk Score:</strong> {row['risk_score']} ({row['risk_level']})<br>
                            <strong>Current Status:</strong> {row['alert_status']}<br>
                            <strong>Reason:</strong> {row['alert_reason']}<br>
                            <strong>Prior Notes:</strong> {row['notes'] or 'None recorded'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Quick jump to Investigation Page
                if st.button(f"🔍 Open Transaction #{row['transaction_id']} in Investigation Lab", key="jump_inv"):
                    st.session_state["investigate_tx_id"] = int(row["transaction_id"])
                    st.session_state["nav_selection"] = "🔍 Investigation"
                    st.rerun()

        with action_col2:
            st.markdown("#### Transition Case Status")
            current_status = row["alert_status"] if not alert_detail.empty else "Pending"
            status_options = ["Pending", "Investigating", "Resolved", "False Positive"]
            status_index = status_options.index(current_status) if current_status in status_options else 0

            new_status = st.selectbox("New Investigation Status", status_options, index=status_index)
            investigator_notes = st.text_area(
                "Investigator Notes / Resolution Justification",
                value=row.get("notes") or "" if not alert_detail.empty else "",
                placeholder="Enter justification for resolving or marking as False Positive..."
            )

            if st.button("💾 Execute Status Transition in MySQL", type="primary"):
                try:
                    # Call MySQL stored procedure update_alert_status(p_alert_id, p_new_status, p_notes)
                    results = call_procedure("update_alert_status", (selected_alert_id, new_status, investigator_notes))
                    st.success(f"✅ Alert #{selected_alert_id} successfully updated to '{new_status}' in MySQL!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error calling update_alert_status: {e}")
    else:
        st.info("No alerts found in the database.")
