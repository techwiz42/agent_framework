#!/usr/bin/env python3
import chromadb
import argparse
from typing import Dict, Any
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
persist_dir = '/etc/cyberiad/data/chroma_db'

def inspect_collections(persist_dir: str) -> Dict[str, Any]:
    client = chromadb.PersistentClient(path=persist_dir)
    collection_names = client.list_collections()
    inspection = {
        "raw_collections": [],
        "counts": {
            "total_collections": len(collection_names),
            "collections_with_metadata": 0,
            "collections_with_thread_id": 0,
            "collections_with_owner_id": 0,
            "collections_without_metadata": 0,
            "total_documents": 0
        }
    }
    for name in collection_names:
        collection = client.get_collection(name)
        count = collection.count()
        inspection["counts"]["total_documents"] += count
        documents = collection.get()
        collection_info = {
            "name": name,
            "metadata": collection.metadata,
            "count": count,
            "documents": documents["documents"],
            "metadatas": documents["metadatas"],
            "ids": documents["ids"],
            "embeddings": documents["embeddings"]
        }
        inspection["raw_collections"].append(collection_info)
        if collection.metadata:
            inspection["counts"]["collections_with_metadata"] += 1
            if "thread_id" in collection.metadata:
                inspection["counts"]["collections_with_thread_id"] += 1
            if "owner_id" in collection.metadata:
                inspection["counts"]["collections_with_owner_id"] += 1
        else:
            inspection["counts"]["collections_without_metadata"] += 1
    return inspection

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    results = inspect_collections(persist_dir)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
