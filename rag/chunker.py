import json
import logging
import hashlib
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def run_chunker():
    base_dir = Path(__file__).parent.parent
    processed_dir = base_dir / "data" / "processed"
    chunks_dir = base_dir / "data" / "chunks"
    metadata_file = base_dir / "scraper" / "source_metadata.json"
    
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            source_metadata = json.load(f)
    except FileNotFoundError:
        logging.error("Source metadata not found.")
        return

    # Create mapping from scheme_id to metadata
    meta_map = {}
    for meta in source_metadata:
        # Get scheme_id directly from the new metadata field
        scheme_id = meta.get("scheme_id")
        if scheme_id:
            meta_map[scheme_id] = meta

    # Edge Case 2.B.2, 2.B.3: Max chunk size and sliding window overlap
    # We use 500 characters (approx 100-150 words) and 100 chars overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    all_chunks = []
    seen_hashes = set() # Edge Case 2.B.4: Deduplicate identical content

    for processed_file in processed_dir.glob("*.txt"):
        scheme_id = processed_file.stem
        logging.info(f"Chunking {processed_file.name}...")
        
        with open(processed_file, "r", encoding="utf-8") as f:
            text = f.read()
            
        chunks = text_splitter.split_text(text)
        
        scheme_meta = meta_map.get(scheme_id, {})
        
        valid_chunks_count = 0
        for chunk in chunks:
            # Edge Case 2.B.1: Filter chunks that are too small and lack context
            if len(chunk.strip()) < 50:
                continue
                
            chunk_hash = get_content_hash(chunk)
            
            # Edge Case 2.B.4: De-duplicate
            if chunk_hash in seen_hashes:
                continue
            seen_hashes.add(chunk_hash)
            
            # Edge Case 2.B.5: Tag explicitly with scheme name and URL
            chunk_doc = {
                "content": chunk,
                "metadata": {
                    "source_url": scheme_meta.get("source_url", ""),
                    "scheme_name": scheme_meta.get("scheme_name", ""),
                    "scrape_date": scheme_meta.get("scrape_date", ""),
                    "chunk_hash": chunk_hash
                }
            }
            all_chunks.append(chunk_doc)
            valid_chunks_count += 1
            
        logging.info(f"Generated {valid_chunks_count} chunks for {scheme_id}.")

    output_file = chunks_dir / "all_chunks.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        
    logging.info(f"Chunking complete. {len(all_chunks)} total chunks saved to {output_file.name}")

if __name__ == "__main__":
    run_chunker()
