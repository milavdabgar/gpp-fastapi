from typing import List, Dict, Any, Optional
from fastapi import HTTPException, UploadFile, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct
import csv
import io
import uuid
from datetime import datetime
# Removing pandas dependency
from collections import defaultdict

from app.models.user import User
from app.models.result import Result
from app.schemas import (
    ResultCreate, ResultResponse, ResultAnalysis, BatchResponse,
    PaginatedResponse, PaginatedMeta, ResponseBase, DataResponse
)
from app.middleware.error import AppError

# Get all results with pagination and filtering
async def get_results(
    db: Session, 
    page: int = 1, 
    limit: int = 10,
    search: Optional[str] = None,
    branch: Optional[str] = None,
    semester: Optional[int] = None,
    exam_type: Optional[str] = None,
    sort_by: str = "declaration_date"
) -> PaginatedResponse[List[ResultResponse]]:
    """Get all results with pagination and filtering"""
    query = db.query(Result)
    
    # Apply filters
    if search:
        query = query.filter(Result.name.ilike(f"%{search}%") | 
                          Result.enrollment_no.ilike(f"%{search}%"))
    if branch:
        query = query.filter(Result.branch_name == branch)
    if semester:
        query = query.filter(Result.semester == semester)
    if exam_type:
        query = query.filter(Result.extype == exam_type)
    
    # Apply sorting
    if sort_by == "declaration_date":
        query = query.order_by(Result.declaration_date.desc())
    elif sort_by == "name":
        query = query.order_by(Result.name)
    elif sort_by == "enrollment_no":
        query = query.order_by(Result.enrollment_no)
    elif sort_by == "semester":
        query = query.order_by(Result.semester)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Execute query
    results = query.all()
    
    # Create pagination metadata
    meta = PaginatedMeta(
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit  # Ceiling division
    )
    
    # Return paginated response
    return {
        "data": results,
        "meta": meta
    }

# Get a single result by ID
async def get_result(db: Session, result_id: str) -> ResultResponse:
    """Get a single result by ID"""
    result = db.query(Result).filter(Result.id == result_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return result

# Create a new result
async def create_result(db: Session, result_data: ResultCreate) -> ResultResponse:
    """Create a new result"""
    # Create new result
    new_result = Result(
        id=str(uuid.uuid4()),
        st_id=result_data.st_id,
        enrollment_no=result_data.enrollment_no,
        name=result_data.name,
        semester=result_data.semester,
        branch_name=result_data.branch_name,
        extype=result_data.extype,
        exam=result_data.exam,
        declaration_date=result_data.declaration_date,
        subjects=result_data.subjects,
        total_credits=result_data.total_credits,
        earned_credits=result_data.earned_credits,
        spi=result_data.spi,
        cpi=result_data.cpi,
        result=result_data.result,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add to database
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    
    return new_result

# Delete a result
async def delete_result(db: Session, result_id: str) -> ResponseBase:
    """Delete a result"""
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    db.delete(result)
    db.commit()
    
    return {"status": "success", "message": "Result deleted successfully"}

# Import results from CSV
async def import_results(db: Session, file: UploadFile) -> ResponseBase:
    """Import results from CSV file"""
    content = await file.read()
    
    # Generate batch ID for this upload
    batch_id = str(uuid.uuid4())
    
    try:
        # Process CSV
        rows = content.decode('utf-8').splitlines()
        reader = csv.DictReader(rows)
        
        # Validate data (basic check)
        if 'enrollment_no' not in reader.fieldnames or 'name' not in reader.fieldnames or 'semester' not in reader.fieldnames:
            raise HTTPException(status_code=400, detail="Invalid CSV format. Required columns missing.")
        
        # Process each row
        imported_count = 0
        for row in reader:
            # Create result object
            result_dict = row
            
            # Extract subjects if they are in separate columns
            subject_columns = [col for col in reader.fieldnames if col.startswith('subject_')]
            subjects = []
            for col in subject_columns:
                if row[col]:
                    parts = col.split('_')
                    code = parts[1] if len(parts) > 1 else ""
                    subjects.append({
                        "code": code,
                        "name": row.get(f"subject_name_{code}", ""),
                        "credits": float(row.get(f"subject_credits_{code}", 0)),
                        "grade": row.get(f"subject_grade_{code}", "")
                    })
            
            # Add batch ID to track this upload
            result_dict['upload_batch'] = batch_id
            
            # Convert basic data to expected types
            if 'semester' in result_dict:
                result_dict['semester'] = int(result_dict['semester'])
            
            # Create result
            new_result = Result(
                id=str(uuid.uuid4()),
                **result_dict,
                subjects=subjects,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(new_result)
            imported_count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Successfully imported {imported_count} result records",
            "data": {"count": imported_count, "batch_id": batch_id}
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error importing results: {str(e)}")

# Export results to CSV
async def export_results(db: Session) -> Response:
    """Export results to CSV"""
    # Get all results
    results = db.query(Result).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Enrollment No", "Name", "Exam Type", "Semester",
        "Branch", "SPI", "CPI", "Result", "Declaration Date"
    ])
    
    # Write data
    for result in results:
        writer.writerow([
            result.id,
            result.enrollment_no,
            result.name,
            result.extype,
            result.semester,
            result.branch_name,
            result.spi,
            result.cpi,
            result.result,
            result.declaration_date.isoformat() if result.declaration_date else ""
        ])
    
    # Create response with CSV content
    response = Response(content=output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=results_export.csv"
    response.headers["Content-Type"] = "text/csv"
    
    return response

# Get branch-wise analysis
async def get_branch_analysis(db: Session) -> List[ResultAnalysis]:
    """Get branch-wise analysis of results"""
    # Get distinct branches and semesters
    branch_semesters = db.query(Result.branch_name, Result.semester).distinct().all()
    
    # Prepare analysis
    analysis = []
    
    for branch_name, semester in branch_semesters:
        # Get all results for this branch and semester
        results = db.query(Result).filter(
            Result.branch_name == branch_name,
            Result.semester == semester
        ).all()
        
        total_students = len(results)
        if total_students == 0:
            continue
        
        # Calculate metrics
        pass_count = len([r for r in results if r.result and r.result.lower() == "pass"])
        distinction_count = len([r for r in results if r.spi and r.spi >= 8.5])
        first_class_count = len([r for r in results if r.spi and 7.5 <= r.spi < 8.5])
        second_class_count = len([r for r in results if r.spi and 6.5 <= r.spi < 7.5])
        
        spi_values = [r.spi for r in results if r.spi is not None]
        cpi_values = [r.cpi for r in results if r.cpi is not None]
        
        avg_spi = sum(spi_values) / len(spi_values) if spi_values else 0
        avg_cpi = sum(cpi_values) / len(cpi_values) if cpi_values else 0
        pass_percentage = (pass_count / total_students) * 100 if total_students > 0 else 0
        
        # Create analysis object
        branch_analysis = ResultAnalysis(
            branch_name=branch_name,
            semester=semester,
            total_students=total_students,
            pass_count=pass_count,
            distinction_count=distinction_count,
            first_class_count=first_class_count,
            second_class_count=second_class_count,
            avg_spi=round(avg_spi, 2),
            avg_cpi=round(avg_cpi, 2),
            pass_percentage=round(pass_percentage, 2)
        )
        
        analysis.append(branch_analysis)
    
    # Sort by branch and semester
    analysis.sort(key=lambda x: (x.branch_name, x.semester))
    
    return analysis

# Get upload batches
async def get_upload_batches(db: Session) -> List[BatchResponse]:
    """Get list of uploaded result batches"""
    # Get distinct batch IDs
    batches = db.query(Result.upload_batch).distinct().all()
    
    batch_list = []
    for (batch_id,) in batches:
        if not batch_id:
            continue
        
        # Get count and latest upload date for this batch
        count = db.query(Result).filter(Result.upload_batch == batch_id).count()
        latest = db.query(func.max(Result.created_at)).filter(Result.upload_batch == batch_id).scalar()
        
        batch_info = BatchResponse(
            batch_id=batch_id,
            count=count,
            latest_upload=latest or datetime.utcnow()
        )
        
        batch_list.append(batch_info)
    
    # Sort by latest upload (newest first)
    batch_list.sort(key=lambda x: x.latest_upload, reverse=True)
    
    return batch_list

# Delete results by batch
async def delete_results_by_batch(db: Session, batch_id: str) -> ResponseBase:
    """Delete all results from a specific batch"""
    # Check if batch exists
    count = db.query(Result).filter(Result.upload_batch == batch_id).count()
    if count == 0:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Delete all results from this batch
    db.query(Result).filter(Result.upload_batch == batch_id).delete()
    db.commit()
    
    return {
        "status": "success", 
        "message": f"Successfully deleted {count} results from batch {batch_id}"
    }

# Get student results
async def get_student_results(db: Session, enrollment_no: str) -> List[ResultResponse]:
    """Get all results for a specific student"""
    results = db.query(Result).filter(
        Result.enrollment_no == enrollment_no
    ).order_by(Result.semester).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this student")
    
    return results