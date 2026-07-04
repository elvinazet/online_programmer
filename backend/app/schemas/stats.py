"""Схемы дашборда прогресса."""
from pydantic import BaseModel


class StatsOut(BaseModel):
    solved_total: int
    streak: int = 0
    by_rating: dict[str, int]
    by_tag: dict[str, int]


class TimelinePoint(BaseModel):
    date: str
    count: int


class CfLinkRequest(BaseModel):
    handle: str


class CfSyncResult(BaseModel):
    newly_solved: int
