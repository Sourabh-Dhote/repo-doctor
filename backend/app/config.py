from pydantic_settings import BaseSettings, SettingsConfigDict
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
