import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from backend.services.analyzer import TradingAnalyzer
from backend.models import Position, TradeOpportunity, TraderPerformance
from sqlalchemy import text


def test_analyzer_init():
    """Test TradingAnalyzer initialization."""
    analyzer = TradingAnalyzer()
    assert analyzer is not None
    assert analyzer.confidence_threshold == 70.0


def test_calculate_confidence_score():
    """Test confidence score calculation."""
    analyzer = TradingAnalyzer()
    
    # Test with bad trader metrics
    bad_metrics = {
        "avg_pnl_percentage": -80.0,
        "avg_win_rate": 20.0,
        "total_trades": 100,
        "total_losing_trades": 80
    }
    confidence = analyzer._calculate_confidence_score(bad_metrics)
    assert confidence >= 70  # Should be high confidence for bad trader
    
    # Test with mediocre trader
    mediocre_metrics = {
        "avg_pnl_percentage": -20.0,
        "avg_win_rate": 45.0,
        "total_trades": 50,
        "total_losing_trades": 27
    }
    confidence = analyzer._calculate_confidence_score(mediocre_metrics)
    assert confidence < 70  # Should be lower confidence
    
    # Test with extreme loser
    extreme_metrics = {
        "avg_pnl_percentage": -90.0,
        "avg_win_rate": 10.0,
        "total_trades": 200,
        "total_losing_trades": 180
    }
    confidence = analyzer._calculate_confidence_score(extreme_metrics)
    assert confidence >= 90  # Should be very high confidence


def test_get_recent_positions(test_db, sample_trader, sample_position):
    """Test getting recent positions."""
    analyzer = TradingAnalyzer()
    
    # Get recent positions
    recent = analyzer._get_recent_positions(test_db, hours=1)
    assert len(recent) == 1
    assert recent[0].id == sample_position.id
    
    # Test with older position
    sample_position.opened_at = datetime.utcnow() - timedelta(hours=2)
    test_db.commit()
    
    recent = analyzer._get_recent_positions(test_db, hours=1)
    assert len(recent) == 0


def test_analyze_position(test_db, sample_loser_trader, mock_hyperliquid_api):
    """Test analyzing a single position."""
    analyzer = TradingAnalyzer()
    
    # Create a position for the loser trader
    position = Position(
        trader_id=sample_loser_trader.id,
        coin="BTC",
        side="LONG",
        entry_price=Decimal("50000"),
        size=Decimal("1.0"),
        opened_at=datetime.utcnow(),
        status="OPEN"
    )
    test_db.add(position)
    test_db.commit()
    
    # Analyze the position
    opportunity = analyzer._analyze_position(test_db, position)
    
    assert opportunity is not None
    assert opportunity.coin == "BTC"
    assert opportunity.loser_side == "LONG"
    assert opportunity.suggested_side == "SHORT"
    assert float(opportunity.confidence_score) >= 70


def test_analyze_new_positions(test_db, sample_loser_trader, mock_hyperliquid_api):
    """Test analyzing new positions and generating opportunities."""
    analyzer = TradingAnalyzer()
    
    # Create multiple positions
    positions = [
        Position(
            trader_id=sample_loser_trader.id,
            coin="BTC",
            side="LONG",
            entry_price=Decimal("50000"),
            size=Decimal("1.0"),
            opened_at=datetime.utcnow(),
            status="OPEN"
        ),
        Position(
            trader_id=sample_loser_trader.id,
            coin="ETH",
            side="SHORT",
            entry_price=Decimal("3000"),
            size=Decimal("10.0"),
            opened_at=datetime.utcnow(),
            status="OPEN"
        )
    ]
    for pos in positions:
        test_db.add(pos)
    test_db.commit()
    
    # Need to use contextmanager for get_db in analyzer
    with test_db.bind.begin() as conn:
        # Patch get_db to return our test session
        import backend.database.connection
        original_get_db = backend.database.connection.get_db
        
        def mock_get_db():
            yield test_db
        
        backend.database.connection.get_db = mock_get_db
        
        try:
            # Analyze positions
            opportunities = analyzer.analyze_new_positions()
            
            assert len(opportunities) == 2
            assert opportunities[0].coin == "BTC"
            assert opportunities[0].suggested_side == "SHORT"
            assert opportunities[1].coin == "ETH"
            assert opportunities[1].suggested_side == "LONG"
        finally:
            backend.database.connection.get_db = original_get_db


def test_get_active_opportunities(test_db, sample_trader, sample_position):
    """Test getting active opportunities."""
    analyzer = TradingAnalyzer()
    
    # Create an opportunity
    opportunity = TradeOpportunity(
        position_id=sample_position.id,
        trader_id=sample_trader.id,
        coin="BTC",
        loser_side="LONG",
        suggested_side="SHORT",
        loser_entry_price=Decimal("50000"),
        confidence_score=Decimal("85"),
        status="ACTIVE"
    )
    test_db.add(opportunity)
    test_db.commit()
    
    # Patch get_db
    import backend.database.connection
    original_get_db = backend.database.connection.get_db
    
    def mock_get_db():
        yield test_db
    
    backend.database.connection.get_db = mock_get_db
    
    try:
        # Get active opportunities
        active = analyzer.get_active_opportunities()
        
        assert len(active) == 1
        assert active[0]["coin"] == "BTC"
        assert active[0]["loser_side"] == "LONG"
        assert active[0]["suggested_side"] == "SHORT"
        assert active[0]["confidence_score"] == 85.0
    finally:
        backend.database.connection.get_db = original_get_db


def test_expire_old_opportunities(test_db, sample_trader, sample_position):
    """Test expiring old opportunities."""
    analyzer = TradingAnalyzer()
    
    # Create old opportunity
    old_opportunity = TradeOpportunity(
        position_id=sample_position.id,
        trader_id=sample_trader.id,
        coin="BTC",
        loser_side="LONG",
        suggested_side="SHORT",
        loser_entry_price=Decimal("50000"),
        confidence_score=Decimal("85"),
        status="ACTIVE",
        created_at=datetime.utcnow() - timedelta(hours=25)
    )
    test_db.add(old_opportunity)
    
    # Create recent opportunity
    recent_opportunity = TradeOpportunity(
        position_id=sample_position.id,
        trader_id=sample_trader.id,
        coin="ETH",
        loser_side="SHORT",
        suggested_side="LONG",
        loser_entry_price=Decimal("3000"),
        confidence_score=Decimal("80"),
        status="ACTIVE"
    )
    test_db.add(recent_opportunity)
    test_db.commit()
    
    # Patch get_db
    import backend.database.connection
    original_get_db = backend.database.connection.get_db
    
    def mock_get_db():
        yield test_db
    
    backend.database.connection.get_db = mock_get_db
    
    try:
        # Expire old opportunities
        analyzer.expire_old_opportunities(hours=24)
        
        # Check results
        test_db.refresh(old_opportunity)
        test_db.refresh(recent_opportunity)
        
        assert old_opportunity.status == "EXPIRED"
        assert old_opportunity.expired_at is not None
        assert recent_opportunity.status == "ACTIVE"
        assert recent_opportunity.expired_at is None
    finally:
        backend.database.connection.get_db = original_get_db