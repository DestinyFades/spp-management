from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.database import Base

class SPPVersion(Base):
    __tablename__ = "spp_versions"
    
    id = Column(Integer, primary_key=True)
    version_date = Column(Date, nullable=False)
    valid_from = Column(DateTime, default=datetime.now)
    valid_to = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    elements = relationship("SPPElement", back_populates="version")

class SPPElement(Base):
    __tablename__ = "spp_elements"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("spp_elements.id"))
    version_id = Column(Integer, ForeignKey("spp_versions.id"))
    status = Column(String(20), nullable=False)
    level = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    version = relationship("SPPVersion", back_populates="elements")
    children = relationship("SPPElement", backref="parent", remote_side=[id])
    departments = relationship("Department", secondary="element_departments")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    elements = relationship("SPPElement", secondary="element_departments")

class ElementDepartment(Base):
    __tablename__ = "element_departments"
    
    element_id = Column(Integer, ForeignKey("spp_elements.id"), primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), primary_key=True)

class SavedCalculation(Base):
    __tablename__ = "saved_calculations"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False)
    version_id = Column(Integer, ForeignKey("spp_versions.id"))
    calculation_date = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="active")
    result_data = Column(JSONB, nullable=False)
    total_amount = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
