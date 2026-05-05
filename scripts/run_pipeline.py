import subprocess
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(script_path: Path):
    """Run a Python script and raise an exception if it fails (Edge Case 7.C.1)."""
    logging.info(f"--- Starting {script_path.name} ---")
    result = subprocess.run([sys.executable, str(script_path)])
    if result.returncode != 0:
        logging.error(f"❌ {script_path.name} failed with exit code {result.returncode}. Halting pipeline.")
        sys.exit(result.returncode)
    logging.info(f"✅ {script_path.name} completed successfully.\n")

def main():
    base_dir = Path(__file__).parent.parent
    
    scripts = [
        base_dir / "scraper" / "scraper.py",
        base_dir / "rag" / "parser.py",
        base_dir / "rag" / "chunker.py",
        base_dir / "rag" / "indexer.py"
    ]
    
    logging.info("Starting Mutual Fund FAQ Data Pipeline...")
    
    for script in scripts:
        if not script.exists():
            logging.error(f"Script not found: {script}")
            sys.exit(1)
        run_script(script)
        
    logging.info("🎉 Full pipeline executed successfully.")

if __name__ == "__main__":
    main()
