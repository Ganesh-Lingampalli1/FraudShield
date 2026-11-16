"""
FraudShield - Fraud Rules Configuration & Risk Engine Console
Allows demonstration users to view and modify rule risk weights and active statuses in MySQL,
and execute batch re-evaluation of all transactions via `analyze_all_transactions()`.
"""

import streamlit as st
import pandas as pd
import time
from db_connection import query_df, execute_dml, call_procedure
from utils.helpers import format_number, render_kpi

def render_fraud_rules_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #F9FAFB;">
                ⚙️ Fraud Detection Rules & Risk Engine Configuration
            </h1>
            <p style="color: #9CA3AF; margin-top: 4px; font-size: 1rem;">
                Configure rule point weights, toggle active status in MySQL, and trigger live batch re-scoring across all transactions.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Fetch Current Rules from MySQL table fraud_rules
    rules_df = query_df("""
        SELECT 
            rule_id, 
            rule_code, 
            rule_name, 
            description, 
            risk_points, 
            active_status, 
            created_at, 
            updated_at
        FROM fraud_rules
        ORDER BY rule_id ASC;
    """)

    if rules_df.empty:
        st.warning("No fraud detection rules found in MySQL table `fraud_rules`.")
        return

    # 2. Rule Configuration KPI Summary
    total_rules = len(rules_df)
    active_rules = int(rules_df["active_status"].sum())
    total_points_pool = int(rules_df[rules_df["active_status"] == 1]["risk_points"].sum())

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("Configured Rules", str(total_rules), "Total rules in engine", "#3B82F6")
    with k2:
        render_kpi("Active Rules", str(active_rules), f"Inactive: {total_rules - active_rules}", "#10B981")
    with k3:
        render_kpi("Max Points Pool", str(total_points_pool), "Sum of active rule points", "#F59E0B")
    with k4:
        render_kpi("Risk Thresholds", "30 / 60", "Low: <30 | Med: 30-59 | High: 60+", "#8B5CF6")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Rules Table Overview
    st.markdown("### 📋 Active Detection Rules in MySQL")
    st.caption("These rules are dynamically loaded and evaluated by MySQL Stored Procedure `analyze_transaction()`:")

    display_df = rules_df.copy()
    display_df["Status"] = display_df["active_status"].apply(lambda s: "🟢 Active" if s == 1 else "🔴 Inactive")
    display_df.rename(columns={
        "rule_id": "ID",
        "rule_code": "Code",
        "rule_name": "Rule Name",
        "description": "Rule Detection Logic",
        "risk_points": "Risk Points",
        "updated_at": "Last Updated"
    }, inplace=True)

    st.dataframe(
        display_df[["ID", "Code", "Rule Name", "Risk Points", "Status", "Rule Detection Logic"]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # 4. Interactive Rule Editor (Modify Points or Status)
    st.markdown("### ✏️ Modify Rule Parameters")
    st.caption("Adjust points or enable/disable a rule. All changes are committed directly into the MySQL `fraud_rules` table.")

    edit_col1, edit_col2 = st.columns([1, 1])

    with edit_col1:
        rule_options = {f"{r['rule_id']} - {r['rule_name']} ({r['rule_code']})": r['rule_id'] for _, r in rules_df.iterrows()}
        selected_label = st.selectbox("Select Rule to Configure", list(rule_options.keys()))
        selected_id = rule_options[selected_label]

        # Get current values for this rule
        cur_rule = rules_df[rules_df["rule_id"] == selected_id].iloc[0]

        st.markdown(f"""
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 14px; margin-top: 10px;">
                <div style="font-weight: 600; color: #F9FAFB;">{cur_rule['rule_name']}</div>
                <div style="color: #9CA3AF; font-size: 0.85rem; margin-top: 4px;">{cur_rule['description']}</div>
                <div style="color: #6B7280; font-size: 0.8rem; margin-top: 6px;">Rule Code: <code>{cur_rule['rule_code']}</code></div>
            </div>
        """, unsafe_allow_html=True)

    with edit_col2:
        new_points = st.number_input(
            "Assign Risk Points",
            min_value=1,
            max_value=100,
            value=int(cur_rule["risk_points"]),
            step=5,
            help="Points added to a transaction's risk score when this rule is triggered."
        )

        new_status = st.toggle("Rule Active in Detection Engine", value=bool(cur_rule["active_status"]))

        if st.button("💾 Save Rule to MySQL", type="primary"):
            try:
                sql_update = """
                    UPDATE fraud_rules 
                    SET risk_points = %s, active_status = %s, updated_at = NOW()
                    WHERE rule_id = %s;
                """
                affected, _ = execute_dml(sql_update, [new_points, 1 if new_status else 0, selected_id])
                st.success(f"✅ Successfully updated '{cur_rule['rule_name']}' in MySQL (Points: {new_points}, Active: {new_status})!")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update rule in MySQL: {e}")

    st.markdown("---")

    # 5. Batch Re-Analysis Runner
    st.markdown("### 🚀 Batch Risk Re-Evaluation Engine")
    st.caption("Execute MySQL Stored Procedure `CALL analyze_all_transactions()` to re-score every transaction across the entire ledger using the updated rules:")

    run_col1, run_col2 = st.columns([2, 1])

    with run_col1:
        st.info("💡 **Demonstration Tip:** When you modify rule risk weights or disable a rule above, click the button to the right to run `analyze_all_transactions()`. MySQL will recalculate every transaction score and update the alerts table automatically.")

    with run_col2:
        st.write("")
        if st.button("⚡ Run analyze_all_transactions()", type="secondary", use_container_width=True):
            with st.spinner("Executing MySQL procedure `analyze_all_transactions()` across all transactions..."):
                start_time = time.time()
                try:
                    res_dfs = call_procedure("analyze_all_transactions")
                    elapsed = time.time() - start_time
                    result_msg = res_dfs[0].iloc[0]["result"] if (res_dfs and not res_dfs[0].empty) else "Completed successfully."
                    st.success(f"✅ {result_msg} (Elapsed time: {elapsed:.2f}s)")
                except Exception as e:
                    st.error(f"Error running batch analysis: {e}")
