<<<<<<< HEAD
"""
Tools available to agents.
"""
from langchain_core.tools import tool
from app.core.retrieval.vector_store import get_vector_store
from app.core.retrieval.serialization import serialize_chunks
=======
"""Tools for agents - Pinecone with Gemini embeddings."""

from langchain_core.tools import tool
from ..retrieval.vector_store import vector_store_manager
>>>>>>> d64bd48 (Initial commit)


@tool
def retrieval_tool(query: str) -> str:
    """
<<<<<<< HEAD
    Search the vector database for relevant information.
    
    Args:
        query: Search query string
        
    Returns:
        Formatted context from retrieved documents
    """
    # Get vector store
    vector_store = get_vector_store()
    
    # Perform similarity search
    docs = vector_store.similarity_search(query, k=5)
    
    # Serialize results
    context = serialize_chunks(docs)
    
    return context
=======
    Search Pinecone vector database for relevant information.
    Uses FREE Gemini embeddings for semantic search.
    
    Args:
        query: The search query
        
    Returns:
        Relevant context from Pinecone
    """
    print(f" Searching Pinecone for: {query[:60]}...")
    
    # Semantic search in Pinecone
    results = vector_store_manager.search(query, k=4)
    
    if not results:
        return "No relevant information found in the database."
    
    # Format results with IDs
    context_parts = []
    for i, doc in enumerate(results, 1):
        chunk_id = f"C{i}"
        page = doc.metadata.get("page", "unknown")
        source = doc.metadata.get("source", "unknown")
        
        context_parts.append(
            f"[{chunk_id}] (Page {page}, {source})\n{doc.page_content}"
        )
    
    formatted_context = "\n\n" + ("=" * 60 + "\n\n").join(context_parts)
    
    return formatted_context
>>>>>>> d64bd48 (Initial commit)
