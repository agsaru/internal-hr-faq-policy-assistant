import os
import requests
import streamlit as st

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="HR Policy Assistant", layout="centered")
st.title("HR Policy Assistant")

role = st.sidebar.radio("Select Role", ["HR", "Employee"])

if role == "HR":
    st.subheader("Upload Policy Documents")

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    uploaded_files = st.file_uploader(
        "Choose Markdown, text, or PDF files",
        type=["md", "txt", "pdf"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if uploaded_files and st.button("Upload"):
        errors = []
        try:
            with st.spinner(f"Uploading documents"):
                for uploaded_file in uploaded_files:
                    response = requests.post(
                        f"{BACKEND_API_URL}/documents/upload",
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        },
                        timeout=120,
                    )

                    if response.status_code != 200:
                        errors.append(f"{uploaded_file.name}: {response.json().get('detail', 'Upload failed.')}")

            if not errors:
                st.toast("Successfully uploaded documents.")
                st.session_state.uploader_key += 1
                st.rerun()
            else:
                for err in errors:
                    st.error(err)
        except requests.exceptions.ConnectionError:
            st.error("FastAPI backend is not running.")
        except requests.exceptions.RequestException as exc:
            st.error(f"Upload failed: {exc}")

    st.subheader("Uploaded Policies")

    try:
        response = requests.get(f"{BACKEND_API_URL}/documents/", timeout=30)

        if response.status_code == 200:
            documents = response.json()

            if not documents:
                st.info("No policy documents uploaded yet.")
            else:
                for document in documents:
                    col1, col2 = st.columns([4, 1])
                    filename = document["filename"]

                    with col1:
                        st.write(filename)

                    with col2:
                        if st.button("Delete", key=filename):
                            try:
                                with st.spinner("Deleting document"):
                                    response = requests.delete(
                                        f"{BACKEND_API_URL}/documents/{filename}",
                                        timeout=30,
                                    )
                                if response.status_code == 200:
                                    st.success("Document deleted.")
                                    st.rerun()
                                else:
                                    st.error(
                                        response.json().get(
                                            "detail", "Failed to delete document."
                                        )
                                    )
                            except requests.exceptions.ConnectionError:
                                st.error("FastAPI backend is not running.")
                            except requests.exceptions.RequestException as exc:
                                st.error(f"Delete failed: {exc}")
        else:
            st.error("Could not fetch documents.")
    except requests.exceptions.ConnectionError:
        st.warning("FastAPI backend is not running.")
    except requests.exceptions.RequestException as exc:
        st.warning(f"Could not fetch documents: {exc}")
else:
    question = st.text_input("Enter your question regarding any policy")

    if st.button("Ask"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            try:
                with st.spinner("Searching policies and generating answer"):
                    response = requests.post(
                        f"{BACKEND_API_URL}/chat/ask",
                        json={"question": question},
                        timeout=120,
                    )

                if response.status_code == 200:
                    result = response.json()
                    st.subheader("Answer")
                    st.write(result["answer"])

                    citations = result.get("citations", [])
                    if citations:
                        st.subheader("Sources")
                        for citation in citations:
                            document = citation.get("document")
                            section = citation.get("section")
                            if document:
                                st.write(f"Document: {document}")
                            if section:
                                st.write(f"Section: {section}")
                    else:
                        st.info("No citations available.")
                else:
                    st.error(response.json().get("detail", "Request failed."))
            except requests.exceptions.ConnectionError:
                st.error("FastAPI backend is not running.")
            except requests.exceptions.RequestException as exc:
                st.error(f"Request failed: {exc}")