from typing import List, Optional
from pydantic import BaseModel


class Citation(BaseModel):
    document: str
    section: Optional[str] = None


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    citations: List[Citation]


class LLMResponse(BaseModel):
    answer: str
    documents_used: List[str] = []
    sections_used: List[str] = []