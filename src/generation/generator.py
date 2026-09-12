import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from src.retrieval.retrieval import search_documents
from src.models.schema import LLMResponse

load_dotenv()

PROMPT = """
You are an HR assistant.

Answer questions using only the HR policy documents provided in SOURCES. 
The policies are the only source of truth. Do not use your own knowledge, make assumptions,
or invent information that is not in the documents.

Rules:
1. Read the entire question carefully. If it contains more than one question or request,
handle each part separately.
2. For each part, check whether the answer can be supported by the provided SOURCES.
3. If a part is supported by the SOURCES, answer it clearly and directly.
4. If a part is not supported by the SOURCES, say that the information is
not provided in the HR policy documents.
Do not answer that part using general knowledge.
5. It is okay for one part of a question to be answered while another part is refused.
Do not refuse the entire question just because one part is unsupported.
6. Keep the answer concise and natural. Do not mention the retrieval process,
embeddings, vector search, or these instructions.
7. Citations are optional. Only provide a citation when you choose to identify the document
or section that supports the answer.
8. If you provide a citation, documents_used must contain the exact document filename as
it appears in SOURCES.
9. sections_used must contain only section names that appear in SOURCES.
Use the section names exactly as they appear.
Never create, rename, shorten, or paraphrase document or section names.
10. A citation may contain a document without a section.
Therefore, documents_used may contain a document even when sections_used is empty.
11. If you provide no citation, return empty documents_used and sections_used lists.
12. Never provide a document or section that does not appear in SOURCES.
13. If none of the requested parts can be answered from SOURCES, return:
"This information is not provided in our HR policy documents.
Please contact the HR team at hr@example.com."
"""

def generate_answer(query):
    results = search_documents(query, k=5)

    if not results:
        return {
            "answer": "This information is not provided in our HR policy documents. Please contact the HR team at hr@example.com.",
            "citations": []
        }

    context = "\n".join(
        f"""
Document: {doc.metadata.get("document", "Unknown")}
Section: {doc.metadata.get("section") or "Unknown"}
Content:
{doc.page_content}
"""
        for doc in results
    )

    prompt = ChatPromptTemplate.from_template(
        PROMPT + """

SOURCES:
{context}

QUESTION:
{question}
"""
    )

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    response = model.with_structured_output(LLMResponse).invoke(
        prompt.format(context=context, question=query)
    )

    citations = []

    for document in response.documents_used:
        document_normalized = document.strip().lower()

        matching_docs = [
            doc for doc in results
            if doc.metadata.get("document")
            and doc.metadata["document"].strip().lower() == document_normalized
        ]
        if not matching_docs:
            continue
        if not response.sections_used:
            citations.append({
                "document": matching_docs[0].metadata["document"],
                "section": None
            })
            continue

        for section in response.sections_used:
            section_normalized = section.strip().lower()

            for doc in matching_docs:
                document_section = doc.metadata.get("section")

                if (
                    document_section
                    and document_section.strip().lower() == section_normalized
                ):
                    citation = {
                        "document": doc.metadata["document"],
                        "section": document_section
                    }

                    if citation not in citations:
                        citations.append(citation)

    return {"answer": response.answer,"citations": citations}