from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.admin import router as admin_router
from app.api.departments import router as departments_router
from app.api.faculty import router as faculty_router
from app.api.students import router as students_router

# Combine all routers
api_router = APIRouter(prefix="/api")

# Add all routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(departments_router)
api_router.include_router(faculty_router)
api_router.include_router(students_router)

# Export the combined router
__all__ = ["api_router"]