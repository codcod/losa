"""
Loan Origination System Application (LOSA)

A comprehensive loan origination system built with LangChain and LangGraph.

This package provides:
- Complete loan application lifecycle management
- AI-powered document verification and analysis
- Automated credit assessment and risk evaluation
- Workflow orchestration using LangGraph
- RESTful API for integration
- Database persistence and audit logging

Main Components:
- models: Pydantic models for loan data structures
- workflows: LangGraph workflows for loan processing
- chains: LangChain chains for AI-powered operations
- services: Business logic and data access layer
- api: FastAPI REST endpoints
- database: SQLAlchemy models and database configuration

Usage:
    from losa.main import app
    from losa.services.loan_service import LoanService
    from losa.models.loan import LoanApplication, LoanApplicationCreate
"""

__version__ = '1.0.0'
__author__ = 'LOSA Development Team'
__email__ = 'dev@losa.com'
__description__ = (
    'AI-powered loan origination system built with LangChain and LangGraph'
)

# Package-level imports for convenience
from .models.loan import (
    LoanApplication,
    LoanApplicationCreate,
    LoanApplicationUpdate,
    LoanApplicationSummary,
    LoanStatus,
    LoanType,
    DocumentType,
    Document,
    CreditScore,
    RiskAssessment,
    LoanDecision,
)

from .services.loan_service import LoanService
from .database.config import db_manager, get_sync_session, get_async_session

# Version info tuple
VERSION = tuple(map(int, __version__.split('.')))

# Package metadata
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__email__',
    '__description__',
    'VERSION',
    # Core models
    'LoanApplication',
    'LoanApplicationCreate',
    'LoanApplicationUpdate',
    'LoanApplicationSummary',
    'LoanStatus',
    'LoanType',
    'DocumentType',
    'Document',
    'CreditScore',
    'RiskAssessment',
    'LoanDecision',
    # Services
    'LoanService',
    # Database
    'db_manager',
    'get_sync_session',
    'get_async_session',
]
