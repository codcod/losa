from typing import List, Optional
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
)
from datetime import datetime
import os
import aiofiles
import logging

from ..services.loan_service import LoanService
from ..models.loan import (
    LoanApplication,
    LoanApplicationCreate,
    LoanApplicationUpdate,
    LoanApplicationSummary,
    LoanStatus,
    Document,
    DocumentType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/loans", tags=["loans"])


# Dependency to get loan service
def get_loan_service() -> LoanService:
    return LoanService()


@router.post("/", response_model=LoanApplication)
async def create_loan_application(
    application_data: LoanApplicationCreate,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Create a new loan application"""
    try:
        application = loan_service.create_application(application_data)
        return application
    except Exception as e:
        logger.error(f"Error creating loan application: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create application: {str(e)}"
        )


@router.get("/{application_id}", response_model=LoanApplication)
async def get_loan_application(
    application_id: UUID, loan_service: LoanService = Depends(get_loan_service)
):
    """Get loan application by ID"""
    application = loan_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.get("/number/{application_number}", response_model=LoanApplication)
async def get_loan_application_by_number(
    application_number: str, loan_service: LoanService = Depends(get_loan_service)
):
    """Get loan application by application number"""
    application = loan_service.get_application_by_number(application_number)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.put("/{application_id}", response_model=LoanApplication)
async def update_loan_application(
    application_id: UUID,
    updates: LoanApplicationUpdate,
    user_id: Optional[str] = None,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Update loan application"""
    try:
        application = loan_service.update_application(application_id, updates, user_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update application: {str(e)}"
        )


@router.post("/{application_id}/submit", response_model=LoanApplication)
async def submit_loan_application(
    application_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = None,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Submit loan application for processing"""
    try:
        application = loan_service.submit_application(application_id, user_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Process application through workflow in background
        background_tasks.add_task(
            loan_service.process_application_workflow, application_id
        )

        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit application: {str(e)}"
        )


@router.post("/{application_id}/process")
async def process_loan_application(
    application_id: UUID, loan_service: LoanService = Depends(get_loan_service)
):
    """Manually trigger workflow processing for an application"""
    try:
        application = await loan_service.process_application_workflow(application_id)
        return {
            "message": "Application processed successfully",
            "application_id": application_id,
            "status": application.status,
            "decision": application.decision.decision if application.decision else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process application: {str(e)}"
        )


@router.get("/status/{status}", response_model=List[LoanApplicationSummary])
async def get_applications_by_status(
    status: LoanStatus,
    limit: int = 100,
    offset: int = 0,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Get applications by status"""
    try:
        applications = loan_service.get_applications_by_status(status, limit, offset)
        return applications
    except Exception as e:
        logger.error(f"Error getting applications by status {status}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve applications: {str(e)}"
        )


@router.get(
    "/underwriter/{underwriter_id}", response_model=List[LoanApplicationSummary]
)
async def get_applications_for_underwriter(
    underwriter_id: str,
    limit: int = 50,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Get applications assigned to an underwriter"""
    try:
        applications = loan_service.get_applications_for_underwriter(
            underwriter_id, limit
        )
        return applications
    except Exception as e:
        logger.error(
            f"Error getting applications for underwriter {underwriter_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve applications: {str(e)}"
        )


@router.post("/{application_id}/documents", response_model=Document)
async def upload_document(
    application_id: UUID,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    user_id: Optional[str] = Form(None),
    loan_service: LoanService = Depends(get_loan_service),
):
    """Upload document for loan application"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        # Check file size (10MB limit)
        max_file_size = 10 * 1024 * 1024  # 10MB
        if file.size and file.size > max_file_size:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

        # Validate file type
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Create upload directory if it doesn't exist
        upload_dir = f"uploads/{application_id}"
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{document_type.value}_{timestamp}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Create document record
        document = Document(
            document_type=document_type,
            file_name=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            verified=False,
        )

        # Add to application
        saved_document = loan_service.add_document(application_id, document, user_id)

        return saved_document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error uploading document for application {application_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to upload document: {str(e)}"
        )


@router.delete("/{application_id}")
async def delete_loan_application(
    application_id: UUID,
    user_id: Optional[str] = None,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Delete (cancel) loan application"""
    try:
        success = loan_service.delete_application(application_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Application not found")

        return {
            "message": "Application cancelled successfully",
            "application_id": application_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete application: {str(e)}"
        )


@router.get("/statistics/overview")
async def get_loan_statistics(loan_service: LoanService = Depends(get_loan_service)):
    """Get loan application statistics"""
    try:
        stats = loan_service.get_application_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting loan statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve statistics: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "loan-origination-system",
    }


# Additional utility endpoints


@router.get("/{application_id}/status")
async def get_application_status(
    application_id: UUID, loan_service: LoanService = Depends(get_loan_service)
):
    """Get current status of loan application"""
    application = loan_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "application_id": application_id,
        "application_number": application.application_number,
        "status": application.status,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
        "submitted_at": application.submitted_at,
        "decision_date": application.decision_date,
        "assigned_underwriter": application.assigned_underwriter,
        "priority_level": application.priority_level,
    }


@router.get("/{application_id}/documents")
async def get_application_documents(
    application_id: UUID, loan_service: LoanService = Depends(get_loan_service)
):
    """Get all documents for an application"""
    application = loan_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "application_id": application_id,
        "documents": application.documents,
        "required_documents": application._get_required_documents(),
        "is_complete": application.is_complete,
    }


@router.post("/{application_id}/priority")
async def update_application_priority(
    application_id: UUID,
    priority_level: int,
    user_id: Optional[str] = None,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Update application priority level"""
    if priority_level < 1 or priority_level > 5:
        raise HTTPException(
            status_code=400, detail="Priority level must be between 1 and 5"
        )

    try:
        from ..models.loan import LoanApplicationUpdate

        updates = LoanApplicationUpdate(priority_level=priority_level)
        application = loan_service.update_application(application_id, updates, user_id)

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        return {
            "message": "Priority updated successfully",
            "application_id": application_id,
            "new_priority": priority_level,
        }

    except Exception as e:
        logger.error(
            f"Error updating priority for application {application_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update priority: {str(e)}"
        )


@router.post("/{application_id}/assign")
async def assign_underwriter(
    application_id: UUID,
    underwriter_id: str,
    user_id: Optional[str] = None,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Assign underwriter to application"""
    try:
        from ..models.loan import LoanApplicationUpdate

        updates = LoanApplicationUpdate(assigned_underwriter=underwriter_id)
        application = loan_service.update_application(application_id, updates, user_id)

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        return {
            "message": "Underwriter assigned successfully",
            "application_id": application_id,
            "assigned_underwriter": underwriter_id,
        }

    except Exception as e:
        logger.error(
            f"Error assigning underwriter to application {application_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to assign underwriter: {str(e)}"
        )


@router.get("/{application_id}/workflow-state")
async def get_workflow_state(
    application_id: UUID, loan_service: LoanService = Depends(get_loan_service)
):
    """Get current workflow state of application"""
    application = loan_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "application_id": application_id,
        "status": application.status,
        "workflow_state": application.workflow_state,
        "credit_check_complete": bool(application.credit_score),
        "risk_assessment_complete": bool(application.risk_assessment),
        "decision_complete": bool(application.decision),
        "documents_complete": application.is_complete,
        "human_review_required": application.assigned_underwriter is not None,
    }
