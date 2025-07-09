#!/usr/bin/env python3
"""
RAG System with DeepSeek Integration
Retrieval-Augmented Generation for legal document search and context
"""

import os
import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import numpy as np
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    import requests
    from sqlalchemy import create_engine, text
    from sqlalchemy.ext.asyncio import create_async_engine
    import asyncpg
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install: pip install faiss-cpu sentence-transformers requests sqlalchemy asyncpg")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeepSeekRAGSystem:
    """RAG System with DeepSeek integration for legal document processing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_config()
        self.sentence_model = None
        self.faiss_index = None
        self.documents = []
        self.db_engine = None
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.deepseek_base_url = 'https://api.deepseek.com/v1'
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'embedding_model': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
            'chunk_size': int(os.getenv('CHUNK_SIZE', 500)),
            'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', 50)),
            'top_k': int(os.getenv('RAG_TOP_K', 5)),
            'similarity_threshold': float(os.getenv('SIMILARITY_THRESHOLD', 0.7)),
            'db_url': os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/legalbot'),
            'data_dir': os.getenv('DATA_DIR', './data'),
            'index_dir': os.getenv('INDEX_DIR', './indexes')
        }
    
    async def initialize(self):
        """Initialize the RAG system"""
        try:
            # Initialize embedding model
            logger.info("Loading sentence transformer model...")
            self.sentence_model = SentenceTransformer(self.config['embedding_model'])
            
            # Initialize database connection
            self.db_engine = create_async_engine(self.config['db_url'])
            
            # Create directories
            os.makedirs(self.config['data_dir'], exist_ok=True)
            os.makedirs(self.config['index_dir'], exist_ok=True)
            
            # Load or create FAISS index
            await self._load_or_create_index()
            
            logger.info("RAG system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    async def _load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        index_path = os.path.join(self.config['index_dir'], 'legal_documents.index')
        documents_path = os.path.join(self.config['index_dir'], 'documents.json')
        
        if os.path.exists(index_path) and os.path.exists(documents_path):
            # Load existing index
            try:
                self.faiss_index = faiss.read_index(index_path)
                with open(documents_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded existing index with {len(self.documents)} documents")
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
                await self._create_new_index()
        else:
            # Create new index
            await self._create_new_index()
    
    async def _create_new_index(self):
        """Create new FAISS index from documents"""
        logger.info("Creating new FAISS index...")
        
        # Load documents from database
        documents = await self._load_documents_from_db()
        
        if not documents:
            logger.warning("No documents found in database")
            # Create empty index
            embedding_dim = self.sentence_model.get_sentence_embedding_dimension()
            self.faiss_index = faiss.IndexFlatIP(embedding_dim)
            self.documents = []
            return
        
        # Process documents and create embeddings
        processed_docs = []
        embeddings = []
        
        for doc in documents:
            chunks = self._chunk_document(doc['content'])
            
            for i, chunk in enumerate(chunks):
                processed_doc = {
                    'id': f"{doc['id']}_{i}",
                    'original_id': doc['id'],
                    'title': doc['title'],
                    'content': chunk,
                    'document_type': doc['document_type'],
                    'category': doc['category'],
                    'metadata': doc.get('metadata', {})
                }
                processed_docs.append(processed_doc)
                
                # Generate embedding
                embedding = self.sentence_model.encode(chunk)
                embeddings.append(embedding)
        
        # Create FAISS index
        if embeddings:
            embeddings_array = np.array(embeddings).astype('float32')
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)
            
            # Create index
            embedding_dim = embeddings_array.shape[1]
            self.faiss_index = faiss.IndexFlatIP(embedding_dim)
            self.faiss_index.add(embeddings_array)
            self.documents = processed_docs
            
            # Save index
            await self._save_index()
            
            logger.info(f"Created index with {len(processed_docs)} document chunks")
        else:
            # Create empty index
            embedding_dim = self.sentence_model.get_sentence_embedding_dimension()
            self.faiss_index = faiss.IndexFlatIP(embedding_dim)
            self.documents = []
    
    async def _load_documents_from_db(self) -> List[Dict[str, Any]]:
        """Load documents from database"""
        try:
            async with self.db_engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT id, title, content, document_type, category, metadata
                    FROM legalbot.knowledge_base
                    WHERE active = true
                    ORDER BY created_at DESC
                """))
                
                return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to load documents from database: {e}")
            return []
    
    def _chunk_document(self, content: str) -> List[str]:
        """Split document into chunks"""
        chunk_size = self.config['chunk_size']
        chunk_overlap = self.config['chunk_overlap']
        
        # Simple chunking by sentences
        sentences = content.split('.')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) + 1 > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    
                    # Handle overlap
                    if chunk_overlap > 0:
                        words = current_chunk.split()
                        overlap_words = words[-chunk_overlap:]
                        current_chunk = " ".join(overlap_words) + " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _save_index(self):
        """Save FAISS index and documents to disk"""
        try:
            index_path = os.path.join(self.config['index_dir'], 'legal_documents.index')
            documents_path = os.path.join(self.config['index_dir'], 'documents.json')
            
            faiss.write_index(self.faiss_index, index_path)
            
            with open(documents_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
            logger.info("Index saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    async def search_documents(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search for relevant documents using semantic similarity"""
        if not self.faiss_index or not self.documents:
            return []
        
        try:
            top_k = top_k or self.config['top_k']
            
            # Generate query embedding
            query_embedding = self.sentence_model.encode([query])
            query_embedding = query_embedding.astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Search in FAISS index
            scores, indices = self.faiss_index.search(query_embedding, top_k)
            
            # Filter by similarity threshold
            threshold = self.config['similarity_threshold']
            results = []
            
            for score, idx in zip(scores[0], indices[0]):
                if score >= threshold and idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc['similarity_score'] = float(score)
                    results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def generate_response_with_rag(self, query: str, context: str = "") -> Dict[str, Any]:
        """Generate response using RAG with DeepSeek"""
        try:
            # Search for relevant documents
            relevant_docs = await self.search_documents(query)
            
            # Build context from retrieved documents
            retrieved_context = ""
            if relevant_docs:
                retrieved_context = "\n\n".join([
                    f"Document: {doc['title']}\nContent: {doc['content']}"
                    for doc in relevant_docs[:3]  # Use top 3 documents
                ])
            
            # Build prompt
            prompt = self._build_rag_prompt(query, context, retrieved_context)
            
            # Generate response with DeepSeek
            response = await self._call_deepseek_api(prompt)
            
            return {
                'response': response,
                'retrieved_documents': relevant_docs,
                'context_used': retrieved_context
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return {
                'response': "I apologize, but I encountered an error while processing your request.",
                'retrieved_documents': [],
                'context_used': "",
                'error': str(e)
            }
    
    def _build_rag_prompt(self, query: str, context: str, retrieved_context: str) -> str:
        """Build prompt for RAG response generation"""
        prompt = f"""You are a legal AI assistant. Use the following context to answer the user's question accurately and helpfully.

Retrieved Legal Documents:
{retrieved_context}

Conversation Context:
{context}

User Question: {query}

Please provide a comprehensive answer based on the retrieved documents. If the documents don't contain enough information to answer the question, please state that clearly and provide general guidance where appropriate.

Response:"""
        
        return prompt
    
    async def _call_deepseek_api(self, prompt: str) -> str:
        """Call DeepSeek API to generate response"""
        if not self.deepseek_api_key:
            raise ValueError("DeepSeek API key not provided")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.deepseek_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 2000,
                'temperature': 0.7
            }
            
            response = requests.post(
                f'{self.deepseek_base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            raise
    
    async def add_document(self, title: str, content: str, document_type: str = "legal", 
                          category: str = "general", metadata: Dict[str, Any] = None) -> bool:
        """Add a new document to the knowledge base"""
        try:
            # Add to database
            async with self.db_engine.begin() as conn:
                await conn.execute(text("""
                    INSERT INTO legalbot.knowledge_base 
                    (title, content, document_type, category, metadata)
                    VALUES (:title, :content, :document_type, :category, :metadata)
                """), {
                    'title': title,
                    'content': content,
                    'document_type': document_type,
                    'category': category,
                    'metadata': json.dumps(metadata or {})
                })
            
            # Rebuild index
            await self._create_new_index()
            
            logger.info(f"Added document: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    async def update_knowledge_base(self):
        """Update knowledge base from database"""
        try:
            await self._create_new_index()
            logger.info("Knowledge base updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update knowledge base: {e}")
            return False

async def main():
    """Main function for testing"""
    rag_system = DeepSeekRAGSystem()
    await rag_system.initialize()
    
    # Test search
    query = "What are the requirements for a valid contract?"
    results = await rag_system.search_documents(query)
    
    print(f"Search results for: {query}")
    for result in results:
        print(f"- {result['title']} (Score: {result['similarity_score']:.3f})")
    
    # Test RAG response
    response = await rag_system.generate_response_with_rag(query)
    print(f"\nRAG Response: {response['response']}")

if __name__ == "__main__":
    asyncio.run(main())
