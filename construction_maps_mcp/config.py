"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Yandex Maps API (required)
    yandex_maps_api_key: str = Field(
        ...,
        description="Yandex Maps API key for geocoding and maps",
    )

    # Cache settings
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".construction_maps_mcp",
        description="Directory for SQLite cache storage",
    )
    cache_max_size_mb: int = Field(
        default=500,
        ge=10,
        le=5000,
        description="Maximum cache size in megabytes",
    )

    # Rate limiting
    yandex_rate_limit_rpm: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Yandex Maps API rate limit (requests per minute)",
    )
    rosreestr_rate_limit_rpm: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Rosreestr API rate limit (requests per minute)",
    )

    # Cache TTL (in days)
    cache_ttl_cadastre_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="TTL for cadastral data cache (days)",
    )
    cache_ttl_geocode_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="TTL for geocoding cache (days)",
    )
    cache_ttl_infrastructure_days: int = Field(
        default=1,
        ge=1,
        le=30,
        description="TTL for infrastructure search cache (days)",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or console)",
    )

    # MCP server info
    mcp_server_name: str = Field(
        default="construction-maps-mcp",
        description="MCP server name",
    )
    mcp_server_version: str = Field(
        default="1.0.0",
        description="MCP server version",
    )

    @field_validator("yandex_maps_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate Yandex Maps API key is set."""
        if not v or v == "your_api_key_here":
            raise ValueError(
                "YANDEX_MAPS_API_KEY must be set. "
                "Get your key at https://developer.tech.yandex.ru/"
            )
        return v

    @field_validator("cache_dir")
    @classmethod
    def create_cache_dir(cls, v: Path) -> Path:
        """Create cache directory if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = {"json", "console"}
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(f"Invalid log format: {v}. Must be one of {valid_formats}")
        return v_lower

    # Computed properties
    @property
    def cache_db_path(self) -> Path:
        """Get full path to SQLite cache database."""
        return self.cache_dir / "cache.db"

    @property
    def cache_ttl_cadastre_seconds(self) -> int:
        """Get cadastral cache TTL in seconds."""
        return self.cache_ttl_cadastre_days * 24 * 3600

    @property
    def cache_ttl_geocode_seconds(self) -> int:
        """Get geocoding cache TTL in seconds."""
        return self.cache_ttl_geocode_days * 24 * 3600

    @property
    def cache_ttl_infrastructure_seconds(self) -> int:
        """Get infrastructure cache TTL in seconds."""
        return self.cache_ttl_infrastructure_days * 24 * 3600


# Global settings instance
settings = Settings()
