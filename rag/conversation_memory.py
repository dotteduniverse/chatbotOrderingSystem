"""Advanced conversation memory management"""

from typing import List, Dict, Any
from collections import deque
import json
from datetime import datetime

class ConversationMemory:
    """Manage conversation history with context window"""
    
    def __init__(self, max_history: int = 10):
        self.history = deque(maxlen=max_history)
        self.user_preferences = {}
        self.current_order_context = {}
        
    def add_interaction(self, user_input: str, bot_response: str, metadata: Dict = None):
        """Add an interaction to memory"""
        self.history.append({
            'user': user_input,
            'bot': bot_response,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        
        # Extract preferences
        self._extract_preferences(user_input)
    
    def _extract_preferences(self, text: str):
        """Extract user preferences from conversation"""
        text_lower = text.lower()
        
        preference_keywords = {
            'spicy': ['spicy', 'hot', 'masala'],
            'sweet': ['sweet', 'sugar', 'honey'],
            'healthy': ['healthy', 'low sugar', 'organic', 'green'],
            'quick': ['quick', 'fast', 'urgent'],
            'cold': ['cold', 'iced', 'chilled'],
            'hot': ['hot', 'warm', 'steaming']
        }
        
        for pref, keywords in preference_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                self.user_preferences[pref] = self.user_preferences.get(pref, 0) + 1
    
    def get_context_window(self, n_last: int = 5) -> List[Dict]:
        """Get last n interactions"""
        return list(self.history)[-n_last:]
    
    def get_user_preferences(self) -> Dict[str, int]:
        """Get extracted user preferences"""
        return self.user_preferences
    
    def get_top_preferences(self, n: int = 2) -> List[str]:
        """Get top user preferences"""
        sorted_prefs = sorted(self.user_preferences.items(), key=lambda x: x[1], reverse=True)
        return [pref for pref, _ in sorted_prefs[:n]]
    
    def format_conversation_context(self) -> str:
        """Format conversation history for LLM prompt"""
        if not self.history:
            return "No previous conversation."
        
        context = "CONVERSATION HISTORY:\n"
        for i, interaction in enumerate(list(self.history)[-5:], 1):
            context += f"{i}. Customer: {interaction['user']}\n"
            context += f"   Assistant: {interaction['bot']}\n\n"
        
        if self.user_preferences:
            context += "USER PREFERENCES DETECTED:\n"
            for pref, count in self.user_preferences.items():
                context += f"- {pref} (mentioned {count} times)\n"
        
        return context
    
    def clear(self):
        """Clear conversation memory"""
        self.history.clear()
        self.user_preferences.clear()
        self.current_order_context.clear()
    
    def save_to_file(self, filepath: str = "data/conversation_memory.json"):
        """Save memory to file"""
        data = {
            'history': list(self.history),
            'preferences': self.user_preferences,
            'timestamp': datetime.now().isoformat()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str = "data/conversation_memory.json"):
        """Load memory from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.history = deque(data['history'], maxlen=self.history.maxlen)
                self.user_preferences = data['preferences']
        except FileNotFoundError:
            pass