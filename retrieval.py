from typing import List
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from config import settings

def get_vector_store() -> PineconeVectorStore:
    """Initialize and return the Pinecone Vector Store."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL, 
        task_type="retrieval_query"
    )
    return PineconeVectorStore(
        pinecone_api_key=settings.PINECONE_API_KEY,
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        text_key="text_content"
    )

def retrieve_from_pinecone(query: str, k: int = 5) -> List[Document]:
    """Retrieve documents from Pinecone."""
    try:
        vector_store = get_vector_store()
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(query)
        print("Heres the docs:/n",docs)
        return docs
    except Exception as e:
        print(f"ERROR: Retrieval failed - {e}")
        return []