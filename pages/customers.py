"""
FraudShield - Customers Profile & Risk Dossier Page
Comprehensive 360-degree customer profiling powered by MySQL stored procedure
`customer_risk_summary`, displaying account ownership, device footprint, and transaction habits.
"""

import streamlit as st
import pandas as pd
from db_connection import query_df, call_procedure
from utils.helpers import format_currency, format_number, sanitize_dataframe, get_risk_badge, render_kpi

def render_customers_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #F9FAFB;">
                👤 Customer Surveillance & Risk Dossier
            </h1>
            <p style="color: #9CA3AF; margin-top: 4px; font-size: 1rem;">
                Holistic 360-degree customer profiles, multi-account holdings, device footprint, and behavioral metrics.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Fetch Customers List for Dropdown and Filter
    cust_list_df = query_df("""
        SELECT c.customer_id, c.full_name, c.city, c.state, c.customer_status,
               COALESCE(rs.total_fraud_alerts, 0) AS alert_count,
               COALESCE(rs.high_risk_transactions, 0) AS high_risk_count
        FROM customers c
        LEFT JOIN vw_customer_risk_summary rs ON c.customer_id = rs.customer_id
        ORDER BY rs.high_risk_transactions DESC, rs.total_fraud_alerts DESC, c.full_name ASC;
    """)

    if cust_list_df.empty:
        st.warning("No customer records found in MySQL.")
        return

    # Filter Bar
    fcol1, fcol2 = st.columns([2, 1])
    with fcol1:
        # Pre-format options highlighting those with fraud alerts
        options = []
        for _, row in cust_list_df.iterrows():
            tag = " ⚠️ Flagged" if row["alert_count"] > 0 else ""
            options.append(f"{row['customer_id']} - {row['full_name']} ({row['city']}){tag}")

        selected_option = st.selectbox("Select Customer to Profile", options)
        selected_cust_id = int(selected_option.split(" - ")[0])

    with fcol2:
        search_kw = st.text_input("Quick Search by Name or City", placeholder="e.g. Rahul, Mumbai")
        if search_kw.strip():
            matching = cust_list_df[
                cust_list_df["full_name"].str.contains(search_kw.strip(), case=False, na=False) |
                cust_list_df["city"].str.contains(search_kw.strip(), case=False, na=False)
            ]
            if not matching.empty:
                st.caption(f"Found {len(matching)} matching customer(s).")
                selected_cust_id = int(matching.iloc[0]["customer_id"])

    # 2. Call MySQL Stored Procedure customer_risk_summary(customer_id)
    summary_dfs = call_procedure("customer_risk_summary", (selected_cust_id,))
    if not summary_dfs or summary_dfs[0].empty:
        st.error(f"Failed to load risk profile for Customer #{selected_cust_id}.")
        return

    cdata = summary_dfs[0].iloc[0].to_dict()

    # 3. Customer Header Card
    status_color = "#10B981" if cdata.get("customer_status") == "Active" else "#F59E0B"
    st.markdown(f"""
        <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 20px; margin-top: 12px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 0.85rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.05em;">Customer Dossier</span>
                    <h2 style="margin: 2px 0 0 0; color: #F9FAFB; font-size: 1.8rem; font-weight: 700;">
                        {cdata['full_name']} <span style="font-size: 1rem; color: #9CA3AF; font-weight: 400;">(ID: #{cdata['customer_id']})</span>
                    </h2>
                </div>
                <div style="margin-top: 8px;">
                    <span style="background: rgba(16, 185, 129, 0.1); color: {status_color}; border: 1px solid {status_color}; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;">
                        {cdata.get('customer_status', 'Active')} Account
                    </span>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 16px; padding-top: 14px; border-top: 1px solid #1F2937; font-size: 0.9rem; color: #9CA3AF;">
                <div><strong>Email:</strong> {cdata.get('email', 'N/A')}</div>
                <div><strong>Phone:</strong> {cdata.get('phone', 'N/A')}</div>
                <div><strong>Location:</strong> {cdata.get('city')}, {cdata.get('state')}</div>
                <div><strong>Total Accounts:</strong> {cdata.get('total_accounts', 0)}</div>
                <div><strong>Devices Registered:</strong> {cdata.get('registered_devices', 0)}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 4. KPI Row from MySQL Procedure
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_kpi("Total Transactions", format_number(cdata.get("total_transactions")), "Lifetime activity", "#3B82F6")
    with kpi2:
        render_kpi("Total Spend", format_currency(cdata.get("total_spent")), f"Avg: {format_currency(cdata.get('avg_transaction_amount'))}", "#10B981")
    with kpi3:
        render_kpi("Peak Risk Score", str(cdata.get("peak_risk_score", 0)), f"Avg Score: {cdata.get('avg_risk_score', 0)}", "#EF4444")
    with kpi4:
        render_kpi("High-Risk Tx", format_number(cdata.get("high_risk_transactions")), f"Medium: {cdata.get('medium_risk_transactions', 0)}", "#DC2626")
    with kpi5:
        render_kpi("Fraud Alerts", format_number(cdata.get("total_fraud_alerts")), "Flagged incidents", "#8B5CF6")

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. Accounts & Devices Tabs
    tab_accounts, tab_devices, tab_locations, tab_tx = st.tabs([
        "💳 Associated Bank Accounts", 
        "📱 Registered Devices", 
        "📍 Transaction Locations", 
        "🕒 Recent Ledger History"
    ])

    with tab_accounts:
        acc_df = query_df("""
            SELECT account_id, account_number, account_type, balance, account_status, opened_date
            FROM accounts
            WHERE customer_id = %s
            ORDER BY account_id ASC;
        """, [selected_cust_id])

        if not acc_df.empty:
            acc_display = acc_df.copy()
            acc_display["balance"] = acc_display["balance"].apply(format_currency)
            acc_display.rename(columns={
                "account_id": "Account ID",
                "account_number": "Account Number",
                "account_type": "Account Type",
                "balance": "Current Balance",
                "account_status": "Status",
                "opened_date": "Opened On"
            }, inplace=True)
            st.dataframe(acc_display, use_container_width=True, hide_index=True)
        else:
            st.info("No bank accounts registered for this customer.")

    with tab_devices:
        dev_df = query_df("""
            SELECT device_id, device_name, device_type, operating_system, trusted_status, first_used, last_used
            FROM devices
            WHERE customer_id = %s
            ORDER BY last_used DESC;
        """, [selected_cust_id])

        if not dev_df.empty:
            dev_display = dev_df.copy()
            dev_display["first_used"] = pd.to_datetime(dev_display["first_used"]).dt.strftime("%Y-%m-%d %H:%M")
            dev_display["last_used"] = pd.to_datetime(dev_display["last_used"]).dt.strftime("%Y-%m-%d %H:%M")
            dev_display.rename(columns={
                "device_id": "Device ID",
                "device_name": "Device Model / Name",
                "device_type": "Type",
                "operating_system": "OS",
                "trusted_status": "Trust Status",
                "first_used": "First Recorded",
                "last_used": "Last Activity"
            }, inplace=True)
            st.dataframe(dev_display, use_container_width=True, hide_index=True)
        else:
            st.info("No devices registered for this customer.")

    with tab_locations:
        loc_df = query_df("""
            SELECT l.city AS City, l.state AS State, l.country AS Country,
                   COUNT(t.transaction_id) AS `Transactions`,
                   SUM(t.amount) AS `Total Spent (₹)`
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN locations l ON t.location_id = l.location_id
            WHERE a.customer_id = %s
            GROUP BY l.location_id, l.city, l.state, l.country
            ORDER BY `Transactions` DESC;
        """, [selected_cust_id])

        if not loc_df.empty:
            loc_display = loc_df.copy()
            loc_display["Total Spent (₹)"] = loc_display["Total Spent (₹)"].apply(format_currency)
            st.dataframe(loc_display, use_container_width=True, hide_index=True)
        else:
            st.info("No location history available.")

    with tab_tx:
        cust_tx_df = query_df("""
            SELECT 
                t.transaction_id AS `Tx ID`,
                t.transaction_timestamp AS `Timestamp`,
                t.amount AS `Amount`,
                t.transaction_method AS `Method`,
                l.city AS `City`,
                t.transaction_status AS `Status`,
                t.risk_score AS `Score`,
                t.risk_level AS `Risk`
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN locations l ON t.location_id = l.location_id
            WHERE a.customer_id = %s
            ORDER BY t.transaction_timestamp DESC
            LIMIT 50;
        """, [selected_cust_id])

        if not cust_tx_df.empty:
            tx_disp = cust_tx_df.copy()
            tx_disp["Amount"] = tx_disp["Amount"].apply(format_currency)
            tx_disp["Timestamp"] = pd.to_datetime(tx_disp["Timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(tx_disp, use_container_width=True, hide_index=True)
        else:
            st.info("No transaction history recorded.")
