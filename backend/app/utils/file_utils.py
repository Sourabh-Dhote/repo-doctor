import os

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
