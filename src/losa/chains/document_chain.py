from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..models.loan import Document


class DocumentAnalysisResult(BaseModel):
    """Result of document analysis"""

    document_type: str
    is_valid: bool
    extracted_data: Dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    issues_found: List[str] = Field(default_factory=list)
    verification_notes: str


class IncomeVerificationResult(BaseModel):
    """Result of income verification from documents"""

    annual_income: float
    monthly_income: float
    employment_status: str
    employer_name: Optional[str] = None
    income_sources: List[str]
    verification_confidence: float = Field(ge=0.0, le=1.0)
    discrepancies: List[str] = Field(default_factory=list)


class CreditAnalysisResult(BaseModel):
    """Result of credit analysis"""

    recommended_decision: str  # APPROVE, REJECT, REVIEW
    risk_factors: List[str]
    positive_factors: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    recommended_interest_rate: Optional[float] = None
    recommended_loan_amount: Optional[float] = None
    additional_requirements: List[str] = Field(default_factory=list)


class DocumentAnalysisChain:
    """Chain for analyzing uploaded documents"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.1)

        # Document analysis prompt
        self.analysis_prompt = ChatPromptTemplate.from_template(
            """
        You are an expert document analyst for a loan origination system.
        Analyze the following document and extract relevant information.

        Document Information:
        - Type: {document_type}
        - File Name: {file_name}
        - File Size: {file_size} bytes

        Document Content (OCR/Text Extract):
        {document_content}

        Your task is to:
        1. Verify if this document matches the expected type
        2. Extract all relevant financial and personal information
        3. Identify any issues, inconsistencies, or red flags
        4. Provide a confidence score for the analysis

        Return your analysis in the following JSON format:
        {{
            "document_type": "confirmed document type",
            "is_valid": true/false,
            "extracted_data": {{
                "key1": "value1",
                "key2": "value2"
            }},
            "confidence_score": 0.95,
            "issues_found": ["issue1", "issue2"],
            "verification_notes": "detailed notes about the verification"
        }}

        For income-related documents, ensure you extract:
        - Annual income/salary
        - Monthly income
        - Employer information
        - Employment dates
        - Pay period information

        For identity documents, extract:
        - Full name
        - Date of birth
        - Address
        - ID numbers

        For bank statements, extract:
        - Account balances
        - Monthly deposits
        - Regular expenses
        - Transaction patterns
        """
        )

        self.parser = JsonOutputParser(pydantic_object=DocumentAnalysisResult)

        self.chain = self.analysis_prompt | self.llm | self.parser

    async def analyze_document(
        self, document: Document, document_content: str
    ) -> DocumentAnalysisResult:
        """Analyze a single document"""

        result = await self.chain.ainvoke(
            {
                "document_type": document.document_type.value,
                "file_name": document.file_name,
                "file_size": document.file_size,
                "document_content": document_content,
            }
        )

        return DocumentAnalysisResult(**result)

    async def analyze_documents(
        self, documents: List[Document], document_contents: List[str]
    ) -> List[DocumentAnalysisResult]:
        """Analyze multiple documents"""

        results = []
        for doc, content in zip(documents, document_contents):
            result = await self.analyze_document(doc, content)
            results.append(result)

        return results


class IncomeVerificationChain:
    """Chain for verifying income from multiple sources"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.1)

        self.verification_prompt = ChatPromptTemplate.from_template(
            """
        You are an expert income verification specialist for loan underwriting.

        Analyze the following income-related information and documents to verify the applicant's income:

        Applicant's Declared Information:
        - Annual Income: ${declared_annual_income:,.2f}
        - Monthly Income: ${declared_monthly_income:,.2f}
        - Employment Status: {employment_status}
        - Employer: {employer_name}

        Document Analysis Results:
        {document_analyses}

        Your task is to:
        1. Verify the declared income against document evidence
        2. Identify any discrepancies or red flags
        3. Determine the most reliable income figure
        4. Assess the stability and reliability of income sources
        5. Provide a confidence score for the verification

        Consider factors like:
        - Consistency across multiple documents
        - Seasonal variations in income
        - Bonus and commission income
        - Multiple income sources
        - Employment stability indicators

        Return your analysis in JSON format:
        {{
            "annual_income": verified_annual_amount,
            "monthly_income": verified_monthly_amount,
            "employment_status": "verified_status",
            "employer_name": "verified_employer",
            "income_sources": ["salary", "bonus", "other"],
            "verification_confidence": 0.95,
            "discrepancies": ["list of any discrepancies found"]
        }}
        """
        )

        self.parser = JsonOutputParser(pydantic_object=IncomeVerificationResult)

        self.chain = self.verification_prompt | self.llm | self.parser

    async def verify_income(
        self,
        declared_annual_income: float,
        declared_monthly_income: float,
        employment_status: str,
        employer_name: str,
        document_analyses: List[DocumentAnalysisResult],
    ) -> IncomeVerificationResult:
        """Verify income based on documents and declared information"""

        # Format document analyses for the prompt
        doc_analysis_text = "\n".join(
            [
                f"Document {i+1} ({analysis.document_type}):\n"
                f"- Valid: {analysis.is_valid}\n"
                f"- Extracted Data: {analysis.extracted_data}\n"
                f"- Issues: {analysis.issues_found}\n"
                f"- Confidence: {analysis.confidence_score}\n"
                for i, analysis in enumerate(document_analyses)
            ]
        )

        result = await self.chain.ainvoke(
            {
                "declared_annual_income": declared_annual_income,
                "declared_monthly_income": declared_monthly_income,
                "employment_status": employment_status,
                "employer_name": employer_name or "Not provided",
                "document_analyses": doc_analysis_text,
            }
        )

        return IncomeVerificationResult(**result)


class CreditAnalysisChain:
    """Chain for comprehensive credit analysis and loan decision support"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.1)

        self.analysis_prompt = ChatPromptTemplate.from_template(
            """
        You are a senior credit analyst and underwriter with 20+ years of experience.

        Analyze the following complete loan application and provide your professional assessment:

        APPLICANT PROFILE:
        - Name: {applicant_name}
        - Age: {age}
        - Employment: {employment_status} at {employer}
        - Annual Income: ${annual_income:,.2f} (verified: {income_verified})
        - Monthly Income: ${monthly_income:,.2f}

        LOAN REQUEST:
        - Type: {loan_type}
        - Amount: ${requested_amount:,.2f}
        - Term: {requested_term} months
        - Purpose: {loan_purpose}

        FINANCIAL PROFILE:
        - Credit Score: {credit_score}
        - Debt-to-Income Ratio: {dti_ratio:.1%}
        - Monthly Debt Payments: ${monthly_debt:,.2f}
        - Monthly Housing: ${monthly_housing:,.2f}
        - Savings: ${savings:,.2f}
        - Assets: ${assets:,.2f}

        RISK ASSESSMENT:
        - Overall Risk Score: {risk_score}/100
        - Risk Level: {risk_level}
        - Risk Factors: {risk_factors}

        DOCUMENT VERIFICATION:
        {document_summary}

        Based on your analysis, provide a comprehensive credit decision with the following JSON structure:
        {{
            "recommended_decision": "APPROVE/REJECT/REVIEW",
            "risk_factors": ["factor1", "factor2"],
            "positive_factors": ["factor1", "factor2"],
            "confidence_score": 0.85,
            "recommended_interest_rate": 6.5,
            "recommended_loan_amount": 75000.00,
            "additional_requirements": ["requirement1", "requirement2"]
        }}

        Consider standard underwriting guidelines:
        - DTI should typically be < 43%
        - Credit score minimums vary by loan type
        - Employment stability (2+ years preferred)
        - Adequate liquid reserves
        - Loan-to-value ratios for secured loans

        Provide detailed reasoning for your decision, including:
        1. Key factors that support or oppose approval
        2. Any mitigating circumstances
        3. Recommended loan terms and conditions
        4. Additional documentation or requirements needed
        """
        )

        self.parser = JsonOutputParser(pydantic_object=CreditAnalysisResult)

        self.chain = self.analysis_prompt | self.llm | self.parser

    async def analyze_creditworthiness(
        self,
        application_data: Dict[str, Any],
        document_analyses: List[DocumentAnalysisResult],
        income_verification: IncomeVerificationResult,
    ) -> CreditAnalysisResult:
        """Perform comprehensive credit analysis"""

        # Format document summary
        doc_summary = "Document Verification Summary:\n"
        for i, analysis in enumerate(document_analyses):
            doc_summary += f"- {analysis.document_type}: {'✓ Verified' if analysis.is_valid else '✗ Issues found'} "
            doc_summary += f"(Confidence: {analysis.confidence_score:.1%})\n"

        result = await self.chain.ainvoke(
            {
                "applicant_name": application_data.get("applicant_name", "Unknown"),
                "age": application_data.get("age", "Unknown"),
                "employment_status": application_data.get(
                    "employment_status", "Unknown"
                ),
                "employer": application_data.get("employer", "Unknown"),
                "annual_income": income_verification.annual_income,
                "monthly_income": income_verification.monthly_income,
                "income_verified": income_verification.verification_confidence > 0.8,
                "loan_type": application_data.get("loan_type", "Unknown"),
                "requested_amount": application_data.get("requested_amount", 0),
                "requested_term": application_data.get("requested_term", 0),
                "loan_purpose": application_data.get("loan_purpose", "Not specified"),
                "credit_score": application_data.get("credit_score", 0),
                "dti_ratio": application_data.get("dti_ratio", 0),
                "monthly_debt": application_data.get("monthly_debt", 0),
                "monthly_housing": application_data.get("monthly_housing", 0),
                "savings": application_data.get("savings", 0),
                "assets": application_data.get("assets", 0),
                "risk_score": application_data.get("risk_score", 0),
                "risk_level": application_data.get("risk_level", "Unknown"),
                "risk_factors": application_data.get("risk_factors", []),
                "document_summary": doc_summary,
            }
        )

        return CreditAnalysisResult(**result)


class LoanExplanationChain:
    """Chain for generating loan decision explanations"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)

        self.explanation_prompt = ChatPromptTemplate.from_template(
            """
        You are a loan officer explaining a loan decision to an applicant.
        Create a clear, professional, and empathetic explanation of the loan decision.

        Loan Decision Details:
        - Decision: {decision}
        - Requested Amount: ${requested_amount:,.2f}
        - Approved Amount: ${approved_amount:,.2f} (if approved)
        - Interest Rate: {interest_rate:.2%} (if approved)
        - Term: {term} months (if approved)

        Key Factors:
        - Credit Score: {credit_score}
        - Debt-to-Income Ratio: {dti_ratio:.1%}
        - Risk Factors: {risk_factors}
        - Positive Factors: {positive_factors}

        Conditions/Requirements: {conditions}

        Generate a professional explanation that:
        1. Clearly states the decision
        2. Explains the key factors that influenced the decision
        3. If approved: outlines the terms and any conditions
        4. If rejected: provides constructive feedback and next steps
        5. Maintains a helpful and professional tone

        The explanation should be suitable for direct communication with the applicant.
        """
        )

        self.chain = self.explanation_prompt | self.llm

    async def generate_explanation(self, decision_data: Dict[str, Any]) -> str:
        """Generate a human-readable explanation of the loan decision"""

        result = await self.chain.ainvoke(decision_data)
        return result.content


# Factory functions for creating chains with different configurations


def create_document_analysis_chain(model_name: str = "gpt-4") -> DocumentAnalysisChain:
    """Create a document analysis chain with specified model"""
    llm = ChatOpenAI(model=model_name, temperature=0.1)
    return DocumentAnalysisChain(llm)


def create_income_verification_chain(
    model_name: str = "gpt-4",
) -> IncomeVerificationChain:
    """Create an income verification chain with specified model"""
    llm = ChatOpenAI(model=model_name, temperature=0.1)
    return IncomeVerificationChain(llm)


def create_credit_analysis_chain(model_name: str = "gpt-4") -> CreditAnalysisChain:
    """Create a credit analysis chain with specified model"""
    llm = ChatOpenAI(model=model_name, temperature=0.1)
    return CreditAnalysisChain(llm)


def create_explanation_chain(model_name: str = "gpt-4") -> LoanExplanationChain:
    """Create a loan explanation chain with specified model"""
    llm = ChatOpenAI(model=model_name, temperature=0.3)
    return LoanExplanationChain(llm)


# Composite chain for complete document processing
class CompleteDocumentProcessingChain:
    """Composite chain that handles complete document processing workflow"""

    def __init__(self, model_name: str = "gpt-4"):
        self.document_chain = create_document_analysis_chain(model_name)
        self.income_chain = create_income_verification_chain(model_name)
        self.credit_chain = create_credit_analysis_chain(model_name)
        self.explanation_chain = create_explanation_chain(model_name)

    async def process_complete_application(
        self,
        documents: List[Document],
        document_contents: List[str],
        application_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process complete loan application through all chains"""

        # Step 1: Analyze all documents
        document_analyses = await self.document_chain.analyze_documents(
            documents, document_contents
        )

        # Step 2: Verify income from relevant documents
        income_verification = await self.income_chain.verify_income(
            application_data["declared_annual_income"],
            application_data["declared_monthly_income"],
            application_data["employment_status"],
            application_data["employer_name"],
            document_analyses,
        )

        # Step 3: Perform credit analysis
        credit_analysis = await self.credit_chain.analyze_creditworthiness(
            application_data, document_analyses, income_verification
        )

        # Step 4: Generate explanation
        explanation = await self.explanation_chain.generate_explanation(
            {
                "decision": credit_analysis.recommended_decision,
                "requested_amount": application_data["requested_amount"],
                "approved_amount": credit_analysis.recommended_loan_amount,
                "interest_rate": credit_analysis.recommended_interest_rate or 0,
                "term": application_data["requested_term"],
                "credit_score": application_data["credit_score"],
                "dti_ratio": application_data["dti_ratio"],
                "risk_factors": credit_analysis.risk_factors,
                "positive_factors": credit_analysis.positive_factors,
                "conditions": credit_analysis.additional_requirements,
            }
        )

        return {
            "document_analyses": document_analyses,
            "income_verification": income_verification,
            "credit_analysis": credit_analysis,
            "explanation": explanation,
        }
