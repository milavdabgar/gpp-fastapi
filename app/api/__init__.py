from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.admin import router as admin_router
from app.api.departments import router as departments_router
from app.api.faculty import router as faculty_router
from app.api.students import router as students_router
from app.api.projects import router as projects_router
from app.api.results import router as results_router
from app.api.feedback import router as feedback_router

# Combine all routers
api_router = APIRouter(prefix="/api")

# Add a root handler for the /api path
@api_router.get("/", include_in_schema=False)
async def api_root():
    return RedirectResponse(url="/api/docs")

# Add all routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(departments_router)
api_router.include_router(faculty_router)
api_router.include_router(students_router)
api_router.include_router(projects_router)
api_router.include_router(results_router)
api_router.include_router(feedback_router)

# Export the combined router
__all__ = ["api_router"]