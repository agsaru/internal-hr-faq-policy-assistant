from langchain_core.documents import Document
from unstructured.chunking.title import chunk_by_title


def split_documents(elements):

    print(f"Input elements: {len(elements)}")

    chunks = chunk_by_title(
        elements,
        max_characters=1000,
        new_after_n_chars=750,
        overlap=100,
        combine_text_under_n_chars=200
    )

    print(f"Generated chunks: {len(chunks)}")

    documents = []

    current_section = "General"

    for index, chunk in enumerate(chunks):

        content = str(chunk).strip()
        lines = content.splitlines()

        for line in lines:
            line = line.strip()
            if (line and len(line) >= 3 and line[0].isdigit() and "." in line):
                current_section = line
                break

        metadata = chunk.metadata.to_dict()

        document_name = metadata.get("filename","unknown")

        metadata["document"] = document_name
        metadata["section"] = current_section
        metadata["chunk_index"] = index

        document = Document(page_content=content,metadata=metadata)

        documents.append(document)

        print(f"CHUNK {index}")
        print(f"Length: {len(content)}")
        print(f"Document: {document_name}")
        print(f"Section: {current_section}")
        print("Content:")
        print(content)

    return documents