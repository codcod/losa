from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class LoanType(str, Enum):
    PERSONAL = 'personal'
    AUTO = 'auto'
    HOME = 'home'
    BUSINESS = 'business'
    STUDENT = 'student'


class LoanStatus(str, Enum):
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    UNDER_REVIEW = 'under_review'
    DOCUMENTS_REQUIRED = 'documents_required'
    CREDIT_CHECK = 'credit_check'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    FUNDED = 'funded'
    CANCELLED = 'cancelled'


class EmploymentStatus(str, Enum):
    EMPLOYED = 'employed'
    SELF_EMPLOYED = 'self_employed'
    UNEMPLOYED = 'unemployed'
    RETIRED = 'retired'
    STUDENT = 'student'


class MaritalStatus(str, Enum):
    SINGLE = 'single'
    MARRIED = 'married'
    DIVORCED = 'divorced'
    WIDOWED = 'widowed'


class DocumentType(str, Enum):
    IDENTITY = 'identity'
    INCOME_PROOF = 'income_proof'
    EMPLOYMENT_VERIFICATION = 'employment_verification'
    BANK_STATEMENT = 'bank_statement'
    TAX_RETURN = 'tax_return'
    COLLATERAL_DOCUMENT = 'collateral_document'
    OTHER = 'other'


class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str = Field(..., pattern=r'^\d{5}(-\d{4})?$')
    country: str = 'US'


class PersonalInfo(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: datetime
    ssn: str = Field(..., pattern=r'^\d{3}-\d{2}-\d{4}$')
    phone: str = Field(..., pattern=r'^\+?1?\d{10}$')
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    marital_status: MaritalStatus
    dependents: int = Field(0, ge=0)
    address: Address


class EmploymentInfo(BaseModel):
    status: EmploymentStatus
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    employment_start_date: Optional[datetime] = None
    annual_income: Decimal = Field(..., gt=0)
    monthly_income: Decimal = Field(..., gt=0)
    other_income: Optional[Decimal] = Field(0, ge=0)
    employer_address: Optional[Address] = None

    @validator('monthly_income', always=True)
    def validate_monthly_income(cls, v, values):
        if 'annual_income' in values:
            expected_monthly = values['annual_income'] / 12
            tolerance = expected_monthly * Decimal('0.1')  # 10% tolerance
            if abs(v - expected_monthly) > tolerance:
                raise ValueError(
                    'Monthly income should be approximately annual income / 12'
                )
        return v


class FinancialInfo(BaseModel):
    monthly_rent_mortgage: Decimal = Field(0, ge=0)
    monthly_debt_payments: Decimal = Field(0, ge=0)
    monthly_expenses: Decimal = Field(0, ge=0)
    savings_balance: Decimal = Field(0, ge=0)
    checking_balance: Decimal = Field(0, ge=0)
    existing_loans: List[dict] = Field(default_factory=list)
    credit_cards_debt: Decimal = Field(0, ge=0)
    assets_value: Decimal = Field(0, ge=0)


class LoanDetails(BaseModel):
    loan_type: LoanType
    requested_amount: Decimal = Field(..., gt=0, le=1000000)
    requested_term_months: int = Field(..., ge=6, le=360)
    purpose: str = Field(..., min_length=10, max_length=500)
    collateral_description: Optional[str] = None
    collateral_value: Optional[Decimal] = Field(None, ge=0)


class CreditScore(BaseModel):
    score: int = Field(..., ge=300, le=850)
    bureau: str  # Experian, Equifax, TransUnion
    date_obtained: datetime
    factors: List[str] = Field(default_factory=list)


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_type: DocumentType
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False
    verification_notes: Optional[str] = None


class RiskAssessment(BaseModel):
    debt_to_income_ratio: float = Field(..., ge=0)
    credit_utilization_ratio: float = Field(..., ge=0, le=1)
    payment_history_score: int = Field(..., ge=0, le=100)
    employment_stability_score: int = Field(..., ge=0, le=100)
    overall_risk_score: int = Field(..., ge=0, le=100)
    risk_level: str = Field(..., pattern=r'^(LOW|MEDIUM|HIGH|VERY_HIGH)$')
    risk_factors: List[str] = Field(default_factory=list)


class LoanDecision(BaseModel):
    decision: str = Field(..., pattern=r'^(APPROVED|REJECTED|CONDITIONAL)$')
    approved_amount: Optional[Decimal] = Field(None, gt=0)
    approved_term_months: Optional[int] = Field(None, ge=6, le=360)
    interest_rate: Optional[float] = Field(None, gt=0, le=30)
    conditions: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    decision_date: datetime = Field(default_factory=datetime.utcnow)
    decision_maker: str  # System, Underwriter name, etc.
    confidence_score: float = Field(..., ge=0, le=1)


class LoanApplication(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    application_number: str = Field(..., min_length=1)
    status: LoanStatus = LoanStatus.DRAFT

    # Core application data
    personal_info: PersonalInfo
    employment_info: EmploymentInfo
    financial_info: FinancialInfo
    loan_details: LoanDetails

    # Assessment data
    credit_score: Optional[CreditScore] = None
    risk_assessment: Optional[RiskAssessment] = None
    decision: Optional[LoanDecision] = None

    # Documents and workflow
    documents: List[Document] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    workflow_state: dict = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    decision_date: Optional[datetime] = None

    # Tracking
    assigned_underwriter: Optional[str] = None
    priority_level: int = Field(1, ge=1, le=5)  # 1 = lowest, 5 = highest

    class Config:
        use_enum_values = True
        validate_assignment = True

    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        return datetime.utcnow()

    @property
    def debt_to_income_ratio(self) -> float:
        """Calculate debt-to-income ratio"""
        monthly_income = float(self.employment_info.monthly_income)
        monthly_debts = float(
            self.financial_info.monthly_debt_payments
            + self.financial_info.monthly_rent_mortgage
        )
        return monthly_debts / monthly_income if monthly_income > 0 else 0

    @property
    def is_complete(self) -> bool:
        """Check if application has all required information"""
        required_docs = self._get_required_documents()
        uploaded_doc_types = {doc.document_type for doc in self.documents}
        return all(doc_type in uploaded_doc_types for doc_type in required_docs)

    def _get_required_documents(self) -> List[DocumentType]:
        """Get list of required documents based on loan type"""
        base_docs = [DocumentType.IDENTITY, DocumentType.INCOME_PROOF]

        if self.loan_details.loan_type == LoanType.HOME:
            base_docs.extend([DocumentType.BANK_STATEMENT, DocumentType.TAX_RETURN])
        elif self.loan_details.loan_type == LoanType.BUSINESS:
            base_docs.extend([DocumentType.TAX_RETURN, DocumentType.BANK_STATEMENT])
        elif self.loan_details.requested_amount > 50000:
            base_docs.append(DocumentType.BANK_STATEMENT)

        return base_docs


class LoanApplicationCreate(BaseModel):
    personal_info: PersonalInfo
    employment_info: EmploymentInfo
    financial_info: FinancialInfo
    loan_details: LoanDetails


class LoanApplicationUpdate(BaseModel):
    personal_info: Optional[PersonalInfo] = None
    employment_info: Optional[EmploymentInfo] = None
    financial_info: Optional[FinancialInfo] = None
    loan_details: Optional[LoanDetails] = None
    status: Optional[LoanStatus] = None
    notes: Optional[List[str]] = None
    assigned_underwriter: Optional[str] = None
    priority_level: Optional[int] = Field(None, ge=1, le=5)


class LoanApplicationSummary(BaseModel):
    id: UUID
    application_number: str
    status: LoanStatus
    applicant_name: str
    loan_type: LoanType
    requested_amount: Decimal
    created_at: datetime
    updated_at: datetime
    priority_level: int
    assigned_underwriter: Optional[str] = None
