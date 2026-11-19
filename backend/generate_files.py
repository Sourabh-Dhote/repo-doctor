import os

base_dir = r"c:\Projects\repodoctor-ai\backend"

files = {
    "requirements.txt": """fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
pydantic==2.9.0
pydantic-settings==2.5.0
gitpython==3.1.43
google-genai==1.0.0
python-dotenv==1.0.1
aiofiles==24.1.0
httpx==0.27.0
alembic==1.13.0
""",
    ".env.example": """GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/repodoctor
REPOS_DIR=./temp_repos
MAX_FILE_SIZE_KB=500
MAX_FILES=200
""",
    "app/__init__.py": "",
    "app/config.py": """from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./repodoctor.db"
    REPOS_DIR: str = "./temp_repos"
    MAX_FILE_SIZE_KB: int = 500
    MAX_FILES: int = 200
    ALLOWED_EXTENSIONS: list[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cpp", ".c",
        ".h", ".css", ".html", ".json", ".yaml", ".yml", ".toml", ".md", ".txt",
        ".sql", ".sh", ".bat", ".dockerfile", ".xml", ".env.example", ".gitignore"
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache()
def get_settings():
    return Settings()
""",
    "app/database.py": """from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
""",
    "app/models/__init__.py": """from .repository import Repository
from .analysis import Analysis
from .issue import Issue
""",
    "app/models/repository.py": """import uuid
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    cloned_at = Column(DateTime, default=get_utc_now)
    total_files = Column(Integer, default=0)
    languages = Column(JSON, default=dict)
    
    analyses = relationship("Analysis", back_populates="repository")
""",
    "app/models/analysis.py": """import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    status = Column(String, default="pending")
    health_score = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    started_at = Column(DateTime, default=get_utc_now)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    repository = relationship("Repository", back_populates="analyses")
    issues = relationship("Issue", back_populates="analysis", cascade="all, delete-orphan")
""",
    "app/models/issue.py": """import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Issue(Base):
    __tablename__ = "issues"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    severity = Column(String, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    line_number = Column(Integer, nullable=True)
    suggestion = Column(Text, nullable=True)

    analysis = relationship("Analysis", back_populates="issues")
""",
    "app/schemas/__init__.py": "",
    "app/schemas/analysis.py": """from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime

class AnalyzeRequest(BaseModel):
    url: HttpUrl

class IssueResponse(BaseModel):
    id: str
    analysis_id: str
    severity: str
    category: str
    title: str
    description: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    suggestion: Optional[str]
    
    class Config:
        from_attributes = True

class AnalysisStatusResponse(BaseModel):
    id: str
    status: str
    health_score: Optional[int]
    started_at: datetime
    
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
    health_score: Optional[int]
    summary: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    repository: Optional[RepositoryInfo]
    issues: List[IssueResponse] = []
    
    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    health_score: int
    summary: str
    issues_by_category: Dict[str, List[IssueResponse]]
    repository_stats: Dict
""",
    "app/utils/__init__.py": "",
    "app/utils/file_utils.py": """import os

def is_binary_file(filepath: str) -> bool:
    try:
        with open(filepath, 'tr') as check_file:
            check_file.read(1024)
            return False
    except UnicodeDecodeError:
        return True
    except Exception:
        return True

def get_language_from_extension(ext: str) -> str:
    ext = ext.lower()
    mapping = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript React", ".jsx": "JavaScript React",
        ".java": "Java", ".go": "Go", ".rs": "Rust",
        ".cpp": "C++", ".c": "C", ".h": "C/C++ Header",
        ".css": "CSS", ".html": "HTML", ".json": "JSON",
        ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
        ".md": "Markdown", ".txt": "Text", ".sql": "SQL",
        ".sh": "Shell", ".bat": "Batch", ".dockerfile": "Dockerfile",
        ".xml": "XML"
    }
    return mapping.get(ext, "Unknown")

def should_skip_directory(dirname: str) -> bool:
    skip_dirs = {
        'node_modules', '.git', '__pycache__', 'venv', '.venv',
        'dist', 'build', '.next', 'vendor', '.idea', '.vscode'
    }
    return dirname in skip_dirs

def truncate_content(content: str, max_chars: int = 10000) -> str:
    if len(content) > max_chars:
        return content[:max_chars] + "\\n... [Content Truncated] ..."
    return content
""",
    "app/services/__init__.py": "",
    "app/services/github_service.py": """import re
import os
import shutil
import asyncio
from git import Repo

def validate_github_url(url: str) -> tuple[str, str]:
    pattern = r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$"
    match = re.match(pattern, str(url))
    if not match:
        raise ValueError("Invalid GitHub URL")
    return match.group(1), match.group(2)

async def clone_repo(url: str, target_dir: str) -> str:
    def _clone():
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
        os.makedirs(target_dir, exist_ok=True)
        Repo.clone_from(url, target_dir, depth=1)
        return target_dir

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _clone)

def cleanup_repo(repo_path: str) -> None:
    try:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
    except Exception as e:
        print(f"Failed to cleanup {repo_path}: {e}")
""",
    "app/services/scanner_service.py": """import os
from dataclasses import dataclass
from typing import List, Dict, Optional
import aiofiles
from app.utils.file_utils import should_skip_directory, is_binary_file, get_language_from_extension, truncate_content

@dataclass
class ScanResult:
    file_tree: List[str]
    file_contents: Dict[str, str]
    languages: Dict[str, int]
    readme_content: Optional[str]
    config_files: Dict[str, str]
    has_tests: bool
    test_files: List[str]
    total_files: int
    has_ci: bool
    has_docker: bool
    has_env_example: bool

async def scan_repository(repo_path: str, settings) -> ScanResult:
    file_tree = []
    file_contents = {}
    languages = {}
    readme_content = None
    config_files = {}
    test_files = []
    has_tests = False
    has_ci = False
    has_docker = False
    has_env_example = False
    total_files = 0
    
    config_names = ['package.json', 'requirements.txt', 'pom.xml', 'go.mod', 'cargo.toml']
    ci_dirs = ['.github/workflows', '.gitlab-ci.yml', 'jenkinsfile']
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not should_skip_directory(d)]
        
        for file in files:
            if total_files >= settings.MAX_FILES:
                break
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path).replace("\\\\", "/")
            
            # Checks
            lower_rel_path = rel_path.lower()
            if any(ci in lower_rel_path for ci in ci_dirs):
                has_ci = True
            if 'dockerfile' in lower_rel_path or 'docker-compose' in lower_rel_path:
                has_docker = True
            if 'env.example' in lower_rel_path or '.env.example' in lower_rel_path:
                has_env_example = True
            if 'test' in lower_rel_path or 'spec' in lower_rel_path:
                has_tests = True
                test_files.append(rel_path)
                
            _, ext = os.path.splitext(file)
            if ext and ext not in settings.ALLOWED_EXTENSIONS and not ('dockerfile' in file.lower() or file.lower() == 'makefile'):
                continue
                
            if is_binary_file(file_path):
                continue
                
            file_size_kb = os.path.getsize(file_path) / 1024
            if file_size_kb > settings.MAX_FILE_SIZE_KB:
                continue
                
            total_files += 1
            file_tree.append(rel_path)
            
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    
                lines_count = len(content.splitlines())
                lang = get_language_from_extension(ext)
                if lang != "Unknown":
                    languages[lang] = languages.get(lang, 0) + lines_count
                    
                if file.lower() == 'readme.md':
                    readme_content = content
                    
                if file.lower() in config_names:
                    config_files[file] = truncate_content(content)
                    
                file_contents[rel_path] = truncate_content(content)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                
    return ScanResult(
        file_tree=file_tree,
        file_contents=file_contents,
        languages=languages,
        readme_content=readme_content,
        config_files=config_files,
        has_tests=has_tests,
        test_files=test_files,
        total_files=total_files,
        has_ci=has_ci,
        has_docker=has_docker,
        has_env_example=has_env_example
    )
""",
    "app/services/ai_service.py": """import json
import asyncio
from typing import List, Dict, Any
from google import genai
from app.config import get_settings
from app.services.scanner_service import ScanResult

settings = get_settings()
try:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception:
    client = None

def _parse_response(text: str) -> List[Dict]:
    try:
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Failed to parse JSON: {e}\\nText: {text}")
        return []

async def _call_gemini(prompt: str) -> List[Dict]:
    if not client:
        return []
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model='gemini-2.0-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(response_mime_type='application/json')
        )
        return _parse_response(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return []

async def analyze_security(file_contents: Dict[str, str], file_tree: List[str]) -> List[Dict]:
    prompt = f\"\"\"Analyze the following repository files for security vulnerabilities.
Look for: hardcoded API keys/secrets, SQL injection, XSS, insecure auth patterns, exposed sensitive data, missing input validation.
Files: {list(file_contents.keys())}
Contents:
{json.dumps(file_contents, indent=2)[:50000]}

Return a JSON array of issues with keys: title, description, file_path, line_number (integer or null), severity (critical/warning/improvement/info), category ("security"), suggestion.
\"\"\"
    return await _call_gemini(prompt)

async def analyze_code_quality(file_contents: Dict[str, str], file_tree: List[str]) -> List[Dict]:
    prompt = f\"\"\"Analyze the following repository files for code quality issues.
Look for: missing error handling, duplicate code, overly complex functions, anti-patterns, poor naming conventions, magic numbers.
Files: {list(file_contents.keys())}
Contents:
{json.dumps(file_contents, indent=2)[:50000]}

Return a JSON array of issues with keys: title, description, file_path, line_number (integer or null), severity (critical/warning/improvement/info), category ("code_quality"), suggestion.
\"\"\"
    return await _call_gemini(prompt)

async def analyze_dependencies(config_files: Dict[str, str]) -> List[Dict]:
    if not config_files:
        return []
    prompt = f\"\"\"Analyze the following dependency/config files.
Look for: outdated packages, known vulnerable packages, unnecessary dependencies, missing important dependencies, version pinning issues.
Configs:
{json.dumps(config_files, indent=2)}

Return a JSON array of issues with keys: title, description, file_path, line_number (integer or null), severity (critical/warning/improvement/info), category ("dependencies"), suggestion.
\"\"\"
    return await _call_gemini(prompt)

async def analyze_testing(test_files: List[str], file_tree: List[str], file_contents: Dict[str, str]) -> List[Dict]:
    prompt = f\"\"\"Analyze the testing strategy of the repository.
Look for: test coverage assessment, missing test categories, test quality issues, untested critical paths.
Test files: {test_files}
All files: {file_tree}
Some Contents:
{json.dumps({k:v for k,v in file_contents.items() if k in test_files}, indent=2)[:50000]}

Return a JSON array of issues with keys: title, description, file_path, line_number (integer or null), severity (critical/warning/improvement/info), category ("testing"), suggestion.
\"\"\"
    return await _call_gemini(prompt)

async def analyze_documentation(readme_content: Optional[str], file_contents: Dict[str, str], config_files: Dict[str, str]) -> List[Dict]:
    prompt = f\"\"\"Analyze the documentation of the repository.
Look for: README completeness, missing inline docs, missing API docs, missing env var docs.
README: {readme_content[:5000] if readme_content else 'None'}
Configs: {list(config_files.keys())}

Return a JSON array of issues with keys: title, description, file_path, line_number (integer or null), severity (critical/warning/improvement/info), category ("documentation"), suggestion.
\"\"\"
    return await _call_gemini(prompt)

async def analyze_architecture(file_tree: List[str], file_contents: Dict[str, str]) -> List[Dict]:
    prompt = f\"\"\"Analyze the architecture and structure of the repository.
Look for: folder structure issues, separation of concerns violations, circular dependencies, missing important files, naming convention inconsistencies.
Tree: {file_tree}

Return a JSON array of issues with keys: title, description, file_path, line_number (integer or null), severity (critical/warning/improvement/info), category ("architecture"), suggestion.
\"\"\"
    return await _call_gemini(prompt)

async def run_full_analysis(scan_result: ScanResult) -> List[Dict]:
    tasks = [
        analyze_security(scan_result.file_contents, scan_result.file_tree),
        analyze_code_quality(scan_result.file_contents, scan_result.file_tree),
        analyze_dependencies(scan_result.config_files),
        analyze_testing(scan_result.test_files, scan_result.file_tree, scan_result.file_contents),
        analyze_documentation(scan_result.readme_content, scan_result.file_contents, scan_result.config_files),
        analyze_architecture(scan_result.file_tree, scan_result.file_contents)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_issues = []
    for r in results:
        if isinstance(r, list):
            all_issues.extend(r)
        else:
            print(f"Analysis task failed: {r}")
            
    return all_issues
""",
    "app/services/report_service.py": """from typing import List, Dict, Any
from app.services.scanner_service import ScanResult

def calculate_health_score(issues: List[Dict], scan_result: ScanResult) -> int:
    score = 100
    
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    warning_count = sum(1 for i in issues if i.get("severity") == "warning")
    improvement_count = sum(1 for i in issues if i.get("severity") == "improvement")
    
    score -= min(critical_count * 15, 45)
    score -= min(warning_count * 8, 32)
    score -= min(improvement_count * 3, 15)
    
    if scan_result.has_tests: score += 5
    if scan_result.has_ci: score += 3
    if scan_result.has_docker: score += 2
    if scan_result.has_env_example: score += 2
    if scan_result.readme_content and len(scan_result.readme_content) > 200:
        score += 3
        
    return max(0, min(100, score))

def generate_summary(health_score: int, issues: List[Dict], scan_result: ScanResult) -> str:
    if health_score >= 90:
        base = "The repository is in excellent health."
    elif health_score >= 70:
        base = "The repository is in good health but has some areas for improvement."
    elif health_score >= 50:
        base = "The repository needs attention. There are several issues affecting quality or security."
    else:
        base = "The repository is in poor health with critical issues that need immediate resolution."
        
    criticals = sum(1 for i in issues if i.get("severity") == "critical")
    if criticals > 0:
        base += f" Found {criticals} critical issue(s)."
        
    return base

def compile_report(issues: List[Dict], scan_result: ScanResult) -> Dict[str, Any]:
    health_score = calculate_health_score(issues, scan_result)
    summary = generate_summary(health_score, issues, scan_result)
    
    issues_by_category = {}
    for issue in issues:
        cat = issue.get("category", "other")
        if cat not in issues_by_category:
            issues_by_category[cat] = []
        issues_by_category[cat].append(issue)
        
    return {
        "health_score": health_score,
        "summary": summary,
        "issues_by_category": issues_by_category,
        "repository_stats": {
            "total_files": scan_result.total_files,
            "has_tests": scan_result.has_tests,
            "has_ci": scan_result.has_ci,
            "has_docker": scan_result.has_docker
        }
    }
""",
    "app/routers/__init__.py": "",
    "app/routers/analysis.py": """from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
import os

from app.database import get_db
from app.schemas.analysis import AnalyzeRequest, AnalysisStatusResponse, AnalysisResponse
from app.models.repository import Repository
from app.models.analysis import Analysis
from app.models.issue import Issue
from app.services.github_service import validate_github_url, clone_repo, cleanup_repo
from app.services.scanner_service import scan_repository
from app.services.ai_service import run_full_analysis
from app.services.report_service import compile_report
from app.config import get_settings

router = APIRouter(prefix="/api")

async def run_analysis_pipeline(analysis_id: str, repo_id: str, url: str, owner: str, repo_name: str, db: AsyncSession):
    settings = get_settings()
    repo_path = os.path.join(settings.REPOS_DIR, f"{owner}_{repo_name}_{analysis_id}")
    
    try:
        # Update status scanning
        analysis = await db.get(Analysis, analysis_id)
        if not analysis: return
        analysis.status = "scanning"
        await db.commit()
        
        # Clone
        print(f"Cloning {url} into {repo_path}")
        await clone_repo(url, repo_path)
        
        # Scan
        scan_result = await scan_repository(repo_path, settings)
        
        # Update repo
        repo = await db.get(Repository, repo_id)
        if repo:
            repo.total_files = scan_result.total_files
            repo.languages = scan_result.languages
            await db.commit()
            
        # Update status analyzing
        analysis.status = "analyzing"
        await db.commit()
        
        # Analyze
        issues = await run_full_analysis(scan_result)
        
        # Report
        report = compile_report(issues, scan_result)
        
        # Save issues
        for issue_data in issues:
            new_issue = Issue(
                analysis_id=analysis_id,
                severity=issue_data.get("severity", "info"),
                category=issue_data.get("category", "other"),
                title=issue_data.get("title", "Unknown issue"),
                description=issue_data.get("description"),
                file_path=issue_data.get("file_path"),
                line_number=issue_data.get("line_number"),
                suggestion=issue_data.get("suggestion")
            )
            db.add(new_issue)
            
        analysis.health_score = report["health_score"]
        analysis.summary = report["summary"]
        analysis.status = "completed"
        analysis.completed_at = datetime.now(timezone.utc)
        await db.commit()
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        analysis.status = "failed"
        analysis.error_message = str(e)
        analysis.completed_at = datetime.now(timezone.utc)
        await db.commit()
    finally:
        cleanup_repo(repo_path)

@router.post("/analyze")
async def analyze_repo(req: AnalyzeRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    url_str = str(req.url)
    try:
        owner, repo_name = validate_github_url(url_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    repo = Repository(url=url_str, name=repo_name, owner=owner)
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    
    analysis = Analysis(repository_id=repo.id, status="pending")
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    background_tasks.add_task(run_analysis_pipeline, analysis.id, repo.id, url_str, owner, repo_name, db)
    
    return {"analysis_id": analysis.id, "status": "pending"}

@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    stmt = select(Analysis).options(selectinload(Analysis.repository), selectinload(Analysis.issues)).where(Analysis.id == analysis_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    return analysis

@router.get("/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str, db: AsyncSession = Depends(get_db)):
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    return {
        "id": analysis.id,
        "status": analysis.status,
        "health_score": analysis.health_score
    }
""",
    "app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import create_tables
from app.routers.analysis import router as analysis_router
from app.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    os.makedirs(settings.REPOS_DIR, exist_ok=True)
    await create_tables()
    yield

app = FastAPI(title="RepoDoctor AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)

@app.get("/")
async def root():
    return {"message": "RepoDoctor AI API", "version": "1.0.0"}
"""
}

for rel_path, content in files.items():
    full_path = os.path.join(base_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
print("done")
