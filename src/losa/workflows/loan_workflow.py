from typing import TypedDict, List, Optional, Annotated
from datetime import datetime
from enum import Enum
import operator

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from ..models.loan import (
    LoanApplication,
    LoanStatus,
    RiskAssessment,
    LoanDecision,
    CreditScore,
)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN = "requires_human"


class LoanWorkflowState(TypedDict):
    """State for the loan origination workflow"""

    application: LoanApplication
    messages: Annotated[List[BaseMessage], operator.add]
    next_action: Optional[str]
    workflow_status: WorkflowStatus
    error_message: Optional[str]
    human_review_required: bool
    underwriter_notes: List[str]
    credit_check_complete: bool
    document_verification_complete: bool
    risk_assessment_complete: bool
    decision_complete: bool
    retry_count: int
    stage_results: dict  # Store results from each stage


def validate_application_node(state: LoanWorkflowState) -> LoanWorkflowState:
    """Validate the loan application for completeness and basic requirements"""
    application = state["application"]
    messages = state.get("messages", [])

    validation_errors = []

    # Check basic application completeness
    if not application.personal_info:
        validation_errors.append("Personal information is missing")

    if not application.employment_info:
        validation_errors.append("Employment information is missing")

    if not application.financial_info:
        validation_errors.append("Financial information is missing")

    if not application.loan_details:
        validation_errors.append("Loan details are missing")

    # Validate debt-to-income ratio
    if application.debt_to_income_ratio > 0.43:  # Standard DTI limit
        validation_errors.append(
            f"Debt-to-income ratio too high: {application.debt_to_income_ratio:.2%}"
        )

    # Validate income requirements
    min_income = 30000 if application.loan_details.requested_amount < 100000 else 50000
    if application.employment_info.annual_income < min_income:
        validation_errors.append(
            f"Annual income below minimum requirement: ${min_income}"
        )

    if validation_errors:
        messages.append(
            AIMessage(
                content=f"Application validation failed: {'; '.join(validation_errors)}"
            )
        )
        return {
            **state,
            "messages": messages,
            "workflow_status": WorkflowStatus.FAILED,
            "error_message": f"Validation errors: {'; '.join(validation_errors)}",
            "next_action": "fix_application",
        }

    messages.append(AIMessage(content="Application validation passed"))
    application.status = LoanStatus.UNDER_REVIEW

    return {
        **state,
        "application": application,
        "messages": messages,
        "workflow_status": WorkflowStatus.IN_PROGRESS,
        "next_action": "verify_documents",
    }


def verify_documents_node(state: LoanWorkflowState) -> LoanWorkflowState:
    """Verify required documents are uploaded and valid"""
    application = state["application"]
    messages = state.get("messages", [])

    required_docs = application._get_required_documents()
    uploaded_doc_types = {doc.document_type for doc in application.documents}

    missing_docs = [
        doc_type for doc_type in required_docs if doc_type not in uploaded_doc_types
    ]

    if missing_docs:
        missing_doc_names = [
            doc.value.replace("_", " ").title() for doc in missing_docs
        ]
        messages.append(
            AIMessage(
                content=f"Missing required documents: {', '.join(missing_doc_names)}"
            )
        )
        application.status = LoanStatus.DOCUMENTS_REQUIRED

        return {
            **state,
            "application": application,
            "messages": messages,
            "workflow_status": WorkflowStatus.REQUIRES_HUMAN,
            "next_action": "upload_documents",
            "human_review_required": True,
        }

    # Simulate document verification process
    unverified_docs = [doc for doc in application.documents if not doc.verified]

    if unverified_docs:
        messages.append(
            AIMessage(content=f"Verifying {len(unverified_docs)} documents...")
        )

        # In a real system, this would involve OCR, document analysis, etc.
        for doc in unverified_docs:
            doc.verified = True
            doc.verification_notes = "Automatically verified using AI document analysis"

    messages.append(AIMessage(content="All required documents verified successfully"))

    return {
        **state,
        "application": application,
        "messages": messages,
        "document_verification_complete": True,
        "next_action": "credit_check",
    }


def credit_check_node(state: LoanWorkflowState) -> LoanWorkflowState:
    """Perform credit check and score analysis"""
    application = state["application"]
    messages = state.get("messages", [])

    # Simulate credit bureau API call
    messages.append(AIMessage(content="Initiating credit check..."))

    # In a real system, this would call actual credit bureau APIs
    # For simulation, we'll create a mock credit score based on income and DTI
    base_score = 650

    # Adjust based on income
    if application.employment_info.annual_income > 100000:
        base_score += 50
    elif application.employment_info.annual_income > 75000:
        base_score += 30
    elif application.employment_info.annual_income < 40000:
        base_score -= 40

    # Adjust based on DTI ratio
    dti = application.debt_to_income_ratio
    if dti < 0.2:
        base_score += 40
    elif dti < 0.3:
        base_score += 20
    elif dti > 0.4:
        base_score -= 50

    # Ensure score is within valid range
    credit_score_value = max(300, min(850, base_score))

    credit_score = CreditScore(
        score=credit_score_value,
        bureau="Experian",
        date_obtained=datetime.utcnow(),
        factors=[],
    )

    if credit_score_value < 580:
        credit_score.factors.extend(
            ["Payment history concerns", "High credit utilization"]
        )
    elif credit_score_value < 650:
        credit_score.factors.append("Limited credit history")

    application.credit_score = credit_score
    application.status = LoanStatus.CREDIT_CHECK

    messages.append(
        AIMessage(
            content=f"Credit check completed. Score: {credit_score_value} (Bureau: Experian)"
        )
    )

    return {
        **state,
        "application": application,
        "messages": messages,
        "credit_check_complete": True,
        "stage_results": {
            **state.get("stage_results", {}),
            "credit_score": credit_score_value,
        },
        "next_action": "risk_assessment",
    }


def risk_assessment_node(state: LoanWorkflowState) -> LoanWorkflowState:
    """Perform comprehensive risk assessment"""
    application = state["application"]
    messages = state.get("messages", [])

    messages.append(AIMessage(content="Performing risk assessment..."))

    # Calculate various risk factors
    dti_ratio = application.debt_to_income_ratio
    credit_score = application.credit_score.score if application.credit_score else 600

    # Debt-to-income ratio scoring (0-100)
    if dti_ratio < 0.2:
        dti_score = 100
    elif dti_ratio < 0.3:
        dti_score = 80
    elif dti_ratio < 0.4:
        dti_score = 60
    else:
        dti_score = 30

    # Credit utilization (mock calculation)
    credit_utilization = min(0.9, application.financial_info.credit_cards_debt / 50000)

    # Payment history score based on credit score
    if credit_score >= 750:
        payment_history_score = 95
    elif credit_score >= 700:
        payment_history_score = 85
    elif credit_score >= 650:
        payment_history_score = 70
    elif credit_score >= 600:
        payment_history_score = 55
    else:
        payment_history_score = 30

    # Employment stability score
    employment_months = 24  # Mock value
    if application.employment_info.status.value == "employed":
        if employment_months >= 24:
            employment_stability_score = 90
        elif employment_months >= 12:
            employment_stability_score = 75
        else:
            employment_stability_score = 50
    elif application.employment_info.status.value == "self_employed":
        employment_stability_score = 60
    else:
        employment_stability_score = 20

    # Overall risk score (weighted average)
    overall_risk_score = int(
        payment_history_score * 0.35
        + dti_score * 0.25
        + employment_stability_score * 0.20
        + min(100, credit_score / 8.5) * 0.20
    )

    # Determine risk level
    if overall_risk_score >= 80:
        risk_level = "LOW"
    elif overall_risk_score >= 65:
        risk_level = "MEDIUM"
    elif overall_risk_score >= 45:
        risk_level = "HIGH"
    else:
        risk_level = "VERY_HIGH"

    # Identify risk factors
    risk_factors = []
    if dti_ratio > 0.4:
        risk_factors.append("High debt-to-income ratio")
    if credit_score < 650:
        risk_factors.append("Below-average credit score")
    if application.employment_info.annual_income < 40000:
        risk_factors.append("Low income")
    if credit_utilization > 0.5:
        risk_factors.append("High credit utilization")

    risk_assessment = RiskAssessment(
        debt_to_income_ratio=dti_ratio,
        credit_utilization_ratio=credit_utilization,
        payment_history_score=payment_history_score,
        employment_stability_score=employment_stability_score,
        overall_risk_score=overall_risk_score,
        risk_level=risk_level,
        risk_factors=risk_factors,
    )

    application.risk_assessment = risk_assessment

    messages.append(
        AIMessage(
            content=f"Risk assessment completed. Overall risk score: {overall_risk_score}/100 ({risk_level} risk)"
        )
    )

    return {
        **state,
        "application": application,
        "messages": messages,
        "risk_assessment_complete": True,
        "stage_results": {
            **state.get("stage_results", {}),
            "risk_score": overall_risk_score,
            "risk_level": risk_level,
        },
        "next_action": "make_decision",
    }


def decision_node(state: LoanWorkflowState) -> LoanWorkflowState:
    """Make loan approval/rejection decision"""
    application = state["application"]
    messages = state.get("messages", [])

    messages.append(AIMessage(content="Making loan decision..."))

    risk_score = application.risk_assessment.overall_risk_score
    credit_score = application.credit_score.score
    requested_amount = float(application.loan_details.requested_amount)

    # Decision logic
    decision_type = "REJECTED"
    approved_amount = None
    approved_term = None
    interest_rate = None
    conditions = []
    rejection_reasons = []
    confidence_score = 0.0

    if risk_score >= 75 and credit_score >= 700:
        # High confidence approval
        decision_type = "APPROVED"
        approved_amount = application.loan_details.requested_amount
        approved_term = application.loan_details.requested_term_months
        interest_rate = 4.5 + (750 - credit_score) * 0.01  # Base rate + risk premium
        confidence_score = 0.9

    elif risk_score >= 65 and credit_score >= 650:
        # Conditional approval or reduced amount
        if requested_amount > 100000:
            decision_type = "CONDITIONAL"
            approved_amount = min(requested_amount * 0.8, 100000)
            conditions.append("Reduced loan amount due to risk assessment")
        else:
            decision_type = "APPROVED"
            approved_amount = application.loan_details.requested_amount

        approved_term = application.loan_details.requested_term_months
        interest_rate = 6.0 + (700 - credit_score) * 0.02
        confidence_score = 0.75

        if application.debt_to_income_ratio > 0.35:
            conditions.append("Additional income verification required")

    elif risk_score >= 45 and credit_score >= 600:
        # High-risk approval with conditions
        decision_type = "CONDITIONAL"
        approved_amount = min(requested_amount * 0.6, 50000)
        approved_term = min(
            application.loan_details.requested_term_months, 60
        )  # Shorter term
        interest_rate = 8.0 + (650 - credit_score) * 0.03
        confidence_score = 0.6

        conditions.extend(
            [
                "Reduced loan amount due to high risk",
                "Shorter repayment term",
                "Cosigner required",
                "Additional collateral may be required",
            ]
        )

    else:
        # Rejection
        decision_type = "REJECTED"
        confidence_score = 0.8

        if credit_score < 600:
            rejection_reasons.append("Credit score below minimum requirement")
        if risk_score < 45:
            rejection_reasons.append("High overall risk assessment")
        if application.debt_to_income_ratio > 0.5:
            rejection_reasons.append("Debt-to-income ratio exceeds acceptable limits")

    decision = LoanDecision(
        decision=decision_type,
        approved_amount=approved_amount,
        approved_term_months=approved_term,
        interest_rate=interest_rate,
        conditions=conditions,
        rejection_reasons=rejection_reasons,
        decision_date=datetime.utcnow(),
        decision_maker="AI Underwriting System",
        confidence_score=confidence_score,
    )

    application.decision = decision
    application.decision_date = datetime.utcnow()

    if decision_type == "APPROVED":
        application.status = LoanStatus.APPROVED
        messages.append(
            AIMessage(
                content=f"Loan APPROVED: ${approved_amount:,.2f} at {interest_rate:.2%} APR for {approved_term} months"
            )
        )
    elif decision_type == "CONDITIONAL":
        application.status = LoanStatus.APPROVED  # But with conditions
        messages.append(
            AIMessage(
                content=f"Loan CONDITIONALLY APPROVED: ${approved_amount:,.2f} at {interest_rate:.2%} APR with conditions"
            )
        )
    else:
        application.status = LoanStatus.REJECTED
        messages.append(
            AIMessage(content=f"Loan REJECTED: {'; '.join(rejection_reasons)}")
        )

    # Determine if human review is needed
    human_review_required = False
    if confidence_score < 0.7 or decision_type == "CONDITIONAL":
        human_review_required = True
        messages.append(
            AIMessage(
                content="Human review recommended due to low confidence or conditional approval"
            )
        )

    return {
        **state,
        "application": application,
        "messages": messages,
        "decision_complete": True,
        "human_review_required": human_review_required,
        "workflow_status": (
            WorkflowStatus.COMPLETED
            if not human_review_required
            else WorkflowStatus.REQUIRES_HUMAN
        ),
        "stage_results": {
            **state.get("stage_results", {}),
            "decision": decision_type,
            "confidence": confidence_score,
        },
        "next_action": "complete" if not human_review_required else "human_review",
    }


def human_review_node(state: LoanWorkflowState) -> LoanWorkflowState:
    """Handle cases requiring human underwriter review"""
    application = state["application"]
    messages = state.get("messages", [])

    messages.append(
        AIMessage(
            content="Application flagged for human review. Assigning to underwriter..."
        )
    )

    # In a real system, this would assign to an available underwriter
    application.assigned_underwriter = "Senior Underwriter"

    return {
        **state,
        "application": application,
        "messages": messages,
        "workflow_status": WorkflowStatus.REQUIRES_HUMAN,
        "next_action": "await_human_decision",
    }


def should_continue(state: LoanWorkflowState) -> str:
    """Determine the next step in the workflow"""
    if state.get("workflow_status") == WorkflowStatus.FAILED:
        return "end"

    next_action = state.get("next_action")

    if next_action == "verify_documents":
        return "verify_documents"
    elif next_action == "credit_check":
        return "credit_check"
    elif next_action == "risk_assessment":
        return "risk_assessment"
    elif next_action == "make_decision":
        return "make_decision"
    elif next_action == "human_review":
        return "human_review"
    elif next_action == "complete":
        return "end"
    else:
        return "end"


def create_loan_workflow() -> StateGraph:
    """Create and return the loan origination workflow graph"""

    workflow = StateGraph(LoanWorkflowState)

    # Add nodes
    workflow.add_node("validate_application", validate_application_node)
    workflow.add_node("verify_documents", verify_documents_node)
    workflow.add_node("credit_check", credit_check_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("make_decision", decision_node)
    workflow.add_node("human_review", human_review_node)

    # Add edges
    workflow.add_edge(START, "validate_application")
    workflow.add_conditional_edges(
        "validate_application",
        should_continue,
        {"verify_documents": "verify_documents", "end": END},
    )
    workflow.add_conditional_edges(
        "verify_documents",
        should_continue,
        {"credit_check": "credit_check", "end": END},
    )
    workflow.add_conditional_edges(
        "credit_check",
        should_continue,
        {"risk_assessment": "risk_assessment", "end": END},
    )
    workflow.add_conditional_edges(
        "risk_assessment",
        should_continue,
        {"make_decision": "make_decision", "end": END},
    )
    workflow.add_conditional_edges(
        "make_decision", should_continue, {"human_review": "human_review", "end": END}
    )
    workflow.add_edge("human_review", END)

    return workflow


# Convenience function to run the complete workflow
async def process_loan_application(application: LoanApplication) -> LoanApplication:
    """Process a loan application through the complete workflow"""

    workflow = create_loan_workflow()
    app = workflow.compile()

    initial_state: LoanWorkflowState = {
        "application": application,
        "messages": [
            HumanMessage(
                content=f"Processing loan application {application.application_number}"
            )
        ],
        "next_action": "validate_application",
        "workflow_status": WorkflowStatus.PENDING,
        "error_message": None,
        "human_review_required": False,
        "underwriter_notes": [],
        "credit_check_complete": False,
        "document_verification_complete": False,
        "risk_assessment_complete": False,
        "decision_complete": False,
        "retry_count": 0,
        "stage_results": {},
    }

    # Run the workflow
    final_state = await app.ainvoke(initial_state)

    return final_state["application"]
