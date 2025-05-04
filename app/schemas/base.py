from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List, Dict, Any

T = TypeVar('T')

# Standard response models
class ResponseBase(BaseModel):
    status: str = "success"
    message: Optional[str] = None

class DataResponse(ResponseBase, Generic[T]):
    data: T

class PaginatedMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int

class PaginatedResponse(ResponseBase, Generic[T]):
    data: T
    pagination: PaginatedMeta

# For file uploads
class FileUploadResponse(ResponseBase):
    filename: str
    content_type: str
    size: int

# For CSV import/export
class CSVImportResponse(ResponseBase):
    imported_count: int
    total_rows: int
    errors: Optional[List[str]] = None

class CSVExportResponse(ResponseBase):
    download_url: str

# Error response
class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[Dict[str, Any]] = None

# Common validation schemas
class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 100
    
    class Config:
        orm_mode = True

class SearchParams(PaginationParams):
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    
    class Config:
        orm_mode = True