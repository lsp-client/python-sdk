from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LSP_CLIENT_",
        env_file=".env",
        extra="ignore",
    )

    disable_auto_installation: bool = False
    request_timeout: float = 5.0
    shutdown_timeout: float = 5.0
    container_backend: Literal["docker", "podman"] = "docker"


settings = Settings()
