#!/usr/bin/env python3
"""
LOSA Example: Complete Loan Application Workflow

This example demonstrates how to use the Loan Origination System Application (LOSA)
to create, process, and manage loan applications through the complete AI-powered workflow.

Usage:
    python examples/example_loan_workflow.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv


from losa.models.loan import (
    LoanApplicationCreate,
    PersonalInfo,
    Address,
    EmploymentInfo,
    FinancialInfo,
    LoanDetails,
    LoanType,
    EmploymentStatus,
    MaritalStatus,
    Document,
    DocumentType,
)
from losa.services.loan_service import LoanService

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

load_dotenv()


def create_sample_application() -> LoanApplicationCreate:
    """Create a sample loan application for demonstration"""

    # Personal information
    address = Address(
        street='123 Tech Avenue',
        city='San Francisco',
        state='CA',
        zip_code='94105',
        country='US',
    )

    personal_info = PersonalInfo(
        first_name='Alice',
        middle_name='Marie',
        last_name='Johnson',
        date_of_birth=datetime(1985, 3, 15),
        ssn='123-45-6789',
        phone='4155551234',
        email='alice.johnson@example.com',
        marital_status=MaritalStatus.MARRIED,
        dependents=2,
        address=address,
    )

    # Employment information
    employment_info = EmploymentInfo(
        status=EmploymentStatus.EMPLOYED,
        employer_name='TechCorp Inc.',
        job_title='Senior Software Engineer',
        employment_start_date=datetime(2020, 6, 1),
        annual_income=Decimal('95000'),
        monthly_income=Decimal('7916.67'),
        other_income=Decimal('5000'),  # Side consulting income
    )

    # Financial information
    financial_info = FinancialInfo(
        monthly_rent_mortgage=Decimal('2800'),  # Bay Area housing costs
        monthly_debt_payments=Decimal('450'),  # Car loan + student loans
        monthly_expenses=Decimal('2200'),  # Living expenses
        savings_balance=Decimal('25000'),
        checking_balance=Decimal('8500'),
        credit_cards_debt=Decimal('3500'),
        assets_value=Decimal('35000'),  # Car + some investments
    )

    # Loan details
    loan_details = LoanDetails(
        loan_type=LoanType.PERSONAL,
        requested_amount=Decimal('30000'),
        requested_term_months=48,
        purpose='Home renovation and debt consolidation. Planning to update kitchen and bathrooms while consolidating high-interest credit card debt.',
        collateral_value=Decimal('0'),  # No collateral for personal loan
    )

    return LoanApplicationCreate(
        personal_info=personal_info,
        employment_info=employment_info,
        financial_info=financial_info,
        loan_details=loan_details,
    )


def create_sample_documents(application_id) -> list[Document]:
    """Create sample documents for the application"""

    documents = [
        Document(
            document_type=DocumentType.IDENTITY,
            file_name='drivers_license.jpg',
            file_path=f'/uploads/{application_id}/drivers_license.jpg',
            file_size=1024 * 512,  # 512KB
            mime_type='image/jpeg',
            verified=False,
        ),
        Document(
            document_type=DocumentType.INCOME_PROOF,
            file_name='pay_stub_recent.pdf',
            file_path=f'/uploads/{application_id}/pay_stub_recent.pdf',
            file_size=1024 * 256,  # 256KB
            mime_type='application/pdf',
            verified=False,
        ),
        Document(
            document_type=DocumentType.EMPLOYMENT_VERIFICATION,
            file_name='employment_letter.pdf',
            file_path=f'/uploads/{application_id}/employment_letter.pdf',
            file_size=1024 * 128,  # 128KB
            mime_type='application/pdf',
            verified=False,
        ),
        Document(
            document_type=DocumentType.BANK_STATEMENT,
            file_name='bank_statement_march.pdf',
            file_path=f'/uploads/{application_id}/bank_statement_march.pdf',
            file_size=1024 * 384,  # 384KB
            mime_type='application/pdf',
            verified=False,
        ),
    ]

    return documents


def print_application_summary(application):
    """Print a formatted summary of the loan application"""

    print('\n' + '=' * 60)
    print('📋 LOAN APPLICATION SUMMARY')
    print('=' * 60)

    print(f'📄 Application Number: {application.application_number}')
    print(f'📅 Created: {application.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'🔄 Status: {application.status.upper()}')

    print(
        f'\n👤 Applicant: {application.personal_info.first_name} {application.personal_info.last_name}'
    )
    print(f'📧 Email: {application.personal_info.email}')
    print(f'📱 Phone: {application.personal_info.phone}')

    print(f'\n💼 Employment: {application.employment_info.job_title}')
    print(f'🏢 Employer: {application.employment_info.employer_name}')
    print(f'💰 Annual Income: ${application.employment_info.annual_income:,}')

    print('\n🏦 Loan Request:')
    print(f'   Type: {application.loan_details.loan_type.title()}')
    print(f'   Amount: ${application.loan_details.requested_amount:,}')
    print(f'   Term: {application.loan_details.requested_term_months} months')

    # Calculate and display key ratios
    dti_ratio = application.debt_to_income_ratio
    print('\n📊 Key Metrics:')
    print(f'   Debt-to-Income Ratio: {dti_ratio:.1%}')
    print(f'   Monthly Income: ${application.employment_info.monthly_income:,}')
    print(
        f'   Monthly Debts: ${application.financial_info.monthly_debt_payments + application.financial_info.monthly_rent_mortgage:,}'
    )

    print(f'\n📎 Documents: {len(application.documents)} uploaded')
    for doc in application.documents:
        status = '✅ Verified' if doc.verified else '⏳ Pending'
        print(f'   - {doc.document_type.replace("_", " ").title()}: {status}')


def print_workflow_results(application):
    """Print the results of workflow processing"""

    print('\n' + '=' * 60)
    print('🤖 AI WORKFLOW RESULTS')
    print('=' * 60)

    # Credit Score Results
    if application.credit_score:
        print('\n📊 Credit Assessment:')
        print(f'   Credit Score: {application.credit_score.score}')
        print(f'   Bureau: {application.credit_score.bureau}')
        if application.credit_score.factors:
            print(f'   Factors: {", ".join(application.credit_score.factors)}')

    # Risk Assessment Results
    if application.risk_assessment:
        print('\n⚠️  Risk Assessment:')
        print(
            f'   Overall Risk Score: {application.risk_assessment.overall_risk_score}/100'
        )
        print(f'   Risk Level: {application.risk_assessment.risk_level}')
        print(
            f'   Payment History Score: {application.risk_assessment.payment_history_score}/100'
        )
        print(
            f'   Employment Stability: {application.risk_assessment.employment_stability_score}/100'
        )

        if application.risk_assessment.risk_factors:
            print('   Risk Factors:')
            for factor in application.risk_assessment.risk_factors:
                print(f'     • {factor}')

    # Decision Results
    if application.decision:
        print('\n🏛️  Loan Decision:')

        decision_icon = {'APPROVED': '✅', 'REJECTED': '❌', 'CONDITIONAL': '⚠️'}.get(
            application.decision.decision, '❓'
        )

        print(f'   {decision_icon} Decision: {application.decision.decision}')
        print(
            f'   📅 Decision Date: {application.decision.decision_date.strftime("%Y-%m-%d %H:%M:%S")}'
        )
        print(f'   🤖 Decision Maker: {application.decision.decision_maker}')
        print(f'   🎯 Confidence: {application.decision.confidence_score:.1%}')

        if application.decision.decision in ['APPROVED', 'CONDITIONAL']:
            print('\n💰 Approved Terms:')
            print(f'   Amount: ${application.decision.approved_amount:,}')
            print(f'   Term: {application.decision.approved_term_months} months')
            print(f'   Interest Rate: {application.decision.interest_rate:.2%} APR')

            if application.decision.conditions:
                print('   📋 Conditions:')
                for condition in application.decision.conditions:
                    print(f'     • {condition}')

        elif application.decision.decision == 'REJECTED':
            print('\n❌ Rejection Reasons:')
            for reason in application.decision.rejection_reasons:
                print(f'   • {reason}')

    # Final Status
    print(f'\n🔄 Final Status: {application.status.upper()}')

    if application.assigned_underwriter:
        print(f'👨‍💼 Assigned to: {application.assigned_underwriter}')

    print('=' * 60)


async def demonstrate_complete_workflow():
    """Demonstrate the complete loan application workflow"""

    print('🏦 LOSA - Loan Origination System Application')
    print('🚀 Demonstrating Complete AI-Powered Loan Workflow')
    print('=' * 60)

    try:
        # Initialize the loan service
        loan_service = LoanService()
        print('✅ Loan service initialized')

        # Step 1: Create a new loan application
        print('\n📝 Step 1: Creating loan application...')
        application_data = create_sample_application()
        application = loan_service.create_application(
            application_data, user_id='demo_user'
        )
        print(f'✅ Application created: {application.application_number}')

        # Step 2: Add documents to the application
        print('\n📎 Step 2: Adding required documents...')
        sample_documents = create_sample_documents(application.id)

        for doc in sample_documents:
            added_doc = loan_service.add_document(
                application.id, doc, user_id='demo_user'
            )
            print(f'   ✅ Added: {added_doc.document_type.replace("_", " ").title()}')

        # Refresh application to get updated documents
        application = loan_service.get_application(application.id)

        # Step 3: Show initial application summary
        print_application_summary(application)

        # Step 4: Submit application for processing
        print('\n🚀 Step 3: Submitting application for AI processing...')
        submitted_app = loan_service.submit_application(
            application.id, user_id='demo_user'
        )
        print(f'✅ Application submitted with status: {submitted_app.status}')

        # Step 5: Process through AI workflow
        print('\n🤖 Step 4: Processing through AI workflow...')
        print('   This may take a few moments...')

        # Process the application through the complete workflow
        processed_app = await loan_service.process_application_workflow(application.id)

        print('✅ Workflow processing complete!')

        # Step 6: Display results
        print_workflow_results(processed_app)

        # Step 7: Demonstrate additional operations
        print('\n🔍 Step 5: Additional operations...')

        # Get application statistics
        stats = loan_service.get_application_statistics()
        print('📈 Current system statistics:')
        print(
            f'   Total applications: {sum(v for k, v in stats.items() if k.startswith("status_"))}'
        )
        print(
            f'   Recent applications (30 days): {stats.get("recent_applications", 0)}'
        )

        # Demonstrate status-based queries
        under_review = loan_service.get_applications_by_status(
            processed_app.status, limit=5
        )
        print(
            f"📋 Applications with status '{processed_app.status}': {len(under_review)}"
        )

        print('\n🎉 Demonstration completed successfully!')
        print(f'📄 Final application status: {processed_app.status.upper()}')

        if processed_app.decision:
            decision_summary = f'{processed_app.decision.decision}'
            if processed_app.decision.approved_amount:
                decision_summary += f' - ${processed_app.decision.approved_amount:,}'
            print(f'⚖️  Final decision: {decision_summary}')

        return processed_app

    except Exception as e:
        print(f'❌ Error during workflow demonstration: {str(e)}')
        import traceback

        traceback.print_exc()
        return None


async def demonstrate_manual_processing():
    """Demonstrate manual step-by-step processing"""

    print('\n' + '=' * 60)
    print('🔧 MANUAL WORKFLOW PROCESSING DEMONSTRATION')
    print('=' * 60)

    try:
        from losa.workflows.loan_workflow import (
            validate_application_node,
            verify_documents_node,
            credit_check_node,
            risk_assessment_node,
            decision_node,
        )
        from losa.workflows.loan_workflow import LoanWorkflowState, WorkflowStatus
        from langchain_core.messages import HumanMessage

        # Create a sample application
        loan_service = LoanService()
        application_data = create_sample_application()
        application = loan_service.create_application(application_data)

        # Add documents
        sample_documents = create_sample_documents(application.id)
        for doc in sample_documents:
            loan_service.add_document(application.id, doc)

        # Refresh to get documents
        application = loan_service.get_application(application.id)

        print(f'📝 Processing application: {application.application_number}')

        # Initialize workflow state
        state: LoanWorkflowState = {
            'application': application,
            'messages': [
                HumanMessage(content=f'Processing {application.application_number}')
            ],
            'next_action': None,
            'workflow_status': WorkflowStatus.PENDING,
            'error_message': None,
            'human_review_required': False,
            'underwriter_notes': [],
            'credit_check_complete': False,
            'document_verification_complete': False,
            'risk_assessment_complete': False,
            'decision_complete': False,
            'retry_count': 0,
            'stage_results': {},
        }

        # Step 1: Validate Application
        print('\n🔍 Step 1: Validating application...')
        state = validate_application_node(state)
        print(f'   Status: {state["workflow_status"]}')
        if state.get('error_message'):
            print(f'   Error: {state["error_message"]}')
            return

        # Step 2: Verify Documents
        print('\n📋 Step 2: Verifying documents...')
        state = verify_documents_node(state)
        print(
            f'   Status: Document verification complete: {state.get("document_verification_complete", False)}'
        )

        # Step 3: Credit Check
        print('\n💳 Step 3: Performing credit check...')
        state = credit_check_node(state)
        credit_score = state.get('stage_results', {}).get('credit_score', 'Unknown')
        print(f'   Credit Score: {credit_score}')
        print(
            f'   Status: Credit check complete: {state.get("credit_check_complete", False)}'
        )

        # Step 4: Risk Assessment
        print('\n⚠️  Step 4: Conducting risk assessment...')
        state = risk_assessment_node(state)
        risk_score = state.get('stage_results', {}).get('risk_score', 'Unknown')
        risk_level = state.get('stage_results', {}).get('risk_level', 'Unknown')
        print(f'   Risk Score: {risk_score}/100')
        print(f'   Risk Level: {risk_level}')

        # Step 5: Make Decision
        print('\n⚖️  Step 5: Making loan decision...')
        state = decision_node(state)
        decision = state.get('stage_results', {}).get('decision', 'Unknown')
        confidence = state.get('stage_results', {}).get('confidence', 0)
        print(f'   Decision: {decision}')
        print(f'   Confidence: {confidence:.1%}')
        print(f'   Human Review Required: {state.get("human_review_required", False)}')

        print('\n✅ Manual workflow processing completed!')

        # Display final application state
        final_app = state['application']
        print_workflow_results(final_app)

    except Exception as e:
        print(f'❌ Error during manual processing: {str(e)}')
        import traceback

        traceback.print_exc()


def main():
    """Main demonstration function"""

    print('🏦 LOSA Example: Complete Loan Workflow Demonstration')
    print('=' * 60)

    # Check if we can import the required modules
    try:
        from losa.database.config import check_database_connection

        if not check_database_connection():
            print('❌ Database connection failed!')
            print('Please ensure PostgreSQL is running and configured correctly.')
            print('Run: python run.py --init-db')
            return
    except ImportError:
        print('⚠️  Database check skipped (running without database)')

    print('🎯 This example will demonstrate:')
    print('   1. Creating a loan application')
    print('   2. Adding required documents')
    print('   3. Processing through AI workflow')
    print('   4. Displaying results and decisions')
    print('   5. Manual step-by-step processing')

    input('\nPress Enter to start the demonstration...')

    # Run the async demonstration
    try:
        # Complete workflow demonstration
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(demonstrate_complete_workflow())

        if result:
            print('\n' + '=' * 60)
            input('Press Enter to see manual processing demonstration...')

            # Manual processing demonstration
            loop.run_until_complete(demonstrate_manual_processing())

        loop.close()

    except KeyboardInterrupt:
        print('\n👋 Demonstration stopped by user')
    except Exception as e:
        print(f'\n❌ Demonstration failed: {str(e)}')
        import traceback

        traceback.print_exc()


if __name__ == '__main__':
    main()
