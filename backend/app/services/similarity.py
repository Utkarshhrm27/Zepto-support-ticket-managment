from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel
from app.models import ResolvedTicket

class PrecedentMatch(BaseModel):
    id: str
    action: str
    category: str
    score: float

class SimilarityIndex:
    def __init__(self, resolved_tickets: list[ResolvedTicket]):
        self.ids = [t.id for t in resolved_tickets]
        self.actions = [t.resolution_action for t in resolved_tickets]
        self.categories = [t.category for t in resolved_tickets]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
        
        # Fit-transform requires at least one document
        docs = [t.description for t in resolved_tickets]
        if not docs:
            docs = ["dummy description"]
            
        self.matrix = self.vectorizer.fit_transform(docs)

    def top_k(self, query_text: str, k: int = 3) -> list[PrecedentMatch]:
        qv = self.vectorizer.transform([query_text])
        scores = cosine_similarity(qv, self.matrix).flatten()
        top_idx = scores.argsort()[::-1][:k]
        
        results = []
        for i in top_idx:
            # Handle case where there are fewer precedents than k
            if i < len(self.ids):
                results.append(PrecedentMatch(
                    id=self.ids[i],
                    action=self.actions[i],
                    category=self.categories[i],
                    score=float(scores[i])
                ))
        return results
