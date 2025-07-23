from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from uuid import UUID, uuid4


from ..models.loan import (
    LoanApplication,
    LoanApplicationCreate,
    LoanApplicationUpdate,
    LoanApplicationSummary,
    LoanStatus,
    Document,
    CreditScore,
    RiskAssessment,
    LoanDecision,
)
from ..database.models import (
    LoanApplicationDB,
    DocumentDB,
    CreditScoreDB,
    RiskAssessmentDB,
    create_audit_log,
)
from ..database.config import get_sync_session
from ..workflows.loan_workflow import process_loan_application
from ..chains.document_chain import CompleteDocumentProcessingChain

logger = logging.getLogger(__name__)


class LoanService:
    """Service class for loan application business logic"""

    def __init__(self):
        self.document_processor = CompleteDocumentProcessingChain()

    def _convert_db_to_pydantic(self, db_app: LoanApplicationDB) -> LoanApplication:
        """Convert database model to Pydantic model"""
        from ..models.loan import (
            PersonalInfo,
            Address,
            EmploymentInfo,
            FinancialInfo,
            LoanDetails,
        )

        # Create address
        address = Address(
            street=db_app.street,
            city=db_app.city,
            state=db_app.state,
            zip_code=db_app.zip_code,
            country=db_app.country,
        )

        # Create employer address if available
        employer_address = None
        if db_app.employer_street:
            employer_address = Address(
                street=db_app.employer_street,
                city=db_app.employer_city,
                state=db_app.employer_state,
                zip_code=db_app.employer_zip,
                country='US',
            )

        # Create personal info
        personal_info = PersonalInfo(
            first_name=db_app.first_name,
            last_name=db_app.last_name,
            middle_name=db_app.middle_name,
            date_of_birth=db_app.date_of_birth,
            ssn=db_app.ssn,
            phone=db_app.phone,
            email=db_app.email,
            marital_status=db_app.marital_status,
            dependents=db_app.dependents,
            address=address,
        )

        # Create employment info
        employment_info = EmploymentInfo(
            status=db_app.employment_status,
            employer_name=db_app.employer_name,
            job_title=db_app.job_title,
            employment_start_date=db_app.employment_start_date,
            annual_income=db_app.annual_income,
            monthly_income=db_app.monthly_income,
            other_income=db_app.other_income,
            employer_address=employer_address,
        )

        # Create financial info
        financial_info = FinancialInfo(
            monthly_rent_mortgage=db_app.monthly_rent_mortgage,
            monthly_debt_payments=db_app.monthly_debt_payments,
            monthly_expenses=db_app.monthly_expenses,
            savings_balance=db_app.savings_balance,
            checking_balance=db_app.checking_balance,
            existing_loans=db_app.existing_loans or [],
            credit_cards_debt=db_app.credit_cards_debt,
            assets_value=db_app.assets_value,
        )

        # Create loan details
        loan_details = LoanDetails(
            loan_type=db_app.loan_type,
            requested_amount=db_app.requested_amount,
            requested_term_months=db_app.requested_term_months,
            purpose=db_app.purpose,
            collateral_description=db_app.collateral_description,
            collateral_value=db_app.collateral_value,
        )

        # Convert documents
        documents = []
        for doc_db in db_app.documents:
            doc = Document(
                id=doc_db.id,
                document_type=doc_db.document_type,
                file_name=doc_db.file_name,
                file_path=doc_db.file_path,
                file_size=doc_db.file_size,
                mime_type=doc_db.mime_type,
                uploaded_at=doc_db.created_at,
                verified=doc_db.verified,
                verification_notes=doc_db.verification_notes,
            )
            documents.append(doc)

        # Convert credit score if available
        credit_score = None
        if db_app.credit_scores:
            latest_score = max(db_app.credit_scores, key=lambda x: x.date_obtained)
            credit_score = CreditScore(
                score=latest_score.score,
                bureau=latest_score.bureau,
                date_obtained=latest_score.date_obtained,
                factors=latest_score.factors or [],
            )

        # Convert risk assessment if available
        risk_assessment = None
        if db_app.risk_assessments:
            latest_assessment = max(db_app.risk_assessments, key=lambda x: x.created_at)
            risk_assessment = RiskAssessment(
                debt_to_income_ratio=float(latest_assessment.debt_to_income_ratio),
                credit_utilization_ratio=float(
                    latest_assessment.credit_utilization_ratio
                ),
                payment_history_score=latest_assessment.payment_history_score,
                employment_stability_score=latest_assessment.employment_stability_score,
                overall_risk_score=latest_assessment.overall_risk_score,
                risk_level=latest_assessment.risk_level,
                risk_factors=latest_assessment.risk_factors or [],
            )

        # Convert decision if available
        decision = None
        if db_app.decision:
            decision = LoanDecision(
                decision=db_app.decision,
                approved_amount=db_app.approved_amount,
                approved_term_months=db_app.approved_term_months,
                interest_rate=(
                    float(db_app.interest_rate) if db_app.interest_rate else None
                ),
                conditions=db_app.conditions or [],
                rejection_reasons=db_app.rejection_reasons or [],
                decision_date=db_app.decision_date,
                decision_maker=db_app.decision_maker or 'System',
                confidence_score=(
                    float(db_app.confidence_score) if db_app.confidence_score else 0.0
                ),
            )

        return LoanApplication(
            id=db_app.id,
            application_number=db_app.application_number,
            status=db_app.status,
            personal_info=personal_info,
            employment_info=employment_info,
            financial_info=financial_info,
            loan_details=loan_details,
            credit_score=credit_score,
            risk_assessment=risk_assessment,
            decision=decision,
            documents=documents,
            notes=db_app.notes or [],
            workflow_state=db_app.workflow_state or {},
            created_at=db_app.created_at,
            updated_at=db_app.updated_at,
            submitted_at=db_app.submitted_at,
            decision_date=db_app.decision_date,
            assigned_underwriter=db_app.assigned_underwriter,
            priority_level=db_app.priority_level,
        )

    def _convert_pydantic_to_db(self, application: LoanApplication) -> Dict[str, Any]:
        """Convert Pydantic model to database fields"""
        data = {
            'application_number': application.application_number,
            'status': application.status,
            'first_name': application.personal_info.first_name,
            'last_name': application.personal_info.last_name,
            'middle_name': application.personal_info.middle_name,
            'date_of_birth': application.personal_info.date_of_birth,
            'ssn': application.personal_info.ssn,
            'phone': application.personal_info.phone,
            'email': application.personal_info.email,
            'marital_status': application.personal_info.marital_status,
            'dependents': application.personal_info.dependents,
            'street': application.personal_info.address.street,
            'city': application.personal_info.address.city,
            'state': application.personal_info.address.state,
            'zip_code': application.personal_info.address.zip_code,
            'country': application.personal_info.address.country,
            'employment_status': application.employment_info.status,
            'employer_name': application.employment_info.employer_name,
            'job_title': application.employment_info.job_title,
            'employment_start_date': application.employment_info.employment_start_date,
            'annual_income': application.employment_info.annual_income,
            'monthly_income': application.employment_info.monthly_income,
            'other_income': application.employment_info.other_income,
            'monthly_rent_mortgage': application.financial_info.monthly_rent_mortgage,
            'monthly_debt_payments': application.financial_info.monthly_debt_payments,
            'monthly_expenses': application.financial_info.monthly_expenses,
            'savings_balance': application.financial_info.savings_balance,
            'checking_balance': application.financial_info.checking_balance,
            'credit_cards_debt': application.financial_info.credit_cards_debt,
            'assets_value': application.financial_info.assets_value,
            'existing_loans': application.financial_info.existing_loans,
            'loan_type': application.loan_details.loan_type,
            'requested_amount': application.loan_details.requested_amount,
            'requested_term_months': application.loan_details.requested_term_months,
            'purpose': application.loan_details.purpose,
            'collateral_description': application.loan_details.collateral_description,
            'collateral_value': application.loan_details.collateral_value,
            'workflow_state': application.workflow_state,
            'notes': application.notes,
            'assigned_underwriter': application.assigned_underwriter,
            'priority_level': application.priority_level,
            'submitted_at': application.submitted_at,
            'decision_date': application.decision_date,
        }

        # Add employer address if available
        if application.employment_info.employer_address:
            data.update(
                {
                    'employer_street': application.employment_info.employer_address.street,
                    'employer_city': application.employment_info.employer_address.city,
                    'employer_state': application.employment_info.employer_address.state,
                    'employer_zip': application.employment_info.employer_address.zip_code,
                }
            )

        # Add decision data if available
        if application.decision:
            data.update(
                {
                    'decision': application.decision.decision,
                    'approved_amount': application.decision.approved_amount,
                    'approved_term_months': application.decision.approved_term_months,
                    'interest_rate': application.decision.interest_rate,
                    'conditions': application.decision.conditions,
                    'rejection_reasons': application.decision.rejection_reasons,
                    'decision_maker': application.decision.decision_maker,
                    'confidence_score': application.decision.confidence_score,
                }
            )

        return data

    def generate_application_number(self) -> str:
        """Generate a unique application number"""
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid4())[:8].upper()
        return f'LOAN-{timestamp}-{unique_id}'

    def create_application(
        self, application_data: LoanApplicationCreate, user_id: Optional[str] = None
    ) -> LoanApplication:
        """Create a new loan application"""

        with get_sync_session() as session:
            # Create the application with generated number
            application = LoanApplication(
                application_number=self.generate_application_number(),
                personal_info=application_data.personal_info,
                employment_info=application_data.employment_info,
                financial_info=application_data.financial_info,
                loan_details=application_data.loan_details,
            )

            # Convert to database model
            db_data = self._convert_pydantic_to_db(application)
            db_app = LoanApplicationDB(**db_data)

            session.add(db_app)
            session.flush()  # Get the ID

            # Create audit log
            create_audit_log(
                session=session,
                application_id=str(db_app.id),
                action='APPLICATION_CREATED',
                user_id=user_id,
                user_type='applicant',
                new_values={
                    'status': 'draft',
                    'amount': float(application.loan_details.requested_amount),
                },
                notes='New loan application created',
            )

            session.commit()

            # Convert back to Pydantic model
            application.id = db_app.id
            application.created_at = db_app.created_at
            application.updated_at = db_app.updated_at

            logger.info(f'Created loan application {application.application_number}')
            return application

    def get_application(self, application_id: UUID) -> Optional[LoanApplication]:
        """Get loan application by ID"""

        with get_sync_session() as session:
            db_app = (
                session.query(LoanApplicationDB)
                .filter(LoanApplicationDB.id == application_id)
                .first()
            )

            if not db_app:
                return None

            return self._convert_db_to_pydantic(db_app)

    def get_application_by_number(
        self, application_number: str
    ) -> Optional[LoanApplication]:
        """Get loan application by application number"""

        with get_sync_session() as session:
            db_app = (
                session.query(LoanApplicationDB)
                .filter(LoanApplicationDB.application_number == application_number)
                .first()
            )

            if not db_app:
                return None

            return self._convert_db_to_pydantic(db_app)

    def update_application(
        self,
        application_id: UUID,
        updates: LoanApplicationUpdate,
        user_id: Optional[str] = None,
    ) -> Optional[LoanApplication]:
        """Update loan application"""

        with get_sync_session() as session:
            db_app = (
                session.query(LoanApplicationDB)
                .filter(LoanApplicationDB.id == application_id)
                .first()
            )

            if not db_app:
                return None

            # Store old values for audit
            old_status = db_app.status

            # Apply updates
            update_data = {}
            if updates.personal_info:
                # Update personal info fields
                update_data.update(
                    {
                        'first_name': updates.personal_info.first_name,
                        'last_name': updates.personal_info.last_name,
                        'middle_name': updates.personal_info.middle_name,
                        'date_of_birth': updates.personal_info.date_of_birth,
                        'ssn': updates.personal_info.ssn,
                        'phone': updates.personal_info.phone,
                        'email': updates.personal_info.email,
                        'marital_status': updates.personal_info.marital_status,
                        'dependents': updates.personal_info.dependents,
                        'street': updates.personal_info.address.street,
                        'city': updates.personal_info.address.city,
                        'state': updates.personal_info.address.state,
                        'zip_code': updates.personal_info.address.zip_code,
                        'country': updates.personal_info.address.country,
                    }
                )

            if updates.employment_info:
                # Update employment info fields
                update_data.update(
                    {
                        'employment_status': updates.employment_info.status,
                        'employer_name': updates.employment_info.employer_name,
                        'job_title': updates.employment_info.job_title,
                        'employment_start_date': updates.employment_info.employment_start_date,
                        'annual_income': updates.employment_info.annual_income,
                        'monthly_income': updates.employment_info.monthly_income,
                        'other_income': updates.employment_info.other_income,
                    }
                )

            if updates.financial_info:
                # Update financial info fields
                update_data.update(
                    {
                        'monthly_rent_mortgage': updates.financial_info.monthly_rent_mortgage,
                        'monthly_debt_payments': updates.financial_info.monthly_debt_payments,
                        'monthly_expenses': updates.financial_info.monthly_expenses,
                        'savings_balance': updates.financial_info.savings_balance,
                        'checking_balance': updates.financial_info.checking_balance,
                        'credit_cards_debt': updates.financial_info.credit_cards_debt,
                        'assets_value': updates.financial_info.assets_value,
                        'existing_loans': updates.financial_info.existing_loans,
                    }
                )

            if updates.loan_details:
                # Update loan details fields
                update_data.update(
                    {
                        'loan_type': updates.loan_details.loan_type,
                        'requested_amount': updates.loan_details.requested_amount,
                        'requested_term_months': updates.loan_details.requested_term_months,
                        'purpose': updates.loan_details.purpose,
                        'collateral_description': updates.loan_details.collateral_description,
                        'collateral_value': updates.loan_details.collateral_value,
                    }
                )

            if updates.status:
                update_data['status'] = updates.status

            if updates.notes:
                update_data['notes'] = updates.notes

            if updates.assigned_underwriter:
                update_data['assigned_underwriter'] = updates.assigned_underwriter

            if updates.priority_level:
                update_data['priority_level'] = updates.priority_level

            # Apply updates
            for key, value in update_data.items():
                setattr(db_app, key, value)

            # Create audit log
            create_audit_log(
                session=session,
                application_id=str(application_id),
                action='APPLICATION_UPDATED',
                user_id=user_id,
                user_type='user',
                old_values={'status': old_status.value if old_status else None},
                new_values={'status': updates.status.value if updates.status else None},
                notes='Application updated',
            )

            session.commit()

            return self._convert_db_to_pydantic(db_app)

    def submit_application(
        self, application_id: UUID, user_id: Optional[str] = None
    ) -> Optional[LoanApplication]:
        """Submit loan application for processing"""

        application = self.get_application(application_id)
        if not application:
            return None

        if application.status != LoanStatus.DRAFT:
            raise ValueError(
                f'Application must be in DRAFT status to submit, current status: {application.status}'
            )

        # Update status and submission date
        with get_sync_session() as session:
            session.query(LoanApplicationDB).filter(
                LoanApplicationDB.id == application_id
            ).update(
                {'status': LoanStatus.SUBMITTED, 'submitted_at': datetime.utcnow()}
            )

            create_audit_log(
                session=session,
                application_id=str(application_id),
                action='APPLICATION_SUBMITTED',
                user_id=user_id,
                user_type='applicant',
                old_values={'status': 'draft'},
                new_values={'status': 'submitted'},
                notes='Application submitted for processing',
            )

            session.commit()

        # Trigger workflow processing
        updated_application = self.get_application(application_id)
        if updated_application:
            # Process through workflow (async in background)
            logger.info(
                f'Starting workflow processing for application {application.application_number}'
            )

        return updated_application

    async def process_application_workflow(
        self, application_id: UUID
    ) -> LoanApplication:
        """Process application through the complete workflow"""

        application = self.get_application(application_id)
        if not application:
            raise ValueError(f'Application {application_id} not found')

        try:
            # Process through LangGraph workflow
            processed_application = await process_loan_application(application)

            # Save the results back to database
            self._save_workflow_results(processed_application)

            logger.info(
                f'Completed workflow processing for application {application.application_number}'
            )
            return processed_application

        except Exception as e:
            logger.error(
                f'Error processing application {application.application_number}: {str(e)}'
            )

            # Update status to indicate error
            with get_sync_session() as session:
                session.query(LoanApplicationDB).filter(
                    LoanApplicationDB.id == application_id
                ).update(
                    {
                        'status': LoanStatus.UNDER_REVIEW,
                        'notes': (application.notes or [])
                        + [f'Processing error: {str(e)}'],
                    }
                )

                create_audit_log(
                    session=session,
                    application_id=str(application_id),
                    action='WORKFLOW_ERROR',
                    user_type='system',
                    notes=f'Workflow processing error: {str(e)}',
                )

                session.commit()

            raise

    def _save_workflow_results(self, application: LoanApplication):
        """Save workflow processing results to database"""

        with get_sync_session() as session:
            db_app = (
                session.query(LoanApplicationDB)
                .filter(LoanApplicationDB.id == application.id)
                .first()
            )

            if not db_app:
                return

            # Update application status and workflow state
            db_app.status = application.status
            db_app.workflow_state = application.workflow_state
            db_app.notes = application.notes
            db_app.decision_date = application.decision_date

            # Save credit score if available
            if application.credit_score:
                credit_score = CreditScoreDB(
                    application_id=application.id,
                    score=application.credit_score.score,
                    bureau=application.credit_score.bureau,
                    date_obtained=application.credit_score.date_obtained,
                    factors=application.credit_score.factors,
                )
                session.add(credit_score)

            # Save risk assessment if available
            if application.risk_assessment:
                risk_assessment = RiskAssessmentDB(
                    application_id=application.id,
                    debt_to_income_ratio=application.risk_assessment.debt_to_income_ratio,
                    credit_utilization_ratio=application.risk_assessment.credit_utilization_ratio,
                    payment_history_score=application.risk_assessment.payment_history_score,
                    employment_stability_score=application.risk_assessment.employment_stability_score,
                    overall_risk_score=application.risk_assessment.overall_risk_score,
                    risk_level=application.risk_assessment.risk_level,
                    risk_factors=application.risk_assessment.risk_factors,
                )
                session.add(risk_assessment)

            # Save decision if available
            if application.decision:
                db_app.decision = application.decision.decision
                db_app.approved_amount = application.decision.approved_amount
                db_app.approved_term_months = application.decision.approved_term_months
                db_app.interest_rate = application.decision.interest_rate
                db_app.conditions = application.decision.conditions
                db_app.rejection_reasons = application.decision.rejection_reasons
                db_app.decision_maker = application.decision.decision_maker
                db_app.confidence_score = application.decision.confidence_score

            create_audit_log(
                session=session,
                application_id=str(application.id),
                action='WORKFLOW_COMPLETED',
                user_type='system',
                new_values={
                    'status': application.status,
                    'decision': (
                        application.decision.decision if application.decision else None
                    ),
                },
                notes='Workflow processing completed',
            )

            session.commit()

    def get_applications_by_status(
        self, status: LoanStatus, limit: int = 100, offset: int = 0
    ) -> List[LoanApplicationSummary]:
        """Get applications by status"""

        with get_sync_session() as session:
            db_apps = (
                session.query(LoanApplicationDB)
                .filter(LoanApplicationDB.status == status)
                .order_by(
                    LoanApplicationDB.priority_level.desc(),
                    LoanApplicationDB.created_at.asc(),
                )
                .offset(offset)
                .limit(limit)
                .all()
            )

            summaries = []
            for db_app in db_apps:
                summary = LoanApplicationSummary(
                    id=db_app.id,
                    application_number=db_app.application_number,
                    status=db_app.status,
                    applicant_name=f'{db_app.first_name} {db_app.last_name}',
                    loan_type=db_app.loan_type,
                    requested_amount=db_app.requested_amount,
                    created_at=db_app.created_at,
                    updated_at=db_app.updated_at,
                    priority_level=db_app.priority_level,
                    assigned_underwriter=db_app.assigned_underwriter,
                )
                summaries.append(summary)

            return summaries

    def get_applications_for_underwriter(
        self, underwriter_id: str, limit: int = 50
    ) -> List[LoanApplicationSummary]:
        """Get applications assigned to underwriter"""

        with get_sync_session() as session:
            db_apps = (
                session.query(LoanApplicationDB)
                .filter(LoanApplicationDB.assigned_underwriter == underwriter_id)
                .order_by(
                    LoanApplicationDB.priority_level.desc(),
                    LoanApplicationDB.created_at.asc(),
                )
                .limit(limit)
                .all()
            )

            summaries = []
            for db_app in db_apps:
                summary = LoanApplicationSummary(
                    id=db_app.id,
                    application_number=db_app.application_number,
                    status=db_app.status,
                    applicant_name=f'{db_app.first_name} {db_app.last_name}',
                    loan_type=db_app.loan_type,
                    requested_amount=db_app.requested_amount,
                    created_at=db_app.created_at,
                    updated_at=db_app.updated_at,
                    priority_level=db_app.priority_level,
                    assigned_underwriter=db_app.assigned_underwriter,
                )
                summaries.append(summary)

            return summaries

    def add_document(
        self, application_id: UUID, document: Document, user_id: Optional[str] = None
    ) -> Document:
        """Add document to application"""

        with get_sync_session() as session:
            db_doc = DocumentDB(
                application_id=application_id,
                document_type=document.document_type,
                file_name=document.file_name,
                file_path=document.file_path,
                file_size=document.file_size,
                mime_type=document.mime_type,
                verified=document.verified,
                verification_notes=document.verification_notes,
            )

            session.add(db_doc)
            session.flush()

            create_audit_log(
                session=session,
                application_id=str(application_id),
                action='DOCUMENT_UPLOADED',
                user_id=user_id,
                user_type='applicant',
                new_values={
                    'document_type': document.document_type.value,
                    'file_name': document.file_name,
                },
                notes=f'Document uploaded: {document.file_name}',
            )

            session.commit()

            # Update the document with the generated ID and timestamps
            document.id = db_doc.id
            document.uploaded_at = db_doc.created_at

            return document

    def delete_application(
        self, application_id: UUID, user_id: Optional[str] = None
    ) -> bool:
        """Delete loan application (soft delete by marking as cancelled)"""

        with get_sync_session() as session:
            db_app = (
                session.query(LoanApplicationDB)
                .filter(LoanApplicationDB.id == application_id)
                .first()
            )

            if not db_app:
                return False

            # Only allow deletion of draft or rejected applications
            if db_app.status not in [LoanStatus.DRAFT, LoanStatus.REJECTED]:
                raise ValueError(
                    f'Cannot delete application in status: {db_app.status}'
                )

            db_app.status = LoanStatus.CANCELLED

            create_audit_log(
                session=session,
                application_id=str(application_id),
                action='APPLICATION_CANCELLED',
                user_id=user_id,
                user_type='user',
                notes='Application cancelled/deleted',
            )

            session.commit()
            return True

    def get_application_statistics(self) -> Dict[str, Any]:
        """Get loan application statistics"""

        with get_sync_session() as session:
            stats = {}

            # Count by status
            for status in LoanStatus:
                count = (
                    session.query(LoanApplicationDB)
                    .filter(LoanApplicationDB.status == status)
                    .count()
                )
                stats[f'status_{status.value}'] = count

            # Count by loan type
            for loan_type in ['personal', 'auto', 'home', 'business', 'student']:
                count = (
                    session.query(LoanApplicationDB)
                    .filter(LoanApplicationDB.loan_type == loan_type)
                    .count()
                )
                stats[f'type_{loan_type}'] = count

            # Recent applications (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_count = (
                session.query(LoanApplicationDB)
                .filter(LoanApplicationDB.created_at >= thirty_days_ago)
                .count()
            )
            stats['recent_applications'] = recent_count

            # Average processing time (for completed applications)
            # This would require more complex queries in a real implementation

            return stats
