import requests
import streamlit as st
import os

BACKEND_API_URL = os.getenv("BACKEND_API_URL","http://127.0.0.1:8000") 
 
st.set_page_config( page_title="HR Policy Assistant", layout="centered") 
 
st.title("HR Policy Assistant") 
role = st.sidebar.radio( "Select Role", ["HR", "Employee"] )  
 
if role == "HR": 
    st.subheader("Upload Policy Documents") 
 
    uploaded_file = st.file_uploader( 
        "Choose a Markdown or text file", 
        type=["md", "txt"] 
    ) 
 
    if uploaded_file and st.button("Upload"): 
 
        try: 
            response = requests.post( 
                f"{BACKEND_API_URL}/documents/upload", 
                files={ 
                    "file": ( 
                        uploaded_file.name, 
                        uploaded_file.getvalue(), 
                        uploaded_file.type 
                    ) 
                } 
            ) 
 
            if response.status_code == 200: 
                message = response.json().get( "message", "Policy uploaded successfully." ) 
                st.success(message) 
 
            else: 
                st.error("Upload failed.") 
 
        except requests.exceptions.ConnectionError: 
            st.error("FastAPI backend is not running.") 
 
    st.subheader("Uploaded Policies") 
 
    try: 
        response = requests.get(f"{BACKEND_API_URL}/documents/") 
 
        if response.status_code == 200: 
            documents = response.json() 
 
            if len(documents) == 0: 
                st.info("No policy documents uploaded yet.") 
            else: 
                for document in documents: 
                    col1, col2 = st.columns([4, 1])
 
                    with col1:
                        st.write(f"{document['filename']}")
 
                    with col2:
                        if st.button("Delete", key=document["filename"]):
                            try:
                                delete_response = requests.delete(
                                    f"{BACKEND_API_URL}/documents/{document['filename']}"
                                )

                                if delete_response.status_code == 200:
                                    st.success("Document deleted.")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete document.")

                            except requests.exceptions.ConnectionError:
                                st.error("FastAPI backend is not running.")
 
        else: 
            st.error("Could not fetch documents.") 

    except requests.exceptions.ConnectionError: 
        st.warning("FastAPI backend is not running.") 
 
 
else: 
    question = st.text_input("Enter your question regarding any policy") 
 
    if st.button("Ask"): 
        if not question.strip(): 
            st.warning("Please enter a question.") 
 
        else: 
            try: 
                response = requests.post( 
                    f"{BACKEND_API_URL}/chat/ask", 
                    json={"question": question} 
                ) 
 
                if response.status_code == 200: 
 
                    result = response.json() 
                    st.subheader("Answer") 
                    st.write(result["answer"]) 
 
                    citations = result.get("citations", []) 
 
                    if citations:
                        st.subheader("Sources")

                        for citation in citations:
                            document = citation.get("document","Unknown document")
                            st.write(document)
                    else:
                        st.info("No citations available.")
 
                else: 
                    st.error("Request failed.") 
 
            except requests.exceptions.ConnectionError: 
                st.error("FastAPI backend is not running.") 