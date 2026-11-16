"""
FraudShield - Advanced Analytics & Fraud Intelligence Page
Deep aggregations and trend analysis performed directly inside MySQL:
temporal trends, geographic hotspots, payment method risk, rule breakdown, and hourly distribution.
"""

import streamlit as st
import pandas as pd
from db_connection import query_df
from utils.helpers import format_currency, format_number, sanitize_dataframe, render_kpi

def render_analytics_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #F9FAFB;">
                📈 Fraud Intelligence & Analytical Insights
            </h1>
            <p style="color: #9CA3AF; margin-top: 4px; font-size: 1rem;">
                Macro patterns, attack vectors, temporal peaks, and geographic risk correlation aggregated directly by MySQL.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Top Level Aggregate Metrics
    stat_df = query_df("""
        SELECT 
            COUNT(*) AS total_tx,
            AVG(amount) AS overall_avg_amount,
            AVG(CASE WHEN risk_level = 'HIGH' THEN amount ELSE NULL END) AS high_risk_avg_amount,
            AVG(CASE WHEN risk_level = 'LOW' THEN amount ELSE NULL END) AS low_risk_avg_amount,
            SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_tx_count,
            (SELECT COUNT(*) FROM fraud_alerts) AS total_alerts,
            (SELECT COUNT(*) FROM fraud_alerts WHERE alert_status IN ('Resolved', 'False Positive')) AS closed_alerts
        FROM transactions;
    """)

    if not stat_df.empty:
        s = stat_df.iloc[0].to_dict()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi("Overall Avg Transaction", format_currency(s.get("overall_avg_amount")), "Baseline across all transactions", "#3B82F6")
        with c2:
            render_kpi("High-Risk Avg Transaction", format_currency(s.get("high_risk_avg_amount")), "Suspicious value spike", "#EF4444")
        with c3:
            render_kpi("Low-Risk Avg Transaction", format_currency(s.get("low_risk_avg_amount")), "Legitimate daily spend", "#10B981")
        with c4:
            res_rate = (s.get("closed_alerts", 0) / s.get("total_alerts", 1)) * 100 if s.get("total_alerts", 0) > 0 else 0
            render_kpi("Alert Resolution Rate", f"{res_rate:.1f}%", f"{s.get('closed_alerts', 0)} of {s.get('total_alerts', 0)} closed", "#8B5CF6")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Section: Temporal Trends (Fraud Alerts & Transactions Over Time)
    st.markdown("### 📅 Temporal Trends: Daily Transaction Volume & Alert Velocity")
    st.caption("Aggregated daily activity trend from MySQL group by date:")

    daily_trend_df = query_df("""
        SELECT 
            DATE(t.transaction_timestamp) AS tx_date,
            COUNT(t.transaction_id) AS total_transactions,
            SUM(CASE WHEN t.risk_level IN ('MEDIUM', 'HIGH') THEN 1 ELSE 0 END) AS flagged_suspicious,
            COUNT(fa.alert_id) AS alerts_raised
        FROM transactions t
        LEFT JOIN fraud_alerts fa ON t.transaction_id = fa.transaction_id
        GROUP BY DATE(t.transaction_timestamp)
        ORDER BY tx_date ASC;
    """)

    if not daily_trend_df.empty:
        daily_trend_df["tx_date"] = pd.to_datetime(daily_trend_df["tx_date"]).dt.strftime("%Y-%m-%d")
        daily_chart_data = daily_trend_df.set_index("tx_date")[["total_transactions", "flagged_suspicious"]]
        daily_chart_data.columns = ["Total Transactions", "Flagged (Medium/High)"]
        st.line_chart(daily_chart_data, use_container_width=True)

    st.markdown("---")

    # 3. Section: Two Columns - Hourly Fraud Clock vs Payment Method Risk
    col_hour, col_method = st.columns([1, 1])

    with col_hour:
        st.markdown("### 🕒 Peak Suspicious Transaction Hours")
        st.caption("Hourly distribution of high & medium risk transactions in MySQL:")

        hourly_df = query_df("""
            SELECT 
                HOUR(transaction_timestamp) AS tx_hour,
                COUNT(*) AS total_count,
                SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
                SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_count
            FROM transactions
            GROUP BY HOUR(transaction_timestamp)
            ORDER BY tx_hour ASC;
        """)

        if not hourly_df.empty:
            hourly_df["Hour Label"] = hourly_df["tx_hour"].apply(lambda h: f"{h:02d}:00")
            hour_chart = hourly_df.set_index("Hour Label")[["high_risk_count", "medium_risk_count"]]
            hour_chart.columns = ["High Risk", "Medium Risk"]
            st.bar_chart(hour_chart, color=["#EF4444", "#F59E0B"], use_container_width=True)

    with col_method:
        st.markdown("### 💳 Risk by Payment Method")
        st.caption("Distribution of transaction methods linked to fraud alerts:")

        method_df = query_df("""
            SELECT 
                t.transaction_method AS `Method`,
                COUNT(t.transaction_id) AS `Total Transactions`,
                SUM(CASE WHEN t.risk_level = 'HIGH' THEN 1 ELSE 0 END) AS `High Risk`,
                COUNT(fa.alert_id) AS `Alerts Generated`,
                ROUND(AVG(t.risk_score), 1) AS `Avg Risk Score`
            FROM transactions t
            LEFT JOIN fraud_alerts fa ON t.transaction_id = fa.transaction_id
            GROUP BY t.transaction_method
            ORDER BY `Alerts Generated` DESC;
        """)

        if not method_df.empty:
            st.dataframe(method_df, use_container_width=True, hide_index=True)
            method_chart = method_df.set_index("Method")[["Alerts Generated", "High Risk"]]
            st.bar_chart(method_chart, color=["#8B5CF6", "#DC2626"], use_container_width=True)

    st.markdown("---")

    # 4. Section: Geographic Hotspots & Rule Effectiveness
    col_geo, col_rules = st.columns([1, 1])

    with col_geo:
        st.markdown("### 📍 Geographic Fraud Hotspots")
        st.caption("Cities with the highest density of high-risk transactions:")

        geo_df = query_df("""
            SELECT 
                l.city AS `City`,
                l.state AS `State`,
                COUNT(t.transaction_id) AS `Total Transactions`,
                SUM(CASE WHEN t.risk_level = 'HIGH' THEN 1 ELSE 0 END) AS `High Risk Count`,
                COUNT(fa.alert_id) AS `Alerts Raised`,
                ROUND(SUM(t.amount), 2) AS `Total Volume (₹)`
            FROM locations l
            JOIN transactions t ON l.location_id = t.location_id
            LEFT JOIN fraud_alerts fa ON t.transaction_id = fa.transaction_id
            GROUP BY l.location_id, l.city, l.state
            ORDER BY `High Risk Count` DESC, `Alerts Raised` DESC
            LIMIT 10;
        """)

        if not geo_df.empty:
            geo_display = geo_df.copy()
            geo_display["Total Volume (₹)"] = geo_display["Total Volume (₹)"].apply(format_currency)
            st.dataframe(geo_display, use_container_width=True, hide_index=True)

    with col_rules:
        st.markdown("### ⚡ Fraud Rule Trigger Breakdown")
        st.caption("From MySQL View `vw_fraud_reason_analysis`:")

        rules_breakdown_df = query_df("""
            SELECT 
                rule_name AS `Rule Name`,
                times_triggered AS `Times Triggered`,
                configured_points AS `Configured Points`,
                total_points_awarded AS `Total Points`,
                percentage_of_all_triggers AS `Share (%)`
            FROM vw_fraud_reason_analysis
            ORDER BY times_triggered DESC;
        """)

        if not rules_breakdown_df.empty:
            st.dataframe(rules_breakdown_df, use_container_width=True, hide_index=True)
            st.bar_chart(
                rules_breakdown_df.set_index("Rule Name")["Times Triggered"],
                color="#EF4444",
                use_container_width=True
            )

    st.markdown("---")

    # 5. High-Risk Customer Activity Leaderboard
    st.markdown("### 🚨 High-Risk Customer Surveillance Leaderboard")
    st.caption("Top customers categorized by accumulated fraud alerts and high-risk flags (from MySQL View `vw_customer_risk_summary`):")

    top_cust_df = query_df("""
        SELECT 
            customer_id AS `ID`,
            customer_name AS `Customer`,
            city AS `City`,
            total_transactions AS `Transactions`,
            total_spent AS `Total Spent (₹)`,
            high_risk_transactions AS `High-Risk Tx`,
            total_fraud_alerts AS `Alerts`,
            peak_risk_score AS `Peak Score`,
            avg_risk_score AS `Avg Score`
        FROM vw_customer_risk_summary
        WHERE high_risk_transactions > 0 OR total_fraud_alerts > 0
        ORDER BY high_risk_transactions DESC, total_fraud_alerts DESC, peak_risk_score DESC
        LIMIT 15;
    """)

    if not top_cust_df.empty:
        top_disp = top_cust_df.copy()
        top_disp["Total Spent (₹)"] = top_disp["Total Spent (₹)"].apply(format_currency)
        st.dataframe(top_disp, use_container_width=True, hide_index=True)
    else:
        st.info("No high-risk customer anomalies detected.")
