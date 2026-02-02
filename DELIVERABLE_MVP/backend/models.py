from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date as DateType
from enum import Enum

class RiskLevel(str, Enum):
    """Enumeration for transaction risk levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class LineItem(BaseModel):
    """Represents a single line item within an invoice."""
    description: str = Field(..., description="Description of the item or service")
    quantity: int = Field(..., gt=0, description="Quantity of the item")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    total: float = Field(..., ge=0, description="Total price for the line item")

class Invoice(BaseModel):
    """Core domain model representing a financial invoice."""
    invoice_id: str = Field(..., description="Unique identifier for the invoice")
    vendor_name: str = Field(..., description="Name of the vendor")
    iban: str = Field(..., description="International Bank Account Number")
    date: Optional[DateType] = Field(None, description="Issue date of the invoice")
    amount: float = Field(..., gt=0, description="Total invoice amount")
    currency: str = Field("EUR", description="Currency code (e.g., EUR, USD)")
    department: str = Field("Unknown", description="Assigned department for the expense")
    items: list[LineItem] = Field(default_factory=list, description="List of items in the invoice")
    
    # Metadata for processing
    file_path: Optional[str] = Field(None, description="Path to the source PDF file")

    @validator('currency')
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError('Currency must be a 3-letter code')
        return v.upper()

class CheckStatus(str, Enum):
    """Possible outcomes of a logic gate check."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"

class CheckResult(BaseModel):
    """Results from an individual logic gate execution."""
    check_name: str = Field(..., description="Name of the logic check performed")
    status: CheckStatus = Field(..., description="Outcome of the check")
    message: str = Field(..., description="Detail message explaining the outcome")
    timestamp: float = Field(..., description="Epoch timestamp when the check was performed")

class ProcessingResult(BaseModel):
    """The aggregate result of processing an invoice through all logic gates."""
    invoice: Invoice = Field(..., description="The original invoice data")
    checks: list[CheckResult] = Field(..., description="Collection of all check results")
    final_status: str = Field(..., description="Overall status: APPROVED, DRAFT, or REJECTED")
    risk_score: int = Field(..., ge=0, le=100, description="Calculated risk score (0-100)")
