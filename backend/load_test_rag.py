import os
import sys
import json
import asyncio
import logging
import random
import time
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

import numpy as np
import faker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class SafeJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle various non-serializable types
    Converts complex types to their string representations
    """
    def default(self, obj):
        # Handle UUID
        if isinstance(obj, UUID):
            return str(obj)
        
        # Handle numpy types
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        
        # Handle numpy arrays
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        
        # Fallback to string representation for other types
        try:
            return str(obj)
        except Exception:
            return repr(obj)

class RAGLoadTester:
    def __init__(
        self, 
        rag_storage_service, 
        rag_query_service,
        database_url: str = None,
        config: Dict[str, Any] = None
    ):
        """
        Initialize RAG load tester with configurable parameters
        """
        self.rag_storage_service = rag_storage_service
        self.rag_query_service = rag_query_service
        
        # Default configuration
        self.config = {
            'num_users': 10,               # Number of concurrent users
            'documents_per_user': 50,      # Number of documents to generate per user
            'document_size_range': (500, 2000),  # Range of document sizes (words)
            'query_per_user': 10,          # Number of queries per user
            'query_concurrency': 5,        # Concurrent queries per user
            'query_types': [
                'technical',               # Technical/domain-specific queries
                'general',                 # General knowledge queries
                'specific'                 # Very precise queries
            ],
            'debug_diagnostics': True     # Enable additional diagnostic logging
        }
        
        # Override defaults with provided config
        if config:
            self.config.update(config)
        
        # Setup faker for generating realistic text
        self.faker = faker.Faker()
        
        # Store generated documents for each user
        self.user_documents = {}
        
        # Tracking variables
        self.test_summary = {
            'collections': {
                'created': 0,
                'documents_indexed': 0,
                'total_chunks': 0
            },
            'queries': {
                'total': 0,
                'with_results': 0,
                'without_results': 0,
                'errors': 0
            },
            'performance': {
                'total_query_time': 0,
                'avg_query_time': 0,
                'max_query_time': 0
            },
            'diagnostics': {
                'collection_info': [],
                'query_details': []
            }
        }

    def generate_document(self, document_type: str = 'technical') -> str:
        """
        Generate a synthetic document based on document type
        
        :param document_type: Type of document to generate
        :return: Generated document text
        """
        document_length = random.randint(*self.config['document_size_range'])
        
        if document_type == 'technical':
            # Technical/domain-specific document
            title = self.faker.catch_phrase()
            sections = [
                self.faker.paragraph(nb_sentences=5) 
                for _ in range(random.randint(3, 7))
            ]
            return f"# {title}\n\n" + "\n\n".join(sections)
        
        elif document_type == 'general':
            # General knowledge document
            return self.faker.text(max_nb_chars=document_length)
        
        else:  # specific
            # Very precise, structured document
            return "\n".join([
                f"### {self.faker.sentence()}"
                for _ in range(random.randint(5, 15))
            ])

    async def generate_and_ingest_data(self) -> List[UUID]:
        """
        Generate and ingest test data for multiple users
        
        :return: List of user IDs used in the test
        """
        user_ids = []
        
        for _ in range(self.config['num_users']):
            # Generate unique user ID
            owner_id = uuid4()
            user_ids.append(owner_id)
            
            # Initialize collection for user
            collection = await self.rag_storage_service.initialize_collection(owner_id)
            self.test_summary['collections']['created'] += 1
            
            # Generate and ingest documents
            documents = [
                self.generate_document(
                    random.choice(self.config['query_types'])
                ) 
                for _ in range(self.config['documents_per_user'])
            ]
            
            # Store documents for this user to help with query generation
            self.user_documents[owner_id] = documents
            
            # Add diagnostic information about collection
            if self.config['debug_diagnostics']:
                collection_info = {
                    'owner_id': str(owner_id),
                    'document_count': len(documents)
                }
                try:
                    # Try to get collection count if possible
                    collection_info['collection_count'] = collection.count()
                except Exception as e:
                    collection_info['collection_count_error'] = str(e)
                
                self.test_summary['diagnostics']['collection_info'].append(collection_info)
            
            # Ingest documents
            try:
                ingestion_result = await self.rag_storage_service.add_texts(
                    owner_id=owner_id,
                    texts=documents,
                    metadatas=[
                        {
                            'source_type': 'test_document',
                            'generation_timestamp': str(time.time()),
                            'document_type': 'synthetic_load_test'
                        } 
                        for _ in documents
                    ]
                )
                
                # Update indexing summary
                self.test_summary['collections']['documents_indexed'] += len(documents)
                self.test_summary['collections']['total_chunks'] += len(ingestion_result)
                
                logger.info(f"Ingested {len(documents)} documents for user {owner_id}")
            except Exception as e:
                logger.error(f"Failed to ingest documents for user {owner_id}: {e}")
                self.test_summary['collections']['documents_indexed'] += len(documents)
                self.test_summary['collections']['total_chunks'] += 0
        
        return user_ids

    def generate_query(self, document_type: str, documents: List[str]) -> str:
        """
        Generate a query more likely to match the ingested documents
        
        :param document_type: Type of document to query
        :param documents: List of documents to generate query from
        :return: Generated query string
        """
        if not documents:
            # Fallback to previous query generation if no documents
            return self.faker.sentence()
        
        # Choose a random document to extract a query-like phrase
        sample_doc = random.choice(documents)
        
        # Use more precise query generation based on document type
        if document_type == 'technical':
            # Extract key phrases or use a specific sentence
            words = sample_doc.split()
            # Prefer a meaningful phrase
            meaningful_phrases = [
                ' '.join(words[i:i+3]) 
                for i in range(len(words)-2)
                if not all(word.islower() for word in words[i:i+3])
            ]
            return random.choice(meaningful_phrases) if meaningful_phrases else self.faker.catch_phrase()
        
        elif document_type == 'general':
            # Split into sentences and choose a longer, more specific one
            sentences = [s for s in sample_doc.split('. ') if len(s.split()) > 5]
            return random.choice(sentences) if sentences else self.faker.sentence()
        
        else:  # specific
            # Use a random longer subsection
            sections = [s for s in sample_doc.split('\n### ') if len(s) > 30]
            return random.choice(sections)[:100] if sections else self.faker.word()

    async def run_user_queries(self, owner_id: UUID):
        """
        Simulate queries for a single user
        
        :param owner_id: User ID to run queries for
        """
        query_results = []
        query_times = []
        
        # Get documents for this user
        user_docs = self.user_documents.get(owner_id, [])
        
        for _ in range(self.config['query_per_user']):
            query_type = random.choice(self.config['query_types'])
            query = self.generate_query(query_type, user_docs)
            
            logger.debug(f"Generated query for user {owner_id}: {query}")
            
            # Increment total queries
            self.test_summary['queries']['total'] += 1
            
            start_time = time.time()
            try:
                results = await self.rag_query_service.query_knowledge(
                    owner_id=owner_id,
                    query_text=query,
                    k=5  # Configurable number of results
                )
                
                end_time = time.time()
                query_time = end_time - start_time
                
                result_count = len(results.get('documents', []))
                logger.debug(f"Query results for user {owner_id}: {result_count} documents")
                
                # Store query details for diagnostics
                if self.config['debug_diagnostics']:
                    query_detail = {
                        'owner_id': str(owner_id),
                        'query': query,
                        'query_type': query_type,
                        'result_count': result_count,
                        'query_time': query_time
                    }
                    self.test_summary['diagnostics']['query_details'].append(query_detail)
                
                # Update query result summary
                if result_count > 0:
                    self.test_summary['queries']['with_results'] += 1
                    query_times.append(query_time)
                else:
                    self.test_summary['queries']['without_results'] += 1
                
                query_results.append({
                    'query': query,
                    'type': query_type,
                    'result_count': result_count,
                    'query_time': query_time
                })
                
            except Exception as e:
                logger.error(f"Query failed for user {owner_id}: {e}")
                self.test_summary['queries']['errors'] += 1
                
                # Store error details for diagnostics
                if self.config['debug_diagnostics']:
                    query_detail = {
                        'owner_id': str(owner_id),
                        'query': query,
                        'error': str(e)
                    }
                    self.test_summary['diagnostics']['query_details'].append(query_detail)
        
        # Update performance metrics
        if query_times:
            self.test_summary['performance']['total_query_time'] += sum(query_times)
            self.test_summary['performance']['avg_query_time'] = np.mean(query_times)
            self.test_summary['performance']['max_query_time'] = np.max(query_times)
        
        return {
            'owner_id': str(owner_id),  # Ensure string representation
            'query_results': query_results
        }

    async def run_load_test(self) -> Dict[str, Any]:
        """
        Run the complete load test
        
        :return: Comprehensive test results
        """
        logger.info("Starting RAG Load Test")
        start_time = time.time()
        
        # Generate and ingest test data
        user_ids = await self.generate_and_ingest_data()
        
        # Run queries for each user
        user_query_results = []
        for owner_id in user_ids:
            user_results = await self.run_user_queries(owner_id)
            user_query_results.append(user_results)
        
        end_time = time.time()
        
        # Finalize test summary
        self.test_summary['total_test_time'] = end_time - start_time
        self.test_summary['total_users'] = len(user_ids)
        
        logger.info("Load Test Completed")
        logger.info(f"Test Summary: {json.dumps(self.test_summary, indent=2)}")
        
        return {
            'summary': self.test_summary,
            'user_query_results': user_query_results
        }

    def export_results(self, results: Dict[str, Any], output_file: str = 'rag_load_test_results.json'):
        """
        Export test results to a JSON file
        
        :param results: Test results dictionary
        :param output_file: Output file path
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, cls=SafeJSONEncoder)
            
            logger.info(f"Results exported to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting results: {e}")

def setup_project_path():
    """
    Add project root to Python path to enable imports
    Works whether script is run from load_test directory or project root
    """
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try multiple potential project root paths
    possible_roots = [
        current_dir,  # Current directory
        os.path.dirname(current_dir),  # Parent directory
        os.path.dirname(os.path.dirname(current_dir))  # Grandparent directory
    ]
    
    for root in possible_roots:
        # Check for common project markers
        if os.path.exists(os.path.join(root, 'pyproject.toml')) or \
           os.path.exists(os.path.join(root, 'setup.py')) or \
           os.path.exists(os.path.join(root, 'requirements.txt')):
            sys.path.insert(0, root)
            print(f"Added {root} to Python path")
            return
    
    raise RuntimeError("Could not find project root directory")

async def main():
    # Setup project path before imports
    setup_project_path()

    try:
        # Dynamic imports to ensure path is set up first
        from app.services.rag.storage_service import rag_storage_service
        from app.services.rag.query_service import rag_query_service
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error(f"Current Python path: {sys.path}")
        raise
    
    load_tester = RAGLoadTester(
        rag_storage_service=rag_storage_service,
        rag_query_service=rag_query_service,
        database_url='postgresql+asyncpg://user:pass@localhost/testdb',
        config={
            'num_users': 20,
            'documents_per_user': 100,
            'query_per_user': 15
        }
    )
    
    results = await load_tester.run_load_test()
    load_tester.export_results(results)

if __name__ == '__main__':
    asyncio.run(main())
