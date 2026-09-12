import os
from unstructured.partition.auto import partition

def load_documents(path):
    if not os.path.exists(path):
        raise FileNotFoundError("File could not be loaded.")

    try:
        elements = partition(filename=path, include_page_breaks=True)
    except Exception as exc:
        raise RuntimeError(f"Document loading failed: {exc}") from exc

    if not elements:
        raise ValueError("File contains no readable content.")

    return elements