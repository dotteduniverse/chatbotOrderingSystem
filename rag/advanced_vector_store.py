"""Advanced vector store with multiple embedding strategies"""

from typing import List, Dict, Any, Optional
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma, FAISS
from langchain.schema import Document
import numpy as np
import json

class AdvancedVectorStore:
    """Enhanced vector store with multiple retrieval strategies"""
    
    def __init__(self, persist_directory: str = "data/advanced_chroma_db"):
        self.persist_directory = persist_directory
        
        # Use a better embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.vectorstore = None
        self.faiss_index = None
        
    def create_enriched_documents(self, menu_loader) -> List[Document]:
        """Create enriched documents with metadata"""
        documents = []
        
        # Create documents for each menu item with enriched content
        for _, item in menu_loader.menu_df.iterrows():
            # Create multiple representations for better retrieval
            representations = [
                f"Item: {item['name']}. Price: ${item['price']:.2f}. Category: {item['category']}. Description: {item['description']}",
                f"Order {item['name']} for ${item['price']:.2f}. It's a {item['type']} from our {item['category']} section.",
                f"Looking for {item['name']}? It costs ${item['price']:.2f} and {item['description']}"
            ]
            
            for rep in representations:
                metadata = {
                    "name": item['name'],
                    "category": item['category'],
                    "type": item['type'],
                    "price": float(item['price']),
                    "tags": item['tags'],
                    "preparation_time": int(item['preparation_time'])
                }
                documents.append(Document(page_content=rep, metadata=metadata))
        
        return documents
    
    def build_vectorstore(self, menu_loader):
        """Build or load vector store"""
        import os
        
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            # Load existing
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print(f"Loaded vector store from {self.persist_directory}")
        else:
            # Create new
            documents = self.create_enriched_documents(menu_loader)
            
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            self.vectorstore.persist()
            print(f"Created vector store with {len(documents)} documents")
        
        return self.vectorstore
    
    def hybrid_search(self, query: str, k: int = 5, alpha: float = 0.5) -> List[Document]:
        """Hybrid search combining semantic and keyword matching"""
        # Semantic search
        semantic_results = self.vectorstore.similarity_search(query, k=k)
        
        # Keyword search on metadata
        keyword_results = self.vectorstore.similarity_search(
            query, 
            k=k,
            filter={"name": {"$regex": query, "$options": "i"}} if hasattr(self.vectorstore, 'filter') else None
        )
        
        # Combine results with weights
        combined = {}
        
        for doc in semantic_results:
            key = doc.metadata.get('name', '')
            if key not in combined:
                combined[key] = {'doc': doc, 'score': alpha}
            else:
                combined[key]['score'] += alpha
        
        for doc in keyword_results:
            key = doc.metadata.get('name', '')
            if key not in combined:
                combined[key] = {'doc': doc, 'score': 1 - alpha}
            else:
                combined[key]['score'] += 1 - alpha
        
        # Sort by score and return top k
        sorted_results = sorted(combined.values(), key=lambda x: x['score'], reverse=True)
        return [r['doc'] for r in sorted_results[:k]]
    
    def semantic_search_with_filters(self, query: str, category: Optional[str] = None, 
                                     max_price: Optional[float] = None, k: int = 5) -> List[Document]:
        """Search with metadata filters"""
        filter_dict = {}
        if category:
            filter_dict['category'] = category
        if max_price:
            filter_dict['price'] = {"$lte": max_price}
        
        if filter_dict:
            results = self.vectorstore.similarity_search(query, k=k, filter=filter_dict)
        else:
            results = self.vectorstore.similarity_search(query, k=k)
        
        return results
    
    def get_relevant_context(self, query: str, max_items: int = 3) -> str:
        """Get formatted context for RAG"""
        results = self.hybrid_search(query, k=max_items)
        
        context = "RELEVANT MENU ITEMS:\n\n"
        for doc in results:
            context += f"• {doc.page_content}\n"
            context += f"  - Price: ${doc.metadata.get('price', 0):.2f}\n"
            context += f"  - Category: {doc.metadata.get('category', 'N/A')}\n"
            if doc.metadata.get('tags'):
                context += f"  - Tags: {doc.metadata['tags']}\n"
            context += "\n"
        
        return context