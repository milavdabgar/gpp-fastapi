import uuid
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.models.project import Project, DepartmentEvaluation, CentralEvaluation
from app.models.department import Department
from app.schemas import (
    DeptEvaluationRequest, CentralEvaluationRequest, ProjectResponse
)

# Evaluate project by department jury
async def evaluate_project_by_department(
    db: Session, 
    project_id: str, 
    evaluation_data: DeptEvaluationRequest,
    jury_user: User
) -> ProjectResponse:
    """Add department evaluation to a project"""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if jury is from same department as project
    if jury_user.department_id != project.department_id:
        raise HTTPException(
            status_code=403, 
            detail="Department jury can only evaluate projects from their own department"
        )
    
    # Create evaluation object
    evaluation = DepartmentEvaluation(
        id=str(uuid.uuid4()),
        project_id=project_id,
        completed=True,
        score=evaluation_data.score,
        feedback=evaluation_data.feedback,
        jury_id=jury_user.id,
        evaluated_at=datetime.utcnow()
    )
    
    # Add to database
    db.add(evaluation)
    project.updated_by = jury_user.id
    project.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(project)
    
    return project

# Evaluate project by central jury
async def evaluate_project_by_central(
    db: Session, 
    project_id: str, 
    evaluation_data: CentralEvaluationRequest,
    jury_user: User
) -> ProjectResponse:
    """Add central evaluation to a project"""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if project has department evaluation
    if not project.dept_evaluation:
        raise HTTPException(
            status_code=400, 
            detail="Project must have department evaluation before central evaluation"
        )
    
    # Create evaluation object
    evaluation = CentralEvaluation(
        id=str(uuid.uuid4()),
        project_id=project_id,
        completed=True,
        score=evaluation_data.score,
        feedback=evaluation_data.feedback,
        jury_id=jury_user.id,
        evaluated_at=datetime.utcnow()
    )
    
    # Add to database
    db.add(evaluation)
    project.updated_by = jury_user.id
    project.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(project)
    
    return project

# Get projects for jury based on role and department
async def get_projects_for_jury(
    db: Session,
    jury_user: User,
    is_central_jury: bool = False,
    page: int = 1,
    limit: int = 20,
    evaluated_only: Optional[bool] = False,
    event_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get projects for a jury member based on their role and department"""
    query = db.query(Project)
    
    # Filter projects based on jury role
    if is_central_jury:
        # Central jury can see all projects with department evaluation
        query = query.filter(Project.dept_evaluation != None)
        
        if evaluated_only:
            # If only want evaluated projects
            query = query.filter(Project.central_evaluation != None)
        else:
            # If want all projects eligible for evaluation
            query = query.filter(Project.central_evaluation == None)
    else:
        # Department jury can only see projects from their department
        query = query.filter(Project.department_id == jury_user.department_id)
        
        if evaluated_only:
            # If only want evaluated projects
            query = query.filter(Project.dept_evaluation != None)
        else:
            # If want all projects eligible for evaluation
            query = query.filter(Project.dept_evaluation == None)
    
    # Additional filters
    if event_id:
        query = query.filter(Project.event_id == event_id)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Execute query
    projects = query.all()
    
    # Return response with metadata
    return {
        "projects": projects,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit  # Ceiling division
    }

# Get projects with evaluations by department
async def get_evaluated_projects_by_department(
    db: Session,
    department_id: str
) -> List[ProjectResponse]:
    """Get projects with evaluations for a specific department"""
    projects = db.query(Project).filter(
        Project.department_id == department_id,
        Project.dept_evaluation != None
    ).all()
    return projects

# Get projects with central evaluations (winners)
async def get_central_evaluated_projects(
    db: Session,
    limit: int = 10
) -> List[ProjectResponse]:
    """Get centrally evaluated projects (potential winners)"""
    projects = db.query(Project).filter(
        Project.central_evaluation != None
    ).order_by(
        Project.central_evaluation['score'].desc()
    ).limit(limit).all()
    return projects
