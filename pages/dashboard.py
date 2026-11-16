"""
FraudShield - Dashboard Page
Executive KPI metrics, risk distributions, alert velocity, and triggered rules overview.
All aggregations are retrieved directly from MySQL views and queries.
"""

import streamlit as st
import pandas as pd
from db_connection import query_df
from utils.helpers import format_currency, format_number, render_kpi, get_risk_badge, sanitize_dataframe

def render_dashboard_page():
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #F9FAFB;">
                🛡️ Executive Fraud Dashboard
            </h1>
            <p style="color: #9CA3AF; margin-top: 4px; font-size: 1rem;">
                Real-time transaction surveillance, risk classification, and alert monitoring powered by MySQL.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Fetch KPI metrics from MySQL view vw_fraud_dashboard
    try:
        df_dash = query_df("SELECT * FROM vw_fraud_dashboard;")
    except Exception as e:
        st.error(f"Failed to load dashboard data from MySQL: {e}")
        return

    if df_dash.empty:
        st.warning("No dashboard metrics available. Please run database setup.")
        return

    m = df_dash.iloc[0].to_dict()

    # 2. Render Top KPI Metric Cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_kpi("Total Transactions", format_number(m.get("total_transactions")), "All processed transactions", "#3B82F6")
    with kpi2:
        render_kpi("Total Volume", format_currency(m.get("total_transaction_value")), f"Avg: {format_currency(m.get('avg_transaction_value'))}", "#10B981")
    with kpi3:
        render_kpi("High Risk (60+)", format_number(m.get("high_risk_count")), f"Vol: {format_currency(m.get('high_risk_volume'))}", "#EF4444")
    with kpi4:
        render_kpi("Medium Risk (30-59)", format_number(m.get("medium_risk_count")), "Under surveillance", "#F59E0B")
    with kpi5:
        render_kpi("Fraud Alerts", format_number(m.get("total_fraud_alerts")), f"Pending: {m.get('pending_alerts')} | Inv: {m.get('investigating_alerts')}", "#8B5CF6")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Charts Section
    col_chart_left, col_chart_right = st.columns([1, 1])

    with col_chart_left:
        st.markdown("### 📊 Risk Classification Distribution")
        # Fetch risk distribution from MySQL
        df_risk = query_df("""
            SELECT 
                risk_level, 
                COUNT(*) AS transaction_count,
                ROUND(SUM(amount), 2) AS total_volume
            FROM transactions
            GROUP BY risk_level
            ORDER BY FIELD(risk_level, 'LOW', 'MEDIUM', 'HIGH');
        """)
        if not df_risk.empty:
            df_risk_display = df_risk.copy()
            df_risk_display['total_volume'] = df_risk_display['total_volume'].astype(float)
            st.bar_chart(
                df_risk_display.set_index("risk_level")["transaction_count"],
                color="#2563EB",
                use_container_width=True
            )
            # Metrics summary table
            st.dataframe(
                df_risk_display.rename(columns={
                    "risk_level": "Risk Level",
                    "transaction_count": "Transactions",
                    "total_volume": "Total Volume (₹)"
                }),
                hide_index=True,
                use_container_width=True
            )

    with col_chart_right:
        st.markdown("### ⚡ Most Frequently Triggered Fraud Rules")
        # Fetch from MySQL view vw_fraud_reason_analysis
        df_rules = query_df("""
            SELECT rule_name, times_triggered, configured_points
            FROM vw_fraud_reason_analysis
            WHERE times_triggered > 0
            ORDER BY times_triggered DESC;
        """)
        if not df_rules.empty:
            st.bar_chart(
                df_rules.set_index("rule_name")["times_triggered"],
                color="#EF4444",
                use_container_width=True
            )
            st.caption("Points per rule configured in MySQL `fraud_rules` table.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Timeline & Transaction Methods
    col_time, col_methods = st.columns([3, 2])

    with col_time:
        st.markdown("### 📅 Daily Transaction Volume & Suspicious Activity")
        df_daily = query_df("""
            SELECT 
                DATE(transaction_timestamp) AS tx_date,
                COUNT(*) AS total_count,
                SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
                SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_count
            FROM transactions
            GROUP BY DATE(transaction_timestamp)
            ORDER BY tx_date ASC;
        """)
        if not df_daily.empty:
            df_daily['tx_date'] = pd.to_datetime(df_daily['tx_date'])
            df_daily_chart = df_daily.set_index("tx_date")[["total_count", "high_risk_count", "medium_risk_count"]]
            st.line_chart(df_daily_chart, use_container_width=True)

    with col_methods:
        st.markdown("### 💳 Transaction Methods Breakdown")
        df_methods = query_df("""
            SELECT 
                transaction_method, 
                COUNT(*) AS count,
                SUM(CASE WHEN risk_level IN ('MEDIUM', 'HIGH') THEN 1 ELSE 0 END) AS flagged_count
            FROM transactions
            GROUP BY transaction_method
            ORDER BY count DESC;
        """)
        if not df_methods.empty:
            st.bar_chart(
                df_methods.set_index("transaction_method")[["count", "flagged_count"]],
                use_container_width=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. Recent High-Risk Transactions Table
    st.markdown("### 🚨 Recent Critical High-Risk Transactions")
    df_high = query_df("""
        SELECT 
            transaction_id AS `ID`,
            customer_name AS `Customer`,
            account_number AS `Account`,
            amount AS `Amount (₹)`,
            transaction_method AS `Method`,
            city AS `Location`,
            device_name AS `Device`,
            risk_score AS `Score`,
            risk_level AS `Risk Level`,
            alert_status AS `Alert Status`,
            transaction_timestamp AS `Timestamp`
        FROM vw_high_risk_transactions
        ORDER BY transaction_timestamp DESC
        LIMIT 10;
    """)

    if not df_high.empty:
        df_high_clean = sanitize_dataframe(df_high)
        st.dataframe(
            df_high_clean,
            hide_index=True,
            use_container_width=True
        )
        st.info("💡 To investigate root causes and see exact triggered rules with points breakdown, navigate to the **Investigation** page.")
    else:
        st.success("No High-Risk transactions found.")
