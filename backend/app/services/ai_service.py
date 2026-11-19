import json
import os
import asyncio
from typing import List, Dict, Any, Optional
from google import genai
from app.config import get_settings
from app.services.scanner_service import ScanResult
from app.services.static_analysis_service import run_static_analysis

_client = None

def _get_api_key() -> str:
    settings = get_settings()
    return (settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()

def _get_client():
    global _client
    api_key = _get_api_key()
    if not api_key:
        return None
    if _client is None:
        try:
            _client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"[RepoDoctor] Failed to initialize Gemini Client: {e}")
            return None
    return _client

def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def _parse_response(text: str) -> List[Dict]:
    try:
        cleaned = _clean_json_text(text)
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "issues" in parsed and isinstance(parsed["issues"], list):
            return parsed["issues"]
        return []
    except Exception as e:
        print(f"[RepoDoctor] Failed to parse Gemini JSON: {e}\nRaw preview: {text[:200]}")
        return []

async def _call_gemini(prompt: str) -> List[Dict]:
    client = _get_client()
    if not client:
        return []
    
    # Try models in order of capability / speed
    models = ['gemini-2.0-flash', 'gemini-1.5-flash']
    for model_name in models:
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(response_mime_type='application/json')
            )
            parsed = _parse_response(response.text)
            if parsed:
                return parsed
        except Exception as e:
            print(f"[RepoDoctor] Gemini ({model_name}) error: {e}")
            continue
    return []

async def analyze_security(file_contents: Dict[str, str], file_tree: List[str]) -> List[Dict]:
    if not file_contents:
        return []
    prompt = f"""You are a senior security engineer. Analyze the following code snippets for critical vulnerabilities.
Focus on: injection (SQL, command, LDAP), hardcoded credentials, broken authentication, insecure deserialization, SSRF, XSS.
Files: {list(file_contents.keys())[:30]}
Code snippets:
{json.dumps(file_contents, indent=2)[:35000]}

Return ONLY a JSON array of issue objects with keys:
- title (short string)
- description (clear explanation)
- file_path (relative file path or null)
- line_number (integer or null)
- severity ("critical", "warning", "improvement", or "info")
- category ("security")
- suggestion (actionable code or architecture fix)
"""
    return await _call_gemini(prompt)

async def analyze_code_quality(file_contents: Dict[str, str], file_tree: List[str]) -> List[Dict]:
    if not file_contents:
        return []
    prompt = f"""You are a software architect. Analyze the code for quality, maintainability, and architectural smells.
Focus on: anti-patterns, complex coupled code, missing error handling, resource leaks, race conditions.
Files: {list(file_contents.keys())[:30]}
Code snippets:
{json.dumps(file_contents, indent=2)[:35000]}

Return ONLY a JSON array of issue objects with keys:
- title (short string)
- description (clear explanation)
- file_path (relative file path or null)
- line_number (integer or null)
- severity ("critical", "warning", "improvement", or "info")
- category ("code_quality")
- suggestion (actionable fix)
"""
    return await _call_gemini(prompt)

async def analyze_dependencies(config_files: Dict[str, str]) -> List[Dict]:
    if not config_files:
        return []
    prompt = f"""Analyze the following package/dependency configuration files.
Look for: outdated versions, known CVEs, unpinned packages, redundant libraries, insecure registries.
Configs:
{json.dumps(config_files, indent=2)[:20000]}

Return ONLY a JSON array of issue objects with keys:
- title, description, file_path, line_number, severity, category ("dependencies"), suggestion.
"""
    return await _call_gemini(prompt)

def _merge_issues(static_issues: List[Dict], ai_issues: List[Dict]) -> List[Dict]:
    """Merge static analysis issues with AI issues, avoiding duplicate titles on the same file."""
    seen_keys = set()
    merged: List[Dict] = []

    for issue in static_issues + ai_issues:
        if not isinstance(issue, dict):
            continue
        title = str(issue.get("title", "")).strip().lower()
        file_path = str(issue.get("file_path", "")).strip().lower()
        key = (title[:30], file_path)
        if key not in seen_keys:
            seen_keys.add(key)
            # Normalize severity and category
            sev = str(issue.get("severity", "info")).lower()
            if sev not in ("critical", "warning", "improvement", "info"):
                sev = "info"
            cat = str(issue.get("category", "code_quality")).lower()
            if cat not in ("security", "code_quality", "dependencies", "testing", "documentation", "architecture"):
                cat = "code_quality"

            merged.append({
                "title": issue.get("title") or "Unknown issue",
                "description": issue.get("description") or "",
                "file_path": issue.get("file_path"),
                "line_number": issue.get("line_number"),
                "severity": sev,
                "category": cat,
                "suggestion": issue.get("suggestion") or ""
            })

    return merged

async def run_full_analysis(scan_result: ScanResult) -> List[Dict]:
    """Run both robust static analysis and AI passes, merging the results."""
    # 1. Run static analysis immediately
    print(f"[RepoDoctor] Executing rule-based static analysis engine...")
    static_issues = run_static_analysis(scan_result)
    print(f"[RepoDoctor] Static analysis found {len(static_issues)} issues")

    # 2. Check if Gemini AI is configured
    client = _get_client()
    if not client:
        print("[RepoDoctor] GEMINI_API_KEY not set. Using comprehensive static analysis findings.")
        return static_issues

    # 3. Run AI analysis passes concurrently
    print(f"[RepoDoctor] Calling Gemini AI for semantic passes...")
    ai_tasks = [
        analyze_security(scan_result.file_contents, scan_result.file_tree),
        analyze_code_quality(scan_result.file_contents, scan_result.file_tree),
        analyze_dependencies(scan_result.config_files),
    ]
    
    results = await asyncio.gather(*ai_tasks, return_exceptions=True)
    ai_issues = []
    for r in results:
        if isinstance(r, list):
            ai_issues.extend(r)
        elif isinstance(r, Exception):
            print(f"[RepoDoctor] AI pass error: {r}")

    print(f"[RepoDoctor] Gemini AI returned {len(ai_issues)} semantic issues")
    return _merge_issues(static_issues, ai_issues)
