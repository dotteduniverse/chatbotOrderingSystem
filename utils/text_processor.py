"""Advanced text processing utilities"""

import re
from typing import List, Tuple, Dict, Any
import numpy as np

class TextProcessor:
    """Advanced text processing for order understanding"""
    
    @staticmethod
    def extract_quantities(text: str) -> List[Tuple[str, int]]:
        """Extract quantities and items from text"""
        patterns = [
            (r'(\d+)\s*(?:x\s*)?([a-zA-Z\s]+)', int),  # "2 samosas"
            (r'(?:a|an)\s+([a-zA-Z\s]+)', 1),  # "a tea"
            (r'(?:one|two|three|four|five|six|seven|eight|nine|ten)\s+([a-zA-Z\s]+)', None)  # Word numbers
        ]
        
        # Number words mapping
        number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        results = []
        text_lower = text.lower()
        
        # Pattern 1: Digit patterns
        for pattern, _ in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    quantity = int(match[0])
                    item = match[1].strip()
                    results.append((item, quantity))
                else:
                    results.append((match, 1))
        
        # Pattern 2: Word numbers
        for word, number in number_words.items():
            if word in text_lower:
                pattern = rf'{word}\s+([a-zA-Z\s]+)'
                matches = re.findall(pattern, text_lower)
                for item in matches:
                    results.append((item.strip(), number))
        
        return results
    
    @staticmethod
    def extract_variants(text: str, available_variants: List[str]) -> List[str]:
        """Extract variant preferences (hot/iced, etc.)"""
        text_lower = text.lower()
        found_variants = []
        
        for variant in available_variants:
            if variant.lower() in text_lower:
                found_variants.append(variant)
        
        return found_variants
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        # Simple implementation - in production, use embeddings
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing spaces
        text = text.strip()
        return text

class IntentClassifier:
    """Classify user intent using simple NLP"""
    
    INTENTS = {
        'order': ['want', 'like', 'get', 'order', 'buy', 'have', 'need', 'would like', 'give me'],
        'menu': ['menu', 'what do you have', 'items', 'offer', 'available', 'list', 'show me'],
        'checkout': ['checkout', 'confirm', 'pay', 'complete', 'finish', 'order now', 'place order'],
        'cancel': ['cancel', 'remove', 'delete', 'clear', 'stop', 'nevermind'],
        'modify': ['change', 'modify', 'update', 'replace', 'instead of', 'swap'],
        'info': ['info', 'details', 'about', 'tell me', 'what is', 'price', 'cost'],
        'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'greetings'],
        'help': ['help', 'support', 'assist', 'what can you do', 'how to']
    }
    
    @classmethod
    def classify(cls, text: str) -> str:
        """Classify the intent of the user message"""
        text_lower = text.lower()
        
        # Count matches for each intent
        scores = {}
        for intent, keywords in cls.INTENTS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return 'unknown'
        
        # Return intent with highest score
        return max(scores, key=scores.get)
    
    @classmethod
    def needs_rag(cls, intent: str) -> bool:
        """Determine if RAG is needed for this intent"""
        return intent in ['menu', 'info', 'order']