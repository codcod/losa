from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    Boolean,
    Numeric,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from ..models.loan import (
    LoanType,
    LoanStatus,
    EmploymentStatus,
    MaritalStatus,
    DocumentType,
)

Base = declarative_base()


class TimestampMixin:
    """Mixin to add timestamp fields to models"""

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LoanApplicationDB(Base, TimestampMixin):
    """Database model for loan applications"""

    __tablename__ = "loan_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(
        SQLEnum(LoanStatus), nullable=False, default=LoanStatus.DRAFT, index=True
    )

    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=False)
    ssn = Column(String(11), nullable=False)  # encrypted in production
    phone = Column(String(15), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    marital_status = Column(SQLEnum(MaritalStatus), nullable=False)
    dependents = Column(Integer, nullable=False, default=0)

    # Address
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(10), nullable=False)
    country = Column(String(50), nullable=False, default="US")

    # Employment Information
    employment_status = Column(SQLEnum(EmploymentStatus), nullable=False)
    employer_name = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    employment_start_date = Column(DateTime, nullable=True)
    annual_income = Column(Numeric(12, 2), nullable=False)
    monthly_income = Column(Numeric(12, 2), nullable=False)
    other_income = Column(Numeric(12, 2), nullable=False, default=0)

    # Employer Address
    employer_street = Column(String(255), nullable=True)
    employer_city = Column(String(100), nullable=True)
    employer_state = Column(String(50), nullable=True)
    employer_zip = Column(String(10), nullable=True)

    # Financial Information
    monthly_rent_mortgage = Column(Numeric(12, 2), nullable=False, default=0)
    monthly_debt_payments = Column(Numeric(12, 2), nullable=False, default=0)
    monthly_expenses = Column(Numeric(12, 2), nullable=False, default=0)
    savings_balance = Column(Numeric(12, 2), nullable=False, default=0)
    checking_balance = Column(Numeric(12, 2), nullable=False, default=0)
    credit_cards_debt = Column(Numeric(12, 2), nullable=False, default=0)
    assets_value = Column(Numeric(12, 2), nullable=False, default=0)
    existing_loans = Column(JSON, nullable=True)

    # Loan Details
    loan_type = Column(SQLEnum(LoanType), nullable=False, index=True)
    requested_amount = Column(Numeric(12, 2), nullable=False)
    requested_term_months = Column(Integer, nullable=False)
    purpose = Column(Text, nullable=False)
    collateral_description = Column(Text, nullable=True)
    collateral_value = Column(Numeric(12, 2), nullable=True)

    # Workflow and Processing
    workflow_state = Column(JSON, nullable=True)
    notes = Column(JSON, nullable=True)
    assigned_underwriter = Column(String(100), nullable=True, index=True)
    priority_level = Column(Integer, nullable=False, default=1)

    # Decision Information
    decision = Column(String(20), nullable=True)
    approved_amount = Column(Numeric(12, 2), nullable=True)
    approved_term_months = Column(Integer, nullable=True)
    interest_rate = Column(Numeric(5, 4), nullable=True)
    conditions = Column(JSON, nullable=True)
    rejection_reasons = Column(JSON, nullable=True)
    decision_date = Column(DateTime, nullable=True)
    decision_maker = Column(String(100), nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)

    # Important dates
    submitted_at = Column(DateTime, nullable=True)

    # Relationships
    documents = relationship(
        "DocumentDB", back_populates="application", cascade="all, delete-orphan"
    )
    credit_scores = relationship(
        "CreditScoreDB", back_populates="application", cascade="all, delete-orphan"
    )
    risk_assessments = relationship(
        "RiskAssessmentDB", back_populates="application", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLogDB", back_populates="application", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_loan_apps_status_created', 'status', 'created_at'),
        Index('ix_loan_apps_underwriter_status', 'assigned_underwriter', 'status'),
        Index('ix_loan_apps_email_status', 'email', 'status'),
    )

    def __repr__(self):
        return f"<LoanApplication(id={self.id}, number={self.application_number}, status={self.status})>"


class DocumentDB(Base, TimestampMixin):
    """Database model for uploaded documents"""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("loan_applications.id"),
        nullable=False,
        index=True,
    )

    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)

    # Verification status
    verified = Column(Boolean, nullable=False, default=False)
    verification_notes = Column(Text, nullable=True)
    verification_date = Column(DateTime, nullable=True)
    verified_by = Column(String(100), nullable=True)

    # Document analysis results
    analysis_results = Column(JSON, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)

    # Relationship
    application = relationship("LoanApplicationDB", back_populates="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, type={self.document_type}, verified={self.verified})>"


class CreditScoreDB(Base, TimestampMixin):
    """Database model for credit scores"""

    __tablename__ = "credit_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("loan_applications.id"),
        nullable=False,
        index=True,
    )

    score = Column(Integer, nullable=False)
    bureau = Column(String(50), nullable=False)  # Experian, Equifax, TransUnion
    date_obtained = Column(DateTime, nullable=False)
    factors = Column(JSON, nullable=True)  # Factors affecting the score

    # Credit report details
    trade_lines = Column(JSON, nullable=True)
    inquiries = Column(JSON, nullable=True)
    public_records = Column(JSON, nullable=True)

    # Relationship
    application = relationship("LoanApplicationDB", back_populates="credit_scores")

    def __repr__(self):
        return f"<CreditScore(id={self.id}, score={self.score}, bureau={self.bureau})>"


class RiskAssessmentDB(Base, TimestampMixin):
    """Database model for risk assessments"""

    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("loan_applications.id"),
        nullable=False,
        index=True,
    )

    debt_to_income_ratio = Column(Numeric(5, 4), nullable=False)
    credit_utilization_ratio = Column(Numeric(5, 4), nullable=False)
    payment_history_score = Column(Integer, nullable=False)
    employment_stability_score = Column(Integer, nullable=False)
    overall_risk_score = Column(Integer, nullable=False, index=True)
    risk_level = Column(String(20), nullable=False, index=True)
    risk_factors = Column(JSON, nullable=True)

    # Model information
    model_version = Column(String(50), nullable=True)
    model_features = Column(JSON, nullable=True)

    # Relationship
    application = relationship("LoanApplicationDB", back_populates="risk_assessments")

    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, score={self.overall_risk_score}, level={self.risk_level})>"


class AuditLogDB(Base, TimestampMixin):
    """Database model for audit logs"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("loan_applications.id"),
        nullable=False,
        index=True,
    )

    action = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    user_type = Column(String(50), nullable=True)  # system, underwriter, admin, etc.

    # Change tracking
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Additional context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationship
    application = relationship("LoanApplicationDB", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.user_id})>"


class UnderwriterDB(Base, TimestampMixin):
    """Database model for underwriters"""

    __tablename__ = "underwriters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Professional information
    title = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    hire_date = Column(DateTime, nullable=False)

    # Certification and limits
    certifications = Column(JSON, nullable=True)
    approval_limit = Column(Numeric(12, 2), nullable=False, default=100000)
    loan_types = Column(ARRAY(String), nullable=True)  # Types of loans they can handle

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    current_workload = Column(Integer, nullable=False, default=0)
    max_workload = Column(Integer, nullable=False, default=20)

    def __repr__(self):
        return f"<Underwriter(id={self.id}, name={self.first_name} {self.last_name})>"


class ConfigurationDB(Base, TimestampMixin):
    """Database model for system configuration"""

    __tablename__ = "configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    category = Column(String(100), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)

    # Version control
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)

    # Unique constraint on category + key for active configurations
    __table_args__ = (
        Index(
            'ix_config_category_key_active',
            'category',
            'key',
            'is_active',
            unique=True,
            postgresql_where=(Column('is_active')),
        ),
    )

    def __repr__(self):
        return f"<Configuration(category={self.category}, key={self.key})>"


# Helper functions for common queries


def get_application_by_number(
    session: Session, application_number: str
) -> Optional[LoanApplicationDB]:
    """Get application by application number"""
    return (
        session.query(LoanApplicationDB)
        .filter(LoanApplicationDB.application_number == application_number)
        .first()
    )


def get_applications_by_status(
    session: Session, status: LoanStatus, limit: int = 100
) -> list[LoanApplicationDB]:
    """Get applications by status"""
    return (
        session.query(LoanApplicationDB)
        .filter(LoanApplicationDB.status == status)
        .order_by(LoanApplicationDB.created_at.desc())
        .limit(limit)
        .all()
    )


def get_applications_for_underwriter(
    session: Session, underwriter_id: str, limit: int = 50
) -> list[LoanApplicationDB]:
    """Get applications assigned to a specific underwriter"""
    return (
        session.query(LoanApplicationDB)
        .filter(LoanApplicationDB.assigned_underwriter == underwriter_id)
        .order_by(
            LoanApplicationDB.priority_level.desc(), LoanApplicationDB.created_at.asc()
        )
        .limit(limit)
        .all()
    )


def get_pending_applications(
    session: Session, limit: int = 100
) -> list[LoanApplicationDB]:
    """Get applications requiring attention"""
    return (
        session.query(LoanApplicationDB)
        .filter(
            LoanApplicationDB.status.in_(
                [
                    LoanStatus.SUBMITTED,
                    LoanStatus.UNDER_REVIEW,
                    LoanStatus.DOCUMENTS_REQUIRED,
                    LoanStatus.CREDIT_CHECK,
                ]
            )
        )
        .order_by(
            LoanApplicationDB.priority_level.desc(), LoanApplicationDB.created_at.asc()
        )
        .limit(limit)
        .all()
    )


def get_configuration(
    session: Session, category: str, key: str
) -> Optional[ConfigurationDB]:
    """Get configuration value"""
    return (
        session.query(ConfigurationDB)
        .filter(
            ConfigurationDB.category == category,
            ConfigurationDB.key == key,
            ConfigurationDB.is_active,
        )
        .first()
    )


def create_audit_log(
    session: Session,
    application_id: str,
    action: str,
    user_id: Optional[str] = None,
    user_type: Optional[str] = "system",
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    notes: Optional[str] = None,
) -> AuditLogDB:
    """Create an audit log entry"""
    audit_log = AuditLogDB(
        application_id=application_id,
        action=action,
        user_id=user_id,
        user_type=user_type,
        old_values=old_values,
        new_values=new_values,
        notes=notes,
    )
    session.add(audit_log)
    return audit_log


# Database initialization and migration helpers
def create_all_tables(engine):
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
