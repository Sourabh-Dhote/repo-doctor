import os
from dataclasses import dataclass, field
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
    has_license: bool = False
    has_gitignore: bool = False
    raw_files: List[str] = field(default_factory=list)

async def scan_repository(repo_path: str, settings) -> ScanResult:
    file_tree = []
    file_contents = {}
    languages = {}
    readme_content = None
    config_files = {}
    test_files = []
    raw_files = []
    has_tests = False
    has_ci = False
    has_docker = False
    has_env_example = False
    has_license = False
    has_gitignore = False
    total_files = 0
    
    config_names = {
        'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
        'requirements.txt', 'pom.xml', 'go.mod', 'cargo.toml', 'pyproject.toml',
        'dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
        '.eslintrc.json', '.eslintrc.js', 'tsconfig.json', 'vite.config.ts', 'webpack.config.js'
    }
    ci_dirs = ['.github/workflows', '.gitlab-ci.yml', 'jenkinsfile', '.travis.yml']
    
    stopped_early = False

    for root, dirs, files in os.walk(repo_path):
        if stopped_early:
            break

        # Filter out directories to skip
        dirs[:] = [d for d in dirs if not should_skip_directory(d)]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path).replace("\\", "/")
            raw_files.append(rel_path)

            lower_file = file.lower()
            lower_rel_path = rel_path.lower()

            # Global repository indicators
            if any(ci in lower_rel_path for ci in ci_dirs):
                has_ci = True
            if 'dockerfile' in lower_file or 'docker-compose' in lower_file:
                has_docker = True
            if 'env.example' in lower_rel_path or '.env.example' in lower_rel_path:
                has_env_example = True
            if lower_file in ('license', 'license.md', 'license.txt'):
                has_license = True
            if lower_file == '.gitignore':
                has_gitignore = True
            if 'test' in lower_rel_path or 'spec' in lower_rel_path or lower_file.startswith('test_'):
                has_tests = True
                test_files.append(rel_path)

            if total_files >= settings.MAX_FILES:
                stopped_early = True
                break

            _, ext = os.path.splitext(file)
            if ext and ext not in settings.ALLOWED_EXTENSIONS and not ('dockerfile' in lower_file or lower_file == 'makefile'):
                continue
                
            if is_binary_file(file_path):
                continue
                
            try:
                file_size_kb = os.path.getsize(file_path) / 1024
                if file_size_kb > settings.MAX_FILE_SIZE_KB:
                    continue
            except OSError:
                continue
                
            total_files += 1
            file_tree.append(rel_path)
            
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                    
                lines_count = len(content.splitlines())
                lang = get_language_from_extension(ext)
                if lang != "Unknown":
                    languages[lang] = languages.get(lang, 0) + lines_count
                    
                if lower_file == 'readme.md':
                    readme_content = content
                    
                if lower_file in config_names:
                    config_files[lower_file] = truncate_content(content)
                    
                file_contents[rel_path] = truncate_content(content)
            except Exception as e:
                print(f"[RepoDoctor] Error reading {file_path}: {e}")
                
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
        has_env_example=has_env_example,
        has_license=has_license,
        has_gitignore=has_gitignore,
        raw_files=raw_files
    )
