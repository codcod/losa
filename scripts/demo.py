#!/usr/bin/env python3
"""
LOSA Demonstration Script
========================

This script demonstrates the core features of the Loan Origination System Application (LOSA)
without requiring external services like databases or OpenAI API.

It shows:
1. Creating loan applications with validation
2. Document processing simulation
3. Risk assessment calculations
4. LangGraph workflow structure
5. Decision making logic

Run: python demo.py
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def print_header(title: str, char: str = '='):
    """Print a formatted header"""
    print(f'\n{char * 60}')
    print(f'🏦 {title}')
    print(f'{char * 60}')


def print_section(title: str):
    """Print a section header"""
    print(f'\n{"─" * 40}')
    print(f'📋 {title}')
    print(f'{"─" * 40}')


class DemoLoanApplication:
    """Simplified loan application for demonstration"""

    def __init__(self, data: Dict[str, Any]):
        self.id = f'demo-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
        self.application_number = (
            f'LOAN-{datetime.now().strftime("%Y%m%d")}-{self.id[-4:].upper()}'
        )
        self.data = data
        self.status = 'draft'
        self.documents = []
        self.credit_score = None
        self.risk_assessment = None
        self.decision = None
        self.created_at = datetime.now()

    def add_document(self, doc_type: str, filename: str):
        """Add a document to the application"""
        self.documents.append(
            {
                'type': doc_type,
                'filename': filename,
                'verified': False,
                'uploaded_at': datetime.now(),
            }
        )

    def calculate_dti_ratio(self) -> float:
        """Calculate debt-to-income ratio"""
        monthly_income = self.data.get('monthly_income', 0)
        monthly_debts = self.data.get('monthly_rent', 0) + self.data.get(
            'monthly_debt_payments', 0
        )
        return monthly_debts / monthly_income if monthly_income > 0 else 0

    def get_risk_factors(self) -> List[str]:
        """Identify risk factors"""
        factors = []

        dti = self.calculate_dti_ratio()
        if dti > 0.4:
            factors.append('High debt-to-income ratio')

        annual_income = self.data.get('annual_income', 0)
        if annual_income < 40000:
            factors.append('Low income')

        employment_months = self.data.get('employment_months', 0)
        if employment_months < 12:
            factors.append('Short employment history')

        savings = self.data.get('savings', 0)
        requested_amount = self.data.get('requested_amount', 0)
        if savings < (requested_amount * 0.1):
            factors.append('Low savings relative to loan amount')

        return factors

    def calculate_risk_score(self) -> int:
        """Calculate overall risk score (0-100, higher is better)"""
        score = 70  # Base score

        # Income factor
        annual_income = self.data.get('annual_income', 0)
        if annual_income > 100000:
            score += 15
        elif annual_income > 75000:
            score += 10
        elif annual_income > 50000:
            score += 5
        elif annual_income < 30000:
            score -= 20

        # DTI factor
        dti = self.calculate_dti_ratio()
        if dti < 0.2:
            score += 15
        elif dti < 0.3:
            score += 10
        elif dti > 0.4:
            score -= 20
        elif dti > 0.5:
            score -= 30

        # Employment stability
        employment_months = self.data.get('employment_months', 0)
        if employment_months > 24:
            score += 10
        elif employment_months > 12:
            score += 5
        elif employment_months < 6:
            score -= 15

        # Savings factor
        savings = self.data.get('savings', 0)
        if savings > 50000:
            score += 10
        elif savings > 20000:
            score += 5
        elif savings < 5000:
            score -= 10

        return max(0, min(100, score))


class DemoWorkflow:
    """Demonstration of LangGraph-style workflow"""

    def __init__(self):
        self.current_step = None
        self.completed_steps = []
        self.errors = []

    def validate_application(self, app: DemoLoanApplication) -> Dict[str, Any]:
        """Step 1: Validate application completeness"""
        self.current_step = 'validation'
        print('🔍 Validating loan application...')

        errors = []

        # Check required fields
        required_fields = [
            'first_name',
            'last_name',
            'annual_income',
            'requested_amount',
        ]
        for field in required_fields:
            if not app.data.get(field):
                errors.append(f'Missing required field: {field}')

        # Business rule validation
        if app.data.get('annual_income', 0) < 20000:
            errors.append('Annual income below minimum requirement ($20,000)')

        if app.data.get('requested_amount', 0) > 500000:
            errors.append('Requested amount exceeds maximum limit ($500,000)')

        dti = app.calculate_dti_ratio()
        if dti > 0.5:
            errors.append(f'Debt-to-income ratio too high: {dti:.1%}')

        if errors:
            self.errors.extend(errors)
            return {'status': 'failed', 'errors': errors}

        self.completed_steps.append('validation')
        print('   ✅ Application validation passed')
        return {'status': 'passed'}

    def verify_documents(self, app: DemoLoanApplication) -> Dict[str, Any]:
        """Step 2: Verify document completeness"""
        self.current_step = 'document_verification'
        print('📋 Verifying required documents...')

        required_docs = ['identity', 'income_proof']
        loan_amount = app.data.get('requested_amount', 0)

        if loan_amount > 50000:
            required_docs.extend(['bank_statement', 'tax_return'])

        uploaded_types = [doc['type'] for doc in app.documents]
        missing_docs = [doc for doc in required_docs if doc not in uploaded_types]

        if missing_docs:
            error = f'Missing required documents: {", ".join(missing_docs)}'
            self.errors.append(error)
            print(f'   ❌ {error}')
            return {'status': 'incomplete', 'missing_documents': missing_docs}

        # Simulate document verification
        for doc in app.documents:
            doc['verified'] = True
            print(f'   ✅ Verified: {doc["type"]} ({doc["filename"]})')

        self.completed_steps.append('document_verification')
        return {'status': 'verified'}

    def perform_credit_check(self, app: DemoLoanApplication) -> Dict[str, Any]:
        """Step 3: Simulate credit check"""
        self.current_step = 'credit_check'
        print('💳 Performing credit check...')

        # Simulate credit score calculation
        base_score = 650

        # Adjust based on income
        annual_income = app.data.get('annual_income', 0)
        if annual_income > 100000:
            base_score += 50
        elif annual_income > 75000:
            base_score += 30
        elif annual_income < 40000:
            base_score -= 40

        # Adjust based on DTI
        dti = app.calculate_dti_ratio()
        if dti < 0.2:
            base_score += 40
        elif dti < 0.3:
            base_score += 20
        elif dti > 0.4:
            base_score -= 50

        # Ensure score is in valid range
        credit_score = max(300, min(850, base_score))

        app.credit_score = {
            'score': credit_score,
            'bureau': 'Demo Credit Bureau',
            'date': datetime.now(),
            'factors': [],
        }

        if credit_score < 600:
            app.credit_score['factors'].extend(
                ['Payment history concerns', 'High credit utilization']
            )
        elif credit_score < 650:
            app.credit_score['factors'].append('Limited credit history')

        print(f'   📊 Credit Score: {credit_score}')
        print('   🏛️  Bureau: Demo Credit Bureau')

        if app.credit_score['factors']:
            print(f'   ⚠️  Factors: {", ".join(app.credit_score["factors"])}')

        self.completed_steps.append('credit_check')
        return {'status': 'completed', 'credit_score': credit_score}

    def assess_risk(self, app: DemoLoanApplication) -> Dict[str, Any]:
        """Step 4: Perform risk assessment"""
        self.current_step = 'risk_assessment'
        print('⚠️  Conducting risk assessment...')

        risk_score = app.calculate_risk_score()
        risk_factors = app.get_risk_factors()

        # Determine risk level
        if risk_score >= 80:
            risk_level = 'LOW'
        elif risk_score >= 65:
            risk_level = 'MEDIUM'
        elif risk_score >= 45:
            risk_level = 'HIGH'
        else:
            risk_level = 'VERY_HIGH'

        app.risk_assessment = {
            'overall_risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'dti_ratio': app.calculate_dti_ratio(),
            'assessment_date': datetime.now(),
        }

        print(f'   📊 Risk Score: {risk_score}/100')
        print(f'   🎯 Risk Level: {risk_level}')
        print(f'   📈 DTI Ratio: {app.calculate_dti_ratio():.1%}')

        if risk_factors:
            print('   🚨 Risk Factors:')
            for factor in risk_factors:
                print(f'      • {factor}')

        self.completed_steps.append('risk_assessment')
        return {
            'status': 'completed',
            'risk_score': risk_score,
            'risk_level': risk_level,
        }

    def make_decision(self, app: DemoLoanApplication) -> Dict[str, Any]:
        """Step 5: Make loan decision"""
        self.current_step = 'decision_making'
        print('⚖️  Making loan decision...')

        credit_score = app.credit_score['score']
        risk_score = app.risk_assessment['overall_risk_score']
        requested_amount = app.data.get('requested_amount', 0)

        # Decision logic
        decision_type = 'REJECTED'
        approved_amount = None
        interest_rate = None
        conditions = []
        rejection_reasons = []
        confidence_score = 0.0

        if risk_score >= 75 and credit_score >= 700:
            # High confidence approval
            decision_type = 'APPROVED'
            approved_amount = requested_amount
            interest_rate = 0.045 + (750 - credit_score) * 0.0001
            confidence_score = 0.9

        elif risk_score >= 65 and credit_score >= 650:
            # Conditional approval or reduced amount
            if requested_amount > 100000:
                decision_type = 'CONDITIONAL'
                approved_amount = min(requested_amount * 0.8, 100000)
                conditions.append('Reduced loan amount due to risk assessment')
            else:
                decision_type = 'APPROVED'
                approved_amount = requested_amount

            interest_rate = 0.06 + (700 - credit_score) * 0.0002
            confidence_score = 0.75

            if app.calculate_dti_ratio() > 0.35:
                conditions.append('Additional income verification required')

        elif risk_score >= 45 and credit_score >= 600:
            # High-risk conditional approval
            decision_type = 'CONDITIONAL'
            approved_amount = min(requested_amount * 0.6, 50000)
            interest_rate = 0.08 + (650 - credit_score) * 0.0003
            confidence_score = 0.6

            conditions.extend(
                [
                    'Reduced loan amount due to high risk',
                    'Cosigner required',
                    'Additional collateral may be required',
                ]
            )

        else:
            # Rejection
            decision_type = 'REJECTED'
            confidence_score = 0.8

            if credit_score < 600:
                rejection_reasons.append('Credit score below minimum requirement')
            if risk_score < 45:
                rejection_reasons.append('High overall risk assessment')
            if app.calculate_dti_ratio() > 0.5:
                rejection_reasons.append(
                    'Debt-to-income ratio exceeds acceptable limits'
                )

        app.decision = {
            'decision': decision_type,
            'approved_amount': approved_amount,
            'interest_rate': interest_rate,
            'conditions': conditions,
            'rejection_reasons': rejection_reasons,
            'confidence_score': confidence_score,
            'decision_date': datetime.now(),
            'decision_maker': 'Demo AI System',
        }

        # Print decision details
        decision_icon = {'APPROVED': '✅', 'REJECTED': '❌', 'CONDITIONAL': '⚠️'}.get(
            decision_type, '❓'
        )
        print(f'   {decision_icon} Decision: {decision_type}')
        print(f'   🎯 Confidence: {confidence_score:.1%}')

        if decision_type in ['APPROVED', 'CONDITIONAL']:
            print(f'   💰 Approved Amount: ${approved_amount:,.2f}')
            print(f'   📊 Interest Rate: {interest_rate:.2%} APR')

            if conditions:
                print('   📋 Conditions:')
                for condition in conditions:
                    print(f'      • {condition}')

        elif decision_type == 'REJECTED':
            print('   ❌ Rejection Reasons:')
            for reason in rejection_reasons:
                print(f'      • {reason}')

        app.status = decision_type.lower()
        self.completed_steps.append('decision_making')

        return {
            'status': 'completed',
            'decision': decision_type,
            'confidence': confidence_score,
        }


def create_sample_applications():
    """Create sample loan applications for demonstration"""

    applications = [
        {
            'name': 'High-Quality Applicant',
            'data': {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'annual_income': 95000,
                'monthly_income': 7916.67,
                'employment_months': 36,
                'requested_amount': 30000,
                'loan_type': 'personal',
                'purpose': 'Home renovation',
                'monthly_rent': 2000,
                'monthly_debt_payments': 400,
                'savings': 25000,
                'credit_cards_debt': 2000,
            },
            'documents': [
                ('identity', 'drivers_license.jpg'),
                ('income_proof', 'pay_stub.pdf'),
                ('bank_statement', 'bank_statement.pdf'),
            ],
        },
        {
            'name': 'Medium-Risk Applicant',
            'data': {
                'first_name': 'Bob',
                'last_name': 'Smith',
                'annual_income': 55000,
                'monthly_income': 4583.33,
                'employment_months': 18,
                'requested_amount': 25000,
                'loan_type': 'personal',
                'purpose': 'Debt consolidation',
                'monthly_rent': 1500,
                'monthly_debt_payments': 800,
                'savings': 8000,
                'credit_cards_debt': 5000,
            },
            'documents': [
                ('identity', 'passport.jpg'),
                ('income_proof', 'employment_letter.pdf'),
            ],
        },
        {
            'name': 'High-Risk Applicant',
            'data': {
                'first_name': 'Charlie',
                'last_name': 'Brown',
                'annual_income': 35000,
                'monthly_income': 2916.67,
                'employment_months': 8,
                'requested_amount': 20000,
                'loan_type': 'personal',
                'purpose': 'Medical expenses',
                'monthly_rent': 1200,
                'monthly_debt_payments': 600,
                'savings': 2000,
                'credit_cards_debt': 8000,
            },
            'documents': [
                ('identity', 'drivers_license.jpg'),
                ('income_proof', 'pay_stub.pdf'),
            ],
        },
    ]

    return applications


def demonstrate_single_application(app_data: Dict[str, Any], workflow: DemoWorkflow):
    """Demonstrate processing a single loan application"""

    print_section(f'Processing: {app_data["name"]}')

    # Create application
    app = DemoLoanApplication(app_data['data'])
    print(f'📄 Application: {app.application_number}')
    print(f'👤 Applicant: {app.data["first_name"]} {app.data["last_name"]}')
    print(f'💰 Requested: ${app.data["requested_amount"]:,} ({app.data["loan_type"]})')
    print(f'💼 Income: ${app.data["annual_income"]:,}/year')
    print(f'📊 DTI Ratio: {app.calculate_dti_ratio():.1%}')

    # Add documents
    for doc_type, filename in app_data['documents']:
        app.add_document(doc_type, filename)

    # Process through workflow
    workflow_steps = [
        workflow.validate_application,
        workflow.verify_documents,
        workflow.perform_credit_check,
        workflow.assess_risk,
        workflow.make_decision,
    ]

    for step in workflow_steps:
        result = step(app)
        if result.get('status') in ['failed', 'incomplete']:
            print(f'\n❌ Workflow stopped at step: {workflow.current_step}')
            if workflow.errors:
                print('🚨 Errors:')
                for error in workflow.errors:
                    print(f'   • {error}')
            return app

    print('\n✅ Workflow completed successfully!')
    return app


def print_application_summary(app: DemoLoanApplication):
    """Print a detailed summary of the processed application"""

    print_section('Application Summary')

    print(f'📄 Application: {app.application_number}')
    print(f'👤 Applicant: {app.data["first_name"]} {app.data["last_name"]}')
    print(f'📅 Created: {app.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'🔄 Status: {app.status.upper()}')

    print('\n💼 Employment & Income:')
    print(f'   Annual Income: ${app.data["annual_income"]:,}')
    print(f'   Employment: {app.data["employment_months"]} months')
    print(f'   DTI Ratio: {app.calculate_dti_ratio():.1%}')

    print('\n🏦 Loan Details:')
    print(f'   Type: {app.data["loan_type"].title()}')
    print(f'   Requested: ${app.data["requested_amount"]:,}')
    print(f'   Purpose: {app.data["purpose"]}')

    if app.credit_score:
        print('\n📊 Credit Assessment:')
        print(f'   Score: {app.credit_score["score"]}')
        print(f'   Bureau: {app.credit_score["bureau"]}')
        if app.credit_score['factors']:
            print(f'   Factors: {", ".join(app.credit_score["factors"])}')

    if app.risk_assessment:
        print('\n⚠️  Risk Assessment:')
        print(f'   Risk Score: {app.risk_assessment["overall_risk_score"]}/100')
        print(f'   Risk Level: {app.risk_assessment["risk_level"]}')
        if app.risk_assessment['risk_factors']:
            print('   Risk Factors:')
            for factor in app.risk_assessment['risk_factors']:
                print(f'      • {factor}')

    if app.decision:
        decision = app.decision
        decision_icon = {'approved': '✅', 'rejected': '❌', 'conditional': '⚠️'}.get(
            app.status, '❓'
        )

        print(f'\n{decision_icon} Final Decision: {decision["decision"]}')
        print(f'   Confidence: {decision["confidence_score"]:.1%}')

        if decision['decision'] in ['APPROVED', 'CONDITIONAL']:
            print(f'   Approved Amount: ${decision["approved_amount"]:,}')
            print(f'   Interest Rate: {decision["interest_rate"]:.2%} APR')

            if decision['conditions']:
                print('   Conditions:')
                for condition in decision['conditions']:
                    print(f'      • {condition}')

        if decision['rejection_reasons']:
            print('   Rejection Reasons:')
            for reason in decision['rejection_reasons']:
                print(f'      • {reason}')


def demonstrate_batch_processing():
    """Demonstrate processing multiple applications"""

    print_header('LOSA Batch Processing Demo')

    sample_apps = create_sample_applications()
    results = []

    for app_data in sample_apps:
        workflow = DemoWorkflow()  # Fresh workflow for each application
        processed_app = demonstrate_single_application(app_data, workflow)
        results.append(processed_app)
        print('\n' + '─' * 60)

    # Summary statistics
    print_section('Batch Processing Summary')

    approved = sum(1 for app in results if app.status == 'approved')
    conditional = sum(1 for app in results if app.status == 'conditional')
    rejected = sum(1 for app in results if app.status == 'rejected')

    print('📊 Results Summary:')
    print(f'   ✅ Approved: {approved}')
    print(f'   ⚠️  Conditional: {conditional}')
    print(f'   ❌ Rejected: {rejected}')
    print(f'   📈 Approval Rate: {(approved + conditional) / len(results) * 100:.1f}%')

    return results


def demonstrate_langraph_concept():
    """Demonstrate the LangGraph workflow concept"""

    print_header('LangGraph Workflow Concept', '=')

    print(
        """
🔄 LOAN ORIGINATION WORKFLOW GRAPH:

    START
      ↓
  [Validate Application]
      ↓
  [Verify Documents] ←──── (Missing docs? Request upload)
      ↓
  [Credit Check]
      ↓
  [Risk Assessment]
      ↓
  [Make Decision]
      ↓
  Decision: APPROVED? → [Funding Process]
           CONDITIONAL? → [Human Review] → [Final Decision]
           REJECTED? → [Send Notification] → END
      ↓
    END

🎯 Key Features:
   • Conditional Logic: Different paths based on risk/credit scores
   • Human-in-the-Loop: Complex cases route to human review
   • State Management: Each node can access full application context
   • Error Handling: Failed steps can retry or route to manual review
   • Audit Trail: Every step and decision is logged

🧠 AI Integration:
   • Document Analysis: OCR + LLM extraction
   • Risk Assessment: ML models + rule-based logic
   • Decision Explanations: LLM-generated rationale
   • Fraud Detection: Pattern recognition across applications
"""
    )


def demonstrate_key_features():
    """Demonstrate key system features"""

    print_header('LOSA Key Features Demo')

    features = {
        '🤖 AI-Powered Processing': [
            'Document analysis and data extraction',
            'Income verification across multiple sources',
            'Risk assessment with multiple factors',
            'Decision explanations in natural language',
        ],
        '🔄 Workflow Orchestration': [
            'LangGraph-based state machine',
            'Conditional logic and branching',
            'Error handling and recovery',
            'Human-in-the-loop processing',
        ],
        '📊 Risk Management': [
            'Multi-factor risk scoring',
            'Debt-to-income ratio analysis',
            'Employment stability assessment',
            'Configurable risk thresholds',
        ],
        '🛡️ Compliance & Audit': [
            'Complete audit trail',
            'Regulatory compliance features',
            'Data retention policies',
            'Decision transparency',
        ],
        '🚀 Production Ready': [
            'RESTful API with OpenAPI docs',
            'Database persistence',
            'Background job processing',
            'Health monitoring and metrics',
        ],
    }

    for feature_category, feature_list in features.items():
        print(f'\n{feature_category}:')
        for feature in feature_list:
            print(f'   • {feature}')


def main():
    """Main demonstration function"""

    print_header('🏦 LOSA - Loan Origination System Demo')

    print(
        """
Welcome to the LOSA (Loan Origination System Application) demonstration!

This demo shows how LOSA processes loan applications through an AI-powered
workflow using LangChain and LangGraph concepts.

🎯 What you'll see:
   1. Application validation and processing
   2. Document verification simulation
   3. AI-powered credit assessment
   4. Risk evaluation and scoring
   5. Automated decision making
   6. Workflow orchestration concepts
"""
    )

    print('\n📍 Starting the demonstration...')

    try:
        # Feature overview
        demonstrate_key_features()

        print('\n📍 Showing the LangGraph workflow concept...')

        # Workflow concept
        demonstrate_langraph_concept()

        print('\n📍 Processing sample loan applications...')

        # Process sample applications
        results = demonstrate_batch_processing()

        print('\n📍 Showing detailed application summaries...')

        # Show detailed summaries
        for i, app in enumerate(results, 1):
            print_header(f'Detailed Summary - Application {i}')
            print_application_summary(app)

        print_header('🎉 Demonstration Complete!')

        print(
            f"""
✅ Successfully processed {len(results)} loan applications!

🔍 What happened:
   • Applications were validated for completeness
   • Documents were verified (simulated)
   • Credit scores were calculated using income and DTI ratios
   • Risk assessments considered multiple factors
   • Decisions were made using intelligent business rules
   • All steps were tracked and logged

🚀 Next Steps:
   • Try running the full system: python run.py
   • Explore the API docs: http://localhost:8000/docs
   • Run the interactive example: python examples/example_loan_workflow.py
   • Review the code in src/losa/ to see the full implementation

💡 Key Takeaways:
   • LangGraph orchestrates complex, conditional workflows
   • LangChain enables AI-powered document and data processing
   • The system combines rule-based logic with AI insights
   • Every decision is explainable and auditable
"""
        )

    except KeyboardInterrupt:
        print('\n\n👋 Demo interrupted by user. Thanks for trying LOSA!')
    except Exception as e:
        print(f'\n❌ Demo error: {str(e)}')
        print(
            'This is a simplified demo - check the full system for complete functionality!'
        )


if __name__ == '__main__':
    main()
