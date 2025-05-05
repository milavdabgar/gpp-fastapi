from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.models.user import User
from app.models.event import Event
from app.models.department import Department
from app.schemas import (
    EventCreate, EventUpdate, EventResponse,
    ScheduleItemCreate, ScheduleItemUpdate
)

# Get all events
async def get_events(db: Session) -> List[EventResponse]:
    """Get all events"""
    events = db.query(Event).order_by(Event.event_date.desc()).all()
    return events

# Get active events
async def get_active_events(db: Session) -> List[EventResponse]:
    """Get active events"""
    events = db.query(Event).filter(
        Event.is_active == True
    ).order_by(Event.event_date).all()
    return events

# Get a single event by ID
async def get_event(db: Session, event_id: str) -> EventResponse:
    """Get a single event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

# Create a new event
async def create_event(db: Session, event_data: EventCreate, current_user: User) -> EventResponse:
    """Create a new event"""
    # Validate departments if provided
    if event_data.departments:
        for dept_id in event_data.departments:
            department = db.query(Department).filter(Department.id == dept_id).first()
            if not department:
                raise HTTPException(status_code=404, detail=f"Department with ID {dept_id} not found")
    
    # Create new event
    new_event = Event(
        id=str(uuid.uuid4()),
        name=event_data.name,
        description=event_data.description,
        academic_year=event_data.academic_year,
        event_date=event_data.event_date,
        registration_start_date=event_data.registration_start_date,
        registration_end_date=event_data.registration_end_date,
        is_active=event_data.is_active,
        status=event_data.status,
        departments=event_data.departments,
        schedule=event_data.schedule if event_data.schedule else [],
        publish_results=False,  # Default to not publishing results
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # Add to database
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return new_event

# Update an existing event
async def update_event(db: Session, event_id: str, event_data: EventUpdate, current_user: User) -> EventResponse:
    """Update an existing event"""
    # Get event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Validate departments if provided
    if event_data.departments:
        for dept_id in event_data.departments:
            department = db.query(Department).filter(Department.id == dept_id).first()
            if not department:
                raise HTTPException(status_code=404, detail=f"Department with ID {dept_id} not found")
    
    # Update event attributes - only if provided in the request
    update_data = event_data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        # Handle status based on dates
        if key == 'event_date' or key == 'registration_start_date' or key == 'registration_end_date':
            # Update status based on dates
            if not event.is_active:
                event.status = 'cancelled'
            elif datetime.now() > event_data.event_date:
                event.status = 'completed'
            elif datetime.now() >= event_data.registration_start_date and datetime.now() <= event_data.registration_end_date:
                event.status = 'ongoing'
            else:
                event.status = 'upcoming'
        
        setattr(event, key, value)
    
    # Set updated_by and updated_at
    event.updated_by = current_user.id
    event.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(event)
    
    return event

# Delete an event
async def delete_event(db: Session, event_id: str) -> None:
    """Delete an event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check for associated projects before deleting
    # This would require importing Project model which might create circular imports
    # For now, we'll assume this check happens at the API level
    
    # Delete the event
    db.delete(event)
    db.commit()

# Publish/unpublish event results
async def publish_results(db: Session, event_id: str, publish: bool, current_user: User) -> EventResponse:
    """Publish or unpublish event results"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update publish flag
    event.publish_results = publish
    event.updated_by = current_user.id
    event.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(event)
    
    return event

# Get event schedule
async def get_event_schedule(db: Session, event_id: str) -> Dict[str, Any]:
    """Get schedule for an event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "schedule": event.schedule,
        "event_date": event.event_date
    }

# Update event schedule
async def update_event_schedule(db: Session, event_id: str, schedule: List[Dict[str, Any]], current_user: User) -> Dict[str, List[Dict[str, Any]]]:
    """Update schedule for an event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Validate schedule items
    for item in schedule:
        if not item.get("time") or not item.get("activity") or not item.get("location"):
            raise HTTPException(status_code=400, detail="Invalid schedule item")
    
    # Update schedule
    event.schedule = schedule
    event.updated_by = current_user.id
    event.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(event)
    
    return {"schedule": event.schedule}