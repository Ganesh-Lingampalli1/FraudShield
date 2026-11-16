"""
FraudShield - Fraud Transaction Detection & Risk Scoring System
Main Application Entrypoint & Navigation Controller
"""

import streamlit as st
import pandas as pd
from db_connection import test_connection, query_df

# Page Configuration
st.set_page_config(
    page_title="FraudShield | Financial Crime Surveillance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Financial Tech Aesthetics
st.markdown("""
<style>
    /* Global Background and Colors */
    .stApp {
        background-color: #0A0F1D;
        color: #F9FAFB;
    }
    
    /* Top Header Bar */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }

    /* Card Containers */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #F9FAFB !important;
    }
    
    /* Tables and Dataframes */
    div[data-testid="stDataFrame"] {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 8px;
    }

    /* Buttons */
    button[kind="primary"] {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out;
    }
    button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }

    /* Custom Radio Navigation */
    div[data-testid="stRadio"] > label {
        display: none;
    }
    div[data-testid="stRadio"] > div {
        gap: 6px;
    }
    div[data-testid="stRadio"] > div > label {
        padding: 8px 12px;
        border-radius: 6px;
        transition: background 0.15s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# Import Page Renderers
from pages.dashboard import render_dashboard_page
from pages.transactions import render_transactions_page
from pages.fraud_alerts import render_fraud_alerts_page
from pages.investigation import render_investigation_page
from pages.customers import render_customers_page
from pages.analytics import render_analytics_page
from pages.fraud_rules import render_fraud_rules_page

def main():
    # Sidebar Header & Branding
    st.sidebar.markdown("""
        <div style="padding: 10px 0 20px 0; border-bottom: 1px solid #1E293B; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 2rem;">🛡️</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.4rem; font-weight: 800; letter-spacing: -0.02em; color: #F9FAFB;">
                        Fraud<span style="color: #3B82F6;">Shield</span>
                    </h2>
                    <span style="font-size: 0.75rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500;">
                        Risk Engine & Surveillance
                    </span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Database Liveness Check
    db_connected, db_msg = test_connection()

    if not db_connected:
        st.sidebar.error("❌ MySQL Disconnected")
        st.sidebar.caption(f"Error: {db_msg}")
        st.error(f"""
            ### ⚠️ Database Connection Required
            Could not connect to MySQL: **{db_msg}**
            
            Please verify:
            1. MySQL Server is active on localhost:3306.
            2. Database credentials in `.streamlit/secrets.toml` are correct.
            3. Run `python database/setup_database.py` to create the schema and populate sample data.
        """)
        return

    # Navigation Menu Setup
    nav_options = [
        "🛡️ Dashboard",
        "💳 Transactions",
        "🚨 Fraud Alerts",
        "🔍 Investigation",
        "👤 Customers",
        "📈 Analytics",
        "⚙️ Fraud Rules"
    ]

    # Support programmatic navigation across pages
    if "nav_selection" not in st.session_state:
        st.session_state["nav_selection"] = "🛡️ Dashboard"

    # Match index
    default_index = 0
    if st.session_state["nav_selection"] in nav_options:
        default_index = nav_options.index(st.session_state["nav_selection"])

    st.sidebar.markdown("<p style='font-size: 0.8rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;'>Surveillance Navigation</p>", unsafe_allow_html=True)
    
    selected_page = st.sidebar.radio(
        "Navigation",
        nav_options,
        index=default_index,
        key="nav_radio"
    )

    st.session_state["nav_selection"] = selected_page

    # Sidebar Quick Stats & Status Box
    try:
        quick_stats = query_df("""
            SELECT 
                (SELECT COUNT(*) FROM transactions) AS tx_count,
                (SELECT COUNT(*) FROM fraud_alerts WHERE alert_status = 'Pending') AS pending_alerts;
        """)
        if not quick_stats.empty:
            tx_cnt = quick_stats.iloc[0]["tx_count"]
            pending_cnt = quick_stats.iloc[0]["pending_alerts"]
            
            st.sidebar.markdown(f"""
                <div style="background: #111827; border: 1px solid #1E293B; border-radius: 8px; padding: 12px; margin-top: 24px; margin-bottom: 16px;">
                    <div style="font-size: 0.75rem; color: #9CA3AF; text-transform: uppercase; font-weight: 600;">System Health</div>
                    <div style="display: flex; align-items: center; gap: 6px; margin-top: 4px;">
                        <span style="height: 8px; width: 8px; background: #10B981; border-radius: 50%; display: inline-block;"></span>
                        <span style="font-size: 0.85rem; color: #10B981; font-weight: 600;">MySQL 8.0 Live</span>
                    </div>
                    <div style="border-top: 1px solid #1E293B; margin-top: 10px; padding-top: 8px; font-size: 0.8rem; color: #9CA3AF;">
                        <div>Total Transactions: <strong style="color: #F9FAFB;">{tx_cnt:,}</strong></div>
                        <div>Pending Alerts: <strong style="color: {'#EF4444' if pending_cnt > 0 else '#10B981'};">{pending_cnt}</strong></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass

    st.sidebar.markdown("""
        <div style="font-size: 0.75rem; color: #64748B; text-align: center; margin-top: 30px;">
            FraudShield v1.0.0 &bull; Educational Edition<br>
            Powered by MySQL 8.0 & Streamlit
        </div>
    """, unsafe_allow_html=True)

    # Route Page
    if selected_page == "🛡️ Dashboard":
        render_dashboard_page()
    elif selected_page == "💳 Transactions":
        render_transactions_page()
    elif selected_page == "🚨 Fraud Alerts":
        render_fraud_alerts_page()
    elif selected_page == "🔍 Investigation":
        render_investigation_page()
    elif selected_page == "👤 Customers":
        render_customers_page()
    elif selected_page == "📈 Analytics":
        render_analytics_page()
    elif selected_page == "⚙️ Fraud Rules":
        render_fraud_rules_page()

if __name__ == "__main__":
    main()
