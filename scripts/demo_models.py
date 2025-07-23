#!/usr/bin/env python3
"""
LOSA Models Demonstration
========================

This script demonstrates the core Pydantic models of the Loan Origination System
without requiring database or external service dependencies.
"""

import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Direct import to avoid package-level dependencies
import importlib.util
import os

# Load the loan models module directly
models_path = os.path.join(
    os.path.dirname(Path(__file__).parent), 'src', 'losa', 'models', 'loan.py'
)
spec = importlib.util.spec_from_file_location("loan_models", models_path)
loan_models = importlib.util.module_from_spec(spec)
sys.modules["loan_models"] = loan_models
spec.loader.exec_module(loan_models)

# Import the classes we need
LoanType = loan_models.LoanType
LoanStatus = loan_models.LoanStatus
EmploymentStatus = loan_models.EmploymentStatus
MaritalStatus = loan_models.MaritalStatus
DocumentType = loan_models.DocumentType
Address = loan_models.Address
PersonalInfo = loan_models.PersonalInfo
EmploymentInfo = loan_models.EmploymentInfo
FinancialInfo = loan_models.FinancialInfo
LoanDetails = loan_models.LoanDetails
Document = loan_models.Document
CreditScore = loan_models.CreditScore
RiskAssessment = loan_models.RiskAssessment
LoanDecision = loan_models.LoanDecision
LoanApplication = loan_models.LoanApplication
LoanApplicationCreate = loan_models.LoanApplicationCreate


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'=' * 60}")
    print(f"🏦 {title}")
    print(f"{'=' * 60}")


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'─' * 40}")
    print(f"📋 {title}")
    print(f"{'─' * 40}")


def demonstrate_enums():
    """Demonstrate the enum types"""
    print_section("Available Options")

    print("🎯 Loan Types:")
    for loan_type in LoanType:
        print(f"   • {loan_type.value.title()}")

    print("\n🔄 Application Statuses:")
    for status in LoanStatus:
        print(f"   • {status.value.replace('_', ' ').title()}")

    print("\n💼 Employment Types:")
    for emp_type in EmploymentStatus:
        print(f"   • {emp_type.value.replace('_', ' ').title()}")

    print("\n📎 Document Types:")
    for doc_type in DocumentType:
        print(f"   • {doc_type.value.replace('_', ' ').title()}")


def demonstrate_data_validation():
    """Demonstrate Pydantic validation features"""
    print_section("Data Validation Examples")

    print("✅ Valid Data Examples:")

    # Valid address
    try:
        address = Address(
            street="123 Tech Avenue", city="San Francisco", state="CA", zip_code="94105"
        )
        print(
            f"   📍 Address: {address.street}, {address.city}, {address.state} {address.zip_code}"
        )
    except Exception as e:
        print(f"   ❌ Address error: {e}")

    # Valid phone numbers
    valid_phones = ["4155551234", "14155551234", "+14155551234"]
    for phone in valid_phones:
        try:
            PersonalInfo(
                first_name="John",
                last_name="Doe",
                date_of_birth=datetime(1990, 1, 1),
                ssn="123-45-6789",
                phone=phone,
                email="john@example.com",
                marital_status=MaritalStatus.SINGLE,
                dependents=0,
                address=address,
            )
            print(f"   📱 Valid phone: {phone}")
        except Exception as e:
            print(f"   ❌ Phone error for {phone}: {e}")

    print("\n❌ Invalid Data Examples:")

    # Invalid zip code
    try:
        Address(street="123 Main St", city="Anytown", state="CA", zip_code="invalid")
    except Exception as e:
        print(f"   🚫 Invalid zip code caught: {type(e).__name__}")

    # Invalid email
    try:
        PersonalInfo(
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            ssn="123-45-6789",
            phone="4155551234",
            email="not-an-email",
            marital_status=MaritalStatus.SINGLE,
            dependents=0,
            address=address,
        )
    except Exception as e:
        print(f"   🚫 Invalid email caught: {type(e).__name__}")


def create_sample_application():
    """Create a complete sample loan application"""
    print_section("Complete Loan Application Creation")

    # Address
    address = Address(
        street="456 Innovation Drive", city="Palo Alto", state="CA", zip_code="94301"
    )
    print(f"📍 Address: {address.street}, {address.city}")

    # Personal Information
    personal_info = PersonalInfo(
        first_name="Sarah",
        last_name="Chen",
        date_of_birth=datetime(1988, 3, 15),
        ssn="987-65-4321",
        phone="6505551234",
        email="sarah.chen@techcorp.com",
        marital_status=MaritalStatus.MARRIED,
        dependents=1,
        address=address,
    )
    print(f"👤 Applicant: {personal_info.first_name} {personal_info.last_name}")
    print(f"📧 Email: {personal_info.email}")
    print(
        f"👨‍👩‍👧‍👦 Family: {personal_info.marital_status.value}, {personal_info.dependents} dependents"
    )

    # Employment Information
    employment_info = EmploymentInfo(
        status=EmploymentStatus.EMPLOYED,
        employer_name="TechCorp Innovations",
        job_title="Senior Product Manager",
        employment_start_date=datetime(2019, 8, 1),
        annual_income=Decimal("125000"),
        monthly_income=Decimal("10416.67"),
        other_income=Decimal("2000"),
    )
    print(f"💼 Job: {employment_info.job_title} at {employment_info.employer_name}")
    print(
        f"💰 Income: ${employment_info.annual_income:,}/year (${employment_info.monthly_income:,}/month)"
    )
    print(
        f"📅 Employment: {employment_info.employment_start_date.strftime('%B %Y')} - Present"
    )

    # Financial Information
    financial_info = FinancialInfo(
        monthly_rent_mortgage=Decimal("3500"),
        monthly_debt_payments=Decimal("850"),
        monthly_expenses=Decimal("2800"),
        savings_balance=Decimal("45000"),
        checking_balance=Decimal("8500"),
        credit_cards_debt=Decimal("4200"),
        assets_value=Decimal("75000"),
    )
    print(f"🏠 Housing: ${financial_info.monthly_rent_mortgage:,}/month")
    print(f"💳 Debt Payments: ${financial_info.monthly_debt_payments:,}/month")
    print(f"💰 Savings: ${financial_info.savings_balance:,}")

    # Loan Details
    loan_details = LoanDetails(
        loan_type=LoanType.HOME,
        requested_amount=Decimal("450000"),
        requested_term_months=360,
        purpose="Purchase primary residence in Palo Alto. This will be our family home where we plan to raise our children.",
        collateral_description="Single family home at 789 Oak Street, Palo Alto, CA",
        collateral_value=Decimal("520000"),
    )
    print(
        f"🏡 Loan: ${loan_details.requested_amount:,} {loan_details.loan_type.value} loan"
    )
    print(
        f"📅 Term: {loan_details.requested_term_months} months ({loan_details.requested_term_months//12} years)"
    )
    print(f"🎯 Purpose: {loan_details.purpose[:60]}...")

    # Create the full application
    application = LoanApplication(
        application_number="DEMO-20240722-CHEN",
        personal_info=personal_info,
        employment_info=employment_info,
        financial_info=financial_info,
        loan_details=loan_details,
    )

    # Calculate and display key metrics
    dti_ratio = application.debt_to_income_ratio
    print("\n📊 Key Metrics:")
    print(f"   • Debt-to-Income Ratio: {dti_ratio:.1%}")
    print(
        f"   • Monthly Net Income: ${employment_info.monthly_income - financial_info.monthly_rent_mortgage - financial_info.monthly_debt_payments:,}"
    )
    print(
        f"   • Loan-to-Value Ratio: {(loan_details.requested_amount / loan_details.collateral_value):.1%}"
    )

    return application


def demonstrate_documents():
    """Demonstrate document management"""
    print_section("Document Management")

    documents = [
        Document(
            document_type=DocumentType.IDENTITY,
            file_name="drivers_license.pdf",
            file_path="/uploads/drivers_license.pdf",
            file_size=512 * 1024,  # 512KB
            mime_type="application/pdf",
            verified=True,
            verification_notes="Valid California driver's license, expires 2027",
        ),
        Document(
            document_type=DocumentType.INCOME_PROOF,
            file_name="pay_stubs_recent.pdf",
            file_path="/uploads/pay_stubs_recent.pdf",
            file_size=256 * 1024,  # 256KB
            mime_type="application/pdf",
            verified=True,
            verification_notes="Last 3 pay stubs showing consistent income",
        ),
        Document(
            document_type=DocumentType.TAX_RETURN,
            file_name="tax_return_2023.pdf",
            file_path="/uploads/tax_return_2023.pdf",
            file_size=1024 * 1024,  # 1MB
            mime_type="application/pdf",
            verified=False,
            verification_notes=None,
        ),
    ]

    print("📎 Uploaded Documents:")
    for i, doc in enumerate(documents, 1):
        status = "✅ Verified" if doc.verified else "⏳ Pending"
        size_mb = doc.file_size / (1024 * 1024)
        print(f"   {i}. {doc.document_type.value.replace('_', ' ').title()}")
        print(f"      📄 File: {doc.file_name}")
        print(f"      📊 Size: {size_mb:.1f}MB")
        print(f"      🔍 Status: {status}")
        if doc.verification_notes:
            print(f"      📝 Notes: {doc.verification_notes}")


def demonstrate_assessment_results():
    """Demonstrate credit score and risk assessment"""
    print_section("AI Assessment Results")

    # Credit Score
    credit_score = CreditScore(
        score=742,
        bureau="Experian",
        date_obtained=datetime.now(),
        factors=[
            "Strong payment history",
            "Low credit utilization (18%)",
            "Long credit history (12 years)",
        ],
    )

    print("📊 Credit Assessment:")
    print(f"   🎯 Score: {credit_score.score} ({credit_score.bureau})")
    print(f"   📅 Date: {credit_score.date_obtained.strftime('%Y-%m-%d')}")
    print("   💡 Positive Factors:")
    for factor in credit_score.factors:
        print(f"      • {factor}")

    # Risk Assessment
    risk_assessment = RiskAssessment(
        debt_to_income_ratio=0.418,
        credit_utilization_ratio=0.18,
        payment_history_score=95,
        employment_stability_score=88,
        overall_risk_score=76,
        risk_level="MEDIUM",
        risk_factors=[
            "High loan amount relative to income",
            "California housing market volatility",
        ],
    )

    print("\n⚠️ Risk Assessment:")
    print(f"   📊 Overall Score: {risk_assessment.overall_risk_score}/100")
    print(f"   🎯 Risk Level: {risk_assessment.risk_level}")
    print(f"   📈 DTI Ratio: {risk_assessment.debt_to_income_ratio:.1%}")
    print(f"   💳 Credit Utilization: {risk_assessment.credit_utilization_ratio:.1%}")
    print(f"   📋 Payment History: {risk_assessment.payment_history_score}/100")
    print(
        f"   💼 Employment Stability: {risk_assessment.employment_stability_score}/100"
    )

    if risk_assessment.risk_factors:
        print("   🚨 Risk Factors:")
        for factor in risk_assessment.risk_factors:
            print(f"      • {factor}")


def demonstrate_loan_decision():
    """Demonstrate loan decision making"""
    print_section("Loan Decision")

    decision = LoanDecision(
        decision="APPROVED",
        approved_amount=Decimal("425000"),
        approved_term_months=360,
        interest_rate=0.0675,
        conditions=[
            "Property appraisal must confirm value of at least $520,000",
            "Homeowner's insurance required before closing",
            "Final employment verification within 30 days of closing",
        ],
        rejection_reasons=[],
        decision_date=datetime.now(),
        decision_maker="AI Underwriting System v2.1",
        confidence_score=0.84,
    )

    print("⚖️ Final Decision:")
    decision_icon = (
        "✅"
        if decision.decision == "APPROVED"
        else "❌" if decision.decision == "REJECTED" else "⚠️"
    )
    print(f"   {decision_icon} Status: {decision.decision}")
    print(f"   💰 Approved Amount: ${decision.approved_amount:,}")
    print(f"   📊 Interest Rate: {decision.interest_rate:.3%} APR")
    print(
        f"   📅 Term: {decision.approved_term_months} months ({decision.approved_term_months//12} years)"
    )
    print(f"   🎯 Confidence: {decision.confidence_score:.1%}")
    print(f"   🤖 Decision Maker: {decision.decision_maker}")

    if decision.conditions:
        print("   📋 Conditions:")
        for i, condition in enumerate(decision.conditions, 1):
            print(f"      {i}. {condition}")

    # Calculate monthly payment
    monthly_rate = decision.interest_rate / 12
    num_payments = decision.approved_term_months
    principal = float(decision.approved_amount)

    # Standard mortgage payment calculation
    monthly_payment = (
        principal
        * (monthly_rate * (1 + monthly_rate) ** num_payments)
        / ((1 + monthly_rate) ** num_payments - 1)
    )

    print(f"\n💵 Estimated Monthly Payment: ${monthly_payment:,.2f}")
    print(f"💰 Total Interest: ${(monthly_payment * num_payments) - principal:,.2f}")


def main():
    """Main demonstration function"""

    print_header("LOSA Models & Data Structures Demo")

    print(
        """
This demonstration showcases the core data models and validation features
of the Loan Origination System Application (LOSA).

🎯 What you'll see:
   • Pydantic model validation and type safety
   • Comprehensive loan application data structures
   • Document management capabilities
   • Credit assessment and risk evaluation models
   • Automated decision making results
"""
    )

    try:
        # Show available options
        demonstrate_enums()

        # Show validation features
        demonstrate_data_validation()

        # Create complete application
        create_sample_application()

        # Document management
        demonstrate_documents()

        # Assessment results
        demonstrate_assessment_results()

        # Final decision
        demonstrate_loan_decision()

        print_header("🎉 Models Demonstration Complete!")

        print(
            """
✅ Successfully demonstrated LOSA data models!

🔍 Key Features Shown:
   • Comprehensive data validation with Pydantic
   • Type safety with enums and proper typing
   • Financial precision with Decimal types
   • Complex nested data structures
   • Business rule validation
   • Rich metadata and audit information

💡 Model Highlights:
   • LoanApplication: Complete application with all components
   • Document: File management with verification status
   • CreditScore: Credit bureau integration results
   • RiskAssessment: Multi-factor risk evaluation
   • LoanDecision: Final decision with conditions and explanations

🚀 Next Steps:
   • Run the full demo: python demo.py
   • Try the API: python run.py (requires database setup)
   • Explore workflows: python examples/example_loan_workflow.py
"""
        )

    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
