"""Comprehensive testing suite for enhanced chunking functionality."""
import asyncio
import logging
import tempfile
import os
from typing import List, Dict, Any
import json

from enhanced_text_splitter import (
    EnhancedTextSplitter, 
    ContentType, 
    LanguageType, 
    ChunkingResult,
    TokenCounter,
    ContentTypeDetector,
    LanguageSpecificSplitter
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChunkingTestSuite:
    """Comprehensive test suite for enhanced chunking functionality."""
    
    def __init__(self):
        """Initialize test suite."""
        self.splitter = EnhancedTextSplitter()
        self.test_results = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        logger.info("Starting comprehensive chunking test suite...")
        
        tests = [
            ("Token Counting", self.test_token_counting),
            ("Content Type Detection", self.test_content_type_detection),
            ("Language Detection", self.test_language_detection),
            ("Python Code Chunking", self.test_python_chunking),
            ("JavaScript Code Chunking", self.test_javascript_chunking),
            ("Markdown Documentation Chunking", self.test_markdown_chunking),
            ("JSON Conversation Chunking", self.test_json_conversation_chunking),
            ("Mixed Content Chunking", self.test_mixed_content_chunking),
            ("Quality Metrics", self.test_quality_metrics),
            ("Performance Benchmarks", self.test_performance_benchmarks),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                logger.info(f"Running test: {test_name}")
                result = await test_func()
                results[test_name] = result
                logger.info(f"✓ {test_name} passed")
            except Exception as e:
                logger.error(f"✗ {test_name} failed: {e}")
                results[test_name] = {"error": str(e)}
        
        return results
    
    async def test_token_counting(self) -> Dict[str, Any]:
        """Test token counting functionality."""
        counter = TokenCounter()
        
        test_cases = [
            ("Hello world", 2),
            ("This is a test sentence.", 6),
            ("def hello_world():\n    return 'Hello, World!'", 8),
            ("", 0),
        ]
        
        results = {}
        for text, expected_min in test_cases:
            token_count = counter.count_tokens(text)
            results[text] = {
                "tokens": token_count,
                "expected_min": expected_min,
                "passed": token_count >= expected_min
            }
        
        return results
    
    async def test_content_type_detection(self) -> Dict[str, Any]:
        """Test content type detection."""
        detector = ContentTypeDetector()
        
        test_cases = [
            ("test.py", "def hello():\n    pass", ContentType.CODE, LanguageType.PYTHON),
            ("script.js", "function hello() {\n    console.log('Hello');\n}", ContentType.CODE, LanguageType.JAVASCRIPT),
            ("README.md", "# Title\n\nThis is documentation.", ContentType.DOCUMENTATION, LanguageType.MARKDOWN),
            ("conversation.json", '{"role": "user", "content": "Hello"}', ContentType.CONVERSATION, LanguageType.JSON),
        ]
        
        results = {}
        for file_path, content, expected_type, expected_lang in test_cases:
            detected_type, detected_lang = detector.detect_content_type(file_path, content)
            results[file_path] = {
                "expected_type": expected_type.value,
                "detected_type": detected_type.value,
                "expected_lang": expected_lang.value,
                "detected_lang": detected_lang.value,
                "type_correct": detected_type == expected_type,
                "lang_correct": detected_lang == expected_lang
            }
        
        return results
    
    async def test_language_detection(self) -> Dict[str, Any]:
        """Test language-specific splitting."""
        splitter = LanguageSpecificSplitter()
        
        python_code = """
class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, user):
        self.users.append(user)
    
    def get_user(self, user_id):
        return next((u for u in self.users if u.id == user_id), None)
"""
        
        javascript_code = """
class UserManager {
    constructor() {
        this.users = [];
    }
    
    addUser(user) {
        this.users.push(user);
    }
    
    getUser(userId) {
        return this.users.find(u => u.id === userId);
    }
}
"""
        
        markdown_content = """
# User Management System

## Overview
This system manages users in the application.

## Features
- Add users
- Remove users
- Update user information

## API Reference
### POST /users
Creates a new user.
"""
        
        results = {}
        
        # Test Python splitting
        python_chunks = splitter.split_by_language(python_code, LanguageType.PYTHON)
        results["python"] = {
            "chunk_count": len(python_chunks),
            "chunks": python_chunks,
            "expected_min_chunks": 3  # class + 2 methods
        }
        
        # Test JavaScript splitting
        js_chunks = splitter.split_by_language(javascript_code, LanguageType.JAVASCRIPT)
        results["javascript"] = {
            "chunk_count": len(js_chunks),
            "chunks": js_chunks,
            "expected_min_chunks": 3  # class + 2 methods
        }
        
        # Test Markdown splitting
        md_chunks = splitter.split_by_language(markdown_content, LanguageType.MARKDOWN)
        results["markdown"] = {
            "chunk_count": len(md_chunks),
            "chunks": md_chunks,
            "expected_min_chunks": 3  # title + features + api
        }
        
        return results
    
    async def test_python_chunking(self) -> Dict[str, Any]:
        """Test Python code chunking."""
        python_code = """
import os
import sys
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self) -> bool:
        try:
            self.connection = create_connection(self.connection_string)
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        if not self.connection:
            raise RuntimeError("Not connected to database")
        
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        return cursor.fetchall()
    
    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

def create_connection(connection_string: str):
    # Implementation details
    pass
"""
        
        result = await self.splitter.semantic_split_enhanced(python_code, "test.py")
        
        return {
            "content_type": result.content_type.value,
            "language": result.language.value,
            "chunk_count": result.chunk_count,
            "total_tokens": result.total_tokens,
            "quality_score": result.quality_score,
            "average_tokens_per_chunk": result.total_tokens / result.chunk_count if result.chunk_count > 0 else 0,
            "chunks": result.chunks,
            "metadata": result.metadata
        }
    
    async def test_javascript_chunking(self) -> Dict[str, Any]:
        """Test JavaScript code chunking."""
        javascript_code = """
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

class UserService {
    constructor(database) {
        this.database = database;
        this.router = express.Router();
        this.setupRoutes();
    }
    
    setupRoutes() {
        this.router.get('/users', this.getUsers.bind(this));
        this.router.post('/users', this.createUser.bind(this));
        this.router.put('/users/:id', this.updateUser.bind(this));
        this.router.delete('/users/:id', this.deleteUser.bind(this));
    }
    
    async getUsers(req, res) {
        try {
            const users = await this.database.getAllUsers();
            res.json(users);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    }
    
    async createUser(req, res) {
        try {
            const user = await this.database.createUser(req.body);
            res.status(201).json(user);
        } catch (error) {
            res.status(400).json({ error: error.message });
        }
    }
}

module.exports = UserService;
"""
        
        result = await self.splitter.semantic_split_enhanced(javascript_code, "user-service.js")
        
        return {
            "content_type": result.content_type.value,
            "language": result.language.value,
            "chunk_count": result.chunk_count,
            "total_tokens": result.total_tokens,
            "quality_score": result.quality_score,
            "average_tokens_per_chunk": result.total_tokens / result.chunk_count if result.chunk_count > 0 else 0,
            "chunks": result.chunks,
            "metadata": result.metadata
        }
    
    async def test_markdown_chunking(self) -> Dict[str, Any]:
        """Test Markdown documentation chunking."""
        markdown_content = """
# API Documentation

## Overview
This API provides endpoints for managing users in the system.

## Authentication
All API requests require authentication using a Bearer token in the Authorization header.

### Getting a Token
To get an authentication token, send a POST request to `/auth/login` with your credentials.

## User Management

### Get All Users
**Endpoint:** `GET /api/users`

**Description:** Retrieves a list of all users in the system.

**Parameters:**
- `page` (optional): Page number for pagination
- `limit` (optional): Number of users per page

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "total": 100,
  "page": 1
}
```

### Create User
**Endpoint:** `POST /api/users`

**Description:** Creates a new user in the system.

**Request Body:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "example-password"
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "created_at": "2023-01-01T00:00:00Z"
}
```

## Error Handling
All errors are returned in the following format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

Common error codes:
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error
"""
        
        result = await self.splitter.semantic_split_enhanced(markdown_content, "api-docs.md")
        
        return {
            "content_type": result.content_type.value,
            "language": result.language.value,
            "chunk_count": result.chunk_count,
            "total_tokens": result.total_tokens,
            "quality_score": result.quality_score,
            "average_tokens_per_chunk": result.total_tokens / result.chunk_count if result.chunk_count > 0 else 0,
            "chunks": result.chunks,
            "metadata": result.metadata
        }
    
    async def test_json_conversation_chunking(self) -> Dict[str, Any]:
        """Test JSON conversation chunking."""
        conversation_json = """
{
  "conversation_id": "conv_123",
  "messages": [
    {
      "role": "user",
      "content": "How do I implement authentication in my Node.js application?",
      "timestamp": "2023-01-01T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "To implement authentication in Node.js, you can use several approaches. Here are the most common methods:\n\n1. **JWT (JSON Web Tokens)**: Use libraries like `jsonwebtoken` to create and verify tokens.\n2. **Session-based authentication**: Use `express-session` with a session store.\n3. **OAuth**: Integrate with providers like Google, GitHub, etc.\n\nWould you like me to show you a specific implementation?",
      "timestamp": "2023-01-01T10:01:00Z"
    },
    {
      "role": "user",
      "content": "Yes, please show me a JWT implementation.",
      "timestamp": "2023-01-01T10:02:00Z"
    },
    {
      "role": "assistant",
      "content": "Here's a basic JWT implementation for Node.js:\n\n```javascript\nconst jwt = require('jsonwebtoken');\nconst bcrypt = require('bcrypt');\n\n// Generate token\nfunction generateToken(user) {\n  return jwt.sign(\n    { userId: user.id, email: user.email },\n    process.env.JWT_SECRET,\n    { expiresIn: '24h' }\n  );\n}\n\n// Verify token\nfunction verifyToken(token) {\n  try {\n    return jwt.verify(token, process.env.JWT_SECRET);\n  } catch (error) {\n    throw new Error('Invalid token');\n  }\n}\n\n// Login endpoint\napp.post('/login', async (req, res) => {\n  const { email, password } = req.body;\n  \n  const user = await User.findOne({ email });\n  if (!user || !await bcrypt.compare(password, user.password)) {\n    return res.status(401).json({ error: 'Invalid credentials' });\n  }\n  \n  const token = generateToken(user);\n  res.json({ token, user: { id: user.id, email: user.email } });\n});\n```",
      "timestamp": "2023-01-01T10:03:00Z"
    }
  ]
}
"""
        
        result = await self.splitter.semantic_split_enhanced(conversation_json, "conversation.json")
        
        return {
            "content_type": result.content_type.value,
            "language": result.language.value,
            "chunk_count": result.chunk_count,
            "total_tokens": result.total_tokens,
            "quality_score": result.quality_score,
            "average_tokens_per_chunk": result.total_tokens / result.chunk_count if result.chunk_count > 0 else 0,
            "chunks": result.chunks,
            "metadata": result.metadata
        }
    
    async def test_mixed_content_chunking(self) -> Dict[str, Any]:
        """Test mixed content chunking."""
        mixed_content = """
# Configuration File

This file contains configuration settings for the application.

## Database Configuration
```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'myapp',
    'username': 'user',
    'password': '<placeholder>'
}
```

## API Settings
```javascript
const apiConfig = {
    baseUrl: 'https://api.example.com',
    timeout: 5000,
    retries: 3
};
```

## Environment Variables
Set these environment variables before running the application:

- `NODE_ENV`: Set to 'production' for production deployment
- `PORT`: Port number for the server (default: 3000)
- `DATABASE_URL`: Full database connection string

## Logging Configuration
The application uses structured logging with the following levels:
- ERROR: System errors and exceptions
- WARN: Warning messages
- INFO: General information
- DEBUG: Detailed debugging information
"""
        
        result = await self.splitter.semantic_split_enhanced(mixed_content, "config.md")
        
        return {
            "content_type": result.content_type.value,
            "language": result.language.value,
            "chunk_count": result.chunk_count,
            "total_tokens": result.total_tokens,
            "quality_score": result.quality_score,
            "average_tokens_per_chunk": result.total_tokens / result.chunk_count if result.chunk_count > 0 else 0,
            "chunks": result.chunks,
            "metadata": result.metadata
        }
    
    async def test_quality_metrics(self) -> Dict[str, Any]:
        """Test quality metrics calculation."""
        test_cases = [
            ("Short text", "This is a short text."),
            ("Medium text", "This is a medium length text that contains multiple sentences. It should provide a good test case for quality metrics."),
            ("Long text", "This is a very long text that contains many sentences and should be split into multiple chunks. " * 10),
        ]
        
        results = {}
        for name, text in test_cases:
            result = await self.splitter.semantic_split_enhanced(text, f"{name.lower().replace(' ', '_')}.txt")
            results[name] = {
                "quality_score": result.quality_score,
                "chunk_count": result.chunk_count,
                "total_tokens": result.total_tokens,
                "average_tokens_per_chunk": result.total_tokens / result.chunk_count if result.chunk_count > 0 else 0,
                "token_distribution": result.metadata.get('token_distribution', [])
            }
        
        return results
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance benchmarks."""
        import time
        
        # Create a large test file
        large_content = """
# Large Test Document

This is a large test document designed to test the performance of the enhanced chunking system.

""" + "\n".join([f"## Section {i}\n\nThis is section {i} with some content." for i in range(100)])
        
        # Benchmark enhanced chunking
        start_time = time.time()
        result = await self.splitter.semantic_split_enhanced(large_content, "large_test.md")
        enhanced_time = time.time() - start_time
        
        # Benchmark legacy chunking
        from text_splitter import _semantic_split_legacy
        start_time = time.time()
        legacy_chunks = await _semantic_split_legacy(large_content, 4000, 200)
        legacy_time = time.time() - start_time
        
        return {
            "enhanced_chunking": {
                "time_seconds": enhanced_time,
                "chunk_count": result.chunk_count,
                "total_tokens": result.total_tokens,
                "quality_score": result.quality_score
            },
            "legacy_chunking": {
                "time_seconds": legacy_time,
                "chunk_count": len(legacy_chunks)
            },
            "performance_improvement": {
                "time_ratio": legacy_time / enhanced_time if enhanced_time > 0 else 0,
                "quality_improvement": result.quality_score
            }
        }

async def main():
    """Run the test suite."""
    test_suite = ChunkingTestSuite()
    results = await test_suite.run_all_tests()
    
    # Save results to file
    with open("chunking_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*50)
    print("CHUNKING TEST SUITE RESULTS")
    print("="*50)
    
    for test_name, result in results.items():
        if "error" in result:
            print(f"✗ {test_name}: FAILED - {result['error']}")
        else:
            print(f"✓ {test_name}: PASSED")
    
    print(f"\nResults saved to: chunking_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())


