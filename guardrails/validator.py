class ResponseValidator:
    def __init__(self):
        # Edge Case 4.D.1: Subtle advisory language
        self.advisory_words = [
            "recommend", "advice", "should invest", "performed well", 
            "great return", "good time to", "highly suggested", "best fund"
        ]
        
    def validate(self, response: str) -> bool:
        # Check for advisory words
        r = response.lower()
        for word in self.advisory_words:
            if word in r:
                return False # Contains advisory language
                
        return True
