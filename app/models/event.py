# Import ProjectEvent from project model and re-export as Event
from app.models.project import ProjectEvent as Event

# Re-export to maintain compatibility with existing code
__all__ = ["Event"]