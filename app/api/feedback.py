from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.user import User
from app.schemas import (
    DataResponse, ResponseBase,
    FeedbackCreate, FeedbackResponse, FeedbackAnalysisResult
)
from app.services.feedback import (
    get_sample_feedback, process_feedback_csv, analyze_feedback_data,
    get_feedback_report, generate_latex_report, generate_pdf_report,
    generate_feedback_report
)
from app.middleware.auth import get_authenticated_user, require_admin

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"]
)

@router.get("/sample", response_class=Response)
async def get_feedback_sample():
    """Get sample CSV template for feedback data"""
    content = await get_sample_feedback()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback_sample.csv"}
    )

@router.post("/upload", response_model=ResponseBase)
async def upload_feedback_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Upload and process feedback data from CSV"""
    result = await process_feedback_csv(db, file, background_tasks)
    return {"status": "success", "message": result}

@router.get("/report/{feedback_id}", response_model=Dict[str, Any])
async def get_feedback_analysis_report(
    feedback_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    """Get feedback analysis report by ID"""
    return await get_feedback_report(db, feedback_id)

@router.get("/report/{feedback_id}/latex", response_class=Response)
async def get_feedback_latex_report(
    feedback_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    """Get LaTeX format feedback report"""
    content = await generate_latex_report(db, feedback_id)
    return Response(
        content=content,
        media_type="application/x-latex",
        headers={"Content-Disposition": f"attachment; filename=feedback_report_{feedback_id}.tex"}
    )

@router.get("/report/{feedback_id}/pdf", response_class=Response)
async def get_feedback_pdf_report(
    feedback_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    """Get PDF format feedback report"""
    content = await generate_pdf_report(db, feedback_id)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=feedback_report_{feedback_id}.pdf"}
    )

@router.get("/report/{feedback_id}/export", response_class=Response)
async def export_feedback_report(
    feedback_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    """Export feedback report in multiple formats as ZIP"""
    content = await generate_feedback_report(db, feedback_id)
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=feedback_reports_{feedback_id}.zip"}
    )