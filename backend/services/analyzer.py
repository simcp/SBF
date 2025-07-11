import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.database.connection import get_db
from backend.models import Trader, Position, TradeOpportunity, TraderPerformance
from backend.services.hyperliquid_api import HyperliquidAPI

logger = logging.getLogger(__name__)


class TradingAnalyzer:
    """Analyzes trader positions and generates counter-trading opportunities."""
    
    def __init__(self):
        self.api = HyperliquidAPI()
        self.confidence_threshold = 70.0  # Minimum confidence score to generate opportunity
        logger.info("Initialized TradingAnalyzer")
    
    def analyze_new_positions(self) -> List[TradeOpportunity]:
        """Analyze recently opened positions and generate opportunities."""
        opportunities = []
        
        try:
            with get_db() as db:
                # Get positions opened in the last hour that haven't been analyzed
                recent_positions = self._get_recent_positions(db)
                
                for position in recent_positions:
                    # Check if we already created an opportunity for this position
                    existing = db.query(TradeOpportunity).filter_by(
                        position_id=position.id
                    ).first()
                    
                    if not existing:
                        opportunity = self._analyze_position(db, position)
                        if opportunity:
                            db.add(opportunity)
                            opportunities.append(opportunity)
                
                db.commit()
                logger.info(f"Generated {len(opportunities)} new trade opportunities")
                
        except Exception as e:
            logger.error(f"Error analyzing positions: {e}")
        
        return opportunities
    
    def _get_recent_positions(self, db: Session, hours: int = 1) -> List[Position]:
        """Get positions opened in the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        positions = db.query(Position).join(Trader).filter(
            and_(
                Position.opened_at >= cutoff_time,
                Position.status == "OPEN",
                Trader.is_active == True
            )
        ).all()
        
        return positions
    
    def _analyze_position(self, db: Session, position: Position) -> Optional[TradeOpportunity]:
        """Analyze a single position and generate opportunity if criteria met."""
        # Get trader's performance metrics
        trader_metrics = self._get_trader_metrics(db, position.trader_id)
        
        if not trader_metrics:
            return None
        
        # Calculate confidence score based on how bad the trader is
        confidence = self._calculate_confidence_score(trader_metrics)
        
        if confidence < self.confidence_threshold:
            return None
        
        # Get current market price for suggested entry
        mids = self.api.get_all_mids()
        current_price = mids.get(position.coin, float(position.entry_price))
        
        # Create opportunity
        opportunity = TradeOpportunity(
            position_id=position.id,
            trader_id=position.trader_id,
            coin=position.coin,
            loser_side=position.side,
            suggested_side=position.opposite_side,
            loser_entry_price=position.entry_price,
            suggested_entry_price=Decimal(str(current_price)),
            confidence_score=Decimal(str(confidence)),
            status="ACTIVE"
        )
        
        logger.info(
            f"Generated opportunity: {position.trader.address} went {position.side} {position.coin}, "
            f"suggesting {opportunity.suggested_side} with {confidence:.1f}% confidence"
        )
        
        return opportunity
    
    def _get_trader_metrics(self, db: Session, trader_id: int) -> Optional[Dict[str, Any]]:
        """Get trader's 30-day performance metrics."""
        # Get average metrics for last 30 days
        thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
        
        metrics = db.query(
            TraderPerformance.trader_id,
            func.avg(TraderPerformance.pnl_percentage).label("avg_pnl_percentage"),
            func.avg(TraderPerformance.win_rate).label("avg_win_rate"),
            func.sum(TraderPerformance.total_trades).label("total_trades"),
            func.sum(TraderPerformance.losing_trades).label("total_losing_trades")
        ).filter(
            and_(
                TraderPerformance.trader_id == trader_id,
                TraderPerformance.date >= thirty_days_ago
            )
        ).group_by(TraderPerformance.trader_id).first()
        
        if not metrics:
            return None
        
        return {
            "avg_pnl_percentage": float(metrics.avg_pnl_percentage) if metrics.avg_pnl_percentage else 0,
            "avg_win_rate": float(metrics.avg_win_rate) if metrics.avg_win_rate else 0,
            "total_trades": metrics.total_trades or 0,
            "total_losing_trades": metrics.total_losing_trades or 0
        }
    
    def _calculate_confidence_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence score based on trader metrics."""
        # Base confidence on multiple factors
        pnl_factor = min(abs(metrics["avg_pnl_percentage"]) / 100 * 50, 50)  # Max 50 points
        win_rate_factor = max(0, (100 - metrics["avg_win_rate"]) / 100 * 30)  # Max 30 points
        trade_count_factor = min(metrics["total_trades"] / 100 * 20, 20)  # Max 20 points
        
        confidence = pnl_factor + win_rate_factor + trade_count_factor
        
        # Bonus for extremely bad traders
        if metrics["avg_pnl_percentage"] < -50 and metrics["avg_win_rate"] < 25:
            confidence = min(confidence + 10, 100)
        
        return min(confidence, 100)
    
    def get_active_opportunities(self) -> List[Dict[str, Any]]:
        """Get all active trading opportunities."""
        logger.info("get_active_opportunities called")
        try:
            with get_db() as db:
                # Query opportunities with their positions and traders
                opportunities = db.query(TradeOpportunity).filter_by(
                    status="ACTIVE"
                ).join(Trader).outerjoin(Position).all()
                
                logger.info(f"Found {len(opportunities)} active opportunities")
                
                results = []
                for opp in opportunities:
                    result = {
                        "id": opp.id,
                        "trader_address": opp.trader.address,
                        "coin": opp.coin,
                        "loser_side": opp.loser_side,
                        "suggested_side": opp.suggested_side,
                        "loser_entry_price": float(opp.loser_entry_price),
                        "suggested_entry_price": float(opp.suggested_entry_price) if opp.suggested_entry_price else None,
                        "confidence_score": float(opp.confidence_score),
                        "transaction_hash": opp.position.transaction_hash if opp.position else None,
                        "created_at": opp.created_at.isoformat(),
                        # Raw data
                        "position_size": float(opp.position.size) if opp.position else None,
                        "position_value": float(opp.position.position_value) if opp.position and opp.position.position_value else None,
                        "leverage": float(opp.position.leverage) if opp.position and opp.position.leverage else None,
                        "unrealized_pnl": float(opp.position.unrealized_pnl) if opp.position and opp.position.unrealized_pnl else None,
                        "opened_at": (opp.position.opened_at.isoformat() if opp.position and opp.position.opened_at 
                                    else opp.created_at.isoformat()),
                        # Formatted display strings (ready for frontend)
                        "formatted_size": self._format_size(opp.position.size if opp.position else None, opp.coin),
                        "formatted_price": f"${float(opp.loser_entry_price):.4f}",
                        "formatted_leverage": f"{float(opp.position.leverage)}x" if opp.position and opp.position.leverage else None,
                        "formatted_pnl": self._format_currency(opp.position.unrealized_pnl if opp.position and opp.position.unrealized_pnl else None),
                        "formatted_time_ago": self._get_time_ago(opp.position.opened_at if opp.position and opp.position.opened_at else opp.created_at),
                        "explorer_url": self._get_explorer_url(opp.trader.address, opp.position.transaction_hash if opp.position else None)
                    }
                    results.append(result)
                
                logger.info(f"Returning {len(results)} opportunities")
                logger.info(f"First opportunity: {results[0] if results else 'None'}")
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting active opportunities: {e}", exc_info=True)
            return []
    
    def expire_old_opportunities(self, hours: int = 24):
        """Expire opportunities older than specified hours."""
        try:
            with get_db() as db:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                
                expired_count = db.query(TradeOpportunity).filter(
                    and_(
                        TradeOpportunity.status == "ACTIVE",
                        TradeOpportunity.created_at < cutoff_time
                    )
                ).update({
                    "status": "EXPIRED",
                    "expired_at": datetime.utcnow()
                })
                
                db.commit()
                
                if expired_count > 0:
                    logger.info(f"Expired {expired_count} old opportunities")
                    
        except Exception as e:
            logger.error(f"Error expiring opportunities: {e}")
    
    def _format_size(self, size, coin):
        """Format position size for display."""
        if not size:
            return ""
        size = float(size)
        if size >= 1000000:
            return f"{(size / 1000000):.1f}M"
        if size >= 1000:
            return f"{(size / 1000):.1f}K"
        # Different precision for different coins
        if coin == 'BTC':
            return f"{size:.4f}"
        elif coin == 'ETH':
            return f"{size:.3f}"
        else:
            return f"{size:.1f}"
    
    def _format_currency(self, amount):
        """Format currency amount for display."""
        if amount is None:
            return None
        amount = float(amount)
        if abs(amount) >= 1000000:
            return f"${(amount / 1000000):.1f}M"
        if abs(amount) >= 1000:
            return f"${(amount / 1000):.1f}K"
        return f"${amount:.0f}"
    
    def _get_time_ago(self, timestamp):
        """Get formatted time ago string."""
        if not timestamp:
            return ""
        
        from datetime import datetime
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        now = datetime.utcnow()
        if timestamp.tzinfo:
            import pytz
            now = now.replace(tzinfo=pytz.UTC)
            
        diff = now - timestamp
        total_seconds = int(diff.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        elif total_seconds < 3600:
            return f"{total_seconds // 60}m ago"
        elif total_seconds < 86400:
            return f"{total_seconds // 3600}h ago"
        else:
            return f"{total_seconds // 86400}d ago"
    
    def _get_explorer_url(self, trader_address, transaction_hash):
        """Get appropriate Hyperliquid explorer URL."""
        if transaction_hash and transaction_hash != "0x0000000000000000000000000000000000000000000000000000000000000000":
            return f"https://app.hyperliquid.xyz/explorer/tx/{transaction_hash}"
        return f"https://app.hyperliquid.xyz/explorer/address/{trader_address}"


# Add missing import
from sqlalchemy import func