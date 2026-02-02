import os
import random
import csv
from datetime import date, timedelta
from fpdf import FPDF
from faker import Faker

fake = Faker()

DATA_DIR = "data"
INVOICE_DIR = os.path.join(DATA_DIR, "invoices")

# --- Configuration for Mock Data ---
DEPARTMENTS = ["IT", "Marketing", "HR", "Operations", "Legal"]
VENDORS_COUNT = 15
INVOICES_COUNT = 12 

def setup_directories():
    os.makedirs(INVOICE_DIR, exist_ok=True)

def generate_reference_data():
    """Generates CSVs for Vendors, Budgets, and Contracts."""
    
    # 1. Vendors
    vendors = []
    for _ in range(VENDORS_COUNT):
        vendor_name = fake.company()
        risk = random.choice(["Low", "Low", "Low", "Medium", "High"]) 
        iban = fake.iban()
        vendors.append({
            "vendor_name": vendor_name,
            "iban": iban,
            "risk_level": risk
        })
    
    vendors.append({"vendor_name": "Dark Web Corp", "iban": fake.iban(), "risk_level": "High"})
    vendors.append({"vendor_name": "Fraud Inc", "iban": "XXINVALIDIBAN", "risk_level": "Low"})

    with open(os.path.join(DATA_DIR, "vendors.csv"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["vendor_name", "iban", "risk_level"])
        writer.writeheader()
        writer.writerows(vendors)

    # 2. Budgets
    budgets = []
    for dept in DEPARTMENTS:
        budgets.append({
            "department": dept,
            "total_budget": round(random.uniform(50000, 200000), 2),
            "remaining_budget": round(random.uniform(1000, 50000), 2)
        })
        
    with open(os.path.join(DATA_DIR, "budgets.csv"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["department", "total_budget", "remaining_budget"])
        writer.writeheader()
        writer.writerows(budgets)

    # 3. Contracts
    contracts = []
    today = date.today()
    for v in vendors:
        if random.random() < 0.8:
            start_date = today - timedelta(days=random.randint(30, 300))
            end_date = today + timedelta(days=random.randint(30, 300))
            contracts.append({
                "vendor_name": v["vendor_name"],
                "start_date": start_date,
                "end_date": end_date,
                "is_active": True
            })
    
    with open(os.path.join(DATA_DIR, "contracts.csv"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["vendor_name", "start_date", "end_date", "is_active"])
        writer.writeheader()
        writer.writerows(contracts)
        
    return vendors, budgets, contracts

class InvoicePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INVOICE', 0, 1, 'R')

def generate_invoices(vendors):
    """Generates PDF invoices."""
    
    for i in range(INVOICES_COUNT):
        vendor = random.choice(vendors)
        dept = random.choice(DEPARTMENTS)
        
        pdf = InvoicePDF()
        pdf.add_page()
        
        inv_num = f"INV-{fake.year()}-{random.randint(1000, 9999)}"
        inv_date = fake.date_between(start_date='-6m', end_date='today')
        amount = round(random.uniform(100, 15000), 2)
        
        layout_type = random.choice([1, 2, 3])
        
        pdf.set_font("Arial", size=10)
        
        # Content common strings
        str_vendor = f"Vendor: {vendor['vendor_name']}"
        str_date = f"Date: {inv_date}"
        str_num = f"Invoice #: {inv_num}"
        str_iban = f"IBAN: {vendor['iban']}"
        str_dept = f"Department: {dept}"
        str_total = f"Total Amount: EUR {amount}"
        
        if layout_type == 1:
            pdf.cell(200, 10, txt=str_vendor, ln=1)
            pdf.cell(200, 10, txt=str_date, ln=1)
            pdf.cell(200, 10, txt=str_num, ln=1)
            pdf.cell(200, 10, txt=str_iban, ln=1)
            pdf.cell(200, 10, txt=str_dept, ln=1)
            pdf.ln(20)
            pdf.cell(200, 10, txt=str_total, ln=1)
            
        elif layout_type == 2:
            pdf.cell(200, 10, txt=f"{vendor['vendor_name']}", ln=1, align='R')
            pdf.cell(200, 10, txt=f"IBAN: {vendor['iban']}", ln=1, align='R')
            pdf.ln(20)
            pdf.cell(100, 10, txt=str_num, ln=0)
            pdf.cell(100, 10, txt=str_date, ln=1)
            pdf.cell(100, 10, txt=str_dept, ln=1)
            pdf.ln(10)
            pdf.cell(200, 10, txt=f"BALANCE DUE: {amount} EUR", ln=1, align='C')

        elif layout_type == 3:
            pdf.set_font("Courier", size=12)
            pdf.cell(200, 10, txt=f"FROM: {vendor['vendor_name']}", ln=1)
            pdf.cell(200, 10, txt=f"PAY TO: {vendor['iban']}", ln=1)
            pdf.ln(10)
            pdf.cell(200, 10, txt=f"REF: {inv_num} / {inv_date}", ln=1)
            pdf.cell(200, 10, txt=f"DEPT: {dept}", ln=1)
            pdf.ln(20)
            pdf.cell(200, 10, txt=f"TOTAL: {amount}", ln=1)

        filename = f"invoice_{i+1:03d}_{vendor['vendor_name'].replace(' ', '_')}.pdf"
        pdf.output(os.path.join(INVOICE_DIR, filename))
        
    print(f"Generated {INVOICES_COUNT} invoices.")

if __name__ == "__main__":
    setup_directories()
    vendors, budgets, contracts = generate_reference_data()
    generate_invoices(vendors)
    print("Mock data generation complete.")
