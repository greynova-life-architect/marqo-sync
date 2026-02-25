"""Text splitting functionality for code indexing."""
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

# Import enhanced functionality
try:
    from .enhanced_text_splitter import EnhancedTextSplitter, semantic_split_enhanced
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    logger.warning("Enhanced text splitter not available, using basic functionality")

def simple_sentence_split(text):
    """Simple regex-based sentence splitter."""
    # Split on period followed by space or newline, exclamation mark, or question mark
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

async def semantic_split(text, max_chars=4000, overlap=200, file_path: str = "", use_enhanced: bool = True):
    """Split text into chunks with overlap.
    
    Enhanced version with token-based chunking and content-type awareness.
    Falls back to character-based chunking if enhanced version is not available.
    
    Args:
        text: Text to split
        max_chars: Maximum characters per chunk (legacy parameter)
        overlap: Overlap in characters (legacy parameter)
        file_path: File path for content type detection
        use_enhanced: Whether to use enhanced token-based chunking
    
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    # Try enhanced splitting first
    if use_enhanced and ENHANCED_AVAILABLE:
        try:
            splitter = EnhancedTextSplitter()
            result = await splitter.semantic_split_enhanced(text, file_path)
            logger.info(f"Enhanced chunking: {result.chunk_count} chunks, "
                       f"quality score: {result.quality_score:.2f}, "
                       f"content type: {result.content_type.value}")
            return result.chunks
        except Exception as e:
            logger.warning(f"Enhanced chunking failed, falling back to basic: {e}")
    
    # Fall back to original character-based chunking
    return await _semantic_split_legacy(text, max_chars, overlap)

async def _semantic_split_legacy(text, max_chars=4000, overlap=200):
    """Legacy character-based semantic splitting."""
    if not text or not text.strip():
        return []
    
    # Ensure text is a string
    text = str(text)
    
    sentences = simple_sentence_split(text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # Skip empty sentences
        if not sentence.strip():
            continue
            
        # If single sentence exceeds max_chars, handle it specially
        if len(sentence) > max_chars:
            logger.warning(f"Single sentence exceeds max_chars ({max_chars}): {sentence[:100]}...")
            
            # If current chunk has content, save it first
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Split extremely long sentence into smaller chunks
            sentence_chunks = []
            remaining = sentence
            while len(remaining) > 0:
                # Take up to max_chars, but try to break at word boundaries
                if len(remaining) <= max_chars:
                    chunk = remaining
                    remaining = ""
                else:
                    # Try to break at word boundary
                    chunk = remaining[:max_chars]
                    last_space = chunk.rfind(' ')
                    if last_space > max_chars * 0.8:  # If we can break at a reasonable word boundary
                        chunk = chunk[:last_space]
                        remaining = remaining[last_space + 1:]
                    else:
                        # Force break if no good word boundary
                        remaining = remaining[max_chars:]
                
                if chunk.strip():
                    sentence_chunks.append(chunk.strip())
            
            # Add all sentence chunks
            chunks.extend(sentence_chunks)
            continue
        
        # Normal case: sentence fits in current chunk
        if len(current_chunk + sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            # Current chunk is full, save it and start new one
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    # Add final chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Filter out empty chunks and ensure all chunks are within limits
    filtered_chunks = []
    for chunk in chunks:
        if chunk.strip() and len(chunk) <= max_chars:
            filtered_chunks.append(chunk)
        elif chunk.strip():
            # If chunk is still too long, split it further
            logger.warning(f"Chunk still exceeds max_chars after processing: {len(chunk)} chars")
            while len(chunk) > 0:
                if len(chunk) <= max_chars:
                    filtered_chunks.append(chunk)
                    break
                else:
                    filtered_chunks.append(chunk[:max_chars])
                    chunk = chunk[max_chars:]
    
    # Add overlap between chunks (only if we have multiple chunks)
    if len(filtered_chunks) <= 1:
        return filtered_chunks
    
    overlapped_chunks = []
    for i, chunk in enumerate(filtered_chunks):
        if i > 0:
            # Add overlap from previous chunk
            prefix = filtered_chunks[i-1][-overlap:] if overlap < len(filtered_chunks[i-1]) else filtered_chunks[i-1]
            chunk = prefix + " " + chunk
        if i < len(filtered_chunks) - 1:
            # Add overlap to next chunk
            suffix = filtered_chunks[i+1][:overlap] if overlap < len(filtered_chunks[i+1]) else filtered_chunks[i+1]
            chunk = chunk + " " + suffix
        overlapped_chunks.append(chunk)
    
    return overlapped_chunks 