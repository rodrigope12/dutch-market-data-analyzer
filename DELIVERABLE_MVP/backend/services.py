import pandas as pd
import time
import logging
from datetime import datetime
from typing import List, Optional
from backend.models import Invoice, CheckResult, CheckStatus, ProcessingResult

logger = logging.getLogger("ComplianceService")

class ComplianceService:
    """
    Evaluates invoices against business rules and compliance checks.
    """
    
    def __init__(self, data_sources: str = "data"):
        self.data_sources = data_sources
        self._initialize_resources()

    def _initialize_resources(self):
        """Loads reference data."""
        try:
            self.vendors = pd.read_csv(f"{self.data_sources}/vendors.csv")
            self.budgets = pd.read_csv(f"{self.data_sources}/budgets.csv")
            self.contracts = pd.read_csv(f"{self.data_sources}/contracts.csv")
            
            # Normalize
            self.vendors['risk_level'] = self.vendors['risk_level'].fillna('Medium')
            logger.info("Reference data loaded")
        except Exception:
            logger.error("Reference data unavailable. Using empty datasets.")
            self.vendors = pd.DataFrame(columns=['vendor_name', 'iban', 'risk_level'])
            self.budgets = pd.DataFrame(columns=['department', 'total_budget', 'remaining_budget'])
            self.contracts = pd.DataFrame(columns=['vendor_name', 'start_date', 'end_date', 'is_active'])

    def process_invoice(self, invoice: Invoice) -> ProcessingResult:
        """Runs all compliance checks on an invoice."""
        logger.info(f"Evaluating Invoice {invoice.invoice_id}")
        
        checks: List[CheckResult] = [
            self._verify_financial_routing(invoice),
            self._assess_vendor_risk(invoice),
            self._validate_budgetary_alignment(invoice),
            self._verify_contractual_standing(invoice)
        ]
        
        # Determine status
        critical_failures = [c for c in checks if c.status == CheckStatus.FAIL]
        warnings = [c for c in checks if c.status == CheckStatus.WARNING]
        
        if critical_failures:
            final_status = "REJECTED"
            risk_score = 100
        elif warnings:
            final_status = "DRAFT" # Review required
            risk_score = 50
        else:
            final_status = "APPROVED"
            risk_score = 0
            
            # Post-Process Action
            self._post_to_odoo_mock(invoice)
            
        return ProcessingResult(
            invoice=invoice,
            checks=checks,
            final_status=final_status,
            risk_score=risk_score
        )

    def _post_to_odoo_mock(self, invoice: Invoice) -> bool:
        """
        Simulation of an API call to Odoo ERP.
        Endpoint: /api/v1/account.move
        """
        print(f"[ODOO INTEGRATION] Posting Invoice {invoice.invoice_id} to Accounting Ledger... SUCCESS")
        return True

    def _verify_financial_routing(self, invoice: Invoice) -> CheckResult:
        # Normalize authorized IBANs (remove spaces) for accurate comparison
        authorized_ibans = [str(i).replace(" ", "") for i in self.vendors['iban'].unique()]
        status = CheckStatus.PASS
        msg = "IBAN verified."
        
        if invoice.iban == "UNKNOWN":
            status = CheckStatus.FAIL
            msg = "Missing IBAN."
        elif invoice.iban not in authorized_ibans:
            status = CheckStatus.FAIL
            msg = f"Unauthorized IBAN: {invoice.iban}"
            
        return CheckResult(check_name="Financial Routing", status=status, message=msg, timestamp=time.time())

    def _assess_vendor_risk(self, invoice: Invoice) -> CheckResult:
        # Normalize for comparison (case-insensitive)
        inv_vendor = invoice.vendor_name.strip().lower()
        
        # Find vendor case-insensitive
        match_mask = self.vendors['vendor_name'].str.strip().str.lower() == inv_vendor
        vendor_data = self.vendors[match_mask]
        
        status = CheckStatus.PASS
        msg = "Vendor risk acceptable."
        
        if vendor_data.empty:
            status = CheckStatus.WARNING
            msg = "Vendor not in master records."
        else:
            risk_level = vendor_data.iloc[0]['risk_level']
            if risk_level == "High":
                status = CheckStatus.FAIL
                msg = "Vendor flagged as High Risk."
        
        return CheckResult(check_name="Vendor Risk", status=status, message=msg, timestamp=time.time())

    def _validate_budgetary_alignment(self, invoice: Invoice) -> CheckResult:
        inv_dept = invoice.department.strip().lower()
        
        # Find department case-insensitive
        match_mask = self.budgets['department'].str.strip().str.lower() == inv_dept
        allocation = self.budgets[match_mask]

        status = CheckStatus.PASS
        msg = "Budget checks passed."
        
        if invoice.department == "Unknown":
            status = CheckStatus.WARNING
            msg = "Department unspecified."
        elif allocation.empty:
            status = CheckStatus.FAIL
            msg = f"No budget found for {invoice.department}."
        else:
            remaining = float(allocation.iloc[0]['remaining_budget'])
            if invoice.amount > remaining:
                status = CheckStatus.FAIL
                msg = f"Insufficent funds. Request: {invoice.amount}, Remaining: {remaining}"
            else:
                msg = f"Funds available ({remaining - invoice.amount:.2f} remaining)"

        return CheckResult(check_name="Budget Check", status=status, message=msg, timestamp=time.time())

    def _verify_contractual_standing(self, invoice: Invoice) -> CheckResult:
        inv_vendor = invoice.vendor_name.strip().lower()
        
        # Find contract case-insensitive
        match_mask = self.contracts['vendor_name'].str.strip().str.lower() == inv_vendor
        agreements = self.contracts[match_mask]
        
        status = CheckStatus.FAIL
        msg = "No active contract."
        
        if not invoice.date:
             return CheckResult(check_name="Contract Check", status=CheckStatus.FAIL, message="Invoice missing date.", timestamp=time.time())

        inv_date_iso = invoice.date.strftime("%Y-%m-%d")
        
        for _, agreement in agreements.iterrows():
            if agreement['is_active'] and agreement['start_date'] <= inv_date_iso <= agreement['end_date']:
                status = CheckStatus.PASS
                msg = f"Covered by contract."
                break
        
        return CheckResult(check_name="Contract Check", status=status, message=msg, timestamp=time.time())
