from pydantic import BaseModel, Field
from typing import Optional, Literal


class FindPathsPlan(BaseModel):
    source_entity: str
    target_entity: str
    depth: int = Field(default=4, ge=1, le=4)
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    currency: Optional[str] = None
    max_paths: int = Field(default=10, ge=1, le=50)
    type_a: Optional[str] = None
    type_b: Optional[str] = None


class Plan(BaseModel):
    action: Literal["FIND_PATHS", "GRAPH_QUERY", "CALL_SPECIALIST", "ASK_CLARIFICATION", "UNKNOWN"]
    find_paths: Optional[FindPathsPlan] = None
    clarification_question: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        extra = "forbid"
