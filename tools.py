from langchain.tools import tool
from retrieval import retrieve_from_pinecone

@tool
def ayurvedic_source(query: str) -> str:
    """
    Retrieves information from the Ayurvedic classical texts/source based on the user's query.
    Always use this to verify facts before answering.
    """
    print("Loading Vector from Pinecone storage...")
    
    try:
        docs = retrieve_from_pinecone(query)
        if not docs:
            return "No relevant ayurvedic source found for the given query."
    except Exception as e:
        return f"Error loading Vector Store: {e}"

    formatted_sources = []
    signal = ""

    for doc in docs:
        metadata = doc.metadata or {}
        
        # Guardrail check
        if metadata.get('safety_level', '').upper() == 'CRITICAL':
            signal = "[CRITICAL ADVICE DETECTED] "

        context_block = (
            f"CONTEXT STARTS HERE\n"
            f"Sutra: {metadata.get('sutra_name', 'N/A')}\n"
            f"Primary Category: {metadata.get('primary_category', 'N/A')}\n"
            f"Safety Level: {metadata.get('safety_level', 'N/A')}\n"
            f"Target Dosha: {metadata.get('target_dosha', 'N/A')}\n"
            f"Advice Type: {metadata.get('advice_type', 'N/A')}\n"
            f"Content: {doc.page_content}\n"
            f"CONTEXT ENDS HERE\n"
            "-----\n"
        )
        formatted_sources.append(context_block)

    return signal + "\n".join(formatted_sources)

# List of tools to be bound to the LLM
ALL_TOOLS = [ayurvedic_source]