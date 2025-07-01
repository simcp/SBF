import pytest
from decimal import Decimal
from backend.services.hyperliquid_api import HyperliquidAPI


def test_hyperliquid_api_init(mock_hyperliquid_api):
    """Test HyperliquidAPI initialization."""
    api = HyperliquidAPI()
    assert api is not None
    assert hasattr(api, 'info')


def test_get_user_state(mock_hyperliquid_api):
    """Test getting user state."""
    api = HyperliquidAPI()
    state = api.get_user_state("0x123")
    
    assert state is not None
    assert "marginSummary" in state
    assert "assetPositions" in state
    assert state["marginSummary"]["accountValue"] == "10000.0"


def test_get_user_fills(mock_hyperliquid_api):
    """Test getting user fills."""
    api = HyperliquidAPI()
    fills = api.get_user_fills("0x123", limit=10)
    
    assert isinstance(fills, list)
    assert len(fills) == 2
    assert fills[0]["coin"] == "BTC"
    assert fills[0]["side"] == "B"  # Buy
    assert fills[1]["coin"] == "ETH"
    assert fills[1]["side"] == "S"  # Sell


def test_get_all_mids(mock_hyperliquid_api):
    """Test getting mid prices."""
    api = HyperliquidAPI()
    mids = api.get_all_mids()
    
    assert isinstance(mids, dict)
    assert mids["BTC"] == 50500.0
    assert mids["ETH"] == 3100.0
    assert mids["SOL"] == 100.0


def test_calculate_trader_performance(mock_hyperliquid_api):
    """Test calculating trader performance."""
    api = HyperliquidAPI()
    performance = api.calculate_trader_performance("0x123", days=30)
    
    assert isinstance(performance, dict)
    assert "pnl_absolute" in performance
    assert "pnl_percentage" in performance
    assert "win_rate" in performance
    assert "total_trades" in performance
    assert performance["total_trades"] == 2
    assert performance["winning_trades"] == 1
    assert performance["losing_trades"] == 1


def test_get_open_positions(mock_hyperliquid_api):
    """Test getting open positions."""
    api = HyperliquidAPI()
    positions = api.get_open_positions("0x123")
    
    assert isinstance(positions, list)
    assert len(positions) == 1
    assert positions[0]["coin"] == "BTC"
    assert positions[0]["side"] == "LONG"
    assert positions[0]["size"] == Decimal("1.0")
    assert positions[0]["entry_price"] == Decimal("50000.0")
    assert positions[0]["unrealized_pnl"] == Decimal("500.0")


def test_empty_performance_metrics(mock_hyperliquid_api):
    """Test empty performance metrics structure."""
    api = HyperliquidAPI()
    empty_metrics = api._empty_performance_metrics()
    
    assert isinstance(empty_metrics, dict)
    assert empty_metrics["pnl_absolute"] == 0.0
    assert empty_metrics["pnl_percentage"] == 0.0
    assert empty_metrics["win_rate"] == 0.0
    assert empty_metrics["total_trades"] == 0
    assert empty_metrics["winning_trades"] == 0
    assert empty_metrics["losing_trades"] == 0