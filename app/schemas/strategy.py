from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StrategyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = None
    entry_criteria: list[Any] = []
    exit_criteria: list[Any] = []


class StrategyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    entry_criteria: list[Any] | None = None
    exit_criteria: list[Any] | None = None


class StrategyResponse(BaseModel):
    id: str
    name: str
    description: str | None
    entry_criteria: list[Any]
    exit_criteria: list[Any]
    created_at: datetime

    @classmethod
    def from_model(cls, s) -> "StrategyResponse":
        return cls(
            id=s.id,
            name=s.name,
            description=s.description,
            entry_criteria=s.entry_criteria or [],
            exit_criteria=s.exit_criteria or [],
            created_at=s.created_at,
        )
