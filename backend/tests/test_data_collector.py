import pytest
from datetime import datetime, date
from decimal import Decimal
from backend.services.data_collector import DataCollector
from backend.models import Trader, TraderPerformance, Position


def test_data_collector_init():
    """Test DataCollector initialization."""
    collector = DataCollector()
    assert collector is not None
    assert hasattr(collector, 'api')


def test_get_or_create_trader_new(test_db):
    """Test creating a new trader."""
    collector = DataCollector()
    
    # Create new trader
    trader = collector._get_or_create_trader(test_db, "0xnew123")
    
    assert trader is not None
    assert trader.address == "0xnew123"
    assert trader.is_active is True
    
    # Verify it was saved
    saved_trader = test_db.query(Trader).filter_by(address="0xnew123").first()
    assert saved_trader is not None
    assert saved_trader.id == trader.id


def test_get_or_create_trader_existing(test_db, sample_trader):
    """Test getting an existing trader."""
    collector = DataCollector()
    
    # Get existing trader
    trader = collector._get_or_create_trader(test_db, sample_trader.address)
    
    assert trader is not None
    assert trader.id == sample_trader.id
    assert trader.address == sample_trader.address


def test_update_trader_performance(test_db, sample_trader, mock_hyperliquid_api):
    """Test updating trader performance."""
    collector = DataCollector()
    
    # Update performance
    collector._update_trader_performance(test_db, sample_trader)
    test_db.commit()
    
    # Check that performance was created
    today = date.today()
    perf = test_db.query(TraderPerformance).filter_by(
        trader_id=sample_trader.id,
        date=today
    ).first()
    
    assert perf is not None
    assert perf.total_trades == 2
    assert perf.winning_trades == 1
    assert perf.losing_trades == 1


def test_update_trader_positions(test_db, sample_trader, mock_hyperliquid_api):
    """Test updating trader positions."""
    collector = DataCollector()
    
    # Update positions
    collector._update_trader_positions(test_db, sample_trader)
    test_db.commit()
    
    # Check that position was created
    positions = test_db.query(Position).filter_by(
        trader_id=sample_trader.id,
        status="OPEN"
    ).all()
    
    assert len(positions) == 1
    assert positions[0].coin == "BTC"
    assert positions[0].side == "LONG"
    assert float(positions[0].size) == 1.0


def test_collect_trader_data(test_db, mock_hyperliquid_api):
    """Test collecting all data for a trader."""
    collector = DataCollector()
    
    # Collect data
    success = collector.collect_trader_data("0xtest123")
    
    assert success is True
    
    # Verify trader was created
    trader = test_db.query(Trader).filter_by(address="0xtest123").first()
    assert trader is not None
    
    # Verify performance was recorded
    perf = test_db.query(TraderPerformance).filter_by(trader_id=trader.id).first()
    assert perf is not None
    
    # Verify positions were recorded
    positions = test_db.query(Position).filter_by(trader_id=trader.id).all()
    assert len(positions) == 1


def test_collect_multiple_traders(test_db, mock_hyperliquid_api):
    """Test collecting data for multiple traders."""
    collector = DataCollector()
    
    addresses = ["0xtest1", "0xtest2", "0xtest3"]
    results = collector.collect_multiple_traders(addresses)
    
    assert len(results) == 3
    assert all(results.values())  # All should succeed
    
    # Verify all traders were created
    for address in addresses:
        trader = test_db.query(Trader).filter_by(address=address).first()
        assert trader is not None


def test_get_top_losers_empty(test_db):
    """Test getting top losers with no data."""
    collector = DataCollector()
    losers = collector.get_top_losers(limit=10)
    
    assert isinstance(losers, list)
    assert len(losers) == 0


def test_get_top_losers_with_data(test_db, sample_loser_trader):
    """Test getting top losers with data."""
    collector = DataCollector()
    
    # Need to create the view manually for SQLite
    test_db.execute("""
        CREATE VIEW v_top_losers AS
        SELECT 
            t.id,
            t.address,
            AVG(tp.pnl_percentage) as avg_pnl_percentage,
            SUM(tp.pnl_absolute) as total_pnl,
            AVG(tp.win_rate) as avg_win_rate,
            SUM(tp.total_trades) as total_trades,
            1 as loss_rank
        FROM traders t
        JOIN trader_performance tp ON t.id = tp.trader_id
        WHERE tp.date >= date('now', '-30 days')
        GROUP BY t.id, t.address
        HAVING AVG(tp.pnl_percentage) < 0
        ORDER BY AVG(tp.pnl_percentage) ASC
        LIMIT 500
    """)
    test_db.commit()
    
    losers = collector.get_top_losers(limit=10)
    
    assert isinstance(losers, list)
    assert len(losers) == 1
    assert losers[0]["address"] == sample_loser_trader.address
    assert losers[0]["pnl_percentage"] == -85.5
    assert losers[0]["win_rate"] == 15.0


def test_position_closing(test_db, sample_trader, sample_position, mock_hyperliquid_api):
    """Test that positions are closed when no longer open."""
    collector = DataCollector()
    
    # Modify mock to return no positions
    class MockInfoEmpty:
        def user_state(self, address):
            return {
                "marginSummary": {"accountValue": "10000.0"},
                "assetPositions": []  # No positions
            }
    
    collector.api.info = MockInfoEmpty()
    
    # Update positions - should close the existing one
    collector._update_trader_positions(test_db, sample_trader)
    test_db.commit()
    
    # Verify position was closed
    test_db.refresh(sample_position)
    assert sample_position.status == "CLOSED"
    assert sample_position.closed_at is not None