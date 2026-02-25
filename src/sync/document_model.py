from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class DocumentType(Enum):
    CONVERSATION = "conversation"
    DOCUMENT = "document"
    PROFILE = "profile"
    CODE = "code"
    MEMORY = "memory"
    OTHER = "other"

class ProfileType(Enum):
    USER = "user"
    AGENT = "agent"
    ORGANIZATION = "organization"

class AccessLevel(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"

class ConversationRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class DocumentMetadata:
    document_type: DocumentType
    category: str
    subcategory: Optional[str] = None
    
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    accessed_at: Optional[float] = None
    expires_at: Optional[float] = None
    
    parent_document_id: Optional[str] = None
    related_documents: List[str] = field(default_factory=list)
    conversation_thread_id: Optional[str] = None
    
    context_tags: List[str] = field(default_factory=list)
    importance_score: float = 0.5
    access_level: AccessLevel = AccessLevel.PRIVATE
    
    profile_type: Optional[ProfileType] = None
    profile_attributes: Dict[str, Any] = field(default_factory=dict)
    
    conversation_role: Optional[ConversationRole] = None
    conversation_turn: Optional[int] = None
    conversation_summary: Optional[str] = None
    
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    
    embedding_model: Optional[str] = None
    search_priority: str = "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if value is None:
                continue
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, list):
                result[key] = value
            elif isinstance(value, dict):
                result[key] = value
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        kwargs = {}
        for key, value in data.items():
            if key == 'document_type' and isinstance(value, str):
                kwargs[key] = DocumentType(value)
            elif key == 'profile_type' and isinstance(value, str):
                kwargs[key] = ProfileType(value)
            elif key == 'access_level' and isinstance(value, str):
                kwargs[key] = AccessLevel(value)
            elif key == 'conversation_role' and isinstance(value, str):
                kwargs[key] = ConversationRole(value)
            else:
                kwargs[key] = value
        return cls(**kwargs)

def create_document(
    content: str,
    document_type: DocumentType,
    category: str,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    import time
    
    metadata = DocumentMetadata(
        document_type=document_type,
        category=category,
        tenant_id=tenant_id,
        agent_id=agent_id,
        user_id=user_id,
        created_at=time.time(),
        updated_at=time.time(),
        accessed_at=time.time(),
        **kwargs
    )
    
    doc_id = f"{document_type.value}_{category}_{int(time.time())}"
    if tenant_id:
        doc_id = f"{tenant_id}_{doc_id}"
    
    return {
        "_id": doc_id,
        "content": content,
        **metadata.to_dict()
    }

