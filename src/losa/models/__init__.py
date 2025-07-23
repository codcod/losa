"""
LOSA Models Package

This package contains all the Pydantic models and data structures used throughout
the Loan Origination System Application.
"""

from .loan import (
    # Main application models
    LoanApplication,
    LoanApplicationCreate,
    LoanApplicationUpdate,
    LoanApplicationSummary,
    # Enums
    LoanType,
    LoanStatus,
    EmploymentStatus,
    MaritalStatus,
    DocumentType,
    # Component models
    PersonalInfo,
    Address,
    EmploymentInfo,
    FinancialInfo,
    LoanDetails,
    Document,
    CreditScore,
    RiskAssessment,
    LoanDecision,
)

__all__ = [
    # Main models
    "LoanApplication",
    "LoanApplicationCreate",
    "LoanApplicationUpdate",
    "LoanApplicationSummary",
    # Enums
    "LoanType",
    "LoanStatus",
    "EmploymentStatus",
    "MaritalStatus",
    "DocumentType",
    # Component models
    "PersonalInfo",
    "Address",
    "EmploymentInfo",
    "FinancialInfo",
    "LoanDetails",
    "Document",
    "CreditScore",
    "RiskAssessment",
    "LoanDecision",
]
