from typing import List, Dict, Any
from app.services.scanner_service import ScanResult

def calculate_health_score(issues: List[Dict], scan_result: ScanResult) -> int:
    score = 100
    
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    warning_count = sum(1 for i in issues if i.get("severity") == "warning")
    improvement_count = sum(1 for i in issues if i.get("severity") == "improvement")
    
    # Deductions based on issues
    score -= min(critical_count * 15, 55)
    score -= min(warning_count * 7, 35)
    score -= min(improvement_count * 2, 15)
    
    # Structural health checks
    if not scan_result.has_tests and scan_result.total_files > 3:
        score -= 8
    if not scan_result.has_ci and scan_result.total_files > 4:
        score -= 5
    if not scan_result.readme_content or len(scan_result.readme_content.strip()) < 100:
        score -= 5
    if not getattr(scan_result, 'has_license', False):
        score -= 3
        
    return max(15, min(100, score))

def generate_summary(health_score: int, issues: List[Dict], scan_result: ScanResult) -> str:
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    warning_count = sum(1 for i in issues if i.get("severity") == "warning")
    improvement_count = sum(1 for i in issues if i.get("severity") == "improvement")
    
    if health_score >= 88:
        rating = "Excellent"
        opening = "The codebase demonstrates strong architecture, consistent practices, and solid foundation."
    elif health_score >= 72:
        rating = "Good"
        opening = "The repository is well-structured and functional, though several key optimizations and safety measures should be addressed."
    elif health_score >= 50:
        rating = "Needs Attention"
        opening = "The repository has noticeable technical debt and security/architectural risks requiring prompt remediation."
    else:
        rating = "Critical Risk"
        opening = "The repository contains critical vulnerabilities or severe architectural deficiencies that require immediate remediation."
        
    lines = [
        f"Health Rating: {rating} ({health_score}/100)",
        f"{opening}\n",
        f"• Total Files Inspected: {scan_result.total_files}",
        f"• Identified Findings: {len(issues)} total ({critical_count} critical, {warning_count} warnings, {improvement_count} improvements)",
    ]

    # Security highlights
    sec_issues = [i for i in issues if i.get("category") == "security"]
    if sec_issues:
        lines.append(f"• Security: {len(sec_issues)} security finding(s) detected. Prioritize reviewing exposed credentials and injection risks.")
    else:
        lines.append("• Security: No immediate credential leaks or high-risk injection vulnerabilities detected.")

    # Testing & CI highlights
    if scan_result.has_tests:
        lines.append(f"• Testing: Test files detected ({len(scan_result.test_files)} test suite files).")
    else:
        lines.append("• Testing: No automated unit or integration test suite detected.")

    if scan_result.has_ci:
        lines.append("• CI/CD: Automated continuous integration pipeline is configured.")
    else:
        lines.append("• CI/CD: Missing automated workflow pipeline (e.g. GitHub Actions).")

    # Top recommendations
    recommendations = []
    if critical_count > 0:
        recommendations.append("Resolve all critical security and credential warnings.")
    if not scan_result.has_tests and scan_result.total_files > 3:
        recommendations.append("Set up an automated test framework (e.g. pytest / Vitest) to guard against regressions.")
    if not scan_result.has_ci:
        recommendations.append("Configure a GitHub Actions workflow for automated testing and linting.")
    if not getattr(scan_result, 'has_license', False):
        recommendations.append("Add an open source LICENSE file to define repository terms of use.")

    if recommendations:
        lines.append("\nRecommended Next Steps:")
        for idx, rec in enumerate(recommendations[:3], 1):
            lines.append(f"{idx}. {rec}")

    return "\n".join(lines)

def compile_report(issues: List[Dict], scan_result: ScanResult) -> Dict[str, Any]:
    health_score = calculate_health_score(issues, scan_result)
    summary = generate_summary(health_score, issues, scan_result)
    
    issues_by_category = {}
    for issue in issues:
        cat = issue.get("category", "code_quality")
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
            "has_docker": scan_result.has_docker,
            "has_license": getattr(scan_result, 'has_license', False),
            "has_gitignore": getattr(scan_result, 'has_gitignore', False),
        }
    }
