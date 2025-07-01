from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class TradeOpportunity(Base):
    __tablename__ = "trade_opportunities"
    
    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey("positions.id", ondelete="CASCADE"))
    trader_id = Column(Integer, ForeignKey("traders.id", ondelete="CASCADE"), nullable=False)
    coin = Column(String(20), nullable=False)
    loser_side = Column(String(10), nullable=False)
    suggested_side = Column(String(10), nullable=False)
    loser_entry_price = Column(Numeric(20, 8), nullable=False)
    suggested_entry_price = Column(Numeric(20, 8))
    confidence_score = Column(Numeric(5, 2))
    status = Column(String(20), default="ACTIVE")  # 'ACTIVE', 'EXECUTED', 'EXPIRED', 'CANCELLED'
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    expired_at = Column(DateTime)
    
    # Relationships
    position = relationship("Position", back_populates="opportunities")
    trader = relationship("Trader", back_populates="opportunities")
    our_trades = relationship("OurTrade", back_populates="opportunity", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TradeOpportunity(coin={self.coin}, loser_side={self.loser_side}, suggested_side={self.suggested_side})>"
    
    @property
    def is_active(self):
        """Check if opportunity is still active."""
        return self.status == "ACTIVE"


class OurTrade(Base):
    __tablename__ = "our_trades"
    
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey("trade_opportunities.id", ondelete="CASCADE"))
    coin = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    size = Column(Numeric(20, 8), nullable=False)
    exit_price = Column(Numeric(20, 8))
    pnl = Column(Numeric(20, 8))
    pnl_percentage = Column(Numeric(10, 2))
    status = Column(String(20), default="OPEN")
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Relationships
    opportunity = relationship("TradeOpportunity", back_populates="our_trades")
    
    def __repr__(self):
        return f"<OurTrade(coin={self.coin}, side={self.side}, status={self.status})>"