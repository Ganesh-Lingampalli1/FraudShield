"""
FraudShield - Forensic Investigation Page
Deep-dive forensic inspection of individual transactions.
Shows genuine explainable risk scoring retrieved directly from MySQL junction table
`transaction_rule_matches`, customer baselines, device metadata, and geolocation.
"""

import streamlit as st
import pandas as pd
from db_connection import query_df, query_row, call_procedure
from utils.helpers import format_currency, format_number, sanitize_dataframe, get_risk_badge, get_status_badge

def render_investigation_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #F9FAFB;">
                🔍 Forensic Transaction Investigation Lab
            </h1>
            <p style="color: #9CA3AF; margin-top: 4px; font-size: 1rem;">
                Detailed audit trail explaining exactly why a transaction was flagged, powered by MySQL stored procedures.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Transaction Selection
    # Check if a transaction ID was forwarded from other pages
    default_tx = st.session_state.get("investigate_tx_id", None)

    # Quick selection pills for suspicious transactions
    high_risk_samples = query_df("""
        SELECT t.transaction_id, c.full_name, t.amount, t.risk_score, t.risk_level
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        JOIN customers c ON a.customer_id = c.customer_id
        WHERE t.risk_level IN ('HIGH', 'MEDIUM')
        ORDER BY t.risk_score DESC, t.transaction_id ASC
        LIMIT 10;
    """)

    st.markdown("#### ⚡ Quick Select Suspicious Transactions")
    if not high_risk_samples.empty:
        pill_cols = st.columns(min(len(high_risk_samples), 5))
        for idx, row in high_risk_samples.head(5).iterrows():
            col_idx = idx % 5
            badge_color = "#DC2626" if row["risk_level"] == "HIGH" else "#D97706"
            label = f"Tx #{row['transaction_id']} (Score: {row['risk_score']})"
            if pill_cols[col_idx].button(label, key=f"quick_tx_{row['transaction_id']}"):
                default_tx = int(row["transaction_id"])
                st.session_state["investigate_tx_id"] = default_tx

    sel_col1, sel_col2, sel_col3 = st.columns([2, 1, 1])
    with sel_col1:
        tx_input = st.number_input(
            "Enter Transaction ID to Inspect",
            min_value=1,
            value=int(default_tx) if default_tx else 1,
            step=1
        )
    with sel_col2:
        st.write("")
        st.write("")
        load_btn = st.button("🔎 Load Investigation Case", type="primary", use_container_width=True)
    with sel_col3:
        st.write("")
        st.write("")
        reanalyze_btn = st.button("⚡ Re-run MySQL Risk Engine", use_container_width=True)

    target_tx_id = int(tx_input)

    # Handle Re-analyze button click
    if reanalyze_btn:
        try:
            call_procedure("analyze_transaction", (target_tx_id,))
            st.success(f"Transaction #{target_tx_id} successfully re-analyzed via `CALL analyze_transaction({target_tx_id})`!")
        except Exception as e:
            st.error(f"Error re-analyzing transaction: {e}")

    # 2. Fetch Comprehensive Transaction Record
    tx_sql = """
        SELECT 
            t.transaction_id,
            t.account_id,
            t.amount,
            t.transaction_type,
            t.transaction_method,
            t.transaction_timestamp,
            t.transaction_status,
            t.merchant_name,
            t.risk_score,
            t.risk_level,
            t.location_id,
            t.device_id,
            a.account_number,
            a.account_type,
            a.balance,
            c.customer_id,
            c.full_name AS customer_name,
            c.email AS customer_email,
            c.phone AS customer_phone,
            c.city AS customer_home_city,
            d.device_name,
            d.device_type,
            d.operating_system,
            d.trusted_status,
            d.first_used AS device_first_used,
            d.last_used AS device_last_used,
            l.city AS tx_city,
            l.state AS tx_state,
            l.country AS tx_country,
            l.latitude,
            l.longitude
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        JOIN customers c ON a.customer_id = c.customer_id
        JOIN locations l ON t.location_id = l.location_id
        LEFT JOIN devices d ON t.device_id = d.device_id
        WHERE t.transaction_id = %s;
    """

    tx_data = query_row(tx_sql, [target_tx_id])

    if not tx_data:
        st.warning(f"Transaction #{target_tx_id} does not exist in the database.")
        return

    # Fetch Alert Record if any
    alert_data = query_row("""
        SELECT alert_id, risk_score, risk_level, alert_reason, alert_status, created_at, resolved_at, notes
        FROM fraud_alerts
        WHERE transaction_id = %s;
    """, [target_tx_id])

    # Fetch Rule Matches directly from transaction_rule_matches junction table
    matches_df = query_df("""
        SELECT 
            fr.rule_name AS `Rule Triggered`,
            fr.rule_code AS `Rule Code`,
            trm.points_awarded AS `Points`,
            trm.match_reason AS `Reason / Finding`,
            trm.detected_at AS `Evaluated At`
        FROM transaction_rule_matches trm
        JOIN fraud_rules fr ON trm.rule_id = fr.rule_id
        WHERE trm.transaction_id = %s
        ORDER BY trm.points_awarded DESC;
    """, [target_tx_id])

    # Fetch Customer Historical Average using stored function or aggregation query
    hist_avg_df = query_df("""
        SELECT get_customer_historical_avg(%s, %s, %s) AS hist_avg;
    """, [tx_data["customer_id"], tx_data["transaction_timestamp"], target_tx_id])
    historical_avg = hist_avg_df.iloc[0]["hist_avg"] if not hist_avg_df.empty else 0.0

    st.markdown("---")

    # 3. Header Summary Banner
    risk_level = tx_data["risk_level"]
    risk_badge = get_risk_badge(risk_level, tx_data["risk_score"])
    status_badge = get_status_badge(alert_data["alert_status"]) if alert_data else "<span style='color: #9CA3AF;'>No Alert</span>"

    st.markdown(f"""
        <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 20px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 0.9rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.05em;">Transaction Dossier</span>
                    <h2 style="margin: 4px 0 0 0; color: #F9FAFB; font-size: 1.8rem; font-weight: 700;">
                        Tx #{tx_data['transaction_id']} &bull; {tx_data['customer_name']}
                    </h2>
                </div>
                <div style="display: flex; gap: 12px; align-items: center; margin-top: 8px;">
                    <div>{risk_badge}</div>
                    <div>{status_badge}</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #1F2937;">
                <div>
                    <span style="color: #9CA3AF; font-size: 0.8rem;">TRANSACTION AMOUNT</span>
                    <div style="color: #F9FAFB; font-size: 1.25rem; font-weight: 700;">{format_currency(tx_data['amount'])}</div>
                </div>
                <div>
                    <span style="color: #9CA3AF; font-size: 0.8rem;">ACCOUNT</span>
                    <div style="color: #F9FAFB; font-size: 1rem; font-weight: 600;">{tx_data['account_number']} ({tx_data['account_type']})</div>
                </div>
                <div>
                    <span style="color: #9CA3AF; font-size: 0.8rem;">TIMESTAMP</span>
                    <div style="color: #F9FAFB; font-size: 1rem; font-weight: 600;">{pd.to_datetime(tx_data['transaction_timestamp']).strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div>
                    <span style="color: #9CA3AF; font-size: 0.8rem;">METHOD & STATUS</span>
                    <div style="color: #F9FAFB; font-size: 1rem; font-weight: 600;">{tx_data['transaction_method']} &bull; {tx_data['transaction_status']}</div>
                </div>
                <div>
                    <span style="color: #9CA3AF; font-size: 0.8rem;">MERCHANT</span>
                    <div style="color: #F9FAFB; font-size: 1rem; font-weight: 600;">{tx_data['merchant_name'] or 'N/A'}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 4. Two-Column Layout: Left = Risk Justification (Explainable Scoring), Right = Environmental Context
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("### ⚖️ Explainable Risk Scoring Engine")
        st.caption("Points breakdown calculated by MySQL stored procedure from configured `fraud_rules`:")

        if matches_df.empty:
            st.success("✅ **Clean Transaction**: No fraud rules were triggered by the MySQL risk engine. Risk score = 0 (LOW).")
        else:
            # Render explainable breakdown table
            score_rows = ""
            total_calc = 0
            for _, r in matches_df.iterrows():
                total_calc += int(r["Points"])
                score_rows += f"""
                    <tr style="border-bottom: 1px solid #1F2937;">
                        <td style="padding: 10px; font-weight: 600; color: #F9FAFB;">{r['Rule Triggered']}</td>
                        <td style="padding: 10px; color: #9CA3AF; font-size: 0.85rem;">{r['Reason / Finding']}</td>
                        <td style="padding: 10px; text-align: right; font-weight: 700; color: #EF4444; font-size: 1rem;">+{r['Points']}</td>
                    </tr>
                """

            score_table_html = f"""
                <table style="width: 100%; border-collapse: collapse; background: #111827; border-radius: 8px; overflow: hidden; border: 1px solid #1F2937;">
                    <thead>
                        <tr style="background: #1F2937; text-align: left; color: #9CA3AF; font-size: 0.8rem; text-transform: uppercase;">
                            <th style="padding: 10px;">Rule Name</th>
                            <th style="padding: 10px;">Forensic Evidence</th>
                            <th style="padding: 10px; text-align: right;">Points</th>
                        </tr>
                    </thead>
                    <tbody>
                        {score_rows}
                        <tr style="background: #1E293B; font-weight: 700;">
                            <td colspan="2" style="padding: 12px; color: #F9FAFB; font-size: 1rem;">TOTAL RISK SCORE (Sum)</td>
                            <td style="padding: 12px; text-align: right; color: #F87171; font-size: 1.2rem;">{total_calc}</td>
                        </tr>
                        <tr style="background: #0F172A;">
                            <td colspan="2" style="padding: 10px; color: #9CA3AF; font-size: 0.85rem;">CLASSIFICATION TIER</td>
                            <td style="padding: 10px; text-align: right;">{risk_badge}</td>
                        </tr>
                    </tbody>
                </table>
            """
            st.markdown(score_table_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Baseline Comparison Card
        st.markdown("#### 📊 Customer Spending Baseline Analysis")
        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            st.metric("Historical Avg Spend", format_currency(historical_avg))
        with bcol2:
            st.metric("Current Tx Amount", format_currency(tx_data["amount"]))
        with bcol3:
            ratio = (float(tx_data["amount"]) / float(historical_avg)) if float(historical_avg) > 0 else 0
            st.metric("Multiplier vs Baseline", f"{ratio:.1f}x" if ratio > 0 else "N/A")

        if alert_data:
            st.markdown("#### 🚨 Alert Status & Notes")
            st.markdown(f"""
                <div style="background: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 14px;">
                    <div><strong>Alert ID:</strong> #{alert_data['alert_id']} &bull; <strong>Status:</strong> {alert_data['alert_status']}</div>
                    <div style="margin-top: 6px; color: #9CA3AF;"><strong>Flagged Reason:</strong> {alert_data['alert_reason']}</div>
                    <div style="margin-top: 6px; color: #9CA3AF;"><strong>Investigator Notes:</strong> {alert_data['notes'] or 'None'}</div>
                    <div style="margin-top: 6px; font-size: 0.8rem; color: #6B7280;">Flagged: {pd.to_datetime(alert_data['created_at']).strftime('%Y-%m-%d %H:%M')}</div>
                </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 📱 Device Intelligence")
        dev_trusted = tx_data.get("trusted_status")
        dev_badge = f"<span style='color: {'#10B981' if dev_trusted == 'Trusted' else '#EF4444'}; font-weight: 600;'>{dev_trusted or 'Unknown'}</span>"
        
        st.markdown(f"""
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <div style="font-weight: 600; font-size: 1rem; color: #F9FAFB;">
                    {tx_data.get('device_name') or 'Unregistered / Web Browser'}
                </div>
                <div style="color: #9CA3AF; font-size: 0.85rem; margin-top: 8px; line-height: 1.6;">
                    <strong>Type:</strong> {tx_data.get('device_type') or 'N/A'}<br>
                    <strong>Operating System:</strong> {tx_data.get('operating_system') or 'N/A'}<br>
                    <strong>Trust Status:</strong> {dev_badge}<br>
                    <strong>First Seen:</strong> {tx_data.get('device_first_used') or 'N/A'}<br>
                    <strong>Last Used:</strong> {tx_data.get('device_last_used') or 'N/A'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📍 Geolocation & Traveling Velocity")
        st.markdown(f"""
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <div style="font-weight: 600; font-size: 1rem; color: #F9FAFB;">
                    {tx_data['tx_city']}, {tx_data['tx_state']}, {tx_data['tx_country']}
                </div>
                <div style="color: #9CA3AF; font-size: 0.85rem; margin-top: 8px; line-height: 1.6;">
                    <strong>Customer Registered City:</strong> {tx_data['customer_home_city']}<br>
                    <strong>Coordinates:</strong> {tx_data['latitude']}, {tx_data['longitude']}<br>
                    <strong>Location Match:</strong> {'✅ Home City' if tx_data['tx_city'] == tx_data['customer_home_city'] else '⚠️ Remote Location'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Map display if coordinates available
        if pd.notna(tx_data["latitude"]) and pd.notna(tx_data["longitude"]):
            map_data = pd.DataFrame({
                "lat": [float(tx_data["latitude"])],
                "lon": [float(tx_data["longitude"])]
            })
            st.map(map_data, zoom=6, use_container_width=True)

    # 5. Temporal Surrounding Activity (Velocity Timeline)
    st.markdown("---")
    st.markdown("### ⏱️ Account Activity Velocity Timeline (±2 Hours Window)")
    st.caption("Transactions immediately preceding or following this event on the same account:")

    surrounding_df = query_df("""
        SELECT 
            t.transaction_id AS `ID`,
            t.transaction_timestamp AS `Timestamp`,
            t.amount AS `Amount`,
            t.transaction_method AS `Method`,
            l.city AS `City`,
            t.transaction_status AS `Status`,
            t.risk_score AS `Score`,
            t.risk_level AS `Risk`
        FROM transactions t
        JOIN locations l ON t.location_id = l.location_id
        WHERE t.account_id = %s
          AND t.transaction_timestamp BETWEEN DATE_SUB(%s, INTERVAL 3 HOUR) AND DATE_ADD(%s, INTERVAL 3 HOUR)
        ORDER BY t.transaction_timestamp ASC;
    """, [tx_data["account_id"], tx_data["transaction_timestamp"], tx_data["transaction_timestamp"]])

    if not surrounding_df.empty:
        s_display = surrounding_df.copy()
        s_display["Amount"] = s_display["Amount"].apply(format_currency)
        s_display["Timestamp"] = pd.to_datetime(s_display["Timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(s_display, use_container_width=True, hide_index=True)
    else:
        st.info("No other account transactions found within the 3-hour velocity window.")
