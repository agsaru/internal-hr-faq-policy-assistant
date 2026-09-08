from fastapi import APIRouter, HTTPException

from src.models.schema import Question, Answer
from src.generation.generator import generate_answer


router = APIRouter()


@router.post("/ask", response_model=Answer)
def ask_question(question: Question):

    query = question.question.strip()

    if not query:
        raise HTTPException(status_code=400,detail="Question cannot be empty")

    return generate_answer(query)