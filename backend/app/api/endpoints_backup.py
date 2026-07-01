from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json
import uuid
import logging
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db, get_redis
from app.models import SPPVersion, SPPElement, Department, SavedCalculation
from app.services.tree_service import TreeService
from app.services.distribution import DistributionService
from app.services.export import ExportService
from app.services.sse_manager import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pydantic модели ---
class ElementCreate(BaseModel):
    code: str
    name: str
    parent_id: Optional[int] = None
    status: str = "Действующий"
    level: int = 1
    department_ids: List[int] = []

class ElementUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    department_ids: Optional[List[int]] = None

class DistributionRequest(BaseModel):
    version_id: int
    selected_ids: List[int]
    total_amount: float

# --- Эндпоинты ---
@router.get("/tree/{version_id}")
async def get_tree(version_id: int, db: Session = Depends(get_db)):
    tree = await TreeService.build_tree(version_id, db)
    if not tree:
        raise HTTPException(404, "Версия не найдена")
    return tree

@router.get("/dates")
async def get_dates(db: Session = Depends(get_db)):
    return await TreeService.get_versions(db)

# --- CRUD для элементов ---
@router.post("/elements", status_code=status.HTTP_201_CREATED)
async def create_element(
    element: ElementCreate,
    db: Session = Depends(get_db)
):
    new_version = SPPVersion(version_date=datetime.now().date())
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    
    new_element = SPPElement(
        code=element.code,
        name=element.name,
        parent_id=element.parent_id,
        version_id=new_version.id,
        status=element.status,
        level=element.level
    )
    db.add(new_element)
    db.commit()
    db.refresh(new_element)
    
    if element.department_ids:
        depts = db.query(Department).filter(Department.id.in_(element.department_ids)).all()
        new_element.departments = depts
        db.commit()
    
    return new_element

@router.put("/elements/{element_id}")
async def update_element(
    element_id: int,
    element: ElementUpdate,
    db: Session = Depends(get_db)
):
    current = db.query(SPPElement).filter(SPPElement.id == element_id).first()
    if not current:
        raise HTTPException(404, "Элемент не найден")
    
    version = db.query(SPPVersion).filter(SPPVersion.id == current.version_id).first()
    if version:
        version.is_current = False
        version.valid_to = datetime.now()
        db.commit()
    
    new_version = SPPVersion(version_date=datetime.now().date())
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    
    if element.code:
        current.code = element.code
    if element.name:
        current.name = element.name
    if element.status:
        current.status = element.status
    current.version_id = new_version.id
    db.commit()
    
    if element.department_ids is not None:
        depts = db.query(Department).filter(Department.id.in_(element.department_ids)).all()
        current.departments = depts
        db.commit()
    
    return current

@router.delete("/elements/{element_id}")
async def delete_element(
    element_id: int,
    db: Session = Depends(get_db)
):
    element = db.query(SPPElement).filter(SPPElement.id == element_id).first()
    if not element:
        raise HTTPException(404, "Элемент не найден")
    
    element.status = "Недействующий"
    db.commit()
    
    return {"message": "Элемент деактивирован"}

# --- Распределение ---
@router.post("/distribute")
async def distribute(
    request: DistributionRequest,
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    try:
        logger.info(f"Распределение: version_id={request.version_id}, selected_ids={request.selected_ids}, total={request.total_amount}")
        
        tree = await TreeService.build_tree(request.version_id, db)
        if not tree:
            raise HTTPException(404, "Версия не найдена")
        
        existing_ids = set()
        def collect_ids(node):
            existing_ids.add(node["id"])
            for child in node.get("children", []):
                collect_ids(child)
        collect_ids(tree)
        
        for sid in request.selected_ids:
            if sid not in existing_ids:
                raise HTTPException(400, f"Элемент с ID {sid} не найден в дереве")
        
        result = await DistributionService.distribute(
            request.selected_ids,
            request.total_amount,
            tree
        )
        
        calc_id = str(uuid.uuid4())
        calc_data = {
            "id": calc_id,
            "tree": result,
            "version_id": request.version_id,
            "total_amount": request.total_amount,
            "created_at": datetime.now().isoformat()
        }
        
        redis.setex(f"calc:{calc_id}", 3600, json.dumps(calc_data))
        await sse_manager.publish(calc_id, result)
        
        return {"calc_id": calc_id, "tree": result}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Ошибка распределения: {e}")
        raise HTTPException(500, f"Ошибка распределения: {str(e)}")

@router.post("/save/{calc_id}")
async def save_calculation(
    calc_id: str,
    session_id: str = "default",
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    try:
        data = redis.get(f"calc:{calc_id}")
        if not data:
            raise HTTPException(404, "Расчёт не найден или истёк TTL")
        
        calc_data = json.loads(data)
        
        saved = SavedCalculation(
            session_id=session_id,
            version_id=calc_data["version_id"],
            result_data=calc_data["tree"],
            total_amount=calc_data["total_amount"]
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)
        
        redis.delete(f"calc:{calc_id}")
        await sse_manager.notify_session(session_id, saved.id)
        
        return {"id": saved.id, "status": "saved"}
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        raise HTTPException(500, f"Ошибка сохранения: {str(e)}")

@router.get("/saved/{session_id}")
async def get_saved_calculations(session_id: str, db: Session = Depends(get_db)):
    try:
        calculations = db.query(SavedCalculation).filter(
            SavedCalculation.session_id == session_id
        ).order_by(SavedCalculation.created_at.desc()).all()
        
        return [{
            "id": c.id,
            "version_id": c.version_id,
            "total_amount": c.total_amount,
            "created_at": c.created_at.isoformat(),
            "status": c.status
        } for c in calculations]
    except Exception as e:
        logger.error(f"Ошибка получения сохраненных расчетов: {e}")
        raise HTTPException(500, str(e))

@router.get("/saved/{calc_id}/load")
async def load_saved_calculation(calc_id: int, db: Session = Depends(get_db)):
    try:
        calculation = db.query(SavedCalculation).filter(
            SavedCalculation.id == calc_id
        ).first()
        
        if not calculation:
            raise HTTPException(404, "Расчёт не найден")
        
        return {
            "id": calculation.id,
            "tree": calculation.result_data,
            "total_amount": calculation.total_amount,
            "created_at": calculation.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки сохраненного расчета: {e}")
        raise HTTPException(500, str(e))

@router.get("/export/{calc_id}")
async def export_excel(calc_id: int, db: Session = Depends(get_db)):
    try:
        calculation = db.query(SavedCalculation).filter(
            SavedCalculation.id == calc_id
        ).first()
        
        if not calculation:
            raise HTTPException(404, "Расчёт не найден")
        
        excel_file = await ExportService.generate_excel(
            calculation.result_data,
            calculation.total_amount
        )
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=calc_{calc_id}.xlsx"}
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")
        raise HTTPException(500, f"Ошибка экспорта: {str(e)}")

