import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag.parser import parse_html_to_text

def test_parse_html_basic():
    html = "<html><body><h1>Test Fund Title</h1><p>This is a test paragraph.</p></body></html>"
    text = parse_html_to_text(html)
    assert "Test Fund Title" in text
    assert "This is a test paragraph." in text

def test_parse_html_table():
    html = "<html><body><table><tr><td>Column 1</td><td>Column 2</td></tr></table></body></html>"
    text = parse_html_to_text(html)
    assert "Column 1 | Column 2" in text

def test_strip_disclaimers():
    html = "<html><body><p>Valid text</p><p>Disclaimer: Mutual fund investments are subject to market risks.</p></body></html>"
    text = parse_html_to_text(html)
    assert "Valid text" in text
    assert "Disclaimer:" not in text
