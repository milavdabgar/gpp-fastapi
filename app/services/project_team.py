from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.models.user import User
from app.models.team import Team
from app.models.department import Department
from app.schemas import (
    TeamCreate, TeamUpdate, TeamResponse, TeamMemberCreate,
    PaginatedResponse, PaginatedMeta
)

# Get all teams with pagination
async def get_teams(
    db: Session, 
    page: int = 1, 
    limit: int = 10
) -> PaginatedResponse[List[TeamResponse]]:
    """Get all teams with pagination"""
    query = db.query(Team)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Execute query
    teams = query.all()
    
    # Create pagination metadata
    meta = PaginatedMeta(
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit  # Ceiling division
    )
    
    # Return paginated response
    return {
        "data": teams,
        "meta": meta
    }

# Get a single team by ID
async def get_team(db: Session, team_id: str) -> TeamResponse:
    """Get a single team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team

# Create a new team
async def create_team(db: Session, team_data: TeamCreate, current_user: User) -> TeamResponse:
    """Create a new team"""
    # Validate department
    department = db.query(Department).filter(Department.id == team_data.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Create new team
    new_team = Team(
        id=str(uuid.uuid4()),
        name=team_data.name,
        department_id=team_data.department_id,
        event_id=team_data.event_id,
        members=team_data.members,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # Add to database
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    
    return new_team

# Update an existing team
async def update_team(db: Session, team_id: str, team_data: TeamUpdate, current_user: User) -> TeamResponse:
    """Update an existing team"""
    # Get team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Update team attributes - only if provided in the request
    update_data = team_data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(team, key, value)
    
    # Set updated_by and updated_at
    team.updated_by = current_user.id
    team.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(team)
    
    return team

# Delete a team
async def delete_team(db: Session, team_id: str) -> None:
    """Delete a team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    db.delete(team)
    db.commit()

# Get teams by department
async def get_teams_by_department(db: Session, department_id: str) -> List[TeamResponse]:
    """Get teams for a specific department"""
    teams = db.query(Team).filter(Team.department_id == department_id).all()
    return teams

# Get teams by event
async def get_teams_by_event(db: Session, event_id: str) -> List[TeamResponse]:
    """Get teams for a specific event"""
    teams = db.query(Team).filter(Team.event_id == event_id).all()
    return teams

# Get team members
async def get_team_members(db: Session, team_id: str) -> List[Dict[str, Any]]:
    """Get members of a specific team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team.members

# Add team member
async def add_team_member(db: Session, team_id: str, member_data: TeamMemberCreate, current_user: User) -> TeamResponse:
    """Add a member to a team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if user already in team
    for member in team.members:
        if member["user_id"] == member_data.user_id:
            raise HTTPException(status_code=400, detail="User already in team")
    
    # Add member
    team.members.append(member_data.dict())
    
    # Update metadata
    team.updated_by = current_user.id
    team.updated_at = datetime.utcnow()
    
    # Save changes
    db.commit()
    db.refresh(team)
    
    return team

# Remove team member
async def remove_team_member(db: Session, team_id: str, user_id: str, current_user: User) -> TeamResponse:
    """Remove a member from a team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Find member
    member_index = None
    for i, member in enumerate(team.members):
        if member["user_id"] == user_id:
            member_index = i
            break
    
    if member_index is None:
        raise HTTPException(status_code=404, detail="Member not found in team")
    
    # Remove member
    team.members.pop(member_index)
    
    # Update metadata
    team.updated_by = current_user.id
    team.updated_at = datetime.utcnow()
    
    # Save changes
    db.commit()
    db.refresh(team)
    
    return team

# Set team leader
async def set_team_leader(db: Session, team_id: str, user_id: str, current_user: User) -> TeamResponse:
    """Set a team member as the leader"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Find member and update leader status
    found = False
    for member in team.members:
        if member["user_id"] == user_id:
            member["is_leader"] = True
            found = True
        else:
            # Ensure only one leader
            member["is_leader"] = False
    
    if not found:
        raise HTTPException(status_code=404, detail="Member not found in team")
    
    # Update metadata
    team.updated_by = current_user.id
    team.updated_at = datetime.utcnow()
    
    # Save changes
    db.commit()
    db.refresh(team)
    
    return team