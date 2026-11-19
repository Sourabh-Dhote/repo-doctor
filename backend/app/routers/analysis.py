from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import os
import asyncio
from typing import List

from app.database import get_db, async_session
from app.schemas.analysis import (
    AnalyzeRequest,
    AnalysisStatusResponse,
    AnalysisResponse,
    RecentAnalysisItem,
)
from app.models.repository import Repository
from app.models.analysis import Analysis
from app.models.issue import Issue
from app.services.github_service import validate_github_url, clone_repo, cleanup_repo
from app.services.scanner_service import scan_repository
from app.services.ai_service import run_full_analysis
from app.services.report_service import compile_report
from app.config import get_settings

router = APIRouter(prefix="/api")


async def run_analysis_pipeline(analysis_id: str, repo_id: str, url: str, owner: str, repo_name: str):
    """Background task that runs the full cloning, scanning, and analysis pipeline."""
    settings = get_settings()
    repo_path = os.path.join(settings.REPOS_DIR, f"{owner}_{repo_name}_{analysis_id[:8]}")

    async with async_session() as db:
        try:
            # 1. Update status → scanning
            analysis = await db.get(Analysis, analysis_id)
            if not analysis:
                print(f"[RepoDoctor] Analysis {analysis_id} not found in DB")
                return
            analysis.status = "scanning"
            await db.commit()

            # 2. Clone repository
            print(f"[RepoDoctor] Cloning {url} into {repo_path}")
            await clone_repo(url, repo_path)
            print(f"[RepoDoctor] Clone completed successfully")

            # 3. Scan repository
            print(f"[RepoDoctor] Scanning repository files...")
            scan_result = await scan_repository(repo_path, settings)
            print(f"[RepoDoctor] Scan finished: {scan_result.total_files} files, {len(scan_result.languages)} languages")

            # 4. Update repository record with scan info
            repo = await db.get(Repository, repo_id)
            if repo:
                repo.total_files = scan_result.total_files
                repo.languages = scan_result.languages
                await db.commit()

            # 5. Update status → analyzing
            analysis.status = "analyzing"
            await db.commit()

            # 6. Run static analysis + AI analysis
            print(f"[RepoDoctor] Running comprehensive analysis passes...")
            issues = await run_full_analysis(scan_result)
            print(f"[RepoDoctor] Found {len(issues)} total findings across all categories")

            # 7. Compile report and calculate health score
            report = compile_report(issues, scan_result)

            # 8. Save issues to database
            for issue_data in issues:
                new_issue = Issue(
                    analysis_id=analysis_id,
                    severity=issue_data.get("severity", "info"),
                    category=issue_data.get("category", "code_quality"),
                    title=issue_data.get("title", "Unknown issue"),
                    description=issue_data.get("description"),
                    file_path=issue_data.get("file_path"),
                    line_number=issue_data.get("line_number"),
                    suggestion=issue_data.get("suggestion"),
                )
                db.add(new_issue)

            # 9. Update analysis with final results
            analysis.health_score = report["health_score"]
            analysis.summary = report["summary"]
            analysis.status = "completed"
            analysis.completed_at = datetime.now(timezone.utc)
            await db.commit()
            print(f"[RepoDoctor] [OK] Analysis complete! Health Score: {report['health_score']}/100")

        except Exception as e:
            error_str = str(e)
            if "not found" in error_str.lower() or "repository not found" in error_str.lower():
                user_friendly_error = "Repository not found or is private. Please ensure the URL is correct and the repository is public."
            elif "terminal prompts disabled" in error_str.lower():
                user_friendly_error = "Repository is private or authentication is required. RepoDoctor currently supports public repositories."
            else:
                user_friendly_error = f"Analysis failed: {error_str}"

            print(f"[RepoDoctor] [ERROR] Analysis failed for {url}: {user_friendly_error}")
            try:
                analysis = await db.get(Analysis, analysis_id)
                if analysis:
                    analysis.status = "failed"
                    analysis.error_message = user_friendly_error
                    analysis.completed_at = datetime.now(timezone.utc)
                    await db.commit()
            except Exception as db_err:
                print(f"[RepoDoctor] Failed to record error status in DB: {db_err}")
        finally:
            cleanup_repo(repo_path)


@router.post("/analyze")
async def analyze_repo(
    req: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a new repository analysis."""
    url_str = req.url.strip().rstrip("/")
    try:
        owner, repo_name = validate_github_url(url_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create repository record
    repo = Repository(url=url_str, name=repo_name, owner=owner)
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    # Create analysis record
    analysis = Analysis(repository_id=repo.id, status="pending")
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # Launch background analysis
    background_tasks.add_task(
        run_analysis_pipeline, analysis.id, repo.id, url_str, owner, repo_name
    )

    return {"analysis_id": analysis.id, "status": "pending"}


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Get full analysis results including all issues and repository metadata."""
    stmt = (
        select(Analysis)
        .options(selectinload(Analysis.repository), selectinload(Analysis.issues))
        .where(Analysis.id == analysis_id)
    )
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis


@router.get("/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Lightweight endpoint for polling analysis progress."""
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "id": analysis.id,
        "status": analysis.status,
        "health_score": analysis.health_score,
        "error_message": analysis.error_message,
    }


@router.get("/analyses", response_model=List[RecentAnalysisItem])
async def list_recent_analyses(db: AsyncSession = Depends(get_db)):
    """List recent analyses for history and dashboard views."""
    stmt = (
        select(Analysis)
        .options(selectinload(Analysis.repository))
        .order_by(Analysis.started_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    analyses = result.scalars().all()

    items = []
    for a in analyses:
        items.append(
            RecentAnalysisItem(
                id=a.id,
                status=a.status,
                health_score=a.health_score,
                started_at=a.started_at,
                completed_at=a.completed_at,
                repo_name=a.repository.name if a.repository else "Unknown",
                repo_owner=a.repository.owner if a.repository else "Unknown",
                repo_url=a.repository.url if a.repository else "",
            )
        )
    return items
