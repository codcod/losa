"""
LOSA Chains Package

This package contains LangChain chains for AI-powered operations in the loan
origination system. Each chain handles specific aspects of document processing,
credit analysis, and decision making.
"""

from .document_chain import (
    # Main chain classes
    DocumentAnalysisChain,
    IncomeVerificationChain,
    CreditAnalysisChain,
    LoanExplanationChain,
    CompleteDocumentProcessingChain,
    # Result models
    DocumentAnalysisResult,
    IncomeVerificationResult,
    CreditAnalysisResult,
    # Factory functions
    create_document_analysis_chain,
    create_income_verification_chain,
    create_credit_analysis_chain,
    create_explanation_chain,
)

__all__ = [
    # Chain classes
    'DocumentAnalysisChain',
    'IncomeVerificationChain',
    'CreditAnalysisChain',
    'LoanExplanationChain',
    'CompleteDocumentProcessingChain',
    # Result models
    'DocumentAnalysisResult',
    'IncomeVerificationResult',
    'CreditAnalysisResult',
    # Factory functions
    'create_document_analysis_chain',
    'create_income_verification_chain',
    'create_credit_analysis_chain',
    'create_explanation_chain',
]
