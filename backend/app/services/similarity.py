import math
from collections import Counter
import re
from pydantic import BaseModel
from app.models import ResolvedTicket

class PrecedentMatch(BaseModel):
    id: str
    action: str
    category: str
    score: float

def get_ngrams(text: str, n: int = 2):
    words = re.findall(r'\b\w+\b', str(text).lower())
    stop_words = {"the", "a", "an", "is", "in", "and", "or", "of", "to", "for", "with", "on", "at", "by"}
    words = [w for w in words if w not in stop_words]
    ngrams = list(words)
    for i in range(len(words)-1):
        ngrams.append(words[i] + " " + words[i+1])
    return ngrams

class SimilarityIndex:
    def __init__(self, resolved_tickets: list[ResolvedTicket]):
        self.ids = [t.id for t in resolved_tickets]
        self.actions = [t.resolution_action for t in resolved_tickets]
        self.categories = [t.category for t in resolved_tickets]
        
        docs = [t.description if t.description else "" for t in resolved_tickets]
        if not docs:
            docs = ["dummy description"]
            
        self.doc_freqs = Counter()
        self.doc_ngrams = []
        for doc in docs:
            ng = get_ngrams(doc)
            self.doc_ngrams.append(ng)
            for unique_ng in set(ng):
                self.doc_freqs[unique_ng] += 1
                
        self.N = len(docs)
        self.idf = {ng: math.log((1 + self.N) / (1 + freq)) + 1 for ng, freq in self.doc_freqs.items()}
        
        self.doc_vectors = []
        for ngs in self.doc_ngrams:
            tf = Counter(ngs)
            vec = {ng: count * self.idf.get(ng, 0) for ng, count in tf.items()}
            norm = math.sqrt(sum(v**2 for v in vec.values()))
            if norm > 0:
                vec = {ng: v/norm for ng, v in vec.items()}
            self.doc_vectors.append(vec)

    def top_k(self, query_text: str, k: int = 3) -> list[PrecedentMatch]:
        q_ngrams = get_ngrams(query_text)
        q_tf = Counter(q_ngrams)
        if not q_ngrams:
            return []
            
        q_vec = {ng: count * self.idf.get(ng, 0) for ng, count in q_tf.items()}
        q_norm = math.sqrt(sum(v**2 for v in q_vec.values()))
        if q_norm > 0:
            q_vec = {ng: v/q_norm for ng, v in q_vec.items()}
            
        scores = []
        for i, doc_vec in enumerate(self.doc_vectors):
            score = sum(v * doc_vec.get(ng, 0) for ng, v in q_vec.items())
            scores.append((score, i))
            
        scores.sort(reverse=True)
        top_idx = scores[:k]
        
        results = []
        for score, i in top_idx:
            if i < len(self.ids):
                results.append(PrecedentMatch(
                    id=self.ids[i],
                    action=self.actions[i],
                    category=self.categories[i],
                    score=float(score)
                ))
        return results
