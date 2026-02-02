import pdfplumber
import re
import logging
from datetime import datetime
from typing import Optional
from backend.models import Invoice

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Processor")

class PDFProcessor:
    """
    Handles PDF text extraction and parsing for invoice data.
    """
    
    def parse(self, file_path: str) -> Invoice:
        logger.info(f"Processing: {file_path}")
        
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    content = page.extract_text()
                    if content:
                        text += content + "\n"
            
            if not text.strip():
                logger.warning(f"Empty content in {file_path}")
                raise ValueError("Text extraction returned empty result")

            # Extraction
            vendor = self._extract_vendor(text)
            iban = self._extract_iban(text)
            inv_id = self._extract_invoice_id(text)
            inv_date = self._extract_date(text)
            amount = self._extract_amount(text)
            dept = self._extract_department(text)
            
            logger.info(f"Parsed {inv_id} from {vendor}")
            
            return Invoice(
                invoice_id=inv_id,
                vendor_name=vendor,
                iban=iban,
                date=inv_date,
                amount=amount,
                currency="EUR",
                department=dept,
                file_path=file_path
            )
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            raise

    def _extract_vendor(self, text: str) -> str:
        # Priority 1: Labelled match
        match = re.search(r"(?:Vendor|FROM|Issuer):\s*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Priority 2: First non-generic line
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines:
            # Skip common headers
            if line.upper() in ["INVOICE", "BILL", "RECEIPT"]:
                continue
            # Assume vendor is the first significant text
            return line
            
        return "Unknown Vendor"

    def _extract_iban(self, text: str) -> str:
        # Narrower regex to capture exactly an IBAN pattern (2 letters + 15-32 alphanumeric/spaces)
        match = re.search(r"(?:IBAN|Account|PAY TO)[:,]?\s*([A-Z]{2}[0-9A-Z\s]{13,32})", text, re.IGNORECASE)
        if match:
            # Clean only the IBAN part
            raw_iban = match.group(1).strip()
            # Stop if we hit a newline or double space
            clean_iban = re.split(r'\n|\s{2,}', raw_iban)[0]
            return clean_iban.replace(" ", "").strip()
        return "UNKNOWN"

    def _extract_invoice_id(self, text: str) -> str:
        match = re.search(r"(?:Invoice #|REF|Invoice Number|ID):\s*([A-Z0-9\-/]+)", text, re.IGNORECASE)
        if match:
            # Cleanup if it captured the date too (e.g., "INV-123 / 2023-01-01")
            val = match.group(1).split('/')[0].strip()
            return val
        
        fallback = re.search(r"INV-\d{4}-\d+", text)
        return fallback.group(0) if fallback else "UNKNOWN"

    def _extract_date(self, text: str) -> Optional[datetime.date]:
        # Priority 1: Labelled Date
        match = re.search(r"(?:Date|Issued):\s*(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
        if match:
            try:
                return datetime.strptime(match.group(1).strip(), "%Y-%m-%d").date()
            except ValueError:
                pass

        # Priority 2: Any YYYY-MM-DD pattern
        match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if match:
            try:
                return datetime.strptime(match.group(1).strip(), "%Y-%m-%d").date()
            except ValueError:
                pass
                
        return None

    def _extract_amount(self, text: str) -> float:
        # Prio 1: specific Balance Due / Total Amount
        # Supports both EU (1.234,56) and US (1,234.56) formats via simple heuristic
        match = re.search(r"(?:Total Amount|BALANCE DUE|TOTAL|Grand Total)[:\s]*(?:EUR|€)?\s*([\d\.,]+)", text, re.IGNORECASE)
        if match:
            try:
                raw_val = match.group(1).strip()
                # Heuristic: if ',' is the last separator, it's likely decimal (EU)
                if ',' in raw_val and '.' in raw_val:
                    if raw_val.rfind(',') > raw_val.rfind('.'):
                        # 1.234,56 -> replace . with nothing, replace , with .
                        raw_val = raw_val.replace('.', '').replace(',', '.')
                    else:
                        # 1,234.56 -> replace , with nothing
                        raw_val = raw_val.replace(',', '')
                elif ',' in raw_val:
                    # Assumes simple comma decimal if no dots present: 123,45
                    # OR thousands separator: 12,345 (Ambiguous! Defaulting to decimal for EU context)
                     if len(raw_val.split(',')[-1]) == 2: # e.g. ,50
                         raw_val = raw_val.replace(',', '.')
                     else:
                         # Likely thousands 12,000 -> 12000
                         raw_val = raw_val.replace(',', '')
                
                return float(raw_val)
            except ValueError:
                pass
        return 0.0

    def _extract_department(self, text: str) -> str:
        match = re.search(r"(?:Department|DEPT|Cost Center):\s*(\w+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else "Unknown"


