"""Pydantic models for configuration handling."""

from typing import Optional
from pydantic import BaseModel


class Brief(BaseModel):
    """Configuration for a brief message."""

    file: str
    role: str = "assistant"


class ProfileConfig(BaseModel):
    """Configuration for a single profile."""

    model: Optional[str] = None
    role: Optional[str] = None
    output: Optional[str] = None
    prompt_prepend: Optional[str] = None
    temperature: Optional[float] = None


class FullConfig(BaseModel):
    """Full configuration with profiles."""

    profiles: dict[str, ProfileConfig] = {}
    brief: Optional[Brief] = None
