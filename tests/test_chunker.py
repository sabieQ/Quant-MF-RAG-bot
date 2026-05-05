import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag.chunker import get_content_hash

def test_chunk_hashing():
    hash1 = get_content_hash("Standard text chunk for mutual fund.")
    hash2 = get_content_hash("Standard text chunk for mutual fund.")
    hash3 = get_content_hash("Different text chunk.")
    
    assert hash1 == hash2
    assert hash1 != hash3
