from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time

@dataclass
class Category:
    category_id: str
    name: str
    description: Optional[str] = None
    
    parent_category_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    document_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self.category_id,
            "content": f"Category: {self.name} - {self.description or ''}",
            **{k: v for k, v in self.__dict__.items() if k != 'category_id'}
        }

class CategoryManager:
    def __init__(self, marqo_client, index_name: str = "categories"):
        self.marqo_client = marqo_client
        self.index_name = index_name
    
    def create_category(self, category: Category) -> bool:
        try:
            doc = category.to_dict()
            doc["_id"] = category.category_id
            self.marqo_client.index(self.index_name).add_documents([doc])
            return True
        except Exception as e:
            print(f"Error creating category: {e}")
            return False
    
    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        try:
            results = self.marqo_client.index(self.index_name).get_documents([category_id])
            if results and 'results' in results and results['results']:
                return results['results'][0]
            return None
        except Exception as e:
            print(f"Error getting category: {e}")
            return None
    
    def update_category(self, category_id: str, updates: Dict[str, Any]) -> bool:
        try:
            category = self.get_category(category_id)
            if not category:
                return False
            
            for key, value in updates.items():
                category[key] = value
            category['updated_at'] = time.time()
            
            self.marqo_client.index(self.index_name).add_documents([category])
            return True
        except Exception as e:
            print(f"Error updating category: {e}")
            return False
    
    def delete_category(self, category_id: str) -> bool:
        try:
            self.marqo_client.index(self.index_name).delete_documents([category_id])
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
            return False
    
    def list_categories(self, tenant_id: Optional[str] = None, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            filters = []
            if tenant_id:
                filters.append(f"tenant_id:{tenant_id}")
            if parent_id:
                filters.append(f"parent_category_id:{parent_id}")
            elif parent_id is None:
                filters.append("parent_category_id:null")
            
            filter_string = " AND ".join(filters) if filters else None
            
            results = self.marqo_client.index(self.index_name).search(
                "",
                filter_string=filter_string,
                limit=100
            )
            
            if results and 'hits' in results:
                return results['hits']
            return []
        except Exception as e:
            print(f"Error listing categories: {e}")
            return []
    
    def get_category_tree(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            all_categories = self.list_categories(tenant_id=tenant_id)
            
            root_categories = [c for c in all_categories if not c.get('parent_category_id')]
            category_map = {c['_id']: c for c in all_categories}
            
            def build_tree(category):
                children = [c for c in all_categories if c.get('parent_category_id') == category['_id']]
                category['children'] = [build_tree(child) for child in children]
                return category
            
            tree = [build_tree(root) for root in root_categories]
            return {"tree": tree, "map": category_map}
        except Exception as e:
            print(f"Error building category tree: {e}")
            return {"tree": [], "map": {}}

