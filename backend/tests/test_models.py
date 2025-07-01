import pytest
from datetime import datetime
from decimal import Decimal
from backend.models import Trader, TraderPerformance, Position, TradeOpportunity


def test_trader_model(test_db):
    """Test Trader model."""
    trader = Trader(
        address="0x1234567890123456789012345678901234567890"
    )
    test_db.add(trader)
    test_db.commit()
    
    assert trader.id is not None
    assert trader.address == "0x1234567890123456789012345678901234567890"
    assert trader.is_active is True
    assert trader.short_address == "0x1234...7890"


def test_trader_performance_model(test_db, sample_trader):
    """Test TraderPerformance model."""
    perf = TraderPerformance(
        trader_id=sample_trader.id,
        date=datetime.utcnow().date(),
        pnl_percentage=Decimal("-50.5"),
        pnl_absolute=Decimal("-1000"),
        win_rate=Decimal("25.0"),
        total_trades=100,
        winning_trades=25,
        losing_trades=75
    )
    test_db.add(perf)
    test_db.commit()
    
    assert perf.id is not None
    assert perf.trader_id == sample_trader.id
    assert perf.is_profitable is False
    assert float(perf.pnl_percentage) == -50.5


def test_position_model(test_db, sample_trader):
    """Test Position model."""
    position = Position(
        trader_id=sample_trader.id,
        coin="BTC",
        side="LONG",
        entry_price=Decimal("50000"),
        size=Decimal("1.0"),
        opened_at=datetime.utcnow()
    )
    test_db.add(position)
    test_db.commit()
    
    assert position.id is not None
    assert position.is_open is True
    assert position.opposite_side == "SHORT"
    assert position.status == "OPEN"


def test_trade_opportunity_model(test_db, sample_trader, sample_position):
    """Test TradeOpportunity model."""
    opportunity = TradeOpportunity(
        position_id=sample_position.id,
        trader_id=sample_trader.id,
        coin="BTC",
        loser_side="LONG",
        suggested_side="SHORT",
        loser_entry_price=Decimal("50000"),
        confidence_score=Decimal("85.5")
    )
    test_db.add(opportunity)
    test_db.commit()
    
    assert opportunity.id is not None
    assert opportunity.is_active is True
    assert float(opportunity.confidence_score) == 85.5


def test_model_relationships(test_db, sample_trader):
    """Test model relationships."""
    # Add performance record
    perf = TraderPerformance(
        trader_id=sample_trader.id,
        date=datetime.utcnow().date(),
        pnl_percentage=Decimal("-50")
    )
    test_db.add(perf)
    
    # Add position
    position = Position(
        trader_id=sample_trader.id,
        coin="ETH",
        side="SHORT",
        entry_price=Decimal("3000"),
        size=Decimal("10"),
        opened_at=datetime.utcnow()
    )
    test_db.add(position)
    test_db.commit()
    
    # Refresh to load relationships
    test_db.refresh(sample_trader)
    
    assert len(sample_trader.performance_history) == 1
    assert len(sample_trader.positions) == 1
    assert sample_trader.performance_history[0].pnl_percentage == Decimal("-50")
    assert sample_trader.positions[0].coin == "ETH"