import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.connection import get_db
from backend.models import Trader, TraderPerformance, Position
from backend.services.hyperliquid_api import HyperliquidAPI

logger = logging.getLogger(__name__)


class DataCollector:
    """Service for collecting and storing trader data from Hyperliquid."""
    
    def __init__(self):
        self.api = HyperliquidAPI()
        logger.info("Initialized DataCollector")
    
    def collect_trader_data(self, address: str) -> bool:
        """Collect and store all data for a single trader."""
        try:
            with get_db() as db:
                # Get or create trader
                trader = self._get_or_create_trader(db, address)
                
                # Update performance metrics
                self._update_trader_performance(db, trader)
                
                # Update positions
                self._update_trader_positions(db, trader)
                
                # Update last_updated timestamp
                trader.last_updated = datetime.utcnow()
                db.commit()
                
                logger.info(f"Successfully collected data for trader {address}")
                return True
                
        except Exception as e:
            logger.error(f"Error collecting data for trader {address}: {e}")
            return False
    
    def collect_multiple_traders(self, addresses: List[str]) -> Dict[str, bool]:
        """Collect data for multiple traders."""
        results = {}
        for address in addresses:
            results[address] = self.collect_trader_data(address)
        return results
    
    def _get_or_create_trader(self, db: Session, address: str) -> Trader:
        """Get existing trader or create new one."""
        trader = db.query(Trader).filter_by(address=address).first()
        if not trader:
            trader = Trader(address=address)
            db.add(trader)
            db.commit()
            logger.info(f"Created new trader record for {address}")
        return trader
    
    def _update_trader_performance(self, db: Session, trader: Trader):
        """Update trader's performance metrics."""
        # Calculate performance for last 30 days
        performance = self.api.calculate_trader_performance(trader.address, days=30)
        
        # Check if we already have today's performance record
        today = date.today()
        existing = db.query(TraderPerformance).filter_by(
            trader_id=trader.id,
            date=today
        ).first()
        
        if existing:
            # Update existing record
            existing.pnl_percentage = performance["pnl_percentage"]
            existing.pnl_absolute = performance["pnl_absolute"]
            existing.win_rate = performance["win_rate"]
            existing.total_trades = performance["total_trades"]
            existing.winning_trades = performance["winning_trades"]
            existing.losing_trades = performance["losing_trades"]
            existing.avg_win = performance["avg_win"]
            existing.avg_loss = performance["avg_loss"]
            existing.account_value = performance["account_value"]
        else:
            # Create new record
            perf_record = TraderPerformance(
                trader_id=trader.id,
                date=today,
                pnl_percentage=performance["pnl_percentage"],
                pnl_absolute=performance["pnl_absolute"],
                win_rate=performance["win_rate"],
                total_trades=performance["total_trades"],
                winning_trades=performance["winning_trades"],
                losing_trades=performance["losing_trades"],
                avg_win=performance["avg_win"],
                avg_loss=performance["avg_loss"],
                account_value=performance["account_value"]
            )
            db.add(perf_record)
    
    def _update_trader_positions(self, db: Session, trader: Trader):
        """Update trader's current positions."""
        # Get current positions from API
        api_positions = self.api.get_open_positions(trader.address)
        
        # Get existing open positions from DB
        db_positions = db.query(Position).filter_by(
            trader_id=trader.id,
            status="OPEN"
        ).all()
        
        # Create a mapping of existing positions
        existing_map = {
            (pos.coin, pos.side): pos for pos in db_positions
        }
        
        # Track which positions we've seen
        seen_positions = set()
        
        # Update or create positions
        for api_pos in api_positions:
            key = (api_pos["coin"], api_pos["side"])
            seen_positions.add(key)
            
            if key in existing_map:
                # Update existing position
                pos = existing_map[key]
                pos.size = api_pos["size"]
                pos.unrealized_pnl = api_pos["unrealized_pnl"]
                pos.position_value = api_pos["position_value"]
                pos.leverage = api_pos["leverage"]
                pos.liquidation_price = api_pos["liquidation_price"]
                pos.margin_used = api_pos["margin_used"]
                pos.updated_at = datetime.utcnow()
            else:
                # Create new position
                new_pos = Position(
                    trader_id=trader.id,
                    coin=api_pos["coin"],
                    side=api_pos["side"],
                    entry_price=api_pos["entry_price"],
                    size=api_pos["size"],
                    leverage=api_pos["leverage"],
                    position_value=api_pos["position_value"],
                    unrealized_pnl=api_pos["unrealized_pnl"],
                    margin_used=api_pos["margin_used"],
                    liquidation_price=api_pos["liquidation_price"],
                    opened_at=datetime.utcnow(),
                    status="OPEN"
                )
                db.add(new_pos)
                logger.info(f"New position detected: {trader.address} {api_pos['side']} {api_pos['coin']}")
        
        # Close positions that are no longer open
        for (coin, side), pos in existing_map.items():
            if (coin, side) not in seen_positions:
                pos.status = "CLOSED"
                pos.closed_at = datetime.utcnow()
                # TODO: Get actual close price and realized PnL from fills
                logger.info(f"Position closed: {trader.address} {side} {coin}")
    
    def get_top_losers(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Get top losing traders based on 30-day performance."""
        try:
            with get_db() as db:
                # Query using the view we created
                query = db.execute(
                    """
                    SELECT 
                        t.id,
                        t.address,
                        v.avg_pnl_percentage,
                        v.total_pnl,
                        v.avg_win_rate,
                        v.total_trades,
                        v.loss_rank
                    FROM v_top_losers v
                    JOIN traders t ON t.id = v.id
                    LIMIT :limit
                    """,
                    {"limit": limit}
                )
                
                results = []
                for row in query:
                    results.append({
                        "id": row[0],
                        "address": row[1],
                        "pnl_percentage": float(row[2]) if row[2] else 0,
                        "total_pnl": float(row[3]) if row[3] else 0,
                        "win_rate": float(row[4]) if row[4] else 0,
                        "total_trades": row[5] or 0,
                        "rank": row[6]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting top losers: {e}")
            return []
    
    def discover_traders_from_leaderboard(self) -> List[str]:
        """Discover trader addresses from various sources."""
        # TODO: Implement leaderboard scraping or API calls
        # For now, return empty list - can be expanded later
        logger.warning("Trader discovery not yet implemented")
        return []