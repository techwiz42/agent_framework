import os
import logging
import tempfile
import PyPDF2
import docx
import pandas as pd
import json
import xml.etree.ElementTree as ET
import xmltodict

logger = logging.getLogger(__name__)

class FileExtractionService:
    def __init__(self):
        # Comprehensive list of supported MIME types
        self.SUPPORTED_MIME_TYPES = [
            # Document types
            'text/plain',
            'text/csv',
            'application/pdf',
            'text/markdown',
            'text/html',
            'application/json',
            'application/xml',
            
            # Microsoft Office
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
            'application/msword',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/vnd.ms-excel',
            
            # Google Workspace
            'application/vnd.google-apps.document',
            'application/vnd.google-apps.spreadsheet',
            'application/vnd.google-apps.presentation',
            'application/vnd.google-apps.form',
            
            # Programming Languages
            'text/plain',
            'text/x-python',
            'text/x-java',
            'text/x-c++',
            'text/x-c',
            'text/x-csharp',
            'text/x-javascript',
            'text/x-typescript',
            'application/typescript',
            'application/javascript',
            'text/x-ruby',
            'text/x-php',
            'text/x-go',
            'text/x-rust',
            'text/x-swift',
            'text/x-kotlin',
            'text/x-scala',
            'text/x-perl',
            'text/x-haskell',
            'text/x-lua',
            'text/x-shell',
            'text/x-sql',
            
            # Additional source code types
            'application/x-python',
            'application/x-java',
            'application/x-php',
            'application/octet-stream',
            'application/x-shellscript'
        ]
        
        # File extensions for programming languages
        self.PROGRAMMING_LANGUAGE_EXTENSIONS = {
            'python': ['.py', '.pyw'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cxx', '.cc', '.c++', '.h', '.hpp'],
            'c': ['.c', '.h'],
            'csharp': ['.cs'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'ruby': ['.rb'],
            'php': ['.php'],
            'go': ['.go'],
            'rust': ['.rs'],
            'swift': ['.swift'],
            'kotlin': ['.kt', '.kts'],
            'scala': ['.scala'],
            'perl': ['.pl', '.pm'],
            'haskell': ['.hs', '.lhs'],
            'lua': ['.lua'],
            'shell': ['.sh', '.bash', '.zsh'],
            'sql': ['.sql']
        }

    async def extract_text_for_type(
        self, 
        file_path: str, 
        mime_type: str, 
        preserve_formatting: bool = False
    ) -> str:
        """Extract text content based on file mime type."""
        try:
            # Check if we should try to determine a more specific MIME type
            if mime_type == "application/octet-stream":
                # Try to get a better MIME type based on extension
                better_mime_type = self.get_mime_type_for_extension(file_path)
                if better_mime_type:
                    logger.info(f"Refined MIME type from octet-stream to {better_mime_type} based on extension")
                    mime_type = better_mime_type

            # PDF extraction
            if mime_type == "application/pdf":
                return await self._extract_text_from_pdf(file_path, preserve_formatting)
    
            # Word document extraction
            elif mime_type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                "application/msword"
            ]:
                return await self._extract_text_from_word(file_path, preserve_formatting)
    
            # Excel extraction
            elif mime_type in [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                "application/vnd.ms-excel"
            ]:
                return await self._extract_text_from_excel(file_path, preserve_formatting)
    
            # JSON extraction
            elif mime_type == "application/json":
                return await self._extract_text_from_json(file_path, preserve_formatting)
    
            # XML extraction
            elif mime_type == "application/xml":
                return await self._extract_text_from_xml(file_path, preserve_formatting)
        
            # Google Docs/Sheets extraction
            elif mime_type == "application/vnd.google-apps.document":
                # Google Drive API should have already exported this as text/plain
                return await self._extract_text_from_text(file_path, preserve_formatting)
            
            elif mime_type == "application/vnd.google-apps.spreadsheet":
                # Google Drive API should have already exported this as text/csv
                return await self._extract_text_from_text(file_path, preserve_formatting)
    
            # Text-based and source code extractions
            elif (mime_type.startswith('text/') or 
                  mime_type.startswith('text/x-') or 
                  mime_type.startswith('application/x-') or
                  mime_type == 'application/typescript' or
                  mime_type == 'application/javascript'):
                return await self._extract_text_from_text(file_path, preserve_formatting)
        
            # For octet-stream or unhandled types, try as text
            elif mime_type == "application/octet-stream":
                logger.info(f"Attempting to extract text from octet-stream file: {file_path}")
                try:
                    return await self._extract_text_from_text(file_path, preserve_formatting)
                except Exception as binary_e:
                    logger.warning(f"Could not extract text from octet-stream file {file_path}: {str(binary_e)}")
                    return ""
        
            else:
                logger.warning(f"Unsupported mime type for text extraction: {mime_type}")
                return ""
    
        except Exception as e:
            logger.error(f"Error extracting text from file {file_path}: {str(e)}")
            return ""

    async def _extract_text_from_text(self, file_path: str, preserve_formatting: bool = False) -> str:
        """Extract text from plain text and source code files."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as text_file:
                text = text_file.read()
                if not preserve_formatting:
                    # Remove extra whitespace and normalize line breaks
                    text = ' '.join(text.split())
                return text
        except Exception as e:
            logger.error(f"Error extracting text from text file {file_path}: {str(e)}")
            return ""

    async def _extract_text_from_pdf(self, file_path: str, preserve_formatting: bool = False) -> str:
        """Extract text from a PDF."""
        try:
            pdf_reader = PyPDF2.PdfReader(file_path)
            full_text = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    full_text.append(text)
            
            text = '\n\n'.join(full_text)
            if not preserve_formatting:
                # Remove extra whitespace and normalize line breaks
                text = ' '.join(text.split())
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return ""

    async def _extract_text_from_word(self, file_path: str, preserve_formatting: bool = False) -> str:
        """Extract text from a Word (.docx) file."""
        try:
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            text = '\n\n'.join(full_text)
            if not preserve_formatting:
                # Remove extra whitespace and normalize line breaks
                text = ' '.join(text.split())
            return text
        except Exception as e:
            logger.error(f"Error extracting text from Word file {file_path}: {str(e)}")
            return ""

    async def _extract_text_from_excel(self, file_path: str, preserve_formatting: bool = False) -> str:
        """Extract text from an Excel file."""
        try:
            df = pd.read_excel(file_path, sheet_name=None)
            text_content = []
            for sheet_name, sheet_data in df.items():
                if preserve_formatting:
                    text_content.append(f"--- Sheet: {sheet_name} ---")
                    text_content.append(sheet_data.to_string(index=False, header=True))
                else:
                    # Flatten data without formatting
                    text_content.extend(sheet_data.values.flatten())
            
            text = ' '.join(map(str, text_content))
            return text
        except Exception as e:
            logger.error(f"Error extracting text from Excel file {file_path}: {str(e)}")
            return ""

    async def _extract_text_from_json(self, file_path: str, preserve_formatting: bool = False) -> str:
        """Extract text from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                text = json.dumps(json_data, indent=2 if preserve_formatting else None)
                if not preserve_formatting:
                    text = ' '.join(text.split())
                return text
        except Exception as e:
            logger.error(f"Error extracting text from JSON file {file_path}: {str(e)}")
            return ""

    async def _extract_text_from_xml(self, file_path: str, preserve_formatting: bool = False) -> str:
        """Extract text from an XML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as xml_file:
                xml_content = xml_file.read()
                # Convert XML to dictionary
                xml_dict = xmltodict.parse(xml_content)
                # Convert back to formatted or unformatted string
                text = json.dumps(xml_dict, indent=2 if preserve_formatting else None)
                if not preserve_formatting:
                    text = ' '.join(text.split())
                return text
        except Exception as e:
            logger.error(f"Error extracting text from XML file {file_path}: {str(e)}")
            return ""

    def sanitize_text(self, text: str) -> str:
        """Remove null bytes and sanitize text for storage."""
        if not isinstance(text, str):
            return ''
        return text.replace('\x00', '').encode('utf-8', errors='ignore').decode('utf-8')

    def chunk_text(self, text: str, max_chunk_size: int = 1000) -> list:
        """Split text into chunks of specified max size."""
        if not isinstance(text, str):
            logger.error(f"Invalid text type: {type(text)}")
            return []

        if not text.strip():
            logger.error("Empty text content")
            return []

        try:
            words = text.split()
            logger.info(f"Total words: {len(words)}")
        
            chunks = []
            current_chunk = []
            current_length = 0

            for word in words:
                if current_length + len(word) > max_chunk_size:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    current_chunk.append(word)
                    current_length += len(word)

            if current_chunk:
                chunks.append(' '.join(current_chunk))

            logger.info(f"Generated chunks: {len(chunks)}")
            return chunks
        except Exception as e:
            logger.error(f"Chunking error: {e}")
            return []

    def is_supported_mime_type(self, mime_type: str) -> bool:
        """Check if the given mime type is supported."""
        return (
            mime_type in self.SUPPORTED_MIME_TYPES or 
            mime_type.startswith('text/x-') or  # Source code files
            mime_type.startswith('application/x-')  # Additional source code files
        )

    def get_language_for_extension(self, filename: str) -> str:
        """Determine programming language based on file extension."""
        file_ext = os.path.splitext(filename)[1].lower()
        
        for lang, extensions in self.PROGRAMMING_LANGUAGE_EXTENSIONS.items():
            if file_ext in extensions:
                return lang
        
        return "unknown"

    def get_mime_type_for_extension(self, filename: str) -> str:
        """
        Determine MIME type based on file extension when magic detection fails
        or returns a generic type.
        """
        file_ext = os.path.splitext(filename)[1].lower()
    
        # Extension to MIME type mapping
        extension_to_mime = {
            # TypeScript
            '.ts': 'application/typescript',
            '.tsx': 'application/typescript',
        
            # Other text-based files that might be misidentified
            '.js': 'application/javascript',
            '.jsx': 'application/javascript',
            '.py': 'text/x-python',
            '.md': 'text/markdown',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
        }
    
        return extension_to_mime.get(file_ext, None)

file_extraction_service = FileExtractionService()
