"""Схемы дашборда прогресса."""
from pydantic import BaseModel


class StatsOut(BaseModel):
    solved_total: int
    by_rating: dict[str, int]
    by_tag: dict[str, int]


class CfLinkRequest(BaseModel):
    handle: str


class CfSyncResult(BaseModel):
    newly_solved: int
