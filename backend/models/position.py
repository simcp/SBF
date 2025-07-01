from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    trader_id = Column(Integer, ForeignKey("traders.id", ondelete="CASCADE"), nullable=False)
    coin = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # 'LONG' or 'SHORT'
    entry_price = Column(Numeric(20, 8), nullable=False)
    size = Column(Numeric(20, 8), nullable=False)
    leverage = Column(Numeric(5, 2))
    position_value = Column(Numeric(20, 8))
    unrealized_pnl = Column(Numeric(20, 8))
    margin_used = Column(Numeric(20, 8))
    liquidation_price = Column(Numeric(20, 8))
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime)
    close_price = Column(Numeric(20, 8))
    realized_pnl = Column(Numeric(20, 8))
    status = Column(String(20), default="OPEN")  # 'OPEN', 'CLOSED'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trader = relationship("Trader", back_populates="positions")
    opportunities = relationship("TradeOpportunity", back_populates="position", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Position(trader_id={self.trader_id}, coin={self.coin}, side={self.side}, status={self.status})>"
    
    @property
    def is_open(self):
        """Check if position is still open."""
        return self.status == "OPEN"
    
    @property
    def opposite_side(self):
        """Get the opposite side for counter-trading."""
        return "SHORT" if self.side == "LONG" else "LONG"