from sqlalchemy import Column, String, Integer
from src.configs.database import Base

class PowerPlantModel(Base):
    __tablename__ = 'pomp_power_plant_basic'

    id = Column(String(50), primary_key=True, comment='电站ID')
    power_number = Column(String(100), nullable=False, comment='电站编号')
    company_id = Column(Integer, nullable=False, comment='所属公司ID')

    def __repr__(self):
        return f"<PowerPlant(id={self.id}, power_number='{self.power_number}')>"