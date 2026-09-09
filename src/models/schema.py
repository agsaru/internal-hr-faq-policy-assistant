from pydantic import BaseModel
from typing import List

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
    sections_used: List[str]