import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.retrieval.retrieval import search_documents


load_dotenv()

PROMPT="""You are a senior HR.
Your task is to answer employees questions only using the provided policy documents.
RULES:
1. Do not answer any question which is out of context from the provided documents
2. Do not guess or invent any policy on your own.
3. Do not hallucinate while answering
4. If the do not know answer the answer or you can just respond like
  -"This information is not provided in our HR policy documents. Please contact the HR team at hr@example.com"
"""

def generate_answer(query):
    documents=search_documents(query,3)
    if not documents:
        return "This information is not available in our policy documents. Please Contact the HR team at hr@example.com."
    FULL_PROMPT = ChatPromptTemplate.from_template(
    PROMPT + """
DOCUMENTS:
{documents}
QUESTION:
{question}
"""
).format(documents=documents,question=query)
    model=ChatGoogleGenerativeAI(
        model='gemini-3.5-flash',
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )
    response=model.invoke(FULL_PROMPT)
    if isinstance(response.content, list):
        return response.content[0]["text"]
    return response.content