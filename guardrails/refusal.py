REFUSAL_TEMPLATE = """I'm a facts-only assistant and cannot provide investment advice or recommendations. For guidance on mutual fund investing, please visit: https://www.amfiindia.com/investor-corner/knowledge-center"""

class RefusalHandler:
    def get_refusal(self, query: str = "") -> str:
        q = query.lower()
        # Edge Case 4.C.2: Why can't you give advice?
        if "why" in q and ("can't" in q or "cannot" in q) and "advice" in q:
            return "As an automated AI assistant, I am not a SEBI-registered investment advisor. Therefore, I can only provide factual information found in the official scheme documents."
            
        return REFUSAL_TEMPLATE
