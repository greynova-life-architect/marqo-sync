# Unified Indexing System

## Overview

The Marqo Sync service now uses a **unified indexing approach** that creates only **3 indexes** instead of separate indexes for each project or conversation type. This provides better search capabilities and more efficient resource usage.

## Index Structure

### 1. `codebase` Index
- **Purpose**: All source code from all projects
- **Projects**: `project-a`, `project-b`, and future projects
- **Metadata Fields**:
  - `project_id`: Identifies which project the code belongs to
  - `index_type`: Always "codebase"
  - `file_type`: File extension (e.g., ".py", ".js", ".ts")
  - Standard file metadata (size, modified date, etc.)

### 2. `codex` Index  
- **Purpose**: All folder structure information
- **Projects**: `project-a`, `project-b`, and future projects
- **Metadata Fields**:
  - `project_id`: Identifies which project the structure belongs to
  - `index_type`: Always "codex"
  - Standard file metadata

### 3. `conversations` Index
- **Purpose**: All conversation/chat history
- **Types**: `chatgpt`, `claude`, and future AI services
- **Metadata Fields**:
  - `conversation_type`: Identifies the AI service (chatgpt, claude, etc.)
  - `index_type`: Always "conversations"
  - Standard file metadata

## Configuration

### Environment Variables

```bash
# Unified codebase configuration - all projects go into single 'codebase' index
SYNC_CODEBASES=project-a:./projects/project-a,project-b:./projects/project-b

# Unified codex configuration - all projects go into single 'codex' index  
SYNC_CODEX=project-a:./projects/project-a,project-b:./projects/project-b

# Unified conversation configuration - all types go into single 'conversations' index
SYNC_CONVERSATIONS=chatgpt:./data/chatgpt,claude:./data/claude
```

### Format
- **Projects**: `name:path,name2:path2,...`
- **Conversations**: `type:path,type2:path2,...`

## Search Capabilities

### Filtering by Project
```python
# Search only project-a codebase
results = marqo_client.index("codebase").search(
    q="authentication logic",
    filter_string="project_id:project-a"
)

# Search only project-b codex
results = marqo_client.index("codex").search(
    q="folder structure",
    filter_string="project_id:project-b"
)
```

### Filtering by Conversation Type
```python
# Search only ChatGPT conversations
results = marqo_client.index("conversations").search(
    q="machine learning discussion",
    filter_string="conversation_type:chatgpt"
)

# Search only Claude conversations
results = marqo_client.index("conversations").search(
    q="code review",
    filter_string="conversation_type:claude"
)
```

### Cross-Project Search
```python
# Search across all projects in codebase
results = marqo_client.index("codebase").search(
    q="database connection",
    # No filter - searches all projects
)

# Search across all conversation types
results = marqo_client.index("conversations").search(
    q="API design",
    # No filter - searches all conversation types
)
```

## Migration from Old System

### Before (Multiple Indexes)
- `codebase_project-a`
- `codebase_project-b`
- `codex_project-a_structure`
- `codex_project-b_structure`
- `conversation_chatgpt`
- `conversation_claude`

### After (Unified Indexes)
- `codebase` (with `project_id` metadata)
- `codex` (with `project_id` metadata)
- `conversations` (with `conversation_type` metadata)

## Benefits

1. **Simplified Management**: Only 3 indexes to manage instead of 6+
2. **Better Search**: Can search across all projects or filter by specific project
3. **Efficient Resource Usage**: Fewer indexes means less memory and storage overhead
4. **Scalable**: Easy to add new projects or conversation types without creating new indexes
5. **Consistent Metadata**: All documents have consistent metadata structure

## Implementation Details

### Indexer Context
Each indexer now supports context setting:
- `set_project_context(project_id, project_path)` for codebase/codex indexers
- `set_conversation_context(conversation_type, conversation_path)` for conversation indexers

### Metadata Enhancement
The system automatically adds appropriate metadata to each document:
- `project_id` for codebase/codex documents
- `conversation_type` for conversation documents
- `index_type` to identify the index type

### File Watching
The system creates separate file watchers for each project/type while indexing to a unified index, ensuring real-time updates are properly tagged with the correct metadata.

## Usage Examples

### Adding a New Project
1. Update `SYNC_CODEBASES` environment variable:
   ```bash
   SYNC_CODEBASES=project-a:./projects/project-a,project-b:./projects/project-b,newproject:./projects/newproject
   ```
2. Restart the sync service
3. The new project will be indexed into the existing `codebase` index with `project_id:newproject`

### Adding a New Conversation Type
1. Update `SYNC_CONVERSATIONS` environment variable:
   ```bash
   SYNC_CONVERSATIONS=chatgpt:M:\path\to\chatgpt,claude:M:\path\to\claude,gemini:M:\path\to\gemini
   ```
2. Restart the sync service
3. The new conversation type will be indexed into the existing `conversations` index with `conversation_type:gemini`
