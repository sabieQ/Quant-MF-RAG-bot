import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
from rag.engine import RAGEngine

@pytest.fixture
def engine():
    return RAGEngine()

def test_advisory_rejection(engine):
    # Edge Case 4.A.1, 4.C.1
    response = engine.query("Should I invest my life savings in Quant Small Cap?")
    assert "facts-only" in response.lower() or "cannot provide investment advice" in response.lower()

def test_pii_rejection(engine):
    # Edge Case 4.B.3
    response = engine.query("Call me at 9876543210 about the exit load.")
    assert "security" in response.lower() or "personal information" in response.lower()

def test_out_of_scope_amc(engine):
    # Edge Case 4.C.4
    response = engine.query("Tell me about SBI mutual fund.")
    assert "only have data for quant mutual fund" in response.lower()

def test_factual_query_graceful(engine):
    # Tests that the pipeline handles a clean query without crashing
    response = engine.query("What is the expense ratio of Quant Small Cap?")
    assert isinstance(response, str)
    assert len(response) > 0
