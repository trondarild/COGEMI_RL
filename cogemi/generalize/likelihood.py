# generalize/likelihood.py
from typing import Dict, List, Tuple


class ContextLikelihoodModel:
    '''A simple likelihood model that estimates the probability of a context given features.'''
    def __init__(self):
        self.contexts: Dict[Tuple, Dict[str, int]] = {}
        self.all_contexts: set = set()
        self.total_count: int = 0

    def fit(self, X: List[List[str]], y: List[str]) -> None:
        for features, context in zip(X, y):
            features_tuple = tuple(features)
            if features_tuple not in self.contexts:
                self.contexts[features_tuple] = {}
            if context not in self.contexts[features_tuple]:
                self.contexts[features_tuple][context] = 0
            self.contexts[features_tuple][context] += 1
            self.all_contexts.add(context)
            self.total_count += 1

    def predict_proba(self, features: List[str]) -> Dict[str, float]:
        features_tuple = tuple(features)
        if features_tuple not in self.contexts:
            # Uniform distribution over all known contexts
            n = len(self.all_contexts) or 1
            return {context: 1.0 / n for context in self.all_contexts}
        context_counts = self.contexts[features_tuple]
        total_context_count = sum(context_counts.values())
        return {context: count / total_context_count for context, count in context_counts.items()}
