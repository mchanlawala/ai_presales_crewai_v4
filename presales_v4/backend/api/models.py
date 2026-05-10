from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class WorkflowStatus(str, Enum):
    IDLE       = "idle"
    INTAKE     = "intake"
    ANALYZING  = "analyzing"
    QUESTIONING= "questioning"
    GENERATING = "generating"
    REVIEWING  = "reviewing"
    APPROVED   = "approved"
    PUBLISHED  = "published"
    ERROR      = "error"

class IntakeRequest(BaseModel):
    query: str
    industry_hint: Optional[str] = None
    session_id: Optional[str] = None

class AnswerRequest(BaseModel):
    session_id: str
    answers: Dict[str, str]

class ReviewDecision(BaseModel):
    session_id: str
    decision: str   # approve | request_changes | reject
    comments: Optional[str] = None
    document_feedback: Optional[Dict[str, str]] = None

class KnowledgeBaseCreate(BaseModel):
    industry: str
    content: str
    description: Optional[str] = None
