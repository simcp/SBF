import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from hyperliquid.info import Info
from hyperliquid.utils import constants
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class HyperliquidAPI:
    """Wrapper for Hyperliquid API with error handling and rate limiting."""
    
    def __init__(self):
        self.env = os.getenv("HYPERLIQUID_ENV", "mainnet")
        self.api_url = (
            constants.MAINNET_API_URL if self.env == "mainnet" 
            else constants.TESTNET_API_URL
        )
        self.info = Info(self.api_url, skip_ws=True)
        logger.info(f"Initialized HyperliquidAPI for {self.env}")
    
    def get_user_state(self, address: str) -> Optional[Dict[str, Any]]:
        """Get current state for a user including positions and account value."""
        try:
            state = self.info.user_state(address)
            return state
        except Exception as e:
            logger.error(f"Error getting user state for {address}: {e}")
            return None
    
    def get_user_fills(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent fills (trades) for a user."""
        try:
            # Get fills for the user
            fills = self.info.user_fills(address)
            return fills[:limit] if fills else []
        except Exception as e:
            logger.error(f"Error getting fills for {address}: {e}")
            return []
    
    def get_clearinghouse_state(self, address: str) -> Optional[Dict[str, Any]]:
        """Get clearinghouse state including margin and liquidation info."""
        try:
            state = self.info.clearinghouse_state(address)
            return state
        except Exception as e:
            logger.error(f"Error getting clearinghouse state for {address}: {e}")
            return None
    
    def get_all_mids(self) -> Dict[str, float]:
        """Get mid prices for all trading pairs."""
        try:
            return self.info.all_mids()
        except Exception as e:
            logger.error(f"Error getting mid prices: {e}")
            return {}
    
    def get_meta(self) -> Dict[str, Any]:
        """Get exchange metadata including available coins."""
        try:
            return self.info.meta()
        except Exception as e:
            logger.error(f"Error getting exchange metadata: {e}")
            return {}
    
    def calculate_trader_performance(self, address: str, days: int = 30) -> Dict[str, Any]:
        """Calculate trader performance metrics over specified days."""
        try:
            # Get user fills
            fills = self.get_user_fills(address, limit=1000)
            if not fills:
                return self._empty_performance_metrics()
            
            # Filter fills by date
            cutoff_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
            recent_fills = [f for f in fills if f.get("time", 0) > cutoff_time]
            
            if not recent_fills:
                return self._empty_performance_metrics()
            
            # Calculate metrics
            total_trades = len(recent_fills)
            total_pnl = sum(Decimal(str(f.get("closedPnl", 0))) for f in recent_fills)
            
            # Separate winning and losing trades
            winning_trades = [f for f in recent_fills if Decimal(str(f.get("closedPnl", 0))) > 0]
            losing_trades = [f for f in recent_fills if Decimal(str(f.get("closedPnl", 0))) < 0]
            
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            
            avg_win = (
                sum(Decimal(str(f.get("closedPnl", 0))) for f in winning_trades) / len(winning_trades)
                if winning_trades else Decimal(0)
            )
            avg_loss = (
                sum(Decimal(str(f.get("closedPnl", 0))) for f in losing_trades) / len(losing_trades)
                if losing_trades else Decimal(0)
            )
            
            # Get current account value
            user_state = self.get_user_state(address)
            account_value = Decimal(str(user_state.get("marginSummary", {}).get("accountValue", 0))) if user_state else Decimal(0)
            
            # Calculate PnL percentage (approximate)
            pnl_percentage = (total_pnl / account_value * 100) if account_value > 0 else 0
            
            return {
                "pnl_absolute": float(total_pnl),
                "pnl_percentage": float(pnl_percentage),
                "win_rate": float(win_rate),
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "avg_win": float(avg_win),
                "avg_loss": float(avg_loss),
                "account_value": float(account_value)
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance for {address}: {e}")
            return self._empty_performance_metrics()
    
    def _empty_performance_metrics(self) -> Dict[str, Any]:
        """Return empty performance metrics structure."""
        return {
            "pnl_absolute": 0.0,
            "pnl_percentage": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "account_value": 0.0
        }
    
    def get_recent_fill_hash(self, address: str, coin: str, side: str, limit: int = 20) -> Optional[str]:
        """Get the most recent transaction hash for a position opening."""
        try:
            fills = self.get_user_fills(address, limit=limit)
            
            # Look for recent fills that opened positions for this coin and side
            for fill in fills:
                if (fill.get("coin") == coin and 
                    fill.get("hash") and 
                    fill.get("hash") != "0x0000000000000000000000000000000000000000000000000000000000000000"):
                    
                    # Check if this fill opened a position in the direction we're looking for
                    fill_dir = fill.get("dir", "")
                    
                    # For LONG positions, look for "Open Long" or buys that increase long position
                    # For SHORT positions, look for "Open Short" or sells that increase short position
                    if side == "LONG":
                        if ("Open Long" in fill_dir or 
                            (fill.get("side") == "B" and "Close" not in fill_dir)):
                            return fill.get("hash")
                    elif side == "SHORT":
                        if ("Open Short" in fill_dir or 
                            (fill.get("side") == "A" and "Close" not in fill_dir)):
                            return fill.get("hash")
            
            return None
        except Exception as e:
            logger.error(f"Error getting recent fill hash for {address}: {e}")
            return None
    
    def get_open_positions(self, address: str) -> List[Dict[str, Any]]:
        """Get current open positions for a trader."""
        try:
            user_state = self.get_user_state(address)
            if not user_state:
                return []
            
            positions = []
            asset_positions = user_state.get("assetPositions", [])
            
            for asset_pos in asset_positions:
                pos = asset_pos.get("position", {})
                if pos and Decimal(str(pos.get("szi", 0))) != 0:  # Has open position
                    positions.append({
                        "coin": pos.get("coin"),
                        "side": "LONG" if Decimal(str(pos.get("szi", 0))) > 0 else "SHORT",
                        "size": abs(Decimal(str(pos.get("szi", 0)))),
                        "entry_price": Decimal(str(pos.get("entryPx", 0))),
                        "position_value": Decimal(str(pos.get("positionValue", 0))),
                        "unrealized_pnl": Decimal(str(pos.get("unrealizedPnl", 0))),
                        "return_on_equity": Decimal(str(pos.get("returnOnEquity", 0))),
                        "leverage": asset_pos.get("leverage", {}).get("value", 1),
                        "liquidation_price": Decimal(str(pos.get("liquidationPx", 0))) if pos.get("liquidationPx") else None,
                        "margin_used": Decimal(str(pos.get("marginUsed", 0))) if pos.get("marginUsed") else None
                    })
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions for {address}: {e}")
            return []