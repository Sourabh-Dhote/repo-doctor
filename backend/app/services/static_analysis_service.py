import re
from typing import List, Dict, Any, Optional
from app.services.scanner_service import ScanResult

SECRET_PATTERNS = [
    {
        "name": "AWS Access Key",
        "pattern": re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}"),
        "severity": "critical",
        "title": "Hardcoded AWS Access Key",
        "suggestion": "Remove hardcoded AWS credentials immediately and use environment variables, AWS IAM roles, or AWS Secrets Manager."
    },
    {
        "name": "GitHub Personal Access Token",
        "pattern": re.compile(r"(?:ghp_[A-Za-z0-9_]{36}|github_pat_[A-Za-z0-9_]{82})"),
        "severity": "critical",
        "title": "Hardcoded GitHub Access Token",
        "suggestion": "Revoke the exposed GitHub token immediately and load tokens securely via environment variables or GitHub Actions Secrets."
    },
    {
        "name": "OpenAI API Key",
        "pattern": re.compile(r"sk-[a-zA-Z0-9]{32,}|sk-proj-[a-zA-Z0-9_-]{40,}"),
        "severity": "critical",
        "title": "Hardcoded OpenAI API Key",
        "suggestion": "Rotate the exposed OpenAI key immediately. Use OPENAI_API_KEY environment variable."
    },
    {
        "name": "Google Gemini / API Key",
        "pattern": re.compile(r"AIzaSy[a-zA-Z0-9_\-]{33}"),
        "severity": "critical",
        "title": "Hardcoded Google API Key",
        "suggestion": "Rotate this Google API key immediately in the Google Cloud / AI Studio console and load via environment variables."
    },
    {
        "name": "Private Key",
        "pattern": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        "severity": "critical",
        "title": "Exposed Private Cryptographic Key",
        "suggestion": "Never commit private keys to version control. Store keys in a secure secret store or encrypted vault."
    },
    {
        "name": "Generic Secret or Password Assignment",
        "pattern": re.compile(r'''(?i)(?:api_key|apikey|secret_key|client_secret|auth_token|db_password)\s*[:=]\s*['"]([a-zA-Z0-9!@#$%^&*()_\-+=]{16,})['"]'''),
        "severity": "critical",
        "title": "Hardcoded Secret / API Token",
        "suggestion": "Store secrets in an external environment variable (.env) or secrets manager, and ensure .env is included in .gitignore."
    }
]

DANGEROUS_CODE_PATTERNS = [
    {
        "pattern": re.compile(r"\b(?:eval|exec)\s*\("),
        "exts": [".py", ".js", ".ts"],
        "severity": "warning",
        "category": "security",
        "title": "Dangerous Dynamic Code Execution (eval/exec)",
        "desc": "Dynamic code execution using eval() or exec() can allow arbitrary code execution if unsanitized user input reaches it.",
        "suggestion": "Avoid dynamic code execution. Refactor to use safe dispatch tables, JSON parsers, or abstract syntax trees."
    },
    {
        "pattern": re.compile(r"(?i)\.execute\s*\(\s*(?:f['\"].*?(?:SELECT|INSERT|UPDATE|DELETE)|['\"].*?(?:SELECT|INSERT|UPDATE|DELETE).*?%\s*\(|['\"].*?(?:SELECT|INSERT|UPDATE|DELETE).*?\+\s*\w+)"),
        "exts": [".py", ".js", ".ts"],
        "severity": "critical",
        "category": "security",
        "title": "Potential SQL Injection Vulnerability",
        "desc": "SQL query appears to be constructed using string interpolation or concatenation rather than parameterized queries.",
        "suggestion": "Use parameterized queries or ORM query builders to ensure user inputs are automatically escaped."
    },
    {
        "pattern": re.compile(r"\bsubprocess\.(?:Popen|run|call|check_output)\s*\([^)]*shell\s*=\s*True"),
        "exts": [".py"],
        "severity": "warning",
        "category": "security",
        "title": "Command Execution with shell=True",
        "desc": "Invoking subprocesses with shell=True enables shell expansion, making the command susceptible to command injection.",
        "suggestion": "Pass arguments as a list without shell=True, or sanitize arguments with shlex.quote()."
    },
    {
        "pattern": re.compile(r"\bpickle\.(?:loads|load)\s*\("),
        "exts": [".py"],
        "severity": "warning",
        "category": "security",
        "title": "Insecure Deserialization via pickle",
        "desc": "Python's pickle module is not secure against erroneous or maliciously constructed data.",
        "suggestion": "Use safer serialization formats such as JSON, Protocol Buffers, or MessagePack."
    },
    {
        "pattern": re.compile(r"dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:"),
        "exts": [".jsx", ".tsx", ".js", ".ts"],
        "severity": "warning",
        "category": "security",
        "title": "Unsanitized HTML Rendering (dangerouslySetInnerHTML)",
        "desc": "Directly injecting raw HTML into the DOM can lead to Cross-Site Scripting (XSS) attacks.",
        "suggestion": "Sanitize HTML using DOMPurify or sanitize-html before rendering, or prefer safe React text nodes."
    },
    {
        "pattern": re.compile(r"(?:verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]0['\"])"),
        "exts": [".py", ".js", ".ts"],
        "severity": "critical",
        "category": "security",
        "title": "Disabled SSL/TLS Certificate Verification",
        "desc": "Disabling TLS certificate verification leaves network requests vulnerable to Man-in-the-Middle (MitM) attacks.",
        "suggestion": "Ensure TLS verification is enabled and configure valid CA bundles if custom certificates are required."
    }
]

def run_static_analysis(scan_result: ScanResult) -> List[Dict[str, Any]]:
    """Execute high-precision static rules and security heuristics on repository files."""
    issues: List[Dict[str, Any]] = []

    # 1. SECURITY CHECKS
    # Check for committed .env files in file tree
    for file_path in scan_result.raw_files:
        lower_fp = file_path.lower()
        base_name = lower_fp.split("/")[-1]
        if base_name in ('.env', '.env.local', '.env.production', '.env.staging') and 'example' not in base_name:
            issues.append({
                "severity": "critical",
                "category": "security",
                "title": "Sensitive Environment File Committed (.env)",
                "description": f"The environment file '{file_path}' was committed to git. This may expose production credentials, database URIs, or private keys.",
                "file_path": file_path,
                "line_number": 1,
                "suggestion": "Add this file to .gitignore, remove it from git history using git filter-repo or BFG, and rotate any secrets it contained."
            })
        if base_name.endswith(('.pem', '.key', '.pfx', '.p12')) and 'test' not in lower_fp:
            issues.append({
                "severity": "critical",
                "category": "security",
                "title": "Private Key or Certificate File Committed",
                "description": f"File '{file_path}' appears to be a cryptographic certificate or private key committed directly to the repository.",
                "file_path": file_path,
                "line_number": 1,
                "suggestion": "Remove certificate files from version control and inject them at deploy time via environment secrets."
            })

    # Scan file contents for secrets & dangerous patterns
    for rel_path, content in scan_result.file_contents.items():
        lower_rel = rel_path.lower()
        is_test = 'test' in lower_rel or 'spec' in lower_rel or 'mock' in lower_rel
        lines = content.splitlines()

        # Secret patterns check
        for pattern_info in SECRET_PATTERNS:
            for line_idx, line in enumerate(lines, 1):
                # Skip comments or mock tokens in test files
                if is_test and any(mock in line.lower() for mock in ('dummy', 'fake', 'test', 'example', 'sample')):
                    continue
                match = pattern_info["pattern"].search(line)
                if match:
                    # Ignore obvious placeholders
                    matched_str = match.group(0).lower()
                    if any(ph in matched_str for ph in ('your_', 'todo', 'example', 'placeholder', 'dummy', 'xxxx')):
                        continue
                    issues.append({
                        "severity": pattern_info["severity"],
                        "category": "security",
                        "title": pattern_info["title"],
                        "description": f"Detected potential secret or credential in `{rel_path}` at line {line_idx}.",
                        "file_path": rel_path,
                        "line_number": line_idx,
                        "suggestion": pattern_info["suggestion"]
                    })
                    break  # report one per pattern per file

        # Insecure code patterns
        _, ext = rel_path.rsplit(".", 1) if "." in rel_path else ("", "")
        ext = f".{ext.lower()}"
        for rule in DANGEROUS_CODE_PATTERNS:
            if ext in rule["exts"] and not is_test:
                for line_idx, line in enumerate(lines, 1):
                    if rule["pattern"].search(line):
                        issues.append({
                            "severity": rule["severity"],
                            "category": rule["category"],
                            "title": rule["title"],
                            "description": f"{rule['desc']} (Found in `{rel_path}` at line {line_idx})",
                            "file_path": rel_path,
                            "line_number": line_idx,
                            "suggestion": rule["suggestion"]
                        })
                        break

        # 2. CODE QUALITY CHECKS
        # Silent exception swallowing
        if ext == ".py":
            except_pass_re = re.compile(r"except(?:\s+\w+)?\s*:\s*(?:pass|\.\.\.)")
            for line_idx, line in enumerate(lines, 1):
                if except_pass_re.search(line):
                    issues.append({
                        "severity": "warning",
                        "category": "code_quality",
                        "title": "Silently Swallowed Exception (except: pass)",
                        "description": f"Empty exception handler detected in `{rel_path}` at line {line_idx}. Swallowing exceptions hides runtime errors and makes debugging difficult.",
                        "file_path": rel_path,
                        "line_number": line_idx,
                        "suggestion": "Log the error, handle specific exception types, or raise a meaningful custom exception."
                    })
                    break
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            empty_catch_re = re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}")
            debugger_re = re.compile(r"\bdebugger\s*;")
            for line_idx, line in enumerate(lines, 1):
                if empty_catch_re.search(line):
                    issues.append({
                        "severity": "warning",
                        "category": "code_quality",
                        "title": "Empty Catch Block",
                        "description": f"An empty catch block in `{rel_path}` at line {line_idx} silently swallows errors.",
                        "file_path": rel_path,
                        "line_number": line_idx,
                        "suggestion": "Handle or log the caught error to prevent hidden runtime failures."
                    })
                    break
                if debugger_re.search(line) and not is_test:
                    issues.append({
                        "severity": "warning",
                        "category": "code_quality",
                        "title": "Leftover Debugger Statement",
                        "description": f"Found a `debugger;` statement in `{rel_path}` at line {line_idx}.",
                        "file_path": rel_path,
                        "line_number": line_idx,
                        "suggestion": "Remove debugger statements before deploying code to production."
                    })
                    break

        # Very large files
        if len(lines) > 700 and not is_test:
            issues.append({
                "severity": "improvement",
                "category": "code_quality",
                "title": f"Large File Exceeding Recommended Length ({len(lines)} lines)",
                "description": f"`{rel_path}` is {len(lines)} lines long, which indicates high complexity and multiple responsibilities.",
                "file_path": rel_path,
                "line_number": 1,
                "suggestion": "Consider refactoring this file into smaller, focused modules or modular utility functions."
            })

    # 3. DEPENDENCY CHECKS
    # Check for lockfiles
    has_pkg = 'package.json' in scan_result.config_files
    has_lock = any(k in scan_result.config_files or k in scan_result.raw_files for k in ('package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'))
    if has_pkg and not has_lock:
        issues.append({
            "severity": "warning",
            "category": "dependencies",
            "title": "Missing Package Lockfile",
            "description": "Repository contains package.json but no lockfile (package-lock.json, yarn.lock, or pnpm-lock.yaml) was found.",
            "file_path": "package.json",
            "line_number": 1,
            "suggestion": "Commit package-lock.json or your package manager's lockfile to guarantee reproducible builds across environments."
        })

    # Check unpinned requirements.txt
    if 'requirements.txt' in scan_result.config_files:
        req_lines = scan_result.config_files['requirements.txt'].splitlines()
        unpinned = [l.strip() for l in req_lines if l.strip() and not l.strip().startswith('#') and '==' not in l and '<=' not in l and '~=' not in l]
        if len(unpinned) >= 3:
            issues.append({
                "severity": "improvement",
                "category": "dependencies",
                "title": f"Unpinned Python Dependencies ({len(unpinned)} packages)",
                "description": f"Found {len(unpinned)} unpinned dependencies in requirements.txt (e.g., {', '.join(unpinned[:3])}).",
                "file_path": "requirements.txt",
                "line_number": 1,
                "suggestion": "Pin dependencies with exact versions (e.g. package==1.2.3) or use pip-tools / poetry to prevent unexpected breaking changes."
            })

    # 4. TESTING CHECKS
    if not scan_result.has_tests and scan_result.total_files > 3:
        issues.append({
            "severity": "warning",
            "category": "testing",
            "title": "No Automated Test Suite Detected",
            "description": f"No unit or integration tests were detected across {scan_result.total_files} files in this repository.",
            "file_path": None,
            "line_number": None,
            "suggestion": "Add a testing framework (e.g., pytest for Python, Vitest / Jest for JavaScript) to ensure code reliability and prevent regressions."
        })

    # 5. DOCUMENTATION CHECKS
    if not scan_result.readme_content:
        issues.append({
            "severity": "warning",
            "category": "documentation",
            "title": "Missing README Documentation",
            "description": "The repository does not contain a README.md file in the root directory.",
            "file_path": "README.md",
            "line_number": None,
            "suggestion": "Create a README.md explaining the project purpose, architecture, prerequisites, and setup instructions."
        })
    elif len(scan_result.readme_content.strip()) < 150:
        issues.append({
            "severity": "improvement",
            "category": "documentation",
            "title": "Incomplete or Sparse README",
            "description": "The README.md file is very short and lacks comprehensive guidance for users and contributors.",
            "file_path": "README.md",
            "line_number": 1,
            "suggestion": "Expand README.md with detailed features, installation steps, configuration guides, and usage examples."
        })

    if not scan_result.has_license:
        issues.append({
            "severity": "improvement",
            "category": "documentation",
            "title": "Missing Open Source License",
            "description": "No LICENSE file was detected. Without an explicit open-source license, public repositories default to all rights reserved.",
            "file_path": "LICENSE",
            "line_number": None,
            "suggestion": "Add an open-source license file (such as MIT, Apache 2.0, or GPL) to clarify terms of use and distribution."
        })

    # Check for missing .env.example if env vars are referenced
    env_referenced = False
    for content in scan_result.file_contents.values():
        if "process.env" in content or "os.environ" in content or "getenv(" in content:
            env_referenced = True
            break
    if env_referenced and not scan_result.has_env_example:
        issues.append({
            "severity": "improvement",
            "category": "documentation",
            "title": "Missing .env.example Template",
            "description": "The codebase references environment variables, but no .env.example file was found.",
            "file_path": ".env.example",
            "line_number": None,
            "suggestion": "Create a .env.example file demonstrating the required environment variables with dummy values."
        })

    # 6. ARCHITECTURE CHECKS
    if not scan_result.has_ci and scan_result.total_files > 4:
        issues.append({
            "severity": "warning",
            "category": "architecture",
            "title": "Missing CI/CD Workflow Automation",
            "description": "No continuous integration configuration was found (e.g., .github/workflows, .gitlab-ci.yml).",
            "file_path": ".github/workflows/ci.yml",
            "line_number": None,
            "suggestion": "Set up GitHub Actions to automatically run linters, tests, and security scans on pull requests and commits."
        })

    if not scan_result.has_docker and scan_result.total_files > 8:
        issues.append({
            "severity": "info",
            "category": "architecture",
            "title": "Missing Containerization (Docker)",
            "description": "No Dockerfile or docker-compose configuration was found in the repository.",
            "file_path": "Dockerfile",
            "line_number": None,
            "suggestion": "Add a Dockerfile and docker-compose.yml to enable consistent local development and containerized production deployment."
        })

    if not scan_result.has_gitignore:
        issues.append({
            "severity": "warning",
            "category": "architecture",
            "title": "Missing .gitignore File",
            "description": "The repository is missing a .gitignore file, risking accidental commits of dependencies, cache files, and credentials.",
            "file_path": ".gitignore",
            "line_number": None,
            "suggestion": "Add a comprehensive .gitignore tailored to your project languages and frameworks."
        })

    return issues
