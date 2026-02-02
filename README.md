# Finance Monitor
### Automated Transaction Verification System

**Precision of Wall Street. Aesthetics of Apple.**

## Overview
Finance Monitor is a high-performance financial auditing dashboard designed to automate invoice processing, compliance checks, and budget tracking. Built with the speed of **Streamlit** (Python) and styled with a bespoke CSS layer, it bridges the gap between complex data processing and premium user experience.

## Key Features
- **Automated Invoice Parsing**: Intelligent extraction of vendor data, amounts, and dates from PDF documents.
- **Compliance Engine**: customizable rule-based verification (e.g., budget limits, authorized vendors).
- **Real-time Activity Stream**: Live processing feed with visual status indicators.
- **Budget Allocation Visualization**: Sidebar metrics tracking departmental budget usage in real-time.
- **Audit Log**: Detailed, exportable ledger of all processed transactions.

## Technology Stack
- **Frontend**: Streamlit (Custom CSS/Theming)
- **Backend**: Python 3.9+
- **Data Processing**: Pandas, PDFPlumber
- **Validation**: Pydantic models for strict type checking

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/finance-monitor.git
   cd finance-monitor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Design Philosophy
This project rejects the notion that internal tools must be ugly. It implements a glassmorphism-inspired UI, smooth transitions, and a clear information hierarchy to reduce cognitive load for financial operators.
