import streamlit as st
import pandas as pd
import os
import time
import glob
import logging
from backend.models import ProcessingResult
from backend.processor import PDFProcessor
from backend.services import ComplianceService

# Config
logger = logging.getLogger("App")

st.set_page_config(
    page_title="Finance Monitor",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Styles
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Stylesheets could not be loaded.")

# Init services
DATA_DIR = "data/invoices"
processor = PDFProcessor()
engine = ComplianceService()

def process_invoices():
    files = glob.glob(os.path.join(DATA_DIR, "*.pdf"))
    results = []
    
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    total_files = len(files)
    capital_secured = 0.0
    volume_processed = 0.0
    
    st.markdown("### Activity Stream")
    log_container = st.container()
    
    for i, file_path in enumerate(files):
        file_name = os.path.basename(file_path)
        status_msg.caption(f"Processing {file_name}...")
        
        try:
            # Extract
            invoice = processor.parse(file_path)
            
            # Evaluate
            result = engine.process_invoice(invoice)
            results.append(result)
            
            # Aggregate
            volume_processed += invoice.amount
            if result.final_status in ["DRAFT", "REJECTED"]:
                capital_secured += invoice.amount 
            
            # Stream
            with log_container:
                if result.final_status == "APPROVED":
                    st.markdown(f"<span class='status-indicator status-success'></span> **{file_name}** | Approved", unsafe_allow_html=True)
                else:
                    failures = [c.check_name for c in result.checks if c.status == "FAIL"]
                    st.markdown(f"<span class='status-indicator status-error'></span> **{file_name}** | Action Required: {', '.join(failures)}", unsafe_allow_html=True)
                    
        except Exception as e:
            st.markdown(f"<span class='status-indicator status-error'></span> Error processing {file_name}", unsafe_allow_html=True)
            logger.error(f"Error: {e}")
        
        time.sleep(0.1) 
        progress_bar.progress((i + 1) / total_files)

    status_msg.empty()
    return results, capital_secured, volume_processed

# --- UI Layout ---

st.title("Finance Monitor")
st.markdown("Automated Transaction Verification")
st.markdown("---")

# Dashboard
col1, col2, col3, col4 = st.columns(4)
m1 = col1.empty()
m2 = col2.empty()
m3 = col3.empty()
m4 = col4.empty()

# Sidebar
st.sidebar.markdown("**System Status**")
st.sidebar.caption("All services nominal")
st.sidebar.markdown("---")
st.sidebar.markdown("**Budget Allocation**")

try:
    budgets_df = pd.read_csv("data/budgets.csv")
    for _, row in budgets_df.iterrows():
        usage_pct = 1.0 - (row['remaining_budget'] / row['total_budget'])
        st.sidebar.caption(row['department'])
        st.sidebar.progress(max(0.0, min(1.0, usage_pct)))
except Exception:
    st.sidebar.caption("Budget data unavailable")

# Main Action
if st.button("Process Invoices", use_container_width=True):
    results_list, secured_amt, total_vol = process_invoices()
    
    # Update Metrics
    m1.metric("Volume Processed", f"€{total_vol:,.0f}")
    m2.metric("Flagged Amount", f"€{secured_amt:,.0f}")
    m3.metric("Documents", len(results_list))
    m4.metric("Alerts", f"{len([r for r in results_list if r.risk_score > 0])}")
    
    # Results Table
    st.markdown("### Audit Log")
    
    ledger_data = []
    for r in results_list:
        ledger_data.append({
            "Status": "Verified" if r.final_status == "APPROVED" else "Flagged",
            "Vendor": r.invoice.vendor_name,
            "Date": r.invoice.date,
            "Amount": f"€{r.invoice.amount:,.2f}",
            "Department": r.invoice.department,
            "Note": r.checks[0].message if r.checks else "-"
        })
    
    st.dataframe(pd.DataFrame(ledger_data), width="stretch")

else:
    # Idle State
    m1.metric("Volume Processed", "€0.00")
    m2.metric("Flagged Amount", "€0.00")
    m3.metric("System", "Ready")
    m4.metric("Alerts", "0")
    
    st.info("Ready to process documents. Ensure files are in the input directory.")

