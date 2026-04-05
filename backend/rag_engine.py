import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "chroma_db"
KNOWLEDGE_BASE_PATH = "knowledge_base.txt"

embedding_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

def build_knowledge_base():
    print("Building knowledge base...")

    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". "]
    )
    chunks = splitter.split_text(text)
    print(f"Created {len(chunks)} chunks")

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_PATH
    )
    print("Knowledge base built and saved!")
    return vectorstore

def load_knowledge_base():
    if not os.path.exists(CHROMA_PATH):
        return build_knowledge_base()

    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_model
    )

def retrieve_context(query: str, k: int = 3) -> str:
    vectorstore = load_knowledge_base()
    docs = vectorstore.similarity_search(query, k=k)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context