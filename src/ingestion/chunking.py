from langchain_core.documents import Document
from unstructured.chunking.title import chunk_by_title


def split_documents(elements):
    chunks = chunk_by_title(
        elements,
        max_characters=1000,
        new_after_n_chars=750,
        overlap=100,
        combine_text_under_n_chars=100,
    )

    documents = []
    current_section = None

    for index, chunk in enumerate(chunks):
        content = str(chunk).strip()
        orig_elements = getattr(chunk.metadata, "orig_elements", [])
        headings = []
        for element in orig_elements:
            element_type = type(element).__name__
            
            if element_type in ("Title", "Header", "ListItem"):
                heading = str(element).strip()

                if heading:
                    headings.append(heading)

        if headings:
            current_section = headings[-1]

        metadata = chunk.metadata.to_dict()
        document_name = metadata.get("filename", "unknown")

        metadata["document"] = document_name
        metadata["section"] = current_section
        metadata["chunk_index"] = index

        document = Document(page_content=content, metadata=metadata)
        documents.append(document)

    print(f"Generated {len(documents)} chunks.")

    return documents