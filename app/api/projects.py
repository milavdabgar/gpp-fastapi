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

@router.get("/export")
async def export_projects_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Export projects to CSV"""
    return await export_projects_to_csv(db)

@router.post("/import")
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

@router.get("/jury-assignments", response_model=List[ProjectResponse])
async def get_jury_assignments(
    current_user: User = Depends(require_jury),
    db: Session = Depends(get_db)
):
    """Get projects assigned to jury"""
    return await get_projects_for_jury(db, current_user.id)

# Department and Event specific project routes
@router.get("/department/{department_id}", response_model=List[ProjectResponse])
async def get_department_projects(
    department_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get projects by department"""
    return await get_projects_by_department(db, department_id)

@router.get("/event/{event_id}", response_model=List[ProjectResponse])
async def get_event_projects(
    event_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get projects by event"""
    return await get_projects_by_event(db, event_id)

@router.get("/event/{event_id}/winners", response_model=List[ProjectResponse])
async def get_winners(
    event_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get event winners"""
    return await get_event_winners(db, event_id)

@router.get("/team/{team_id}", response_model=List[ProjectResponse])
async def get_team_projects(
    team_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get projects by team"""
    # This endpoint needs to be implemented in the project service
    projects = await get_project(db, {'team_id': team_id})
    if not projects:
        return []
    return projects

# Single project routes
@router.get("/{project_id}", response_model=DataResponse[ProjectResponse])
async def get_project_by_id(
    project_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get a project by ID"""
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"data": project}

@router.patch("/{project_id}", response_model=DataResponse[ProjectResponse])
async def update_project_endpoint(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Update a project"""
    updated_project = await update_project(db, project_id, project_data, current_user)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"data": updated_project}

@router.delete("/{project_id}", response_model=ResponseBase)
async def delete_project_endpoint(
    project_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    result = await delete_project(db, project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}

@router.get("/{project_id}/details", response_model=DataResponse[ProjectWithDetails])
async def get_project_details(
    project_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get project with detailed information"""
    project = await get_project(db, project_id, include_details=True)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"data": project}

@router.post("/{project_id}/department-evaluation", response_model=ResponseBase)
async def evaluate_dept_project(
    project_id: int,
    evaluation_data: dict,
    current_user: User = Depends(require_jury),
    db: Session = Depends(get_db)
):
    """Submit department evaluation for a project"""
    result = await evaluate_project_by_department(db, project_id, evaluation_data, current_user.id)
    return {"message": "Department evaluation submitted successfully"}

@router.post("/{project_id}/central-evaluation", response_model=ResponseBase)
async def evaluate_central_project(
    project_id: int,
    evaluation_data: dict,
    current_user: User = Depends(require_jury),
    db: Session = Depends(get_db)
):
    """Submit central evaluation for a project"""
    result = await evaluate_project_by_central(db, project_id, evaluation_data, current_user.id)
    return {"message": "Central evaluation submitted successfully"}

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

@router.post("/teams", response_model=DataResponse[TeamResponse])
async def create_team_endpoint(
    team_data: TeamCreate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    return await create_team(db, team_data, current_user)

@router.get("/teams/my-teams", response_model=List[TeamResponse])
async def get_my_teams(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get teams for the current user"""
    # This endpoint needs to be implemented in the team service
    # For now we'll filter by department as a fallback
    if hasattr(current_user, 'department_id') and current_user.department_id:
        return await get_teams_by_department(db, current_user.department_id)
    else:
        return []

@router.get("/teams/export")
async def export_teams_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    """Export teams to CSV"""
    # This endpoint needs to be implemented in the team service
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.post("/teams/import")
async def import_teams_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Import teams from CSV"""
    # This endpoint needs to be implemented in the team service
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.get("/teams/department/{department_id}", response_model=List[TeamResponse])
async def get_department_teams(
    department_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get teams by department"""
    return await get_teams_by_department(db, department_id)

@router.get("/teams/event/{event_id}", response_model=List[TeamResponse])
async def get_event_teams(
    event_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get teams by event"""
    return await get_teams_by_event(db, event_id)

@router.get("/teams/{team_id}", response_model=DataResponse[TeamResponse])
async def get_team_by_id(
    team_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get a team by ID"""
    team = await get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"data": team}

@router.patch("/teams/{team_id}", response_model=DataResponse[TeamResponse])
async def update_team_endpoint(
    team_id: int,
    team_data: TeamUpdate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Update a team"""
    updated_team = await update_team(db, team_id, team_data, current_user)
    if not updated_team:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"data": updated_team}

@router.delete("/teams/{team_id}", response_model=ResponseBase)
async def delete_team_endpoint(
    team_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a team"""
    result = await delete_team(db, team_id)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"message": "Team deleted successfully"}

@router.get("/teams/{team_id}/members", response_model=List[dict])
async def get_members(
    team_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get team members"""
    return await get_team_members(db, team_id)

@router.post("/teams/{team_id}/members", response_model=ResponseBase)
async def add_member(
    team_id: int,
    member_data: dict,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Add a team member"""
    result = await add_team_member(db, team_id, member_data["user_id"])
    return {"message": "Team member added successfully"}

@router.delete("/teams/{team_id}/members/{user_id}", response_model=ResponseBase)
async def remove_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Remove a team member"""
    result = await remove_team_member(db, team_id, user_id)
    return {"message": "Team member removed successfully"}

@router.patch("/teams/{team_id}/leader/{user_id}", response_model=ResponseBase)
async def set_leader(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Set team leader"""
    result = await set_team_leader(db, team_id, user_id)
    return {"message": "Team leader set successfully"}

# Event Routes
@router.get("/events", response_model=List[EventResponse])
async def get_all_events(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all project events"""
    return await get_events(db)

@router.post("/events", response_model=DataResponse[EventResponse])
async def create_event_endpoint(
    event_data: EventCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new event"""
    return await create_event(db, event_data)

@router.get("/events/active", response_model=List[EventResponse])
async def get_active_events_endpoint(
    db: Session = Depends(get_db)
):
    """Get active project events"""
    return await get_active_events(db)

@router.get("/events/export")
async def export_events_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Export events to CSV"""
    # This endpoint needs to be implemented in the event service
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.post("/events/import")
async def import_events_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Import events from CSV"""
    # This endpoint needs to be implemented in the event service
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.get("/events/{event_id}", response_model=DataResponse[EventResponse])
async def get_event_by_id(
    event_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get an event by ID"""
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"data": event}

@router.patch("/events/{event_id}", response_model=DataResponse[EventResponse])
async def update_event_endpoint(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update an event"""
    updated_event = await update_event(db, event_id, event_data)
    if not updated_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"data": updated_event}

@router.delete("/events/{event_id}", response_model=ResponseBase)
async def delete_event_endpoint(
    event_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete an event"""
    result = await delete_event(db, event_id)
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}

@router.patch("/events/{event_id}/publish-results", response_model=ResponseBase)
async def publish_event_results(
    event_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Publish event results"""
    result = await publish_results(db, event_id)
    return {"message": "Event results published successfully"}

@router.get("/events/{event_id}/schedule", response_model=dict)
async def get_schedule(
    event_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get event schedule"""
    return await get_event_schedule(db, event_id)

@router.patch("/events/{event_id}/schedule", response_model=ResponseBase)
async def update_schedule(
    event_id: int,
    schedule_data: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update event schedule"""
    result = await update_event_schedule(db, event_id, schedule_data)
    return {"message": "Event schedule updated successfully"}

# Location Routes
@router.get("/locations", response_model=List[LocationResponse])
async def get_all_locations(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all project locations"""
    return await get_locations(db)

@router.post("/locations", response_model=DataResponse[LocationResponse])
async def create_location_endpoint(
    location_data: LocationCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new location"""
    return await create_location(db, location_data)

@router.get("/locations/export")
async def export_locations_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Export locations to CSV"""
    # This endpoint needs to be implemented in the location service
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.post("/locations/import")
async def import_locations_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Import locations from CSV"""
    # This endpoint needs to be implemented in the location service
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.post("/locations/batch", response_model=ResponseBase)
async def create_location_batch(
    location_data: List[LocationCreate],
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create multiple locations at once"""
    # This endpoint needs to be implemented in the location service
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.get("/locations/section/{section}", response_model=List[LocationResponse])
async def get_section_locations(
    section: str,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get locations by section"""
    return await get_locations_by_section(db, section)

@router.get("/locations/department/{department_id}", response_model=List[LocationResponse])
async def get_department_locations(
    department_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get locations by department"""
    return await get_locations_by_department(db, department_id)

@router.get("/locations/event/{event_id}", response_model=List[LocationResponse])
async def get_event_locations(
    event_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get locations by event"""
    return await get_locations_by_event(db, event_id)

@router.get("/locations/{location_id}", response_model=DataResponse[LocationResponse])
async def get_location_by_id(
    location_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get a location by ID"""
    location = await get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"data": location}

@router.patch("/locations/{location_id}", response_model=DataResponse[LocationResponse])
async def update_location_endpoint(
    location_id: int,
    location_data: LocationUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a location"""
    updated_location = await update_location(db, location_id, location_data)
    if not updated_location:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"data": updated_location}

@router.delete("/locations/{location_id}", response_model=ResponseBase)
async def delete_location_endpoint(
    location_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a location"""
    result = await delete_location(db, location_id)
    if not result:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location deleted successfully"}

@router.patch("/locations/{location_id}/assign", response_model=ResponseBase)
async def assign_project(
    location_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Assign project to location"""
    result = await assign_project_to_location(db, location_id, data.get("project_id"))
    return {"message": "Project assigned to location successfully"}

@router.patch("/locations/{location_id}/unassign", response_model=ResponseBase)
async def unassign_project(
    location_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Unassign project from location"""
    result = await unassign_project_from_location(db, location_id)
    return {"message": "Project unassigned from location successfully"}