from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Date, Numeric, DateTime
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class TraderPerformance(Base):
    __tablename__ = "trader_performance"
    
    id = Column(Integer, primary_key=True)
    trader_id = Column(Integer, ForeignKey("traders.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    pnl_percentage = Column(Numeric(10, 2))
    pnl_absolute = Column(Numeric(20, 8))
    win_rate = Column(Numeric(5, 2))
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    avg_win = Column(Numeric(20, 8))
    avg_loss = Column(Numeric(20, 8))
    account_value = Column(Numeric(20, 8))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trader = relationship("Trader", back_populates="performance_history")
    
    def __repr__(self):
        return f"<TraderPerformance(trader_id={self.trader_id}, date={self.date}, pnl%={self.pnl_percentage})>"
    
    @property
    def is_profitable(self):
        """Check if trader was profitable on this date."""
        return self.pnl_percentage > 0 if self.pnl_percentage else False