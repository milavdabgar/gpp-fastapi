# Import ProjectTeam from project model and re-export as Team
from app.models.project import ProjectTeam as Team, TeamMember

# Re-export to maintain compatibility with existing code
__all__ = ["Team", "TeamMember"]