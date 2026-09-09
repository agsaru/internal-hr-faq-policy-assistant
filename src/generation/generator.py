import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.retrieval.retrieval import search_documents
from src.models.schema import LLMResponse

load_dotenv()

PROMPT = """
You are a senior HR.

Your task is to answer employees' questions only using the provided
policy documents.

RULES:
1. Answer only from the provided policy documents.
2. Do not guess or invent policy.
3. If the answer is not provided in the documents, respond something like:
"This information is not provided in our HR policy documents.
Please contact the HR team at hr@example.com."
4. Identify the policy section or sections that are related to your answer.
5. If the answer is not supported by the provided documents,
return an empty sections_used list.
6. Only use section names that appear in the provided documents.
"""

def generate_answer(query):
    results = search_documents(query, k=5)

    if not results:
        return {
            "answer": "This information is not provided in our HR policy documents. Please contact the HR team at hr@example.com.",
            "citations": []
        }

    context = ""
    for doc, score in results:
        context += f"""
Document: {doc.metadata.get("document", "Unknown")}
Section: {doc.metadata.get("section", "Unknown")}
Content:
{doc.page_content}
"""

    prompt = ChatPromptTemplate.from_template(
        PROMPT + """

SOURCES:
{context}

QUESTION:
{question}
"""
    )

    full_prompt = prompt.format(
        context=context,
        question=query
    )

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    structured_model = model.with_structured_output(LLMResponse)
    response = structured_model.invoke(full_prompt)

    print(f"Answer: {response.answer}")

    answer = response.answer
    citations = []

    for section in response.sections_used or []:
        for doc, score in results:
            document_section = doc.metadata.get("section", "Unknown")

            if section.lower() in document_section.lower() or document_section.lower() in section.lower():
                citation = {
                    "document": doc.metadata.get("document", "Unknown"),
                    "section": document_section
                }
                if citation not in citations:
                    citations.append(citation)

    return {"answer": answer, "citations": citations}