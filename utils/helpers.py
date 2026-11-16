"""
FraudShield - Helper Utilities
UI Formatting, Currency, Risk Badges, Metric Card Components, and DataFrame Sanitization
"""

from decimal import Decimal
import pandas as pd
import streamlit as st

def format_currency(value):
    """
    Formats a numeric value as Indian Rupees (INR) currency string.
    e.g. 72000.50 -> ₹72,000.50
    """
    if value is None or pd.isna(value):
        return "₹0.00"
    try:
        val = float(value)
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{value}"

def format_number(value):
    """
    Formats an integer or float with standard comma separators.
    """
    if value is None or pd.isna(value):
        return "0"
    try:
        val = float(value)
        if val.is_integer():
            return f"{int(val):,}"
        return f"{val:,.2f}"
    except (ValueError, TypeError):
        return str(value)

def get_risk_badge(level, score=None):
    """
    Returns an HTML badge string with appropriate risk styling.
    """
    level_str = str(level).upper() if level else "UNKNOWN"
    score_str = f" ({score})" if score is not None else ""
    
    if level_str == "HIGH":
        bg = "#450A0A"
        color = "#FCA5A5"
        border = "#DC2626"
    elif level_str == "MEDIUM":
        bg = "#451A03"
        color = "#FCD34D"
        border = "#D97706"
    elif level_str == "LOW":
        bg = "#064E3B"
        color = "#6EE7B7"
        border = "#059669"
    else:
        bg = "#1F2937"
        color = "#9CA3AF"
        border = "#4B5563"
        
    return f"""<span style="
        background-color: {bg};
        color: {color};
        border: 1px solid {border};
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
        letter-spacing: 0.05em;
    ">{level_str}{score_str}</span>"""

def get_status_badge(status):
    """
    Returns an HTML badge string for alert investigation status.
    """
    status_str = str(status) if status else "Pending"
    
    if status_str == "Pending":
        bg = "#7F1D1D"
        color = "#FCA5A5"
        border = "#EF4444"
    elif status_str == "Investigating":
        bg = "#1E3A8A"
        color = "#93C5FD"
        border = "#3B82F6"
    elif status_str == "Resolved":
        bg = "#064E3B"
        color = "#6EE7B7"
        border = "#10B981"
    elif status_str == "False Positive":
        bg = "#374151"
        color = "#D1D5DB"
        border = "#6B7280"
    else:
        bg = "#1F2937"
        color = "#9CA3AF"
        border = "#4B5563"

    return f"""<span style="
        background-color: {bg};
        color: {color};
        border: 1px solid {border};
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    ">{status_str}</span>"""

def sanitize_dataframe(df):
    """
    Converts Decimal columns to floats and standardizes datetime columns
    for optimal rendering in Streamlit.
    """
    if df is None or df.empty:
        return df
    
    clean = df.copy()
    for col in clean.columns:
        # Convert Decimal to float
        if clean[col].apply(lambda x: isinstance(x, Decimal)).any():
            clean[col] = clean[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
        # Format timestamps
        if "timestamp" in col.lower() or "created_at" in col.lower() or "date" in col.lower():
            try:
                clean[col] = pd.to_datetime(clean[col]).dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
    return clean

def render_kpi(label, value, subtext=None, border_color="#3B82F6"):
    """
    Renders a styled KPI metric card.
    """
    sub_html = f'<div style="font-size: 0.8rem; color: #9CA3AF; margin-top: 4px;">{subtext}</div>' if subtext else ""
    card_html = f"""
    <div style="
        background: #111827;
        border: 1px solid #1F2937;
        border-left: 4px solid {border_color};
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        margin-bottom: 12px;
    ">
        <div style="font-size: 0.85rem; font-weight: 500; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.05em;">{label}</div>
        <div style="font-size: 1.85rem; font-weight: 700; color: #F9FAFB; margin-top: 4px;">{value}</div>
        {sub_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
