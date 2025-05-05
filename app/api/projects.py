from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithDetails,
    TeamCreate, TeamUpdate, TeamResponse, EventCreate, EventUpdate, EventResponse,
    LocationCreate, LocationUpdate, LocationResponse,
    DataResponse, ResponseBase, PaginatedResponse, PaginatedMeta
)
from app.services.project import (
    get_project, get_projects, create_project, update_project, delete_project,
    get_projects_by_department, get_projects_by_event, get_event_winners,
    import_projects_from_csv, export_projects_to_csv,
    get_project_statistics, get_project_counts_by_category
)
from app.services.project_team import (
    get_team, get_teams, create_team, update_team, delete_team,
    get_teams_by_department, get_teams_by_event, get_team_members,
    add_team_member, remove_team_member, set_team_leader
)
from app.services.project_event import (
    get_event, get_events, create_event, update_event, delete_event,
    get_active_events, publish_results, get_event_schedule, update_event_schedule
)
from app.services.project_location import (
    get_location, get_locations, create_location, update_location, delete_location,
    get_locations_by_section, get_locations_by_department, get_locations_by_event,
    assign_project_to_location, unassign_project_from_location
)
from app.services.project_evaluation import (
    evaluate_project_by_department, evaluate_project_by_central,
    get_projects_for_jury
)
from app.middleware.auth import get_authenticated_user, require_admin, require_jury
from app.middleware.error import AppError

router = APIRouter(
    prefix="/projects",
    tags=["projects"]
)

# Project Routes
@router.get("", response_model=PaginatedResponse[List[ProjectResponse]])
async def get_all_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    department: Optional[str] = None,
    event: Optional[str] = None,
    sort_by: str = "created_at",
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all projects with filtering and pagination"""
    return await get_projects(db, page, limit, search, department, event, sort_by)

@router.post("", response_model=DataResponse[ProjectResponse])
async def create_project_endpoint(
    project_data: ProjectCreate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    return await create_project(db, project_data, current_user)

@router.get("/my-projects", response_model=List[ProjectResponse])
async def get_my_projects(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get projects for current user"""
    # Use department-based projects for now as a fallback
    if hasattr(current_user, 'department_id') and current_user.department_id:
        return await get_projects_by_department(db, current_user.department_id)
    else:
        # Return empty list if user has no department
        return []

@router.get("/export-csv", response_class=Response)
async def export_projects_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Export projects to CSV"""
    return await export_projects_to_csv(db)

@router.post("/import-csv", response_model=ResponseBase)
async def import_projects_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Import projects from CSV"""
    return await import_projects_from_csv(db, file)

@router.get("/statistics", response_model=dict)
async def get_statistics(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get project statistics"""
    return await get_project_statistics(db)

@router.get("/categories", response_model=dict)
async def get_category_counts(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get project counts by category"""
    return await get_project_counts_by_category(db)

# Team Routes
@router.get("/teams", response_model=PaginatedResponse[List[TeamResponse]])
async def get_all_teams(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all project teams"""
    return await get_teams(db, page, limit)

# Event Routes
@router.get("/events", response_model=List[EventResponse])
async def get_all_events(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all project events"""
    return await get_events(db)

@router.get("/events/active", response_model=List[EventResponse])
async def get_active_events_endpoint(
    db: Session = Depends(get_db)
):
    """Get active project events"""
    return await get_active_events(db)

# Location Routes
@router.get("/locations", response_model=List[LocationResponse])
async def get_all_locations(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all project locations"""
    return await get_locations(db)

# Add other routes for teams, events, locations, evaluations...