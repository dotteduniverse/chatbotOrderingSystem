"""Advanced RAG pipeline with multiple strategies - Fixed imports"""

from typing import List, Dict, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from .advanced_vector_store import AdvancedVectorStore
from .conversation_memory import ConversationMemory
from backend.advanced_menu_loader import AdvancedMenuLoader

class AdvancedRAGPipeline:
    """Complete RAG pipeline with advanced features"""
    
    def __init__(self, llm, menu_loader: AdvancedMenuLoader):
        self.llm = llm
        self.menu_loader = menu_loader
        self.vector_store = AdvancedVectorStore()
        self.vector_store.build_vectorstore(menu_loader)
        self.conversation_memory = ConversationMemory()
        
        # Create retriever
        self.retriever = self.vector_store.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
    
    def format_docs(self, docs):
        """Format retrieved documents"""
        return "\n\n".join(doc.page_content for doc in docs)
    
    def get_context(self, question: str) -> str:
        """Get relevant context using hybrid search"""
        try:
            relevant_docs = self.vector_store.hybrid_search(question, k=3)
            return self.format_docs(relevant_docs)
        except:
            # Fallback to simple search
            relevant_docs = self.vector_store.vectorstore.similarity_search(question, k=3)
            return self.format_docs(relevant_docs)
    
    def get_personalized_response(self, question: str, order_context: Dict = None) -> str:
        """Generate personalized response using all available context"""
        
        # Get menu context
        menu_context = self.get_context(question)
        
        # Get conversation history
        history_context = self.conversation_memory.format_conversation_context()
        
        # Get user preferences
        preferences = self.conversation_memory.get_top_preferences(2)
        pref_text = ", ".join(preferences) if preferences else "None detected yet"
        
        # Build the prompt
        prompt = f"""You are CafeBot, an intelligent ordering assistant for a cozy cafe.

MENU CONTEXT:
{menu_context}

CONVERSATION HISTORY:
{history_context}

USER PREFERENCES: {pref_text}

CUSTOMER QUESTION: {question}

Please provide a helpful response. If this is an order, acknowledge each item. If asking about the menu, provide relevant details. If you detect preferences, make personalized suggestions.

Response:"""
        
        # Get response from LLM
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            response_text = f"I encountered an error: {str(e)}. Please try again."
        
        # Store in memory
        self.conversation_memory.add_interaction(question, response_text)
        
        return response_text
    
    def process_order_intent(self, question: str) -> Dict[str, Any]:
        """Process order-specific intents with extraction"""
        from utils.text_processor import TextProcessor
        
        # Extract potential order items
        extracted = TextProcessor.extract_quantities(question)
        
        # Match with menu
        order_items = []
        for item_name, quantity in extracted:
            menu_item = self.menu_loader.get_item_details(item_name)
            if menu_item:
                order_items.append({
                    'name': menu_item['name'],
                    'quantity': quantity,
                    'price': menu_item['price'],
                    'preparation_time': menu_item.get('preparation_time', 5)
                })
        
        return {
            'has_order': len(order_items) > 0,
            'items': order_items,
            'total': sum(item['quantity'] * item['price'] for item in order_items)
        }
    
    def get_recommendations(self, context: str) -> List[Dict]:
        """Get personalized recommendations"""
        # Extract preferences from context
        preferences = []
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['spicy', 'spice', 'hot']):
            preferences.append('spicy')
        if any(word in context_lower for word in ['sweet', 'sugar', 'honey']):
            preferences.append('sweet')
        if any(word in context_lower for word in ['healthy', 'organic', 'green']):
            preferences.append('healthy')
        if any(word in context_lower for word in ['quick', 'fast', 'urgent']):
            preferences.append('quick')
        
        if preferences:
            recommendations = self.menu_loader.get_recommendations(preferences)
        else:
            # Default popular items (first 3 from menu)
            recommendations = self.menu_loader.get_recommendations(['popular'], limit=3)
            if not recommendations:
                # Fallback: return first 3 items from menu
                recommendations = self.menu_loader.menu_df.head(3).to_dict('records')
        
        return recommendations
    
    def generate_order_summary(self, order_items: List[Dict]) -> str:
        """Generate a beautiful order summary"""
        from utils.response_formatter import ResponseFormatter
        return ResponseFormatter.format_order_summary(order_items)
    
    def reset_conversation(self):
        """Reset conversation memory"""
        self.conversation_memory.clear()