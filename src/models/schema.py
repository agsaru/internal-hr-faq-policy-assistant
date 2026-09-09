from typing import List
from pydantic import BaseModel


class Citation(BaseModel):
    document: str
    section: str


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    citations: List[Citation]


class LLMResponse(BaseModel):
    answer: str
    sections_used: List[str] = []