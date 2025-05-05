from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.models.user import User
from app.models.location import Location
from app.models.project import Project
from app.models.department import Department
from app.models.event import Event
from app.schemas import (
    LocationCreate, LocationUpdate, LocationResponse,
    PaginatedResponse, PaginatedMeta
)

# Get all locations with pagination and filtering
async def get_locations(
    db: Session, 
    page: int = 1, 
    limit: int = 50,
    department_id: Optional[str] = None,
    event_id: Optional[str] = None,
    section: Optional[str] = None,
    is_assigned: Optional[bool] = None
) -> PaginatedResponse[List[LocationResponse]]:
    """Get all locations with pagination and filtering"""
    query = db.query(Location)
    
    # Apply filters
    if department_id:
        query = query.filter(Location.department_id == department_id)
    if event_id:
        query = query.filter(Location.event_id == event_id)
    if section:
        query = query.filter(Location.section == section)
    if is_assigned is not None:
        query = query.filter(Location.is_assigned == is_assigned)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply sorting and pagination
    query = query.order_by(Location.section, Location.position)
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Execute query
    locations = query.all()
    
    # Create pagination metadata
    meta = PaginatedMeta(
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit  # Ceiling division
    )
    
    # Return paginated response
    return {
        "data": locations,
        "meta": meta
    }

# Get a single location by ID
async def get_location(db: Session, location_id: str) -> LocationResponse:
    """Get a single location"""
    location = db.query(Location).filter(Location.id == location_id).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return location

# Create a new location
async def create_location(db: Session, location_data: LocationCreate, current_user: User) -> LocationResponse:
    """Create a new location"""
    # Validate department
    department = db.query(Department).filter(Department.id == location_data.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Validate event
    event = db.query(Event).filter(Event.id == location_data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if location_id already exists
    existing_location = db.query(Location).filter(Location.location_id == location_data.location_id).first()
    if existing_location:
        raise HTTPException(status_code=400, detail=f"Location ID '{location_data.location_id}' already exists")
    
    # Create new location
    new_location = Location(
        id=str(uuid.uuid4()),
        location_id=location_data.location_id,
        section=location_data.section,
        position=location_data.position,
        department_id=location_data.department_id,
        event_id=location_data.event_id,
        is_assigned=False,  # Default to not assigned
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # Add to database
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    
    return new_location

# Update a location
async def update_location(db: Session, location_id: str, location_data: LocationUpdate, current_user: User) -> LocationResponse:
    """Update a location"""
    # Get location
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Update location attributes - only if provided in the request
    update_data = location_data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(location, key, value)
    
    # Set updated_by and updated_at
    location.updated_by = current_user.id
    location.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(location)
    
    return location

# Delete a location
async def delete_location(db: Session, location_id: str) -> None:
    """Delete a location"""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if location is assigned to a project
    if location.is_assigned:
        raise HTTPException(status_code=400, detail="Cannot delete a location that is assigned to a project")
    
    db.delete(location)
    db.commit()

# Get locations by section
async def get_locations_by_section(db: Session, section: str) -> List[LocationResponse]:
    """Get locations for a specific section"""
    locations = db.query(Location).filter(
        Location.section == section
    ).order_by(Location.position).all()
    return locations

# Get locations by department
async def get_locations_by_department(db: Session, department_id: str) -> List[LocationResponse]:
    """Get locations for a specific department"""
    locations = db.query(Location).filter(
        Location.department_id == department_id
    ).order_by(Location.section, Location.position).all()
    return locations

# Get locations by event
async def get_locations_by_event(db: Session, event_id: str) -> Dict[str, Any]:
    """Get locations for a specific event grouped by section"""
    locations = db.query(Location).filter(
        Location.event_id == event_id
    ).order_by(Location.section, Location.position).all()
    
    # Group locations by section
    sections = {}
    for location in locations:
        if location.section not in sections:
            sections[location.section] = []
        sections[location.section].append(location)
    
    # Format for response
    section_list = [
        {"section": section, "locations": locations}
        for section, locations in sections.items()
    ]
    
    return {
        "sections": section_list,
        "total_locations": len(locations),
        "assigned_locations": sum(1 for loc in locations if loc.is_assigned)
    }

# Assign project to location
async def assign_project_to_location(db: Session, location_id: str, project_id: str, current_user: User) -> LocationResponse:
    """Assign a project to a location"""
    # Get location by its string ID (location_id)
    location = db.query(Location).filter(Location.location_id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=404, 
            detail=f"Location with ID {location_id} not found. Please ensure you are using the location's string ID (e.g., 'A-01') and not its MongoDB _id."
        )
    
    # Check if location is already assigned to another project
    if location.is_assigned and location.project_id != project_id:
        raise HTTPException(status_code=400, detail="Location is already assigned to another project")
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if project is already assigned to a different location
    existing_location = db.query(Location).filter(
        Location.project_id == project_id,
        Location.location_id != location_id
    ).first()
    
    if existing_location:
        raise HTTPException(
            status_code=400, 
            detail=f"Project is already assigned to location {existing_location.location_id}"
        )
    
    # Update location with project
    location.project_id = project_id
    location.is_assigned = True
    location.updated_by = current_user.id
    location.updated_at = datetime.utcnow()
    
    # Update project with location
    project.location_id = location_id
    project.updated_by = current_user.id
    project.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(location)
    
    return location

# Unassign project from location
async def unassign_project_from_location(db: Session, location_id: str, current_user: User) -> LocationResponse:
    """Unassign a project from a location"""
    # Get location by its string ID
    location = db.query(Location).filter(Location.location_id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if location is assigned
    if not location.is_assigned or not location.project_id:
        raise HTTPException(status_code=400, detail="Location is not assigned to any project")
    
    # Get project ID before updating
    project_id = location.project_id
    
    # Update location
    location.project_id = None
    location.is_assigned = False
    location.updated_by = current_user.id
    location.updated_at = datetime.utcnow()
    
    # Update project
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.location_id = None
        project.updated_by = current_user.id
        project.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(location)
    
    return location