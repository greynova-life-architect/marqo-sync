from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time
from enum import Enum

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

@dataclass
class Memory:
    memory_id: str
    memory_type: MemoryType
    
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    related_memories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

class MemoryManager:
    def __init__(self, marqo_client, index_name: str = "memories"):
        self.marqo_client = marqo_client
        self.index_name = index_name
    
    def store_memory(self, memory: Memory) -> bool:
        try:
            doc = {
                "_id": memory.memory_id,
                "content": memory.content,
                **memory.to_dict()
            }
            self.marqo_client.index(self.index_name).add_documents([doc])
            return True
        except Exception as e:
            print(f"Error storing memory: {e}")
            return False
    
    def retrieve_memories(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            filters = []
            if tenant_id:
                filters.append(f"tenant_id:{tenant_id}")
            if agent_id:
                filters.append(f"agent_id:{agent_id}")
            if user_id:
                filters.append(f"user_id:{user_id}")
            if memory_type:
                filters.append(f"memory_type:{memory_type}")
            if min_importance > 0:
                filters.append(f"importance_score:>={min_importance}")
            
            filter_string = " AND ".join(filters) if filters else None
            
            results = self.marqo_client.index(self.index_name).search(
                query,
                filter_string=filter_string,
                limit=limit
            )
            
            if results and 'hits' in results:
                for hit in results['hits']:
                    self._update_access(hit.get('_id'))
                return results['hits']
            return []
        except Exception as e:
            print(f"Error retrieving memories: {e}")
            return []
    
    def _update_access(self, memory_id: str):
        try:
            results = self.marqo_client.index(self.index_name).get_documents([memory_id])
            if results and 'results' in results and results['results']:
                memory = results['results'][0]
                memory['access_count'] = memory.get('access_count', 0) + 1
                memory['last_accessed'] = time.time()
                self.marqo_client.index(self.index_name).add_documents([memory])
        except Exception as e:
            print(f"Error updating memory access: {e}")
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        try:
            results = self.marqo_client.index(self.index_name).get_documents([memory_id])
            if results and 'results' in results and results['results']:
                memory = results['results'][0]
                self._update_access(memory_id)
                return memory
            return None
        except Exception as e:
            print(f"Error getting memory: {e}")
            return None
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        try:
            memory = self.get_memory(memory_id)
            if not memory:
                return False
            
            for key, value in updates.items():
                memory[key] = value
            memory['updated_at'] = time.time()
            
            self.marqo_client.index(self.index_name).add_documents([memory])
            return True
        except Exception as e:
            print(f"Error updating memory: {e}")
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        try:
            self.marqo_client.index(self.index_name).delete_documents([memory_id])
            return True
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False
    
    def get_related_memories(self, memory_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            memory = self.get_memory(memory_id)
            if not memory or not memory.get('related_memories'):
                return []
            
            related_ids = memory['related_memories'][:limit]
            results = self.marqo_client.index(self.index_name).get_documents(related_ids)
            if results and 'results' in results:
                return results['results']
            return []
        except Exception as e:
            print(f"Error getting related memories: {e}")
            return []

