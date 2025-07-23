import pytest
import pathlib
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch

from losa.models.loan import (
    LoanApplication,
    LoanApplicationCreate,
    LoanApplicationUpdate,
    PersonalInfo,
    Address,
    EmploymentInfo,
    FinancialInfo,
    LoanDetails,
    LoanType,
    LoanStatus,
    EmploymentStatus,
    MaritalStatus,
    DocumentType,
    Document,
)
from losa.services.loan_service import LoanService

from dotenv import load_dotenv

env_file = pathlib.Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment from {env_file}")
else:
    env_example = pathlib.Path(__file__).parent.parent / ".env.example"

class TestLoanService:
    """Test cases for LoanService"""

    @pytest.fixture
    def loan_service(self):
        """Create a loan service instance for testing"""
        return LoanService()

    @pytest.fixture
    def sample_address(self):
        """Sample address for testing"""
        return Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            country="US",
        )

    @pytest.fixture
    def sample_personal_info(self, sample_address):
        """Sample personal information for testing"""
        return PersonalInfo(
            first_name="John",
            middle_name=None,
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            ssn="123-45-6789",
            phone="5551234567",
            email="john.doe@example.com",
            marital_status=MaritalStatus.SINGLE,
            dependents=0,
            address=sample_address,
        )

    @pytest.fixture
    def sample_employment_info(self):
        """Sample employment information for testing"""
        return EmploymentInfo(
            status=EmploymentStatus.EMPLOYED,
            employer_name="Tech Corp",
            job_title="Software Engineer",
            employment_start_date=datetime(2020, 1, 1),
            annual_income=Decimal("80000"),
            monthly_income=Decimal("6666.67"),
            other_income=Decimal("0"),
        )

    @pytest.fixture
    def sample_financial_info(self):
        """Sample financial information for testing"""
        return FinancialInfo(
            monthly_rent_mortgage=Decimal("1500"),
            monthly_debt_payments=Decimal("300"),
            monthly_expenses=Decimal("2000"),
            savings_balance=Decimal("10000"),
            checking_balance=Decimal("5000"),
            credit_cards_debt=Decimal("2000"),
            assets_value=Decimal("25000"),
        )

    @pytest.fixture
    def sample_loan_details(self):
        """Sample loan details for testing"""
        return LoanDetails(
            loan_type=LoanType.PERSONAL,
            requested_amount=Decimal("25000"),
            requested_term_months=60,
            purpose="Debt consolidation and home improvements",
            collateral_value=None,
        )

    @pytest.fixture
    def sample_loan_application_create(
        self,
        sample_personal_info,
        sample_employment_info,
        sample_financial_info,
        sample_loan_details,
    ):
        """Sample loan application create request for testing"""
        return LoanApplicationCreate(
            personal_info=sample_personal_info,
            employment_info=sample_employment_info,
            financial_info=sample_financial_info,
            loan_details=sample_loan_details,
        )

    def test_generate_application_number(self, loan_service):
        """Test application number generation"""
        app_number = loan_service.generate_application_number()

        assert app_number.startswith("LOAN-")
        assert len(app_number) == 22  # LOAN-YYYYMMDD-8chars
        assert app_number[5:13].isdigit()  # Date part should be digits

    @patch('losa.services.loan_service.get_sync_session')
    def test_create_application_success(
        self, mock_session, loan_service, sample_loan_application_create
    ):
        """Test successful loan application creation"""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session

        # Mock database operations
        mock_db_app = Mock()
        mock_db_app.id = uuid4()
        mock_db_app.created_at = datetime.utcnow()
        mock_db_app.updated_at = datetime.utcnow()

        mock_db_session.add = Mock()
        mock_db_session.flush = Mock()
        mock_db_session.commit = Mock()

        # Test application creation
        with patch.object(loan_service, '_convert_pydantic_to_db', return_value={}):
            with patch(
                'losa.services.loan_service.LoanApplicationDB', return_value=mock_db_app
            ):
                with patch('losa.services.loan_service.create_audit_log'):
                    application = loan_service.create_application(
                        sample_loan_application_create
                    )

                    assert application is not None
                    assert application.status == LoanStatus.DRAFT
                    assert application.personal_info.first_name == "John"
                    assert application.personal_info.last_name == "Doe"
                    assert application.loan_details.requested_amount == Decimal("25000")

                    # Verify database operations were called
                    mock_db_session.add.assert_called_once()  # only the app, audit log is mocked
                    mock_db_session.flush.assert_called_once()
                    mock_db_session.commit.assert_called_once()

    def test_debt_to_income_ratio_calculation(self, sample_loan_application_create):
        """Test debt-to-income ratio calculation"""
        # Create application with known values
        application = LoanApplication(
            application_number="TEST-001",
            personal_info=sample_loan_application_create.personal_info,
            employment_info=sample_loan_application_create.employment_info,
            financial_info=sample_loan_application_create.financial_info,
            loan_details=sample_loan_application_create.loan_details,
            priority_level=1,
        )

        # DTI = (monthly_debt + monthly_housing) / monthly_income
        # DTI = (300 + 1500) / 6666.67 = 0.27 (27%)
        expected_dti = 0.27
        actual_dti = application.debt_to_income_ratio

        assert (
            abs(actual_dti - expected_dti) < 0.01
        )  # Allow for small rounding differences

    def test_required_documents_personal_loan(self, sample_loan_application_create):
        """Test required documents for personal loan"""
        application = LoanApplication(
            application_number="TEST-002",
            personal_info=sample_loan_application_create.personal_info,
            employment_info=sample_loan_application_create.employment_info,
            financial_info=sample_loan_application_create.financial_info,
            loan_details=sample_loan_application_create.loan_details,
            priority_level=1,
        )

        required_docs = application._get_required_documents()

        # Personal loans should require basic documents
        assert DocumentType.IDENTITY in required_docs
        assert DocumentType.INCOME_PROOF in required_docs

    def test_required_documents_high_amount_loan(self, sample_loan_application_create):
        """Test required documents for high amount loan"""
        # Modify loan details for high amount
        high_amount_details = LoanDetails(
            loan_type=LoanType.PERSONAL,
            requested_amount=Decimal("75000"),  # Above $50k threshold
            requested_term_months=60,
            purpose="Debt consolidation",
            collateral_value=None,
        )

        application = LoanApplication(
            application_number="TEST-003",
            personal_info=sample_loan_application_create.personal_info,
            employment_info=sample_loan_application_create.employment_info,
            financial_info=sample_loan_application_create.financial_info,
            loan_details=high_amount_details,
            priority_level=1,
        )

        required_docs = application._get_required_documents()

        # High amount loans should require additional documents
        assert DocumentType.IDENTITY in required_docs
        assert DocumentType.INCOME_PROOF in required_docs
        assert DocumentType.BANK_STATEMENT in required_docs

    def test_application_completeness_with_documents(
        self, sample_loan_application_create
    ):
        """Test application completeness check with uploaded documents"""
        application = LoanApplication(
            application_number="TEST-004",
            personal_info=sample_loan_application_create.personal_info,
            employment_info=sample_loan_application_create.employment_info,
            financial_info=sample_loan_application_create.financial_info,
            loan_details=sample_loan_application_create.loan_details,
            priority_level=1,
        )

        # Initially incomplete
        assert not application.is_complete

        # Add required documents
        identity_doc = Document(
            document_type=DocumentType.IDENTITY,
            file_name="driver_license.jpg",
            file_path="/uploads/driver_license.jpg",
            file_size=1024,
            mime_type="image/jpeg",
        )

        income_doc = Document(
            document_type=DocumentType.INCOME_PROOF,
            file_name="pay_stub.pdf",
            file_path="/uploads/pay_stub.pdf",
            file_size=2048,
            mime_type="application/pdf",
        )

        application.documents = [identity_doc, income_doc]

        # Now should be complete
        assert application.is_complete

    @patch('losa.services.loan_service.get_sync_session')
    def test_update_application(self, mock_session, loan_service):
        """Test loan application update"""
        application_id = uuid4()

        # Mock database session and existing application
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session

        mock_db_app = Mock()
        mock_db_app.id = application_id
        mock_db_app.status = LoanStatus.DRAFT

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_db_app
        )
        mock_db_session.commit = Mock()

        # Create update data
        updates = LoanApplicationUpdate(status=LoanStatus.SUBMITTED, priority_level=3)

        # Mock the conversion method
        with patch.object(loan_service, '_convert_db_to_pydantic') as mock_convert:
            mock_convert.return_value = Mock(status=LoanStatus.SUBMITTED)

            result = loan_service.update_application(
                application_id, updates, "test_user"
            )

            assert result is not None
            mock_db_session.commit.assert_called_once()

    @patch('losa.services.loan_service.get_sync_session')
    def test_submit_application_invalid_status(self, mock_session, loan_service):
        """Test submitting application with invalid status"""
        application_id = uuid4()

        # Mock getting application in APPROVED status (can't resubmit)
        mock_application = Mock()
        mock_application.status = LoanStatus.APPROVED

        with patch.object(
            loan_service, 'get_application', return_value=mock_application
        ):
            with pytest.raises(ValueError, match="Application must be in DRAFT status"):
                loan_service.submit_application(application_id)

    @patch('losa.services.loan_service.get_sync_session')
    def test_get_applications_by_status(self, mock_session, loan_service):
        """Test getting applications by status"""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session

        # Mock database query results
        mock_app1 = Mock()
        mock_app1.id = uuid4()
        mock_app1.application_number = "LOAN-001"
        mock_app1.status = LoanStatus.UNDER_REVIEW
        mock_app1.first_name = "John"
        mock_app1.last_name = "Doe"
        mock_app1.loan_type = LoanType.PERSONAL
        mock_app1.requested_amount = Decimal("25000")
        mock_app1.created_at = datetime.utcnow()
        mock_app1.updated_at = datetime.utcnow()
        mock_app1.priority_level = 1
        mock_app1.assigned_underwriter = None

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_app1
        ]

        # Test getting applications
        results = loan_service.get_applications_by_status(
            LoanStatus.UNDER_REVIEW, limit=10, offset=0
        )

        assert len(results) == 1
        assert results[0].application_number == "LOAN-001"
        assert results[0].status == LoanStatus.UNDER_REVIEW
        assert results[0].applicant_name == "John Doe"

    @patch('losa.services.loan_service.get_sync_session')
    def test_delete_application_invalid_status(self, mock_session, loan_service):
        """Test deleting application with invalid status"""
        application_id = uuid4()

        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session

        # Mock application in APPROVED status (can't delete)
        mock_db_app = Mock()
        mock_db_app.status = LoanStatus.APPROVED

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_db_app
        )

        # Test deletion should fail
        with pytest.raises(ValueError, match="Cannot delete application in status"):
            loan_service.delete_application(application_id)

    @patch('losa.services.loan_service.get_sync_session')
    def test_add_document_success(self, mock_session, loan_service):
        """Test successful document addition"""
        application_id = uuid4()

        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session

        mock_db_doc = Mock()
        mock_db_doc.id = uuid4()
        mock_db_doc.created_at = datetime.utcnow()

        mock_db_session.add = Mock()
        mock_db_session.flush = Mock()
        mock_db_session.commit = Mock()

        # Create document
        document = Document(
            document_type=DocumentType.IDENTITY,
            file_name="driver_license.jpg",
            file_path="/uploads/driver_license.jpg",
            file_size=1024,
            mime_type="image/jpeg",
        )

        with patch('losa.services.loan_service.DocumentDB', return_value=mock_db_doc):
            with patch('losa.services.loan_service.create_audit_log'):
                result = loan_service.add_document(application_id, document, "test_user")

                assert result is not None
                assert result.document_type == DocumentType.IDENTITY
                assert result.file_name == "driver_license.jpg"

                mock_db_session.add.assert_called_once()  # only document, audit log is mocked
                mock_db_session.flush.assert_called_once()
                mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_application_workflow_success(self, loan_service):
        """Test successful workflow processing"""
        application_id = uuid4()

        # Mock getting application
        mock_application = Mock()
        mock_application.id = application_id
        mock_application.application_number = "TEST-WORKFLOW"
        mock_application.status = LoanStatus.SUBMITTED

        # Mock workflow processing
        processed_application = Mock()
        processed_application.id = application_id
        processed_application.status = LoanStatus.APPROVED

        with patch.object(
            loan_service, 'get_application', return_value=mock_application
        ):
            with patch(
                'losa.services.loan_service.process_loan_application',
                return_value=processed_application,
            ):
                with patch.object(loan_service, '_save_workflow_results'):
                    result = await loan_service.process_application_workflow(
                        application_id
                    )

                    assert result is not None
                    assert result.status == LoanStatus.APPROVED

    @pytest.mark.asyncio
    async def test_process_application_workflow_not_found(self, loan_service):
        """Test workflow processing with non-existent application"""
        application_id = uuid4()

        with patch.object(loan_service, 'get_application', return_value=None):
            with pytest.raises(
                ValueError, match=f"Application {application_id} not found"
            ):
                await loan_service.process_application_workflow(application_id)

    def test_convert_pydantic_to_db(self, loan_service, sample_loan_application_create):
        """Test conversion from Pydantic model to database fields"""
        application = LoanApplication(
            application_number="TEST-CONVERT",
            personal_info=sample_loan_application_create.personal_info,
            employment_info=sample_loan_application_create.employment_info,
            financial_info=sample_loan_application_create.financial_info,
            loan_details=sample_loan_application_create.loan_details,
            priority_level=1,
        )

        db_data = loan_service._convert_pydantic_to_db(application)

        assert db_data["application_number"] == "TEST-CONVERT"
        assert db_data["first_name"] == "John"
        assert db_data["last_name"] == "Doe"
        assert db_data["email"] == "john.doe@example.com"
        assert db_data["annual_income"] == Decimal("80000")
        assert db_data["requested_amount"] == Decimal("25000")
        assert db_data["loan_type"] == LoanType.PERSONAL

    @patch('losa.services.loan_service.get_sync_session')
    def test_get_application_statistics(self, mock_session, loan_service):
        """Test getting application statistics"""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session

        # Mock query results for different counts
        # LoanStatus has 9 values: draft, submitted, under_review, documents_required, credit_check, approved, rejected, funded, cancelled
        # Loan types: personal, auto, home, business, student (5 values)
        # Plus 1 for recent applications = 15 total queries
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [
            5,  # draft applications
            10,  # submitted applications
            8,  # under_review applications
            3,  # documents_required applications
            2,  # credit_check applications
            3,  # approved applications
            2,  # rejected applications
            0,  # funded applications
            0,  # cancelled applications
            15,  # personal loans
            5,  # auto loans
            2,  # home loans
            1,  # business loans
            0,  # student loans
            25,  # recent applications (last 30 days)
        ]

        stats = loan_service.get_application_statistics()

        assert stats["status_draft"] == 5
        assert stats["status_submitted"] == 10
        assert stats["status_under_review"] == 8
        assert stats["status_documents_required"] == 3
        assert stats["status_credit_check"] == 2
        assert stats["status_approved"] == 3
        assert stats["status_rejected"] == 2
        assert stats["status_funded"] == 0
        assert stats["status_cancelled"] == 0
        assert stats["type_personal"] == 15
        assert stats["type_auto"] == 5
        assert stats["type_home"] == 2
        assert stats["type_business"] == 1
        assert stats["type_student"] == 0
        assert stats["recent_applications"] == 25
