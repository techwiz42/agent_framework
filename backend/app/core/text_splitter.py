import nltk
from typing import List, Dict, Any

class SemanticTextSplitter:
    def __init__(self, max_chunk_size=1000, min_chunk_size=100):
        nltk.download('punkt', quiet=True)
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def split_text(self, text: str, original_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Fallback if NLTK fails
        if not text:
            return []

        # Use paragraph splitting as a fallback
        try:
            paragraphs = nltk.tokenize.sent_tokenize(text)
        except Exception:
            paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            # If adding this paragraph would exceed max size, finalize current chunk
            if current_length + len(paragraph) > self.max_chunk_size:
                if current_chunk:
                    chunk_metadata = original_metadata.copy()
                    chunk_metadata['chunk_index'] = len(chunks)
                    chunk_metadata['start_paragraph'] = len(chunks) * len(paragraphs) // max(1, len(paragraphs))
                    
                    chunks.append({
                        'text': ' '.join(current_chunk),
                        'metadata': chunk_metadata
                    })
                    current_chunk = []
                    current_length = 0

            current_chunk.append(paragraph)
            current_length += len(paragraph)

        # Add final chunk if not empty
        if current_chunk:
            chunk_metadata = original_metadata.copy()
            chunk_metadata['chunk_index'] = len(chunks)
            chunk_metadata['start_paragraph'] = len(chunks) * len(paragraphs) // max(1, len(paragraphs))
            
            chunks.append({
                'text': ' '.join(current_chunk),
                'metadata': chunk_metadata
            })

        return chunks