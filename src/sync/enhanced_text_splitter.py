"""Enhanced text splitting functionality with token-based chunking and content-type detection."""
import logging
import re
import tiktoken
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from langdetect import detect, LangDetectException
from pygments import lex
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.util import ClassNotFound

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Content type enumeration for different file types."""
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONVERSATION = "conversation"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class LanguageType(Enum):
    """Language type enumeration for different programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    UNKNOWN = "unknown"

@dataclass
class ChunkingConfig:
    """Configuration for content-type-specific chunking."""
    max_tokens: int
    overlap_tokens: int
    min_tokens: int = 50
    preserve_boundaries: bool = True
    semantic_aware: bool = True

@dataclass
class ChunkingResult:
    """Result of chunking operation with metadata."""
    chunks: List[str]
    content_type: ContentType
    language: LanguageType
    total_tokens: int
    chunk_count: int
    quality_score: float
    metadata: Dict[str, Any]

class TokenCounter:
    """Token counting utility with support for multiple models."""
    
    def __init__(self, model_name: str = "gpt-4"):
        """Initialize token counter with specified model."""
        self.model_name = model_name
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base encoding (used by GPT-4)
            self.encoding = tiktoken.get_encoding("cl100k_base")
            logger.warning(f"Model {model_name} not found, using cl100k_base encoding")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to maximum token count."""
        if not text:
            return text
        
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)

class ContentTypeDetector:
    """Content type and language detection utility."""
    
    def __init__(self):
        """Initialize content type detector."""
        self.code_extensions = {
            '.py': LanguageType.PYTHON,
            '.js': LanguageType.JAVASCRIPT,
            '.ts': LanguageType.TYPESCRIPT,
            '.tsx': LanguageType.TYPESCRIPT,
            '.jsx': LanguageType.JAVASCRIPT,
            '.java': LanguageType.JAVA,
            '.cs': LanguageType.CSHARP,
            '.cpp': LanguageType.CPP,
            '.cc': LanguageType.CPP,
            '.cxx': LanguageType.CPP,
            '.c': LanguageType.C,
            '.h': LanguageType.C,
            '.hpp': LanguageType.CPP,
            '.go': LanguageType.GO,
            '.rs': LanguageType.RUST,
            '.sql': LanguageType.SQL,
        }
        
        self.documentation_extensions = {
            '.md': LanguageType.MARKDOWN,
            '.rst': LanguageType.MARKDOWN,
            '.txt': LanguageType.MARKDOWN,
            '.adoc': LanguageType.MARKDOWN,
        }
        
        self.data_extensions = {
            '.json': LanguageType.JSON,
            '.yaml': LanguageType.YAML,
            '.yml': LanguageType.YAML,
            '.xml': LanguageType.XML,
            '.html': LanguageType.HTML,
            '.htm': LanguageType.HTML,
            '.css': LanguageType.CSS,
        }
    
    def detect_content_type(self, file_path: str, content: str) -> Tuple[ContentType, LanguageType]:
        """Detect content type and language from file path and content."""
        file_ext = self._get_file_extension(file_path)
        
        # Check for conversation patterns
        if self._is_conversation(content):
            return ContentType.CONVERSATION, LanguageType.JSON
        
        # Check file extension first
        if file_ext in self.code_extensions:
            return ContentType.CODE, self.code_extensions[file_ext]
        elif file_ext in self.documentation_extensions:
            return ContentType.DOCUMENTATION, self.documentation_extensions[file_ext]
        elif file_ext in self.data_extensions:
            return ContentType.CODE, self.data_extensions[file_ext]
        
        # Try to detect from content
        language = self._detect_language_from_content(content)
        content_type = self._determine_content_type_from_language(language)
        
        return content_type, language
    
    def _get_file_extension(self, file_path: str) -> str:
        """Get file extension from path."""
        return '.' + file_path.split('.')[-1].lower() if '.' in file_path else ''
    
    def _is_conversation(self, content: str) -> bool:
        """Check if content appears to be a conversation."""
        # Look for conversation patterns
        conversation_patterns = [
            r'"role":\s*"(user|assistant|system)"',
            r'"message":\s*"',
            r'"content":\s*"',
            r'"timestamp":\s*"',
            r'"conversation_id":\s*"',
        ]
        
        for pattern in conversation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _detect_language_from_content(self, content: str) -> LanguageType:
        """Detect language from content using multiple methods."""
        # Try pygments lexer detection
        try:
            lexer = get_lexer_by_name('text')
            # Try to find a better lexer
            for lang_name in ['python', 'javascript', 'java', 'cpp', 'c', 'go', 'rust']:
                try:
                    lexer = get_lexer_by_name(lang_name)
                    # Simple heuristic: if it doesn't throw errors, it might be this language
                    list(lex(content, lexer))
                    return LanguageType(lang_name)
                except:
                    continue
        except:
            pass
        
        # Try language detection for natural language
        try:
            detected_lang = detect(content[:1000])  # Use first 1000 chars for speed
            if detected_lang in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko']:
                return LanguageType.MARKDOWN
        except LangDetectException:
            pass
        
        return LanguageType.UNKNOWN
    
    def _determine_content_type_from_language(self, language: LanguageType) -> ContentType:
        """Determine content type from detected language."""
        if language in [LanguageType.PYTHON, LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT,
                       LanguageType.JAVA, LanguageType.CSHARP, LanguageType.CPP, LanguageType.C,
                       LanguageType.GO, LanguageType.RUST, LanguageType.SQL]:
            return ContentType.CODE
        elif language in [LanguageType.MARKDOWN, LanguageType.HTML, LanguageType.CSS]:
            return ContentType.DOCUMENTATION
        elif language in [LanguageType.JSON, LanguageType.YAML, LanguageType.XML]:
            return ContentType.CODE  # Treat as code for now
        else:
            return ContentType.UNKNOWN

class LanguageSpecificSplitter:
    """Language-specific text splitting utilities."""
    
    def __init__(self):
        """Initialize language-specific splitter."""
        self.splitters = {
            LanguageType.PYTHON: self._split_python,
            LanguageType.JAVASCRIPT: self._split_javascript,
            LanguageType.TYPESCRIPT: self._split_typescript,
            LanguageType.JAVA: self._split_java,
            LanguageType.MARKDOWN: self._split_markdown,
            LanguageType.JSON: self._split_json,
        }
    
    def split_by_language(self, content: str, language: LanguageType) -> List[str]:
        """Split content using language-specific rules."""
        if language in self.splitters:
            return self.splitters[language](content)
        else:
            return self._split_generic(content)
    
    def _split_python(self, content: str) -> List[str]:
        """Split Python code by functions, classes, and logical blocks."""
        # Split by class and function definitions
        patterns = [
            r'^class\s+\w+.*?:$',
            r'^def\s+\w+.*?:$',
            r'^async\s+def\s+\w+.*?:$',
            r'^@\w+.*$',
        ]
        
        return self._split_by_patterns(content, patterns)
    
    def _split_javascript(self, content: str) -> List[str]:
        """Split JavaScript/TypeScript code by functions, classes, and modules."""
        patterns = [
            r'^class\s+\w+.*?\{$',
            r'^function\s+\w+.*?\{$',
            r'^const\s+\w+\s*=\s*\(.*?\)\s*=>\s*\{$',
            r'^export\s+.*$',
            r'^import\s+.*$',
        ]
        
        return self._split_by_patterns(content, patterns)
    
    def _split_typescript(self, content: str) -> List[str]:
        """Split TypeScript code (similar to JavaScript but with type annotations)."""
        return self._split_javascript(content)  # Same patterns work for TS
    
    def _split_java(self, content: str) -> List[str]:
        """Split Java code by classes, methods, and logical blocks."""
        patterns = [
            r'^public\s+class\s+\w+.*?\{$',
            r'^private\s+class\s+\w+.*?\{$',
            r'^public\s+\w+\s+\w+\(.*?\).*?\{$',
            r'^private\s+\w+\s+\w+\(.*?\).*?\{$',
            r'^@\w+.*$',
        ]
        
        return self._split_by_patterns(content, patterns)
    
    def _split_markdown(self, content: str) -> List[str]:
        """Split Markdown by headers and logical sections."""
        patterns = [
            r'^#+\s+.*$',  # Headers
            r'^---$',      # Horizontal rules
            r'^\*\*\*$',   # Horizontal rules
        ]
        
        return self._split_by_patterns(content, patterns)
    
    def _split_json(self, content: str) -> List[str]:
        """Split JSON by objects and arrays."""
        # For JSON, we'll split by top-level objects/arrays
        # This is more complex and might need a proper JSON parser
        return self._split_generic(content)
    
    def _split_by_patterns(self, content: str, patterns: List[str]) -> List[str]:
        """Split content by regex patterns."""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            # Check if line matches any pattern
            matches_pattern = any(re.match(pattern, line.strip()) for pattern in patterns)
            
            if matches_pattern and current_chunk:
                # Start new chunk
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _split_generic(self, content: str) -> List[str]:
        """Generic splitting for unknown languages."""
        # Split by paragraphs (double newlines)
        return [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]

class EnhancedTextSplitter:
    """Enhanced text splitter with token-based chunking and content-type awareness."""
    
    def __init__(self, model_name: str = "gpt-4"):
        """Initialize enhanced text splitter."""
        self.token_counter = TokenCounter(model_name)
        self.content_detector = ContentTypeDetector()
        self.language_splitter = LanguageSpecificSplitter()
        
        # Content-type-specific configurations
        self.chunking_configs = {
            ContentType.CODE: ChunkingConfig(
                max_tokens=220,  # 180-260 range, using middle
                overlap_tokens=64,
                min_tokens=50,
                preserve_boundaries=True,
                semantic_aware=True
            ),
            ContentType.DOCUMENTATION: ChunkingConfig(
                max_tokens=425,  # 350-500 range, using middle
                overlap_tokens=100,
                min_tokens=100,
                preserve_boundaries=True,
                semantic_aware=True
            ),
            ContentType.CONVERSATION: ChunkingConfig(
                max_tokens=300,  # 3-5 turns per chunk
                overlap_tokens=50,
                min_tokens=100,
                preserve_boundaries=True,
                semantic_aware=True
            ),
            ContentType.MIXED: ChunkingConfig(
                max_tokens=300,
                overlap_tokens=75,
                min_tokens=75,
                preserve_boundaries=True,
                semantic_aware=True
            ),
            ContentType.UNKNOWN: ChunkingConfig(
                max_tokens=400,
                overlap_tokens=100,
                min_tokens=100,
                preserve_boundaries=False,
                semantic_aware=False
            )
        }
    
    async def semantic_split_enhanced(self, text: str, file_path: str = "") -> ChunkingResult:
        """Enhanced semantic splitting with content-type awareness."""
        if not text or not text.strip():
            return ChunkingResult(
                chunks=[],
                content_type=ContentType.UNKNOWN,
                language=LanguageType.UNKNOWN,
                total_tokens=0,
                chunk_count=0,
                quality_score=0.0,
                metadata={}
            )
        
        # Detect content type and language
        content_type, language = self.content_detector.detect_content_type(file_path, text)
        config = self.chunking_configs[content_type]
        
        logger.info(f"Detected content type: {content_type.value}, language: {language.value}")
        
        # Split using language-specific rules if available
        if content_type == ContentType.CODE and language in self.language_splitter.splitters:
            initial_chunks = self.language_splitter.split_by_language(text, language)
        else:
            # Fall back to sentence-based splitting
            initial_chunks = self._split_by_sentences(text)
        
        # Apply token-based chunking
        final_chunks = self._apply_token_based_chunking(initial_chunks, config)
        
        # Calculate quality metrics
        quality_score = self._calculate_quality_score(final_chunks, config)
        total_tokens = sum(self.token_counter.count_tokens(chunk) for chunk in final_chunks)
        
        # Generate metadata
        metadata = {
            'content_type': content_type.value,
            'language': language.value,
            'chunking_config': {
                'max_tokens': config.max_tokens,
                'overlap_tokens': config.overlap_tokens,
                'min_tokens': config.min_tokens
            },
            'token_distribution': [self.token_counter.count_tokens(chunk) for chunk in final_chunks],
            'average_tokens_per_chunk': total_tokens / len(final_chunks) if final_chunks else 0
        }
        
        return ChunkingResult(
            chunks=final_chunks,
            content_type=content_type,
            language=language,
            total_tokens=total_tokens,
            chunk_count=len(final_chunks),
            quality_score=quality_score,
            metadata=metadata
        )
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences (fallback method)."""
        # Simple regex-based sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _apply_token_based_chunking(self, initial_chunks: List[str], config: ChunkingConfig) -> List[str]:
        """Apply token-based chunking to initial chunks."""
        final_chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for chunk in initial_chunks:
            chunk_tokens = self.token_counter.count_tokens(chunk)
            
            # If single chunk exceeds max tokens, split it further
            if chunk_tokens > config.max_tokens:
                # Save current chunk if it has content
                if current_chunk.strip():
                    final_chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0
                
                # Split large chunk
                sub_chunks = self._split_large_chunk(chunk, config.max_tokens)
                final_chunks.extend(sub_chunks)
                continue
            
            # Check if adding this chunk would exceed max tokens
            if current_tokens + chunk_tokens > config.max_tokens and current_chunk.strip():
                # Save current chunk and start new one
                final_chunks.append(current_chunk.strip())
                current_chunk = chunk
                current_tokens = chunk_tokens
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += " " + chunk
                else:
                    current_chunk = chunk
                current_tokens += chunk_tokens
        
        # Add final chunk
        if current_chunk.strip():
            final_chunks.append(current_chunk.strip())
        
        # Apply overlap
        if len(final_chunks) > 1 and config.overlap_tokens > 0:
            final_chunks = self._apply_overlap(final_chunks, config.overlap_tokens)
        
        # Filter out chunks that are too small
        final_chunks = [chunk for chunk in final_chunks 
                       if self.token_counter.count_tokens(chunk) >= config.min_tokens]
        
        return final_chunks
    
    def _split_large_chunk(self, chunk: str, max_tokens: int) -> List[str]:
        """Split a large chunk into smaller pieces."""
        tokens = self.token_counter.encoding.encode(chunk)
        sub_chunks = []
        
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            sub_chunk = self.token_counter.encoding.decode(chunk_tokens)
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _apply_overlap(self, chunks: List[str], overlap_tokens: int) -> List[str]:
        """Apply overlap between chunks."""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Add overlap from previous chunk
            if i > 0:
                prev_chunk = chunks[i-1]
                prev_tokens = self.token_counter.encoding.encode(prev_chunk)
                if len(prev_tokens) > overlap_tokens:
                    overlap_text = self.token_counter.encoding.decode(
                        prev_tokens[-overlap_tokens:]
                    )
                    chunk = overlap_text + " " + chunk
            
            # Add overlap to next chunk
            if i < len(chunks) - 1:
                next_chunk = chunks[i+1]
                next_tokens = self.token_counter.encoding.encode(next_chunk)
                if len(next_tokens) > overlap_tokens:
                    overlap_text = self.token_counter.encoding.decode(
                        next_tokens[:overlap_tokens]
                    )
                    chunk = chunk + " " + overlap_text
            
            overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    def _calculate_quality_score(self, chunks: List[str], config: ChunkingConfig) -> float:
        """Calculate quality score for chunks."""
        if not chunks:
            return 0.0
        
        scores = []
        
        for chunk in chunks:
            token_count = self.token_counter.count_tokens(chunk)
            
            # Score based on token count (prefer chunks close to target)
            target_tokens = config.max_tokens
            token_score = 1.0 - abs(token_count - target_tokens) / target_tokens
            token_score = max(0.0, min(1.0, token_score))
            
            # Score based on semantic coherence (simple heuristic)
            coherence_score = self._calculate_coherence_score(chunk)
            
            # Combined score
            chunk_score = (token_score * 0.6 + coherence_score * 0.4)
            scores.append(chunk_score)
        
        return sum(scores) / len(scores)
    
    def _calculate_coherence_score(self, chunk: str) -> float:
        """Calculate semantic coherence score for a chunk."""
        # Simple heuristic: check for complete sentences and proper structure
        sentences = re.split(r'[.!?]+', chunk)
        complete_sentences = [s.strip() for s in sentences if s.strip()]
        
        if not complete_sentences:
            return 0.5
        
        # Score based on sentence completeness and length
        avg_sentence_length = sum(len(s.split()) for s in complete_sentences) / len(complete_sentences)
        
        # Prefer sentences of reasonable length (10-30 words)
        if 10 <= avg_sentence_length <= 30:
            return 1.0
        elif 5 <= avg_sentence_length <= 50:
            return 0.8
        else:
            return 0.6

# Backward compatibility function
async def semantic_split(text: str, max_chars: int = 4000, overlap: int = 200) -> List[str]:
    """Backward compatible semantic split function."""
    splitter = EnhancedTextSplitter()
    result = await splitter.semantic_split_enhanced(text)
    return result.chunks


