import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from src.retrieval.retrieval import search_documents


load_dotenv()


PROMPT = """
You are a senior HR.

Your task is to answer employees' questions only using the provided
policy documents.

RULES:
1. Do not answer any question which is out of context from the provided documents.
2. Do not guess or invent any policy on your own.
3. Do not hallucinate while answering.
4. If the answer is not provided in the documents, respond:
"This information is not provided in our HR policy documents.
Please contact the HR team at hr@example.com."
"""


def generate_answer(query):

    documents = search_documents(query, 3)

    if not documents:
        return {
            "answer": (
                "This information is not provided in our HR policy documents. "
                "Please contact the HR team at hr@example.com."
            ),
            "citations": []
        }

    context = ""

    for doc in documents:
        context += f"""
Document: {doc.metadata.get("document", "Unknown")}
Content:
{doc.page_content}

"""

    full_prompt = ChatPromptTemplate.from_template(
        PROMPT + """
        
DOCUMENTS:
{context}

QUESTION:
{question}
""").format(context=context,question=query)

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )

    response = model.invoke(full_prompt)

    answer = response.content

    if isinstance(answer, list):
        answer = answer[0]["text"]

    citations = []

    for doc in documents:
        document = doc.metadata.get("document", "Unknown")

        if not any(citation["document"] == document for citation in citations):
            citations.append({"document": document})

    return {"answer": answer,"citations": citations}