from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from jose.exceptions import JWTError
from typing import Union, Any

from app.schemas import ErrorResponse

class AppError(Exception):
    """Custom application error class"""
    def __init__(self, message: str, status_code: int = 400, detail: Any = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


async def error_handler(request: Request, call_next) -> JSONResponse:
    """
    Global exception handler for the application.
    Catches all exceptions and returns appropriate JSON responses.
    """
    try:
        return await call_next(request)
    except Exception as exc:
        # Convert detail to dict if it's not already a dict
        def prepare_detail(detail):
            if detail is None:
                return None
            if isinstance(detail, dict):
                return detail
            return {"error": str(detail)}
            
        # Handle custom app errors
        if isinstance(exc, AppError):
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(
                    status="error",
                    message=exc.message,
                    detail=prepare_detail(exc.detail)
                ).dict()
            )
    
        # Handle validation errors
        if isinstance(exc, ValidationError):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=ErrorResponse(
                    status="error",
                    message="Validation error",
                    detail={"errors": exc.errors()}
                ).dict()
            )
        
        # Handle database integrity errors (e.g. unique constraint violations)
        if isinstance(exc, IntegrityError):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    status="error",
                    message="Database integrity error",
                    detail=prepare_detail(str(exc))
                ).dict()
            )
        
        # Handle general database errors
        if isinstance(exc, SQLAlchemyError):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    status="error",
                    message="Database error",
                    detail=prepare_detail(str(exc))
                ).dict()
            )
        
        # Handle JWT errors
        if isinstance(exc, JWTError):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    status="error",
                    message="Invalid authentication credentials",
                    detail=prepare_detail(str(exc))
                ).dict(),
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Handle all other exceptions
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                status="error",
                message="Internal server error",
                detail=prepare_detail(str(exc) if str(exc) else None)
            ).dict()
        )