from sqlalchemy.orm import Session
from app.models import SPPElement, SPPVersion
from typing import Dict, Optional, List

class TreeService:
    @staticmethod
    async def build_tree(version_id: int, db: Session) -> Optional[Dict]:
        elements = db.query(SPPElement).filter(
            SPPElement.version_id == version_id
        ).all()
        
        if not elements:
            return None
        
        element_map = {}
        for e in elements:
            element_map[e.id] = {
                "id": e.id,
                "code": e.code,
                "name": e.name,
                "level": e.level,
                "status": e.status,
                "departments": [d.code for d in e.departments],
                "children": []
            }
        
        root = None
        for e in elements:
            if e.parent_id and e.parent_id in element_map:
                element_map[e.parent_id]["children"].append(element_map[e.id])
            elif not e.parent_id:
                root = element_map[e.id]
        
        return root
    
    @staticmethod
    async def get_versions(db: Session) -> List[Dict]:
        versions = db.query(SPPVersion).filter(
            SPPVersion.is_current == True
        ).order_by(SPPVersion.version_date.desc()).all()
        return [{"id": v.id, "date": v.version_date.isoformat()} for v in versions]
