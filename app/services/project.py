from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
import csv
import io
from datetime import datetime
import uuid

from app.models.user import User
from app.models.project import Project, DepartmentEvaluation, CentralEvaluation, ProjectTeam, TeamMember, ProjectEvent
from app.models.department import Department
from app.models.event import Event
from app.models.location import Location
from app.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithDetails,
    PaginatedResponse, PaginatedMeta, DataResponse
)
from app.middleware.error import AppError

# Get all projects with pagination and filtering
async def get_projects(
    db: Session, 
    page: int = 1, 
    limit: int = 10, 
    search: Optional[str] = None, 
    department_id: Optional[str] = None,
    event_id: Optional[str] = None, 
    sort_by: str = "created_at"
) -> PaginatedResponse[List[ProjectResponse]]:
    """Get all projects with pagination and filtering"""
    query = db.query(Project)

    # Apply filters
    if search:
        query = query.filter(Project.title.ilike(f"%{search}%"))
    if department_id:
        query = query.filter(Project.department_id == department_id)
    if event_id:
        query = query.filter(Project.event_id == event_id)

    # Apply sorting
    if sort_by == "created_at":
        query = query.order_by(Project.created_at.desc())
    elif sort_by == "title":
        query = query.order_by(Project.title)
    # Add more sorting options as needed

    # Get total count for pagination
    total = query.count()

    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)

    # Execute query
    projects = query.all()

    # Create pagination metadata
    meta = PaginatedMeta(
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit  # Ceiling division
    )

    # Return paginated response
    return {
        "data": projects,
        "meta": meta
    }

# Get a single project by ID
async def get_project(db: Session, project_id: str) -> ProjectWithDetails:
    """Get a single project with all details"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

# Create a new project
async def create_project(db: Session, project_data: ProjectCreate, current_user: User) -> DataResponse[ProjectResponse]:
    """Create a new project"""
    # Validate references
    team = db.query(Team).filter(Team.id == project_data.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    department = db.query(Department).filter(Department.id == project_data.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    event = db.query(Event).filter(Event.id == project_data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Create new project
    new_project = Project(
        id=str(uuid.uuid4()),
        title=project_data.title,
        category=project_data.category,
        abstract=project_data.abstract,
        department_id=project_data.department_id,
        status=project_data.status,
        requirements=project_data.requirements.dict(),
        guide=project_data.guide.dict(),
        team_id=project_data.team_id,
        event_id=project_data.event_id,
        location_id=project_data.location_id,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # Add to database
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return {"data": new_project}

# Update an existing project
async def update_project(db: Session, project_id: str, project_data: ProjectUpdate, current_user: User) -> DataResponse[ProjectResponse]:
    """Update an existing project"""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update project attributes - only if provided in the request
    update_data = project_data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(project, key, value)
    
    # Set updated_by
    project.updated_by = current_user.id
    project.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(project)
    
    return {"data": project}

# Delete a project
async def delete_project(db: Session, project_id: str) -> None:
    """Delete a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()

# Get projects by department
async def get_projects_by_department(db: Session, department_id: str) -> List[ProjectResponse]:
    """Get projects for a specific department"""
    projects = db.query(Project).filter(Project.department_id == department_id).all()
    return projects

# Get projects by event
async def get_projects_by_event(db: Session, event_id: str) -> List[ProjectResponse]:
    """Get projects for a specific event"""
    projects = db.query(Project).filter(Project.event_id == event_id).all()
    return projects

# Get event winners
async def get_event_winners(db: Session, event_id: str) -> List[ProjectResponse]:
    """Get winning projects for an event (highest scores)"""
    # Get projects for the event with central evaluation scores
    projects = db.query(Project).filter(
        Project.event_id == event_id,
        Project.central_evaluation != None  # Projects with central evaluation
    ).order_by(
        Project.central_evaluation['score'].desc()  # Order by score (descending)
    ).limit(10).all()
    
    return projects

# Import projects from CSV
async def import_projects_from_csv(db: Session, file: UploadFile) -> Dict[str, Any]:
    """Import projects from CSV file"""
    content = await file.read()
    
    # Process CSV
    projects_data = []
    reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
    
    for row in reader:
        # Process each row
        # This would need to be customized based on your CSV format
        projects_data.append({
            "title": row.get("Title", ""),
            "category": row.get("Category", ""),
            "abstract": row.get("Abstract", ""),
            # Map other fields
        })
    
    # Import data (simplified for example)
    imported_count = 0
    for data in projects_data:
        try:
            # Create project (simplified)
            project = Project(
                id=str(uuid.uuid4()),
                title=data["title"],
                category=data["category"],
                abstract=data["abstract"],
                # Set other fields with appropriate defaults
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(project)
            imported_count += 1
        except Exception as e:
            print(f"Error importing project: {e}")
    
    db.commit()
    
    return {"message": f"Successfully imported {imported_count} projects", "count": imported_count}

# Export projects to CSV
async def export_projects_to_csv(db: Session) -> Any:
    """Export projects to CSV file"""
    # Get all projects
    projects = db.query(Project).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Title", "Category", "Abstract", "Status",
        "Department", "Team", "Event", "Location",
        "Created At", "Updated At"
    ])
    
    # Write data
    for project in projects:
        writer.writerow([
            project.id,
            project.title,
            project.category,
            project.abstract,
            project.status,
            project.department_id,
            project.team_id,
            project.event_id,
            project.location_id,
            project.created_at.isoformat() if project.created_at else "",
            project.updated_at.isoformat() if project.updated_at else ""
        ])
    
    # Create response
    response = output.getvalue()
    return response

# Get project statistics
async def get_project_statistics(db: Session) -> Dict[str, Any]:
    """Get project statistics"""
    total_count = db.query(Project).count()
    
    # Count by status
    status_counts = {}
    for status in ["draft", "submitted", "approved", "rejected", "completed"]:
        count = db.query(Project).filter(Project.status == status).count()
        status_counts[status] = count
    
    # Count by department
    department_counts = {}
    departments = db.query(Department).all()
    for dept in departments:
        count = db.query(Project).filter(Project.department_id == dept.id).count()
        department_counts[dept.name] = count
    
    # Evaluation statistics
    evaluated_count = db.query(Project).filter(
        Project.dept_evaluation != None,
        Project.central_evaluation != None
    ).count()
    
    pending_count = total_count - evaluated_count
    
    return {
        "total": total_count,
        "by_status": status_counts,
        "by_department": department_counts,
        "evaluated": evaluated_count,
        "pending": pending_count
    }

# Get project counts by category
async def get_project_counts_by_category(db: Session) -> Dict[str, Any]:
    """Get project counts grouped by category"""
    # Get all projects
    projects = db.query(Project).all()
    
    # Group by category
    categories = {}
    for project in projects:
        category = project.category
        if category not in categories:
            categories[category] = {
                "count": 0,
                "departments": set()
            }
        
        categories[category]["count"] += 1
        categories[category]["departments"].add(project.department_id)
    
    # Format for response
    result = []
    for category, data in categories.items():
        result.append({
            "category": category,
            "count": data["count"],
            "department_count": len(data["departments"]),
            "department_info": list(data["departments"])
        })
    
    # Sort by count (descending)
    result.sort(key=lambda x: x["count"], reverse=True)
    
    return {"category_counts": result}