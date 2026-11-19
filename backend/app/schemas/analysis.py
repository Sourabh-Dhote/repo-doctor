from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict
from datetime import datetime

class AnalyzeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_and_normalize_url(cls, v: str) -> str:
        cleaned = str(v).strip().strip("'\"")
        if not cleaned:
            raise ValueError("GitHub URL cannot be empty")
        if not cleaned.startswith(("http://", "https://")):
            cleaned = f"https://{cleaned}"
        return cleaned

class IssueResponse(BaseModel):
    id: str
    analysis_id: str
    severity: str
    category: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    
    class Config:
        from_attributes = True

class AnalysisStatusResponse(BaseModel):
    id: str
    status: str
    health_score: Optional[int] = None
    started_at: datetime
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class RepositoryInfo(BaseModel):
    id: str
    url: str
    name: str
    owner: str
    cloned_at: datetime
    total_files: int
    languages: dict
    
    class Config:
        from_attributes = True

class AnalysisResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    health_score: Optional[int] = None
    summary: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    repository: Optional[RepositoryInfo] = None
    issues: List[IssueResponse] = []
    
    class Config:
        from_attributes = True

class RecentAnalysisItem(BaseModel):
    id: str
    status: str
    health_score: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    repo_name: str
    repo_owner: str
    repo_url: str

    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    health_score: int
    summary: str
    issues_by_category: Dict[str, List[IssueResponse]]
    repository_stats: Dict
