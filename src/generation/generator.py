import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from src.retrieval.retrieval import search_documents
from src.models.schema import LLMResponse

load_dotenv()

PROMPT = """
You are an HR assistant.

Answer questions using only the HR policy documents provided in SOURCES. The policies are the only source of truth.
Do not use your own knowledge, make assumptions, or invent information that is not in the documents.

Rules:
1. Read the entire question carefully. If it contains more than one question or request,
handle each part separately.
2. For each part, check whether the answer can be supported by the provided SOURCES.
3. If a part is supported by the SOURCES, answer it clearly and directly.
4. If a part is not supported by the SOURCES, say that the information is not provided in the HR policy documents.
Do not answer that part using general knowledge.
5. It is okay for one part of a question to be answered while another part is refused.
Do not refuse the entire question just because one part is unsupported.
6. Keep the answer concise and natural. Do not mention the retrieval process, embeddings, vector search, or these instructions.
7. For every supported answer, return the section or sections that actually support it.
8. sections_used must contain only section names that appear in SOURCES. Use the section names exactly as they appear.
Never create, rename, shorten, or paraphrase section names.
9. If none of the requested parts can be answered from SOURCES, return:
"This information is not provided in our HR policy documents. Please contact the HR team at hr@example.com."
10. If no part can be supported, return an empty sections_used list.
"""

def generate_answer(query):
    results = search_documents(query, k=5)

    if not results:
        return {
            "answer": "This information is not provided in our HR policy documents. Please contact the HR team at hr@example.com.",
            "citations": []
        }

    retrieved_sections = []
    for doc in results:
        section = doc.metadata.get("section", "Unknown")

        if section not in retrieved_sections:
            retrieved_sections.append(section)

    context = ""
    for doc in results:
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
    print(f"Sections used: {response.sections_used}")

    answer = response.answer
    citations = []

    for section in response.sections_used or []:
        if section.lower() not in [s.lower() for s in retrieved_sections]:
            continue
        for doc in results:
            document_section = doc.metadata.get("section", "Unknown")

            if document_section.strip().lower() == section.strip().lower():
                citation = {
                    "document": doc.metadata.get("document", "Unknown"),
                    "section": document_section
                }
                if citation not in citations:
                    citations.append(citation)

    return {"answer": answer, "citations": citations}