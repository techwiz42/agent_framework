import os
from dotenv import load_dotenv
import chromadb

# user_id = a5836474-3834-4083-8037-9464be334af9

# Load environment variables from the specific path
load_dotenv('/etc/cyberiad/.env')

from app.core.config import settings

def dump_rag_collection(useer_id):
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    collection_name = f"u{user_id.replace('-', '')}"[:63]
    
    try:
        collection = client.get_collection(name=collection_name)
        
        print(f"Collection Name: {collection_name}")
        print(f"Total Documents: {collection.count()}")
        
        results = collection.get(
            include=["documents", "metadatas", "ids"]
        )
        
        for doc_id, doc, meta in zip(results['ids'], results['documents'], results['metadatas']):
            print(f"\n--- Document ID: {doc_id} ---")
            print(f"Metadata: {meta}")
            print(f"Content Preview (first 500 chars): {doc[:500]}")
    
    except Exception as e:
        print(f"Error dumping collection: {e}")

if __name__ == "__main__":
    #user_id = input("user_id? ")
    user_id = "a5836474-3834-4083-8037-9464be334af9"
    dump_rag_collection(user_id)
