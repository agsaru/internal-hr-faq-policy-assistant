from pydantic import BaseModel
from typing import List

class Citation(BaseModel):
    document: str

class Question(BaseModel):
    question: str

class Answer(BaseModel):
    answer: str
    citations: List[Citation]