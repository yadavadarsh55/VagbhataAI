import pandas as pd
import time
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pinecone import Pinecone, ServerlessSpec

from config import settings


# --- Configuration ---
DATA_FILE = "data/data.csv"
INDEX_NAME = "vagbhata-index"
PINECONE_API_KEY = settings.PINECONE_API_KEY
GOOGLE_API_KEY = settings.GOOGLE_API_KEY

# --- Validation ---
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not set in .env file.")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not set. Please set your API key.")

# --- Clients ---
# Initialize Gemini
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# --- Helper Functions ---

def get_gemini_embeddings(texts, task_type="retrieval_document"):
    """
    Generates embeddings for a list of texts using Gemini.
    """
    # The new Gemini SDK supports embedding a batch of documents directly
    response = gemini_client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type)
    )
    # Extract just the vector values
    return [embedding.values for embedding in response.embeddings]

def setup_pinecone_index(index_name):
    """
    Creates the Pinecone index if it doesn't exist.
    """
    existing_indexes = [i.name for i in pc.list_indexes()]

    if index_name not in existing_indexes:
        print(f"Creating index '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=768, # Gemini text-embedding-004 output dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1" # Or your preferred region
            )
        )
        # Wait a moment for the index to initialize
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
        print(f"Index '{index_name}' created successfully.")
    else:
        print(f"Index '{index_name}' already exists.")

    return pc.Index(index_name)

def batch_process(df, batch_size=50):
    """
    Pinecone works best when data is upserted in batches.
    """
    total_rows = len(df)
    
    # 1. Prepare data structure
    # Pinecone expects data in the format: (id, vector, metadata)
    documents = df['content (Sutra, Meaning, and Key Analysis)'].tolist()
    
    # Ensure metadata is in a dictionary format valid for Pinecone
    # (Values must be strings, numbers, booleans, or lists of strings)
    metadata_df = df[['sutra_name', 'primary_category', 'safety_level', 'target_dosha', 'advice_type']]
    metadatas = metadata_df.to_dict('records')
    
    # Add the text content itself to metadata so we can retrieve it later
    for i, meta in enumerate(metadatas):
        meta['text_content'] = documents[i]

    ids = [str(i) for i in range(total_rows)]
    
    # 2. Process in batches
    chunks = []
    for i in range(0, total_rows, batch_size):
        i_end = min(i + batch_size, total_rows)
        
        # Get batch of text and IDs
        batch_texts = documents[i:i_end]
        batch_ids = ids[i:i_end]
        batch_meta = metadatas[i:i_end]
        
        # Generate embeddings for this batch
        print(f"Generating embeddings for batch {i} to {i_end}...")
        try:
            batch_embeddings = get_gemini_embeddings(batch_texts)
            
            # Format for Pinecone: list of tuples (id, vector, metadata)
            to_upsert = list(zip(batch_ids, batch_embeddings, batch_meta))
            chunks.append(to_upsert)
            
        except Exception as e:
            print(f"Error embedding batch {i}-{i_end}: {e}")
            
    return chunks

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Load Data
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"Error: Could not find {DATA_FILE}.")
        exit()

    # 2. Setup Index
    index = setup_pinecone_index(INDEX_NAME)

    # 3. Process and Upsert
    batches = batch_process(df)
    
    print(f"Starting upload to Pinecone...")
    for batch in batches:
        index.upsert(vectors=batch)
        print(f"Upserted batch of {len(batch)} vectors.")

    print("\n--- Testing Retrieval ---")
    
    query_text = "What happens if I drink cold water immediately after eating food?"
    
    # Embed the query
    query_vector = get_gemini_embeddings([query_text], task_type="retrieval_query")[0]
    
    # Query Pinecone
    results = index.query(
        vector=query_vector,
        top_k=2,
        include_metadata=True
    )
    
    print(f"Query: {query_text}")
    for match in results['matches']:
        print(f"\nScore: {match['score']:.4f}")
        # Retrieve the text we stored in metadata
        print(f"Content: {match['metadata']['text_content'][:200]}...")
        print(f"Category: {match['metadata']['primary_category']}")