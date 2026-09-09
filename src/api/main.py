import uvicorn
from fastapi import FastAPI

from src.api.routes.documents import router as document_router
from src.api.routes.chat import router as chat_router

app = FastAPI(title="HR Policy Assistant API")

app.include_router(document_router, prefix="/documents")
app.include_router(chat_router, prefix="/chat")


@app.get("/")
def hello_world():
    return {"message": "Hello from HR Policy Assistant"}


if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)