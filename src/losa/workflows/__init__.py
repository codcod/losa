"""
LOSA Workflows Package

This package contains LangGraph workflows for orchestrating the loan origination process.
The workflows handle the complete loan application lifecycle from initial validation
through final decision making.
"""

from .loan_workflow import (
    # Main workflow components
    create_loan_workflow,
    process_loan_application,
    # Workflow state and status
    LoanWorkflowState,
    WorkflowStatus,
    # Individual workflow nodes
    validate_application_node,
    verify_documents_node,
    credit_check_node,
    risk_assessment_node,
    decision_node,
    human_review_node,
    # Utility functions
    should_continue,
)

__all__ = [
    # Main workflow
    'create_loan_workflow',
    'process_loan_application',
    # State management
    'LoanWorkflowState',
    'WorkflowStatus',
    # Workflow nodes
    'validate_application_node',
    'verify_documents_node',
    'credit_check_node',
    'risk_assessment_node',
    'decision_node',
    'human_review_node',
    # Utilities
    'should_continue',
]
