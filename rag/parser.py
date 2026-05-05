import json
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Edge Case 2.A.3: PII Regex Patterns
PII_PATTERNS = {
    "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    "Aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "Phone": r"\b[6-9]\d{9}\b",
    "Email": r"\b[\w.-]+@[\w.-]+\.\w+\b",
}

def scan_for_pii(text: str) -> bool:
    """Scans text for PII patterns. Returns True if PII is found."""
    for name, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            logging.warning(f"PII detected: {name}")
            return True
    return False

def parse_html_to_text(html_content: str) -> str:
    """
    Parses HTML, converts tables to text format, and removes boilerplate.
    Mitigates 2.A.1 (boilerplate) and 2.A.2 (tables).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "button"]):
        script.decompose()

    # Extract tables explicitly (Edge Case 2.A.2)
    # We replace tables with a formatted string representation
    for table in soup.find_all('table'):
        table_text = "\n[TABLE START]\n"
        for row in table.find_all('tr'):
            row_data = []
            for cell in row.find_all(['td', 'th']):
                # Clean up cell text
                cell_text = cell.get_text(separator=" ", strip=True)
                row_data.append(cell_text)
            if row_data:
                table_text += " | ".join(row_data) + "\n"
        table_text += "[TABLE END]\n"
        
        # Replace the table tag in the soup with a text node
        table.replace_with(table_text)

    # Extract all text, using a separator for blocks
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def run_parser():
    base_dir = Path(__file__).parent.parent
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    metadata_file = base_dir / "scraper" / "source_metadata.json"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        logging.error("Metadata file not found. Run scraper first.")
        return

    processed_metadata = []

    for meta in metadata:
        scheme_id = meta["source_url"].split('/')[-1].replace('-', '_') # Fallback ID logic
        raw_file = raw_dir / f"{scheme_id}.html"
        
        # In actual implementation, we might map URLs to files differently, 
        # but since we saved them as {scheme_id}.html, let's find the matching file.
        # Since I didn't save scheme_id in metadata explicitly, I'll extract it or just iterate over files.
        pass

    # A better way: iterate over files in raw_dir
    # And match with metadata by trying to guess the id or just read all.
    # Since we know the files, let's just process all .html files.
    for raw_file in raw_dir.glob("*.html"):
        scheme_id = raw_file.stem
        logging.info(f"Parsing {raw_file.name}...")
        
        with open(raw_file, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        clean_text = parse_html_to_text(html_content)
        
        # Edge Case 2.A.5: Minimum content length
        if len(clean_text) < 500:
            logging.error(f"Page {raw_file.name} has too little content ({len(clean_text)} chars). Skip.")
            continue
            
        # Edge Case 2.A.3: Hidden PII
        if scan_for_pii(clean_text):
            logging.error(f"PII found in {raw_file.name}. Skipping or needs manual review.")
            # For this project, we can either strip it or skip. Let's strip using regex or just log and continue.
            # We'll replace PAN and Phone with [REDACTED]
            for pattern in PII_PATTERNS.values():
                clean_text = re.sub(pattern, "[REDACTED_PII]", clean_text)
                
        # Save processed text
        processed_file = processed_dir / f"{scheme_id}.txt"
        with open(processed_file, "w", encoding="utf-8") as f:
            f.write(clean_text)
            
        logging.info(f"Saved cleaned text to {processed_file.name}")

if __name__ == "__main__":
    run_parser()
