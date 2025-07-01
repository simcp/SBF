from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class Trader(Base):
    __tablename__ = "traders"
    
    id = Column(Integer, primary_key=True)
    address = Column(String(42), unique=True, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    performance_history = relationship("TraderPerformance", back_populates="trader", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="trader", cascade="all, delete-orphan")
    opportunities = relationship("TradeOpportunity", back_populates="trader", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Trader(address={self.address}, id={self.id})>"
    
    @property
    def short_address(self):
        """Return shortened address for display."""
        return f"{self.address[:6]}...{self.address[-4:]}"