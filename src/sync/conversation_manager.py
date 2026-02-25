from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time
from enum import Enum

class ConversationStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"

@dataclass
class ConversationMetadata:
    conversation_id: str
    thread_id: str
    tenant_id: Optional[str] = None
    
    participants: Dict[str, List[str]] = field(default_factory=dict)
    
    topic: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    status: ConversationStatus = ConversationStatus.ACTIVE
    current_turn: int = 0
    total_turns: int = 0
    
    started_at: float = field(default_factory=time.time)
    last_message_at: float = field(default_factory=time.time)
    archived_at: Optional[float] = None
    
    related_conversations: List[str] = field(default_factory=list)
    related_documents: List[str] = field(default_factory=list)
    
    summary: Optional[str] = None
    key_points: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

@dataclass
class ConversationMessage:
    message_id: str
    conversation_id: str
    thread_id: str
    
    role: str
    content: str
    
    turn_number: int
    timestamp: float = field(default_factory=time.time)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self.message_id,
            "content": self.content,
            "conversation_id": self.conversation_id,
            "thread_id": self.thread_id,
            "role": self.role,
            "turn_number": self.turn_number,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

class ConversationManager:
    def __init__(self, marqo_client, conversation_index: str = "conversations", message_index: str = "conversation_messages"):
        self.marqo_client = marqo_client
        self.conversation_index = conversation_index
        self.message_index = message_index
    
    def create_conversation(self, metadata: ConversationMetadata) -> bool:
        try:
            doc = {
                "_id": metadata.conversation_id,
                "content": f"Conversation: {metadata.topic or 'Untitled'}",
                **metadata.to_dict()
            }
            self.marqo_client.index(self.conversation_index).add_documents([doc])
            return True
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return False
    
    def add_message(self, message: ConversationMessage) -> bool:
        try:
            doc = message.to_dict()
            self.marqo_client.index(self.message_index).add_documents([doc])
            
            self.update_conversation_metadata(
                message.conversation_id,
                {
                    "current_turn": message.turn_number,
                    "total_turns": message.turn_number,
                    "last_message_at": message.timestamp
                }
            )
            return True
        except Exception as e:
            print(f"Error adding message: {e}")
            return False
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        try:
            results = self.marqo_client.index(self.conversation_index).get_documents([conversation_id])
            if results and 'results' in results and results['results']:
                return results['results'][0]
            return None
        except Exception as e:
            print(f"Error getting conversation: {e}")
            return None
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            results = self.marqo_client.index(self.message_index).search(
                "",
                filter_string=f"conversation_id:{conversation_id}",
                limit=limit,
                sort=["turn_number:asc"]
            )
            if results and 'hits' in results:
                return results['hits']
            return []
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def update_conversation_metadata(self, conversation_id: str, updates: Dict[str, Any]) -> bool:
        try:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            for key, value in updates.items():
                conversation[key] = value
            
            self.marqo_client.index(self.conversation_index).add_documents([conversation])
            return True
        except Exception as e:
            print(f"Error updating conversation: {e}")
            return False
    
    def archive_conversation(self, conversation_id: str) -> bool:
        return self.update_conversation_metadata(
            conversation_id,
            {
                "status": ConversationStatus.ARCHIVED.value,
                "archived_at": time.time()
            }
        )
    
    def search_conversations(self, query: str, tenant_id: Optional[str] = None, status: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            filter_string = None
            filters = []
            if tenant_id:
                filters.append(f"tenant_id:{tenant_id}")
            if status:
                filters.append(f"status:{status}")
            if filters:
                filter_string = " AND ".join(filters)
            
            results = self.marqo_client.index(self.conversation_index).search(
                query,
                filter_string=filter_string,
                limit=limit
            )
            
            if results and 'hits' in results:
                return results['hits']
            return []
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []

