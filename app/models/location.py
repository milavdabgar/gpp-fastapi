# Import ProjectLocation from project model and re-export as Location
from app.models.project import ProjectLocation as Location

# Re-export to maintain compatibility with existing code
__all__ = ["Location"]