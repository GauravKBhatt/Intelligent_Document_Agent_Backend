# services/text_processor.py - Text Extraction and Chunking Service
import PyPDF2
import pdfplumber
from typing import List, Dict, Any
import re
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import settings

class TextProcessor:
    """Service for extracting and chunking text from files"""
    
    def __init__(self):
        self.semantic_model = None
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF or TXT files"""
        file_extension = file_path.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            return self._extract_from_pdf(file_path)
        elif file_extension == 'txt':
            return self._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber for better accuracy"""
        text = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            # Fallback to PyPDF2 if pdfplumber fails
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        
        return self._clean_text(text)
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT files"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return self._clean_text(file.read())
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\']+', '', text)
        # Remove multiple consecutive periods
        text = re.sub(r'\.{3,}', '...', text)
        return text.strip()
    
    def chunk_text(self, text: str, method: str = "recursive") -> List[str]:
        """
        Chunk text using different strategies
        
        Args:
            text: Input text to chunk
            method: Chunking method ('recursive', 'semantic', 'custom')
        
        Returns:
            List of text chunks
        """
        if method == "recursive":
            return self._recursive_chunking(text)
        elif method == "semantic":
            return self._semantic_chunking(text)
        elif method == "custom":
            return self._custom_chunking(text)
        else:
            raise ValueError(f"Unknown chunking method: {method}")
    
    def _recursive_chunking(self, text: str) -> List[str]:
        """
        Recursive chunking: Try to split by paragraphs, then sentences, then words
        """
        chunk_size = settings.CHUNK_SIZE
        chunk_overlap = settings.CHUNK_OVERLAP
        
        # First, try to split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk + paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Create overlap by keeping last part of current chunk
                    current_chunk = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else ""
                
                # If paragraph itself is too long, split it further
                if len(paragraph) > chunk_size:
                    chunks.extend(self._split_long_text(paragraph, chunk_size, chunk_overlap))
                    current_chunk = ""
                else:
                    current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _split_long_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Split long text by sentences, then by words if necessary"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else ""
                
                # If sentence is still too long, split by words
                if len(sentence) > chunk_size:
                    words = sentence.split()
                    word_chunk = ""
                    for word in words:
                        if len(word_chunk + word) > chunk_size:
                            if word_chunk:
                                chunks.append(word_chunk.strip())
                                word_chunk = word_chunk[-chunk_overlap:] if len(word_chunk) > chunk_overlap else ""
                        word_chunk += " " + word if word_chunk else word
                    
                    if word_chunk:
                        current_chunk = word_chunk
                else:
                    current_chunk = sentence
            else:
                current_chunk += ". " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _semantic_chunking(self, text: str) -> List[str]:
        """
        Semantic chunking: Group sentences by semantic similarity
        """
        if not self.semantic_model:
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return [text]
        
        # Generate embeddings for sentences
        sentence_embeddings = self.semantic_model.encode(sentences)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(sentence_embeddings)
        
        # Group sentences by semantic similarity
        chunks = []
        used_indices = set()
        threshold = 0.5  # Similarity threshold
        
        for i, sentence in enumerate(sentences):
            if i in used_indices:
                continue
            
            current_chunk = [sentence]
            used_indices.add(i)
            current_length = len(sentence)
            
            # Find similar sentences to group together
            for j in range(i + 1, len(sentences)):
                if j in used_indices:
                    continue
                
                if similarity_matrix[i][j] > threshold:
                    # Check if adding this sentence would exceed chunk size
                    if current_length + len(sentences[j]) < settings.CHUNK_SIZE:
                        current_chunk.append(sentences[j])
                        used_indices.add(j)
                        current_length += len(sentences[j])
            
            chunks.append(". ".join(current_chunk))
        
        return chunks
    
    def _custom_chunking(self, text: str) -> List[str]:
        """
        Custom chunking: Domain-specific chunking based on patterns
        """
        chunks = []
        
        # Look for common document structures
        section_patterns = [
            r'\n\s*(?:Chapter|Section|Part)\s+\d+',
            r'\n\s*\d+\.\s+[A-Z]',  # Numbered sections
            r'\n\s*[A-Z][A-Z\s]+\n',  # ALL CAPS headers
            r'\n\s*#{1,6}\s+',  # Markdown headers
        ]
        
        # Try to split by sections first
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            if matches:
                last_end = 0
                for match in matches:
                    if match.start() > last_end:
                        section_text = text[last_end:match.start()].strip()
                        if section_text:
                            # Further split if section is too long
                            if len(section_text) > settings.CHUNK_SIZE:
                                chunks.extend(self._recursive_chunking(section_text))
                            else:
                                chunks.append(section_text)
                    last_end = match.start()
                
                # Add the last section
                last_section = text[last_end:].strip()
                if last_section:
                    if len(last_section) > settings.CHUNK_SIZE:
                        chunks.extend(self._recursive_chunking(last_section))
                    else:
                        chunks.append(last_section)
                
                return chunks
        
        # If no clear structure found, fall back to recursive chunking
        return self._recursive_chunking(text)
    
    def get_chunk_metadata(self, chunks: List[str]) -> List[Dict[str, Any]]:
        """Generate metadata for chunks"""
        metadata = []
        
        for i, chunk in enumerate(chunks):
            # Calculate basic statistics
            word_count = len(chunk.split())
            char_count = len(chunk)
            sentence_count = len(re.split(r'[.!?]+', chunk))
            
            # Extract potential keywords (simple approach)
            words = re.findall(r'\b[a-zA-Z]{4,}\b', chunk.lower())
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            
            metadata.append({
                'chunk_index': i,
                'word_count': word_count,
                'char_count': char_count,
                'sentence_count': sentence_count,
                'keywords': [kw[0] for kw in top_keywords],
                'preview': chunk[:100] + '...' if len(chunk) > 100 else chunk
            })
        
        return metadata