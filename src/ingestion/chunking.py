from langchain_core.documents import Document
from unstructured.chunking.title import chunk_by_title


def split_documents(elements):

    chunks = chunk_by_title(
        elements,
        max_characters=1000,
        new_after_n_chars=750,
        overlap=100,
        combine_text_under_n_chars=200,
    )

    print(f"Generated chunks: {len(chunks)}")

    documents = []
    current_section = "General"

    for index, chunk in enumerate(chunks):
        content = str(chunk).strip()
        orig_elements = getattr(chunk.metadata, "orig_elements", [])
        if orig_elements and type(orig_elements[0]).__name__ in ("Title", "Header"):
            current_section = str(orig_elements[0]).strip()

        metadata = chunk.metadata.to_dict()
        document_name = metadata.get("filename", "unknown")

        metadata["document"] = document_name
        metadata["section"] = current_section
        metadata["chunk_index"] = index

        document = Document(page_content=content, metadata=metadata)
        documents.append(document)

    print(f"Generated {len(documents)} chunks.")

    return documents