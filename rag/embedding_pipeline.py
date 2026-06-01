"""Complete RAG pipeline for intelligent menu queries"""

from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from .vector_store import MenuVectorStore

class RAGPipeline:
    """End-to-end RAG pipeline for menu-based Q&A"""
    
    def __init__(self, llm, menu_loader):
        self.llm = llm
        self.menu_loader = menu_loader
        self.vector_store = MenuVectorStore()
        self.vector_store.build_vectorstore(menu_loader)
        self.retriever = self.vector_store.vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )
        
        # Create RAG prompt
        self.prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant for a small cafe. Your job is to help customers order from the menu.

Context from our menu:
{context}

Customer question: {question}

Guidelines:
1. Be friendly and conversational
2. Suggest items based on what the customer likes
3. Ask clarifying questions about variants (hot/iced) and quantities
4. Mention prices when appropriate
5. If asked about items not on the menu, politely say we don't have it and suggest alternatives

Respond helpfully:
""")
    
    def format_docs(self, docs):
        """Format retrieved documents for prompt"""
        return "\n\n".join(doc.page_content for doc in docs)
    
    def get_chain(self):
        """Create the RAG chain"""
        chain = (
            {
                "context": self.retriever | self.format_docs,
                "question": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()  # This ensures we get a string output
        )
        return chain
    
    def query(self, user_input: str) -> str:
        """Process a user query through the RAG pipeline and return string"""
        chain = self.get_chain()
        response = chain.invoke(user_input)
        
        # Ensure we return a string
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    
    def get_menu_suggestions(self, preferences: str) -> List[Dict[str, Any]]:
        """Get menu suggestions based on user preferences"""
        # Search for relevant items
        relevant_docs = self.vector_store.search_menu(preferences, k=5)
        
        suggestions = []
        for doc in relevant_docs:
            suggestions.append({
                "name": doc.metadata.get("name", "Unknown"),
                "price": doc.metadata.get("price", 0),
                "relevance_score": "high"
            })
        
        return suggestions