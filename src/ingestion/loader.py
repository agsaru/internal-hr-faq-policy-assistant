import os
from unstructured.partition.auto import partition


def load_documents(path):
    if not os.path.exists(path):
        raise FileNotFoundError("File could not be loaded.")

    print(f"Loading Document: {path}")

    try:
        elements = partition(filename=path, include_page_breaks=True)
    except Exception as exc:
        print(f"Document loading error: {exc}")
        raise exc

    if not elements:
        raise ValueError("File contains no readable content.")

    print(f"\nTotal elements extracted: {len(elements)}")

    for index, element in enumerate(elements):
        print(f"Element {index}")
        print(f"Type: {type(element).__name__}")
        print(f"Content: {str(element)[:500]}")
        if element.metadata:
            print(f"Metadata: {element.metadata}")

    return elements