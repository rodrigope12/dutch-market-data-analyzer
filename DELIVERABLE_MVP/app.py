import streamlit as st
import pandas as pd
import os
import time
import glob
import logging
from backend.models import ProcessingResult
from backend.processor import PDFProcessor
from backend.services import ComplianceService

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("App")

st.set_page_config(
    page_title="Finance Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Assets ---
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# --- Initialization ---
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
        status_msg.caption(f"Analyzing {file_name}...")
        
        try:
            # 1. Extraction
            invoice = processor.parse(file_path)
            
            # 2. Compliance Check
            result = engine.process_invoice(invoice)
            results.append(result)
            
            # 3. Aggregation
            volume_processed += invoice.amount
            if result.final_status in ["DRAFT", "REJECTED"]:
                capital_secured += invoice.amount 
            
            # 4. Real-time Stream
            with log_container:
                if result.final_status == "APPROVED":
                    st.markdown(f"<span class='status-indicator status-success'></span> **{file_name}** | Approved", unsafe_allow_html=True)
                else:
                    failures = [c.check_name for c in result.checks if c.status == "FAIL"]
                    st.markdown(f"<span class='status-indicator status-error'></span> **{file_name}** | Action Required: {', '.join(failures)}", unsafe_allow_html=True)
                    
        except Exception as e:
            st.markdown(f"<span class='status-indicator status-error'></span> Error processing {file_name}", unsafe_allow_html=True)
            logger.error(f"Processing error: {e}")
        
        time.sleep(0.15) # UI pacing
        progress_bar.progress((i + 1) / total_files)

    status_msg.empty()
    return results, capital_secured, volume_processed

# --- UI Layout ---

st.title("Finance Monitor")
st.markdown("Automated Transaction Verification Terminal")
st.markdown("---")

# Metrics Dashboard
col1, col2, col3, col4 = st.columns(4)
m1 = col1.empty()
m2 = col2.empty()
m3 = col3.empty()
m4 = col4.empty()

# Sidebar: System Status & Budgets
st.sidebar.markdown("**System Status**")
st.sidebar.caption("All engines operational")
st.sidebar.markdown("---")
st.sidebar.markdown("**Budget Usage**")

try:
    budgets_df = pd.read_csv("data/budgets.csv")
    for _, row in budgets_df.iterrows():
        usage_pct = 1.0 - (row['remaining_budget'] / row['total_budget'])
        st.sidebar.caption(row['department'])
        st.sidebar.progress(max(0.0, min(1.0, usage_pct)))
except Exception:
    st.sidebar.caption("Budget data awaiting synchronization")

# Main Controller
if st.button("EXECUTE AUDIT CYCLE", use_container_width=True):
    results_list, secured_amt, total_vol = process_invoices()
    
    # Update KPIs
    m1.metric("Volume Processed", f"€{total_vol:,.0f}")
    m2.metric("Capital Safeguarded", f"€{secured_amt:,.0f}")
    m3.metric("Documents Scanned", len(results_list))
    m4.metric("Risk Alerts", f"{len([r for r in results_list if r.risk_score > 0])}")
    
    # Audit Log Table
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
    
    st.dataframe(pd.DataFrame(ledger_data), width=1200)

else:
    # Idle State
    m1.metric("Volume Processed", "€0.00")
    m2.metric("Capital Safeguarded", "€0.00")
    m3.metric("System", "Standby")
    m4.metric("Risk Alerts", "0")
    
    st.info("System Ready. Load invoices into input directory to begin audit.")
