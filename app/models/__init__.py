from app.models.user import User, Role, user_roles
from app.models.department import Department
from app.models.faculty import Faculty, FacultyQualification
from app.models.student import (
    Student, StudentGuardian, StudentContact, 
    StudentEducation, StudentSemesterStatus
)
from app.models.project import (
    ProjectEvent, EventSchedule, event_departments,
    ProjectTeam, TeamMember, ProjectLocation, Project,
    DepartmentEvaluation, CentralEvaluation
)
from app.models.result import Result, ResultSubject

# Import all models here to make them available to Alembic
__all__ = [
    'User', 'Role', 'user_roles',
    'Department',
    'Faculty', 'FacultyQualification',
    'Student', 'StudentGuardian', 'StudentContact', 'StudentEducation', 'StudentSemesterStatus',
    'ProjectEvent', 'EventSchedule', 'event_departments',
    'ProjectTeam', 'TeamMember', 'ProjectLocation', 'Project',
    'DepartmentEvaluation', 'CentralEvaluation',
    'Result', 'ResultSubject'
]