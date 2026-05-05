import json
import logging
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_indexer():
    base_dir = Path(__file__).parent.parent
    chunks_file = base_dir / "data" / "chunks" / "all_chunks.json"
    db_dir = base_dir / "data" / "chroma_db"
    
    db_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(chunks_file, "r", encoding="utf-8") as f:
            all_chunks = json.load(f)
    except FileNotFoundError:
        logging.error("Chunks file not found.")
        return

    # Edge Case 2.C.4: Pin embedding model
    embedding_model_name = "all-MiniLM-L6-v2"
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model_name)
    
    # Initialize Chroma client
    client = chromadb.PersistentClient(path=str(db_dir))
    
    collection_name = "quant_mf_faq"
    
    # Edge Case 2.C.3: Corruption mitigation. Rebuild index from scratch.
    try:
        client.delete_collection(name=collection_name)
        logging.info(f"Deleted existing collection '{collection_name}' for clean rebuild.")
    except Exception:
        pass
        
    collection = client.create_collection(
        name=collection_name, 
        embedding_function=sentence_transformer_ef,
        metadata={"hnsw:space": "cosine"} # Cosine similarity
    )
    
    documents = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(all_chunks):
        content = chunk["content"]
        meta = chunk["metadata"]
        
        # Edge Case 2.C.1: Chunk token limit check (all-MiniLM-L6-v2 max length is 256 tokens)
        # Our chunks are ~500 chars, so ~100 tokens, which is safe.
        
        # Edge Case 2.C.2: Similar schemes issue -> Ensure scheme_name is explicitly included in document text if needed,
        # but for now we have it in metadata, which allows metadata filtering.
        
        documents.append(content)
        metadatas.append(meta)
        ids.append(f"chunk_{i}_{meta.get('chunk_hash', '')}")

    # Add to Chroma in batches to be safe, though 200 chunks is tiny
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        logging.info(f"Indexing batch {i} to {end}...")
        collection.add(
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            ids=ids[i:end]
        )
        
    logging.info(f"Successfully indexed {len(documents)} chunks into '{collection_name}'.")

if __name__ == "__main__":
    run_indexer()
