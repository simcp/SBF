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
                # Get transaction hash for new position
                tx_hash = self.api.get_recent_fill_hash(
                    trader.address, 
                    api_pos["coin"], 
                    api_pos["side"]
                )
                
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
                    transaction_hash=tx_hash,
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
        logger.info(f"get_top_losers called with limit={limit}")
        try:
            with get_db() as db:
                logger.info("Database connection established")
                
                # First, let's check if we have any traders at all
                trader_count = db.query(Trader).count()
                perf_count = db.query(TraderPerformance).count()
                logger.info(f"Database has {trader_count} traders and {perf_count} performance records")
                
                # Query traders and their performance directly using SQLAlchemy ORM
                from sqlalchemy import text
                logger.info("Executing SQL query for top losers")
                
                query = db.execute(
                    text("""
                    SELECT 
                        t.id,
                        t.address,
                        tp.pnl_percentage,
                        tp.pnl_absolute,
                        tp.account_value,
                        tp.win_rate,
                        tp.total_trades
                    FROM traders t
                    JOIN trader_performance tp ON t.id = tp.trader_id
                    WHERE tp.pnl_percentage < 0
                    ORDER BY tp.pnl_percentage ASC
                    LIMIT :limit
                    """),
                    {"limit": limit}
                )
                
                logger.info("SQL query executed successfully")
                
                results = []
                row_count = 0
                for row in query:
                    row_count += 1
                    pnl_percent = float(row[2]) if row[2] else 0
                    account_value = float(row[4]) if row[4] else 0
                    
                    result = {
                        "id": row[0],
                        "address": row[1],
                        "roi_30d_percent": pnl_percent,
                        "pnl_30d": float(row[3]) if row[3] else 0,
                        "account_value": account_value,
                        "win_rate": float(row[5]) if row[5] else 0,
                        "total_trades": row[6] or 0,
                        # Formatted display strings (ready for frontend)
                        "formatted_pnl": f"{pnl_percent:.2f}%" if pnl_percent < 0 else f"+{pnl_percent:.2f}%",
                        "formatted_account_value": self._format_currency(account_value),
                        "explorer_url": f"https://app.hyperliquid.xyz/explorer/address/{row[1]}"
                    }
                    results.append(result)
                
                logger.info(f"Processed {row_count} rows, returning {len(results)} results")
                logger.info(f"First result: {results[0] if results else 'No results'}")
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting top losers: {e}", exc_info=True)
            return []
    
    def _format_currency(self, amount):
        """Format currency amount for display."""
        if amount is None:
            return "$0"
        amount = float(amount)
        if abs(amount) >= 1000000:
            return f"${(amount / 1000000):.1f}M"
        if abs(amount) >= 1000:
            return f"${(amount / 1000):.1f}K"
        return f"${amount:.0f}"
    
    def discover_traders_from_leaderboard(self) -> List[str]:
        """Discover trader addresses from various sources."""
        # TODO: Implement leaderboard scraping or API calls
        # For now, return empty list - can be expanded later
        logger.warning("Trader discovery not yet implemented")
        return []