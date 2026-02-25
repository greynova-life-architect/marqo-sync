from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import time

class ProfileType(Enum):
    USER = "user"
    AGENT = "agent"
    ORGANIZATION = "organization"

@dataclass
class UserProfile:
    profile_id: str
    profile_type: ProfileType = ProfileType.USER
    tenant_id: Optional[str] = None
    
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    
    preferences: Dict[str, Any] = field(default_factory=dict)
    current_context: Optional[str] = None
    recent_documents: List[str] = field(default_factory=list)
    favorite_categories: List[str] = field(default_factory=list)
    
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    access_level: str = "user"
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

@dataclass
class AgentProfile:
    profile_id: str
    profile_type: ProfileType = ProfileType.AGENT
    tenant_id: Optional[str] = None
    
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    
    capabilities: List[str] = field(default_factory=list)
    model_config: Dict[str, Any] = field(default_factory=dict)
    
    memory_config: Dict[str, Any] = field(default_factory=dict)
    
    personality_traits: List[str] = field(default_factory=list)
    response_style: str = "professional"
    
    current_session_id: Optional[str] = None
    active_memories: List[str] = field(default_factory=list)
    
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

@dataclass
class OrganizationProfile:
    profile_id: str
    profile_type: ProfileType = ProfileType.ORGANIZATION
    
    name: Optional[str] = None
    description: Optional[str] = None
    
    settings: Dict[str, Any] = field(default_factory=dict)
    members: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    
    shared_categories: List[str] = field(default_factory=list)
    shared_documents: List[str] = field(default_factory=list)
    
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

class ProfileManager:
    def __init__(self, marqo_client, index_name: str = "profiles"):
        self.marqo_client = marqo_client
        self.index_name = index_name
    
    def create_user_profile(self, profile: UserProfile) -> bool:
        try:
            doc = {
                "_id": profile.profile_id,
                "content": f"User profile: {profile.name or profile.profile_id}",
                **profile.to_dict()
            }
            self.marqo_client.index(self.index_name).add_documents([doc])
            return True
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False
    
    def create_agent_profile(self, profile: AgentProfile) -> bool:
        try:
            doc = {
                "_id": profile.profile_id,
                "content": f"Agent profile: {profile.name or profile.profile_id} - {profile.description or ''}",
                **profile.to_dict()
            }
            self.marqo_client.index(self.index_name).add_documents([doc])
            return True
        except Exception as e:
            print(f"Error creating agent profile: {e}")
            return False
    
    def create_organization_profile(self, profile: OrganizationProfile) -> bool:
        try:
            doc = {
                "_id": profile.profile_id,
                "content": f"Organization profile: {profile.name or profile.profile_id} - {profile.description or ''}",
                **profile.to_dict()
            }
            self.marqo_client.index(self.index_name).add_documents([doc])
            return True
        except Exception as e:
            print(f"Error creating organization profile: {e}")
            return False
    
    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        try:
            results = self.marqo_client.index(self.index_name).get_documents([profile_id])
            if results and 'results' in results and results['results']:
                return results['results'][0]
            return None
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None
    
    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> bool:
        try:
            updates['updated_at'] = time.time()
            doc = {
                "_id": profile_id,
                **updates
            }
            self.marqo_client.index(self.index_name).add_documents([doc])
            return True
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False
    
    def search_profiles(self, query: str, tenant_id: Optional[str] = None, profile_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            filter_string = None
            if tenant_id or profile_type:
                filters = []
                if tenant_id:
                    filters.append(f"tenant_id:{tenant_id}")
                if profile_type:
                    filters.append(f"profile_type:{profile_type}")
                filter_string = " AND ".join(filters)
            
            results = self.marqo_client.index(self.index_name).search(
                query,
                filter_string=filter_string,
                limit=limit
            )
            
            if results and 'hits' in results:
                return results['hits']
            return []
        except Exception as e:
            print(f"Error searching profiles: {e}")
            return []

