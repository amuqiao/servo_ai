from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, distinct
from sqlalchemy.orm import Session
from src.models.power_plant_model import PowerPlantModel
from src.configs.database import get_db_conn
from pydantic import BaseModel


class PowerNumberResponse(BaseModel):
    data: list[str]

    class Config:
        orm_mode = True


class BasePlantResponse(BaseModel):
    data: list[dict]

    class Config:
        orm_mode = True

router = APIRouter(prefix="/api/power-plants", tags=["电站管理"])

@router.get("/power-numbers", response_model=PowerNumberResponse)
async def get_power_numbers(company_id: int, db: Session = Depends(get_db_conn)):
    try:
        result = db.execute(
            select(distinct(PowerPlantModel.power_number))
            .where(PowerPlantModel.company_id == company_id)
        )
        numbers = result.scalars().all()
        return {"data": numbers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询异常: {str(e)}")

@router.get("/", response_model=BasePlantResponse)
async def get_plants(limit: int = 10, db: Session = Depends(get_db_conn)):
    if limit <= 0:
        raise HTTPException(status_code=400, detail="查询数量必须大于0")
    
    try:
        result = db.execute(
            select(PowerPlantModel)
            .limit(limit)
        )
        plants = result.scalars().all()
        return {"data": [{"id": p.id, "power_number": p.power_number} for p in plants]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询异常: {str(e)}")