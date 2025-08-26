"""
Configuration module for MOSDAC AI Help Bot
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConfig(BaseSettings):
    """Database configuration settings"""
    
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="password", env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    class Config:
        env_file = ".env"

class OpenAIConfig(BaseSettings):
    """OpenAI configuration settings"""
    
    api_key: str = Field(..., env="OPENAI_API_KEY")
    model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    class Config:
        env_file = ".env"

class MOSDACConfig(BaseSettings):
    """MOSDAC portal configuration settings"""
    
    base_url: str = Field(default="https://www.mosdac.gov.in", env="MOSDAC_BASE_URL")
    api_key: Optional[str] = Field(default=None, env="MOSDAC_API_KEY")
    scraping_delay: float = Field(default=1.0, env="SCRAPING_DELAY")
    max_concurrent_requests: int = Field(default=5, env="MAX_CONCURRENT_REQUESTS")
    user_agent: str = Field(default="MOSDAC-AI-Bot/1.0", env="USER_AGENT")
    
    class Config:
        env_file = ".env"

class ModelConfig(BaseSettings):
    """ML model configuration settings"""
    
    cache_dir: Path = Field(default=Path("./models"), env="MODEL_CACHE_DIR")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    spacy_model: str = Field(default="en_core_web_sm", env="SPACY_MODEL")
    max_text_length: int = Field(default=512, env="MAX_TEXT_LENGTH")
    
    class Config:
        env_file = ".env"

class APIConfig(BaseSettings):
    """API configuration settings"""
    
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"

class WebConfig(BaseSettings):
    """Web interface configuration settings"""
    
    host: str = Field(default="localhost", env="WEB_HOST")
    port: int = Field(default=8501, env="WEB_PORT")
    debug: bool = Field(default=False, env="WEB_DEBUG")
    
    class Config:
        env_file = ".env"

class GeospatialConfig(BaseSettings):
    """Geospatial configuration settings"""
    
    default_crs: str = Field(default="EPSG:4326", env="DEFAULT_CRS")
    supported_crs: list = Field(
        default=["EPSG:4326", "EPSG:3857", "EPSG:32643"],
        env="SUPPORTED_CRS"
    )
    max_buffer_distance: float = Field(default=10000.0, env="MAX_BUFFER_DISTANCE")
    
    class Config:
        env_file = ".env"

class Config(BaseSettings):
    """Main configuration class"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    database: DatabaseConfig = DatabaseConfig()
    
    # OpenAI
    openai: OpenAIConfig = OpenAIConfig()
    
    # MOSDAC Portal
    mosdac: MOSDACConfig = MOSDACConfig()
    
    # ML Models
    models: ModelConfig = ModelConfig()
    
    # API
    api: APIConfig = APIConfig()
    
    # Web Interface
    web: WebConfig = WebConfig()
    
    # Geospatial
    geospatial: GeospatialConfig = GeospatialConfig()
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    models_dir: Path = base_dir / "models"
    logs_dir: Path = base_dir / "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.data_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance"""
    return config

def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return config.database

def get_openai_config() -> OpenAIConfig:
    """Get OpenAI configuration"""
    return config.openai

def get_mosdac_config() -> MOSDACConfig:
    """Get MOSDAC configuration"""
    return config.mosdac

def get_model_config() -> ModelConfig:
    """Get model configuration"""
    return config.models

def get_api_config() -> APIConfig:
    """Get API configuration"""
    return config.api

def get_web_config() -> WebConfig:
    """Get web configuration"""
    return config.web

def get_geospatial_config() -> GeospatialConfig:
    """Get geospatial configuration"""
    return config.geospatial
