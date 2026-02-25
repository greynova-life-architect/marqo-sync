#!/usr/bin/env python3
"""Demo script showing enhanced chunking functionality."""

import asyncio
import sys
import os

# Add the src/sync directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'sync'))

async def demo_python_chunking():
    """Demo Python code chunking."""
    print("🐍 Python Code Chunking Demo")
    print("=" * 40)
    
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
    
    try:
        from enhanced_text_splitter import EnhancedTextSplitter
        
        splitter = EnhancedTextSplitter()
        result = await splitter.semantic_split_enhanced(python_code, "database_manager.py")
        
        print(f"Content Type: {result.content_type.value}")
        print(f"Language: {result.language.value}")
        print(f"Chunks: {result.chunk_count}")
        print(f"Total Tokens: {result.total_tokens}")
        print(f"Quality Score: {result.quality_score:.2f}")
        print(f"Average Tokens per Chunk: {result.total_tokens / result.chunk_count:.1f}")
        
        print("\nChunks:")
        for i, chunk in enumerate(result.chunks):
            print(f"\n--- Chunk {i+1} ---")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        
        return True
        
    except ImportError:
        print("Enhanced chunking not available (dependencies not installed)")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

async def demo_markdown_chunking():
    """Demo Markdown documentation chunking."""
    print("\n📝 Markdown Documentation Chunking Demo")
    print("=" * 40)
    
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
    
    try:
        from enhanced_text_splitter import EnhancedTextSplitter
        
        splitter = EnhancedTextSplitter()
        result = await splitter.semantic_split_enhanced(markdown_content, "api-docs.md")
        
        print(f"Content Type: {result.content_type.value}")
        print(f"Language: {result.language.value}")
        print(f"Chunks: {result.chunk_count}")
        print(f"Total Tokens: {result.total_tokens}")
        print(f"Quality Score: {result.quality_score:.2f}")
        print(f"Average Tokens per Chunk: {result.total_tokens / result.chunk_count:.1f}")
        
        print("\nChunks:")
        for i, chunk in enumerate(result.chunks):
            print(f"\n--- Chunk {i+1} ---")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        
        return True
        
    except ImportError:
        print("Enhanced chunking not available (dependencies not installed)")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

async def demo_conversation_chunking():
    """Demo conversation chunking."""
    print("\n💬 Conversation Chunking Demo")
    print("=" * 40)
    
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
    
    try:
        from enhanced_text_splitter import EnhancedTextSplitter
        
        splitter = EnhancedTextSplitter()
        result = await splitter.semantic_split_enhanced(conversation_json, "conversation.json")
        
        print(f"Content Type: {result.content_type.value}")
        print(f"Language: {result.language.value}")
        print(f"Chunks: {result.chunk_count}")
        print(f"Total Tokens: {result.total_tokens}")
        print(f"Quality Score: {result.quality_score:.2f}")
        print(f"Average Tokens per Chunk: {result.total_tokens / result.chunk_count:.1f}")
        
        print("\nChunks:")
        for i, chunk in enumerate(result.chunks):
            print(f"\n--- Chunk {i+1} ---")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        
        return True
        
    except ImportError:
        print("Enhanced chunking not available (dependencies not installed)")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

async def demo_backward_compatibility():
    """Demo backward compatibility."""
    print("\n🔄 Backward Compatibility Demo")
    print("=" * 40)
    
    test_content = "This is a test content for backward compatibility demonstration."
    
    try:
        from text_splitter import semantic_split
        
        # Test enhanced chunking (if available)
        print("Testing enhanced chunking...")
        enhanced_chunks = await semantic_split(test_content, file_path="test.txt", use_enhanced=True)
        print(f"Enhanced chunking: {len(enhanced_chunks)} chunks")
        
        # Test legacy chunking
        print("Testing legacy chunking...")
        legacy_chunks = await semantic_split(test_content, max_chars=100, overlap=20, use_enhanced=False)
        print(f"Legacy chunking: {len(legacy_chunks)} chunks")
        
        print("✓ Backward compatibility working")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

async def main():
    """Run all demos."""
    print("🚀 Enhanced Chunking Demo")
    print("=" * 50)
    
    demos = [
        ("Python Code Chunking", demo_python_chunking),
        ("Markdown Documentation Chunking", demo_markdown_chunking),
        ("Conversation Chunking", demo_conversation_chunking),
        ("Backward Compatibility", demo_backward_compatibility),
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        try:
            result = await demo_func()
            results.append((demo_name, result))
        except Exception as e:
            print(f"Demo {demo_name} failed: {e}")
            results.append((demo_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("DEMO RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for demo_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{demo_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} demos passed")
    
    if passed == total:
        print("🎉 All demos passed! Enhanced chunking is working correctly.")
    else:
        print("⚠️  Some demos failed. Check dependencies and implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


