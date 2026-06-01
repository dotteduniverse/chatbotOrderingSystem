"""Vector database management for menu items"""

from typing import List, Dict, Any
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
import os

class MenuVectorStore:
    """Manage vector embeddings for menu items"""
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",  # Small, efficient model
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': False}
        )
        self.vectorstore = None
    
    def create_documents_from_menu(self, menu_data: Dict[str, Any]) -> List[Document]:
        """Convert menu items to LangChain Documents"""
        documents = []
        
        # Process beverages
        for category, items in menu_data.get("beverages", {}).items():
            for item in items:
                content = f"""
                Item: {item['name']}
                Category: {category}
                Type: Beverage
                Price: ${item['price']}
                Variants: {', '.join(item.get('variants', ['regular']))}
                Description: {item.get('description', f'Delicious {item["name"].lower()}')}
                """
                
                metadata = {
                    "name": item['name'],
                    "category": category,
                    "type": "beverage",
                    "price": item['price']
                }
                documents.append(Document(page_content=content, metadata=metadata))
        
        # Process snacks
        for item in menu_data.get("snacks", []):
            content = f"""
            Item: {item['name']}
            Type: Snack
            Price: ${item['price']}
            Description: {item.get('description', f'Delicious {item["name"].lower()}')}
            """
            
            metadata = {
                "name": item['name'],
                "type": "snack",
                "price": item['price']
            }
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def build_vectorstore(self, menu_loader):
        """Build or load vector store from menu"""
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            # Load existing vector store
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print(f"Loaded existing vector store from {self.persist_directory}")
        else:
            # Create new vector store
            documents = self.create_documents_from_menu(menu_loader.menu_data)
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            texts = text_splitter.split_documents(documents)
            
            self.vectorstore = Chroma.from_documents(
                documents=texts,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            self.vectorstore.persist()
            print(f"Created new vector store with {len(texts)} chunks")
        
        return self.vectorstore
    
    def search_menu(self, query: str, k: int = 3) -> List[Document]:
        """Search for relevant menu items"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Call build_vectorstore first.")
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def get_relevant_context(self, query: str) -> str:
        """Get relevant menu context as string for LLM prompt"""
        results = self.search_menu(query)
        context = "Relevant menu items:\n\n"
        for doc in results:
            context += f"• {doc.page_content.strip()}\n\n"
        return context